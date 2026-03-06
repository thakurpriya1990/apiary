import json

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import View, TemplateView
from disturbance.components.proposals.models import Proposal, Referral, ProposalType
from disturbance.components.approvals.models import Approval
from disturbance.components.compliances.models import Compliance
from disturbance.components.organisations.models import Organisation
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from disturbance.helpers import is_internal, is_in_organisation_contacts

from reversion.models import Version
from reversion_compare.views import HistoryCompareDetailView

from django.contrib.auth.mixins import UserPassesTestMixin


class InternalHistoryCompareDetailView(UserPassesTestMixin, HistoryCompareDetailView):

    def _get_action_list(self):
        action_list = [
            {"version": version, "revision": version.revision}
            for version in self._order_version_queryset(
                Version.objects.get_for_object(self.get_object()).select_related("revision")
            )
        ]
        return action_list

    def test_func(self):
        return is_internal(self.request)

class ProposalHistoryCompareView(InternalHistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = Proposal
    template_name = 'disturbance/reversion_history.html'

#TODO on-cleanup - this does not appear to do anything more than the other history views
class ProposalHistoryLatestCompareView(InternalHistoryCompareDetailView):
    """
    View for reversion_compare that returns on the x most recent revisions
    """
    model = Proposal
    template_name = 'disturbance/reversion_history.html'

class ProposalFilteredHistoryCompareView(InternalHistoryCompareDetailView):
    """
    View for reversion_compare - with 'status' in the comment field only'
    """

    model = Proposal
    template_name = 'disturbance/reversion_history.html'

    def _get_action_list(self,):
        """ Get only versions when processing_status changed, and add the most recent (current) version """
        try:
            current_revision_id = Version.objects.get_for_object(self.get_object()).first().revision_id 
            action_list = [
                {"version": version, "revision": version.revision}
                for version in self._order_version_queryset(
                    Version.objects.get_for_object(self.get_object()).select_related("revision").filter(Q(revision__comment__icontains='status') | Q(revision_id=current_revision_id))
                )
            ]
            return action_list
        except:
            return []

class ReferralHistoryCompareView(InternalHistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = Referral
    template_name = 'disturbance/reversion_history.html'

class ExternalProposalTemporaryUseSubmitSuccessView(TemplateView):
    model = Proposal
    template_name = 'disturbance/temporary_use_submit_success.html'

    def post(self, request, *args, **kwargs):

        proposal_id = kwargs['proposal_pk']
        p = Proposal.objects.get(id=proposal_id)

        if p.relevant_applicant_type == 'organisation':
            organisation = p.applicant
            if not self.check_owner(organisation):
                raise PermissionDenied
        else:
            if not self.check_individual_owner(p):
                raise PermissionDenied

        return render(request, self.template_name, context={'modified_date': p.modified_date})

    def check_owner(self, organisation):
        return is_in_organisation_contacts(self.request, organisation) or is_internal(self.request) or self.request.user.is_superuser

    def check_individual_owner(self,proposal):
        if not self.request or not self.request.user:
            return False

        return (
            proposal.proxy_applicant == self.request.user if proposal.relevant_applicant_type == 'proxy' else proposal.submitter == self.request.user
        ) or is_internal(self.request) or self.request.user.is_superuser

class ApprovalHistoryCompareView(InternalHistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = Approval
    template_name = 'disturbance/reversion_history.html'

class ComplianceHistoryCompareView(InternalHistoryCompareDetailView):
    """
    View for reversion_compare
    """
    model = Compliance
    template_name = 'disturbance/reversion_history.html'


class PreviewLicencePDFView(View):
    def post(self, request, *args, **kwargs):
        if is_internal(request):
            response = HttpResponse(content_type='application/pdf')
            proposal = self.get_object()
            details = json.loads(request.POST.get('formData'))
            response.content = proposal.preview_approval(request, details)
            return response
        else:
            raise PermissionDenied

    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs['proposal_pk'])
