import logging
from urllib.parse import unquote
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from rest_framework import views
import requests
from disturbance.components.main.models import ApiaryGlobalSettings

logger = logging.getLogger(__name__)


@api_view(['GET'],)
def deed_poll_url(request):
    deed_poll_url = ApiaryGlobalSettings.objects.get(key=ApiaryGlobalSettings.KEY_PRINT_DEED_POLL_URL)
    return Response(deed_poll_url.value)

class GeocodingAddressSearchView(views.APIView):

    def get(self, request, format=None):
        search_term = request.GET.get('search_term') if 'search_term' in request.GET else None
        country = request.GET.get('country') if 'country' in request.GET else 'au'
        limit = request.GET.get('limit') if 'limit' in request.GET else '10'
        bbox = request.GET.get('bbox') if 'bbox' in request.GET else '112.920934,-35.191991,129.0019283,-11.9662455'
        types = request.GET.get('types') if 'types' in request.GET else 'region,postcode,district,place,locality,neighborhood,address,poi'
        proximity = request.GET.get('proximity') if 'proximity' in request.GET else  '115.83984375000001,-31.952162238024975'
        if not search_term:
            # after /api/geocoding_address_search/ instead of as ?search_term=...
            path_prefix = '/api/geocoding_address_search/'
            if request.path.startswith(path_prefix):
                # Remove known prefix and any leading/trailing slashes.
                path_suffix = request.path[len(path_prefix):].strip('/')
                # Trim Django/DRF style format suffix (e.g. .json) if present.
                if path_suffix.endswith('.json'):
                    path_suffix = path_suffix[:-5]
                if path_suffix:
                    # Decode URL-encoded text so "main%20st" becomes "main st".
                    search_term = unquote(path_suffix)

        if search_term and request.user.is_authenticated:
            access_token = settings.GEOCODING_ADDRESS_SEARCH_TOKEN
            if not access_token or access_token == 'ACCESS_TOKEN_NOT_FOUND':
                return Response({'detail': 'Geocoding token is not configured.'}, status=503)

            search_url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{}.json/?access_token={}&country={}&limit={}&bbox={}&types={}&proximity={}".format(
                search_term,access_token,country,limit,bbox,types,proximity
            )
            try:
                r = requests.get(search_url, timeout=15)
                response_json = r.json()
                return Response(response_json, status=r.status_code)
            except requests.RequestException:
                return Response({'detail': 'Geocoding service request failed.'}, status=502)
        else:
            return Response()