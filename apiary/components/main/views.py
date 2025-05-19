import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from rest_framework import views

from apiary.components.main.models import ApiaryGlobalSettings

logger = logging.getLogger(__name__)


@api_view(['GET'],)
def deed_poll_url(request):
    deed_poll_url = ApiaryGlobalSettings.objects.get(key=ApiaryGlobalSettings.KEY_PRINT_DEED_POLL_URL)
    return Response(deed_poll_url.value)


class GeocodingAddressSearchTokenView(views.APIView):
    def get(self, request, format=None):
        return Response({"access_token": settings.GEOCODING_ADDRESS_SEARCH_TOKEN})
