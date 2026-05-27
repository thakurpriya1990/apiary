import traceback
import datetime
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework import viewsets, serializers, mixins
from rest_framework.decorators import action, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from datetime import datetime

from disturbance.components.approvals.models import (
    Approval, ApprovalUserAction, ApprovalDocument,
)
from disturbance.components.approvals.serializers import (
    ApprovalSerializer,
    DTApprovalSerializer,
    ApprovalCancellationSerializer,
    ApprovalSuspensionSerializer,
    ApprovalSurrenderSerializer,
    ApprovalUserActionSerializer,
    ApprovalLogEntrySerializer,
    ApprovalWrapperSerializer,
    ApprovalDocumentHistorySerializer,
)
from disturbance.components.main.decorators import basic_exception_handler
from disturbance.components.proposals.models import OnSiteInformation, Proposal
from disturbance.components.proposals.serializers_apiary import (
        OnSiteInformationSerializer,
        ProposalApiaryTemporaryUseSerializer,
        ApiaryProposalRequirementSerializer,
        )
from disturbance.helpers import is_internal
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from disturbance.components.main.utils import get_template_group, handle_validation_error
from disturbance.components.approvals.utils import annotate_apiary_site_on_approval_geometry
from disturbance.components.approvals.permissions import (
    InternalApprovalPermission,
)

class ApprovalFilterBackend(DatatablesFilterBackend):
    """
    Custom filters
    """

    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()

        def get_choice(status, choices=Approval.STATUS_CHOICES):
            for i in choices:
                if i[1]==status:
                    return i[0]
            return None

        # on the internal dashboard, the Region filter is multi-select - have to use the custom filter below
        region = request.GET.get('region')
        if region and not region.lower() == 'all':
            queryset = queryset.filter(current_proposal__region__name=region)
        proposal_activity = request.GET.get('proposal_activity')
        if proposal_activity and not proposal_activity.lower() == 'all':
            queryset = queryset.filter(current_proposal__activity=proposal_activity)
        approval_status = request.GET.get('approval_status')
        if approval_status and not approval_status.lower() == 'all':
            queryset = queryset.filter(status=get_choice(approval_status))

        start_date_from = request.GET.get('start_date_from')
        start_date_to = request.GET.get('start_date_to')
        if start_date_from:
            queryset = queryset.filter(start_date__gte=start_date_from)
        if start_date_to:
            queryset = queryset.filter(start_date__lte=start_date_to)
        
        expiry_date_from = request.GET.get('expiry_date_from')
        expiry_date_to = request.GET.get('expiry_date_to')
        if expiry_date_from:
            queryset = queryset.filter(expiry_date__gte=expiry_date_from)
        if expiry_date_to:
            queryset = queryset.filter(expiry_date__lte=expiry_date_to)

        fields = self.get_fields(request)
        ordering = self.get_ordering(request, view, fields)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        try:
            queryset = super(ApprovalFilterBackend, self).filter_queryset(request, queryset, view)
        except Exception as e:
            print(e)
        setattr(view, '_datatables_total_count', total_count)
        return queryset


class ApprovalPaginatedViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (ApprovalFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    page_size = 10
    queryset = Approval.objects.none()
    serializer_class = ApprovalSerializer

    def get_queryset(self):
        if is_internal(self.request):
            return Approval.objects.filter(
                    apiary_approval=True
                ).exclude(status='hidden')
        elif self.request.user.is_authenticated:
            user_orgs = [org.id for org in self.request.user.disturbance_organisations.all()]
            queryset =  Approval.objects.filter(
                    apiary_approval=True
                ).filter(Q(applicant_id__in = user_orgs)| Q(proxy_applicant=self.request.user) | Q(proxy_applicant_id=self.request.user.id)).exclude(status='hidden')
            return queryset
        return Approval.objects.none()


    @action(detail=False,methods=['GET',])
    def approvals_external(self, request, *args, **kwargs):
        """
        Paginated serializer for datatables - used by the internal and external dashboard (filtered by the get_queryset method)

        To test:
            http://localhost:8000/api/approval_paginated/approvals_external/?format=datatables&draw=1&length=2
        """

        ids = self.get_queryset().order_by('lodgement_number', '-issue_date').distinct('lodgement_number').values_list('id', flat=True)
        template_group = get_template_group(request)
        qs = self.get_queryset().filter(
                apiary_approval=True
                ).filter(id__in=ids)

        qs = self.filter_queryset(qs)

        # on the internal organisations dashboard, filter the Proposal/Approval/Compliance datatables by applicant/organisation
        applicant_id = request.GET.get('org_id')
        if applicant_id:
            qs = qs.filter(applicant__id=applicant_id)
        submitter_id = request.GET.get('submitter_id', None)
        if submitter_id:
            qs = qs.filter(submitter_id=submitter_id)

        result_page = self.paginator.paginate_queryset(qs, request)
        serializer = DTApprovalSerializer(result_page, context={
            'request':request,
            'template_group': template_group
            }, many=True)
        return self.paginator.get_paginated_response(serializer.data)


class ApprovalViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Approval.objects.none()
    serializer_class = ApprovalSerializer

    def get_queryset(self):
        if is_internal(self.request):
            return Approval.objects.filter(apiary_approval=True)
        elif self.request.user.is_authenticated:
            user_orgs = [org.id for org in self.request.user.disturbance_organisations.all()]
            queryset =  Approval.objects.filter(apiary_approval=True).filter(Q(applicant_id__in = user_orgs)|Q(proxy_applicant_id=self.request.user.id))
            return queryset
        return Approval.objects.none()

    def get_serializer_class(self):
        return ApprovalSerializer

    @action(detail=False,methods=['GET',])
    def filter_list(self, request, *args, **kwargs):
        """ Used by the external dashboard filters """
        region_qs =  self.get_queryset().filter(current_proposal__region__isnull=False).values_list('current_proposal__region__name', flat=True).distinct()
        activity_qs =  self.get_queryset().filter(current_proposal__activity__isnull=False).values_list('current_proposal__activity', flat=True).distinct()
        data = dict(
            regions=region_qs,
            activities=activity_qs,
            approval_status_choices = [i[1] for i in Approval.STATUS_CHOICES],
        )
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        approval = self.get_object()
        serializer = self.get_serializer(approval, context={'request': request})
        res = Response(serializer.data)
        return res

    @action(detail=True,methods=['GET',])
    def approval_wrapper(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_class = ApprovalWrapperSerializer
        serializer = serializer_class(instance)
        res = Response(serializer.data)
        return res

    @action(detail=True,methods=['GET',])
    @basic_exception_handler
    def on_site_information(self, request, *args, **kwargs):
        instance = self.get_object()
        on_site_info_qs = OnSiteInformation.objects.filter(
            apiary_site_on_approval__in=instance.get_relations(),
            datetime_deleted=None
        )
        serializers = OnSiteInformationSerializer(on_site_info_qs, many=True)
        return Response(serializers.data)

    @action(detail=True,methods=['GET',])
    @basic_exception_handler
    def temporary_use(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.proposalapiarytemporaryuse_set
        qs = qs.exclude(proposal__processing_status=Proposal.PROCESSING_STATUS_DISCARDED)
        serializer = ProposalApiaryTemporaryUseSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True,methods=['POST',], permission_classes=[InternalApprovalPermission])
    @basic_exception_handler
    def no_charge_until_date(self, request, *args, **kwargs):
        instance = self.get_object()
        until_date = request.data.get('until_date', None)
        if until_date:
            instance.no_annual_rental_fee_until = datetime.strptime(until_date, '%d/%m/%Y').date()
        else:
            instance.no_annual_rental_fee_until = None
        instance.save()
        instance.log_user_action(ApprovalUserAction.ACTION_UPDATE_NO_CHARGE_DATE_UNTIL.format('' if instance.no_annual_rental_fee_until is None else instance.no_annual_rental_fee_until.strftime('%d/%m/%Y'), instance.id), request)

        return Response({})

    @action(detail=True,methods=['GET',])
    @basic_exception_handler
    def apiary_sites(self, request, *args, **kwargs):
        approval = self.get_object()
        approval_data = annotate_apiary_site_on_approval_geometry(approval.get_relations())
        data = {"features":list(approval_data)}
        return Response(data)

    @action(detail=True,methods=['GET',])
    @basic_exception_handler
    def apiary_site(self, request, *args, **kwargs):
        approval = self.get_object()
        approval_data = annotate_apiary_site_on_approval_geometry(approval.get_relations())
        return Response(list(approval_data))

    @action(detail=True,methods=['POST',], permission_classes=[InternalApprovalPermission])
    @basic_exception_handler
    def approval_cancellation(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ApprovalCancellationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.approval_cancellation(request,serializer.validated_data)
        serializer = ApprovalSerializer(instance,context={'request':request})
        return Response(serializer.data)

    @action(detail=True,methods=['POST',], permission_classes=[InternalApprovalPermission])
    def approval_suspension(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = ApprovalSuspensionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.approval_suspension(request,serializer.validated_data)
            serializer = ApprovalSerializer(instance,context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            handle_validation_error(e)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True,methods=['POST',], permission_classes=[InternalApprovalPermission])
    def approval_reinstate(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.reinstate_approval(request)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            handle_validation_error(e)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True,methods=['POST',])
    def approval_surrender(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = ApprovalSurrenderSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.approval_surrender(request,serializer.validated_data)
            serializer = ApprovalSerializer(instance,context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            handle_validation_error(e)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True,methods=['GET',], permission_classes=[InternalApprovalPermission])
    def approval_pdf_view_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.pdf_view_log(request)
            serializer = ApprovalSerializer(instance,context={'request':request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            handle_validation_error(e)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True,methods=['GET',], permission_classes=[InternalApprovalPermission])
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = ApprovalUserActionSerializer(qs,many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True,methods=['GET',], permission_classes=[InternalApprovalPermission])
    def comms_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.comms_logs.all()
            serializer = ApprovalLogEntrySerializer(qs,many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True,methods=['POST',], permission_classes=[InternalApprovalPermission])
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                request_data = request.data.copy()
                request_data['approval'] = u'{}'.format(instance.id)
                request_data['staff'] = u'{}'.format(request.user.id)
                serializer = ApprovalLogEntrySerializer(data=request_data)
                serializer.is_valid(raise_exception=True)
                comms = serializer.save()
                # Save the files
                for f in request.FILES:
                    document = comms.documents.create(
                            name = str(request.FILES[f]),
                            _file = request.FILES[f]
                            )
                # End Save Documents

                return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=False,methods=['GET',], permission_classes=[InternalApprovalPermission])
    def sti_search(self, request, *args, **kwargs):
        """ Used by the internal users to filter for sti name in ptoposal titlei (for use by external systems) """
        name = request.GET.get('name')
        data = Approval.objects.filter(current_proposal__title__icontains=name).values_list('licence_document___file', flat=True)
        return Response(list(data))

    @action(detail=False,methods=['GET',], permission_classes=[InternalApprovalPermission])
    def sti_unmatched(self, request, *args, **kwargs):
        """ Used by the internal users to filter for sti name in ptoposal titlei (for use by external systems) """

        name = request.GET.get('name')
        data = Approval.objects.filter(current_proposal__title__icontains=name).values_list('licence_document___file', flat=True)

        return Response(list(data))

    @action(detail=True,methods=['GET',])
    def requirements(self, request, *args, **kwargs):
        try:
            approval = self.get_object()
            requirements = []
            for requirement in approval.current_proposal.requirements.all():
                requirements.append(ApiaryProposalRequirementSerializer(requirement).data)
            return Response(requirements)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=False,methods=['GET', ])
    def approval_history(self, request, *args, **kwargs):
        try:
            qs = None
            approval_history_id = request.query_params['approval_history_id']
            return_list = []
            if approval_history_id:
                instance = Approval.objects.get(id=approval_history_id)
                if instance.apiary_approval:
                    qs = instance.documents.all().order_by("-uploaded_date")
                    for item in qs:
                        se = ApprovalDocumentHistorySerializer(item)
                        return_list.append(se.data)
                else:
                    qs=ApprovalDocument.objects.filter(approval__lodgement_number=instance.lodgement_number, name__icontains='approval')
                    qs=qs.order_by("-uploaded_date")
                    for item in qs:
                        se = ApprovalDocumentHistorySerializer(item)
                        return_list.append(se.data)
            return Response(return_list)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))
