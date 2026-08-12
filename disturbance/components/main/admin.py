import requests
import xml.etree.ElementTree as ET
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.contrib import admin
from django.utils.html import format_html
from disturbance.components.main.models import MapLayer, MapColumn, FileExtensionWhitelist


def check_kb_server_status():
    """
    Fetch GetCapabilities and return a tuple: (status_code, layer_names_set)
    status_code: 200 if server is reachable, None/error code if connection failed.
    Caches the result to prevent frequent network requests.
    """
    cache_key_status = "kb_geoserver_status_info"
    cached_info = cache.get(cache_key_status)
    if cached_info:
        return cached_info

    try:
        base_url = (getattr(settings, "KB_SERVER_URL", "") or "").rstrip("/")
        url = f"{base_url}/geoserver/wms?request=GetCapabilities&service=WMS"
        
        auth = None
        if getattr(settings, "KB_USER", None) and getattr(settings, "KB_PASSWORD", None):
            auth = (settings.KB_USER, settings.KB_PASSWORD)

        response = requests.get(url, auth=auth, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            layer_names = set()
            for elem in root.iter():
                if elem.tag.endswith("Layer"):
                    name_elem = elem.find("{*}Name")
                    if name_elem is not None and name_elem.text:
                        layer_names.add(name_elem.text.strip())

            result = (200, layer_names)
            cache.set(cache_key_status, result, 86400)  # Cache for 24 hours on success
            return result
        else:
            result = (response.status_code, set())
            cache.set(cache_key_status, result, 60)  # Cache for 1 minute on HTTP error
            return result
    except Exception:
        result = (None, set())
        cache.set(cache_key_status, result, 60)  # Cache for 1 minute on connection exception
        return result


def get_kb_layer_choices():
    """
    Return a list of (layer_name, layer_name) tuples for the form ChoiceField using cached server status.
    """
    choices = [("", "-- Select a Layer --")]
    status_code, layer_names = check_kb_server_status()
    if status_code == 200:
        sorted_layers = sorted(list(layer_names))
        for name in sorted_layers:
            choices.append((name, name))
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
        layer_choices = get_kb_layer_choices()
        
        # If the current instance's layer_name is not in choices, add it so data is not lost
        current_layer = self.instance.layer_name if self.instance and self.instance.layer_name else None
        existing_keys = [c[0] for c in layer_choices]
        if current_layer and current_layer not in existing_keys:
            layer_choices.append((current_layer, f"{current_layer} (Current / Unlisted)"))

        self.fields["layer_name"].choices = layer_choices

        # Restore original help texts
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
        'server_status',
        'option_for_internal',
        'option_for_external',
        'display_all_columns',
        'column_names',
    ]
    list_filter = ['option_for_internal', 'option_for_external', 'display_all_columns']
    search_fields = ['display_name', 'layer_name', 'columns__name']
    form = MyForm
    inlines = [MapColumnInline]

    actions = ['refresh_server_status']

    @admin.action(description="Force refresh KB GeoServer status cache")
    def refresh_server_status(self, request, queryset):
        """
        Action to clear the cached GetCapabilities and force re-fetching from KB GeoServer.
        """
        cache.delete("kb_geoserver_status_info")
        check_kb_server_status()  # Immediately re-fetch from KB GeoServer
        self.message_user(request, "KB GeoServer status cache refreshed successfully.")

    @admin.display(description="KB Server Status")
    def server_status(self, obj):
        """
        Display status of the layer on the KB GeoServer:
        - Green (Found): Server reachable and layer exists.
        - Red (Not Found): Server reachable but layer does not exist.
        - Yellow (Server Offline): Connection to KB server failed.
        """
        if not obj.layer_name:
            return format_html('<span style="color: gray;">⚪ Empty</span>')

        status_code, layer_names = check_kb_server_status()

        # Connection failed or server error
        if status_code != 200:
            return format_html(
                '<span style="color: orange; font-weight: bold;" title="Could not connect to KB Server">🟡 Server Error ({})</span>',
                status_code if status_code else "Offline"
            )

        # Server connected, check if layer exists
        if obj.layer_name in layer_names:
            return format_html('<span style="color: green; font-weight: bold;">🟢 Found</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">🔴 Not Found</span>')


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
    form = forms.ModelForm