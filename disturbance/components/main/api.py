import traceback
from wsgiref.util import FileWrapper

from django.http.response import HttpResponse
from rest_framework import viewsets, serializers, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from disturbance.components.ap_payments import reports
from disturbance.components.main.models import Region, District, Tenure, ApplicationType, ActivityMatrix, MapLayer
from disturbance.components.main.serializers import (
    RegionSerializer, DistrictSerializer, TenureSerializer,
    ApplicationTypeSerializer, ActivityMatrixSerializer, BookingSettlementReportSerializer, OracleSerializer,
    MapLayerSerializer
)
from django.core.exceptions import ValidationError

from disturbance.components.main.utils import handle_validation_error
from disturbance.helpers import is_internal
from disturbance.components.main.permissions import (
    PaymentOfficerPermission,
)

class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = District.objects.all().order_by('id')
    serializer_class = DistrictSerializer


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.none() 
    serializer_class = RegionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Region.objects.all().order_by('id')
        return Region.objects.none()


class ActivityMatrixViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityMatrix.objects.none()
    serializer_class = ActivityMatrixSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # specific to Disturbance application, so only exposing one record (most recent)
            return [ActivityMatrix.objects.filter(name='Disturbance').order_by('-version').first()]
        return ActivityMatrix.objects.none()


class TenureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tenure.objects.all().order_by('order')
    serializer_class = TenureSerializer


class ApplicationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApplicationType.objects.none()
    serializer_class = ApplicationTypeSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return ApplicationType.objects.order_by('order').filter(visible=True)
        return ApplicationType.objects.none()

    @action(detail=False,methods=['GET',])
    def searchable_application_types(self, request, *args, **kwargs):
        queryset = ApplicationType.objects.order_by('order').filter(visible=True, searchable=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BookingSettlementReportView(views.APIView):
    renderer_classes = (JSONRenderer,)
    permission_classes = [PaymentOfficerPermission]

    def get(self,request,format=None):
        try:
            http_status = status.HTTP_200_OK
            #parse and validate data
            report = None
            data = {
                "date":request.GET.get('date'),
            }
            serializer = BookingSettlementReportSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            filename = 'Booking Settlement Report-{}'.format(str(serializer.validated_data['date']))
            # Generate Report
            report = reports.booking_bpoint_settlement_report(serializer.validated_data['date'])
            if report:
                response = HttpResponse(FileWrapper(report), content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(filename)
                return response
            else:
                raise serializers.ValidationError('No report was generated.')
        except serializers.ValidationError:
            raise
        except Exception as e:
            traceback.print_exc()


class OracleJob(views.APIView):
    renderer_classes = [JSONRenderer]
    permission_classes = [PaymentOfficerPermission]

    def get(self, request, format=None):
        try:
            data = {
                "date":request.GET.get("date"),
                "override": request.GET.get("override")
            }
            serializer = OracleSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            data = {'successful':True}
            return Response(data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            handle_validation_error(e)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e[0]))


class MapLayerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MapLayer.objects.none()
    serializer_class = MapLayerSerializer

    def get_queryset(self):
        user = self.request.user
        if is_internal(self.request):
            return MapLayer.objects.filter(option_for_internal=True)
        elif user.is_authenticated:
            return MapLayer.objects.filter(option_for_external=True)
        return MapLayer.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
