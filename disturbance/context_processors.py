from confy import env
from django.conf import settings
from disturbance.settings import (
    TEMPLATE_GROUP,
    TEMPLATE_HEADER_LOGO,
    TEMPLATE_TITLE,
)
from ledger_api_client.helpers import is_payment_admin
from disturbance.settings import KMI_SERVER_URL
import logging
from ledger_api_client import utils as ledger_api_utils
import hashlib

logger = logging.getLogger(__name__)

def apiary_url(request):
    PUBLIC_URL = 'https://apiary.dbca.wa.gov.au/'
    displayed_system_name = settings.APIARY_SYSTEM_NAME
    support_email = settings.APIARY_SUPPORT_EMAIL

    is_payment_officer = is_payment_admin(request.user)
    lt = ledger_api_utils.get_ledger_totals()

    checkouthash = None
    if 'payment_pk' in request.session:
        checkouthash =  hashlib.sha256(str(request.session["payment_pk"]).encode('utf-8')).hexdigest()

    return {
        "template_group": TEMPLATE_GROUP,
        "template_header_logo": TEMPLATE_HEADER_LOGO,
        "template_title": TEMPLATE_TITLE,
        'DEBUG': settings.DEBUG,
        'TEMPLATE_GROUP': 'apiary',
        'SYSTEM_NAME': settings.SYSTEM_NAME,
        'PUBLIC_URL': PUBLIC_URL,
        'APPLICATION_GROUP': 'apiary',
        'DISPLAYED_SYSTEM_NAME': displayed_system_name,
        'SUPPORT_EMAIL': support_email,
        'is_payment_admin': is_payment_officer,
        'build_tag': settings.BUILD_TAG,
        'KMI_SERVER_URL': KMI_SERVER_URL,
        'ledger_totals': lt,
        'LEDGER_UI_URL': f'{settings.LEDGER_UI_URL}',
        'GIT_COMMIT_HASH' : settings.GIT_COMMIT_HASH,
        "vue3_entry_script": settings.VUE3_ENTRY_SCRIPT,
        'LEDGER_SYSTEM_ID': f'{settings.LEDGER_SYSTEM_ID}',
        'DJANGO_SETTINGS': settings,
    }
