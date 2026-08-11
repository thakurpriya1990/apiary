import requests
import xml.etree.ElementTree as ET
from django import forms
from django.core.cache import cache
from django.forms import ModelForm
from django.contrib import admin
from django.conf import settings
from disturbance.components.main.models import MapLayer, MapColumn, FileExtensionWhitelist
from disturbance.settings import KB_SERVER_URL


# class MyForm(ModelForm):
#     def __init__(self, *args, **kwargs):
#         super(MyForm, self).__init__(*args, **kwargs)
#         self.fields['layer_name'].help_text = "Enter the layer name defined in geoserver (<a href='{}' target='_blank'>GeoServer</a>)<br /><div>Example:</div><span style='padding:1em;'>public:dbca_legislated_lands_and_waters</span>".format(KB_SERVER_URL)
#         self.fields['display_all_columns'].help_text = "When checked, display all the attributes(columns) in the table regardless of the configurations below"
#         self.fields['option_for_internal'].help_text = "When checked, a checkbox for this layer is displayed for the internal user"
#         self.fields['option_for_external'].help_text = "When checked, a checkbox for this layer is displayed for the external user"

def get_kb_layer_choices():
    """
    Fetch GetCapabilities from KB GeoServer and return a list of (layer_name, layer_name) tuples.
    Caches the result to prevent slow Django admin response.
    """
    cache_key = "kb_geoserver_getcapabilities_layers"
    cached_choices = cache.get(cache_key)
    if cached_choices:
        return cached_choices

    choices = [("", "-- Select a Layer --")]
    try:
        # Construct GetCapabilities URL
        base_url = (settings.KB_SERVER_URL or "").rstrip("/")
        url = f"{base_url}/geoserver/wms?request=GetCapabilities&service=WMS"
        
        auth = None
        if getattr(settings, "KB_USER", None) and getattr(settings, "KB_PASSWORD", None):
            auth = (settings.KB_USER, settings.KB_PASSWORD)

        response = requests.get(url, auth=auth, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            # Find all <Name> tags inside <Layer> elements (ignoring XML namespaces)
            layer_names = set()
            for elem in root.iter():
                if elem.tag.endswith("Layer"):
                    name_elem = elem.find("{*}Name")
                    if name_elem is not None and name_elem.text:
                        layer_names.add(name_elem.text.strip())

            # Format choices for Django ChoiceField
            sorted_layers = sorted(list(layer_names))
            for name in sorted_layers:
                choices.append((name, name))

            # Cache the choices for 24 hours (86400 seconds)
            cache.set(cache_key, choices, 86400)
    except Exception as e:
        # Fallback in case of network or XML parsing errors
        pass

    return choices


class MyForm(forms.ModelForm):
    layer_name = forms.ChoiceField(
        choices=[],
        required=False,
        help_text="Select a layer from KB GeoServer GetCapabilities"
    )

    class Meta:
        model = MapLayer
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set choices from cached GetCapabilities
        layer_choices = get_kb_layer_choices()
        
        # If the current instance's layer_name is not in choices, add it so data is not lost
        current_layer = self.instance.layer_name if self.instance and self.instance.layer_name else None
        existing_keys = [c[0] for c in layer_choices]
        if current_layer and current_layer not in existing_keys:
            layer_choices.append((current_layer, f"{current_layer} (Current / Unlisted)"))

        self.fields["layer_name"].choices = layer_choices

        if "display_all_columns" in self.fields:
            self.fields["display_all_columns"].help_text = (
                "When checked, display all the attributes(columns) in the table regardless of the configurations below"
            )
        if "option_for_internal" in self.fields:
            self.fields["option_for_internal"].help_text = (
                "When checked, a checkbox for this layer is displayed for the internal user"
            )
        if "option_for_external" in self.fields:
            self.fields["option_for_external"].help_text = (
                "When checked, a checkbox for this layer is displayed for the external user"
            )


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
    search_fields = ['display_name', 'layer_name', 'columns__name',]
    form = MyForm
    inlines = [MapColumnInline,]


@admin.register(FileExtensionWhitelist)
class FileExtensionWhitelistAdmin(admin.ModelAdmin):
    fields = (
        "name",
        "model",
    )
    list_display = (
        "name",
        "model",
    )
    form = ModelForm