import logging
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

        if search_term and request.user.is_authenticated:
            access_token = settings.GEOCODING_ADDRESS_SEARCH_TOKEN
            search_url = "https://api.mapbox.com/geocoding/v5/mapbox.places/{}.json/?access_token={}&country={}&limit={}&bbox={}&type={}&proximity={}".format(
                search_term,access_token,country,limit,bbox,types,proximity
            )
            try:
                r = requests.get(search_url)
                return Response(r.json())
            except:
                return Response()
        else:
            return Response()