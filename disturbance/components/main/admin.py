from django.contrib import admin
from django.forms import ModelForm

from apiary.components.main.models import MapLayer, MapColumn, RegionDbca, DistrictDbca
from apiary.settings import KMI_SERVER_URL


class MyForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(MyForm, self).__init__(*args, **kwargs)
        self.fields['layer_name'].help_text = "Enter the layer name defined in geoserver (<a href='{}' target='_blank'>GeoServer</a>)<br /><div>Example:</div><span style='padding:1em;'>public:dbca_legislated_lands_and_waters</span>".format(KMI_SERVER_URL)
        self.fields['display_all_columns'].help_text = "When checked, display all the attributes(columns) in the table regardless of the configurations below"
        self.fields['option_for_internal'].help_text = "When checked, a checkbox for this layer is displayed for the internal user"
        self.fields['option_for_external'].help_text = "When checked, a checkbox for this layer is displayed for the external user"


class MapColumnInline(admin.TabularInline):
    model = MapColumn
    extra = 0


@admin.register(MapLayer)
class MapLayerAdmin(admin.ModelAdmin):
    list_display = [
        'display_name',
        'layer_name',
        'option_for_internal',
        'option_for_external',
        'display_all_columns',
        'column_names',
    ]
    list_filter = ['option_for_internal', 'option_for_external', 'display_all_columns',]
    form = MyForm
    inlines = [MapColumnInline,]


# @admin.register(RegionDbca)
# class RegionAdmin(admin.ModelAdmin):
#     list_display = ['id', 'region_name', 'office', 'enabled']
#     list_filter = ['enabled',]
#     readonly_fields = ['region_name', 'office', 'enabled', 'object_id',]
#
#
# @admin.register(DistrictDbca)
# class DistrictAdmin(admin.ModelAdmin):
#     list_display = ['id', 'district_name', 'office', 'enabled']
#     list_filter = ['enabled',]
#     readonly_fields = ['district_name', 'office', 'enabled', 'object_id',]

