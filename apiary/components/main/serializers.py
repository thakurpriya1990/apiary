from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from apiary.components.main.models import CommunicationsLogEntry, Region, District, Tenure, ApplicationType, \
    ActivityMatrix, WaCoast, MapLayer, MapColumn
from ledger.accounts.models import EmailUser


class WaCoastOptimisedSerializer(serializers.ModelSerializer):

    class Meta:
        model = WaCoast
        fields = (
            'id',
            'type',
            # 'source',
            # 'smoothed',
        )


class WaCoastSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = WaCoast
        geo_field = 'wkb_geometry'
        fields = (
            'id',
            'type',
            # 'source',
            # 'smoothed',
        )


class CommunicationLogEntrySerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=EmailUser.objects.all(),required=False)
    documents = serializers.SerializerMethodField()
    class Meta:
        model = CommunicationsLogEntry
        fields = (
            'id',
            'customer',
            'to',
            'fromm',
            'cc',
            'type',
            'reference',
            'subject'
            'text',
            'created',
            'staff',
            'proposal'
            'documents'
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ('id', 'name', 'code')


class RegionSerializer(serializers.ModelSerializer):
    districts = DistrictSerializer(many=True)
    class Meta:
        model = Region
        fields = ('id', 'name', 'forest_region', 'districts')

class ActivityMatrixSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityMatrix
        fields = ('id', 'name', 'description', 'version', 'ordered', 'schema')


#class ActivitySerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Activity
#        #ordering = ('order', 'name')
#        fields = ('id', 'name', 'application_type')


class TenureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenure
        fields = ('id', 'name', 'application_type')


class ApplicationTypeSerializer(serializers.ModelSerializer):
    #regions = RegionSerializer(many=True)
    #activity_app_types = ActivitySerializer(many=True)
    tenure_app_types = TenureSerializer(many=True)

    class Meta:
        model = ApplicationType
        #fields = ('id', 'name', 'activity_app_types', 'tenure_app_types')
        fields = ('id', 'name', 'tenure_app_types', 'domain_used',)


class BookingSettlementReportSerializer(serializers.Serializer):
    date = serializers.DateTimeField(input_formats=['%d/%m/%Y'])


class OracleSerializer(serializers.Serializer):
    date = serializers.DateField(input_formats=['%d/%m/%Y','%Y-%m-%d'])
    override = serializers.BooleanField(default=False)


class MapColumnSerializer(serializers.ModelSerializer):

    class Meta:
        model = MapColumn
        fields = (
            'name',
            'option_for_internal',
            'option_for_external',
        )


class MapLayerSerializer(serializers.ModelSerializer):
    layer_full_name = serializers.SerializerMethodField()
    layer_group_name = serializers.SerializerMethodField()
    layer_name = serializers.SerializerMethodField()
    columns = MapColumnSerializer(many=True)

    class Meta:
        model = MapLayer
        fields = (
            'display_name',
            'layer_full_name',
            'layer_group_name',
            'layer_name',
            'display_all_columns',
            'columns',
        )

    def get_layer_full_name(self, obj):
        return obj.layer_name.strip()

    def get_layer_group_name(self, obj):
        return obj.layer_name.strip().split(':')[0]

    def get_layer_name(self, obj):
        return obj.layer_name.strip().split(':')[1]
