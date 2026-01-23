from django.core.exceptions import ImproperlyConfigured

import sys
import os, hashlib
from confy import env
import json
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BASE_DIR", BASE_DIR)

from ledger_api_client.settings_base import *

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = 'disturbance.urls'
SITE_ID = 1
DEPT_DOMAINS = env('DEPT_DOMAINS', ['dpaw.wa.gov.au', 'dbca.wa.gov.au'])
SUPERVISOR_STOP_CMD = env('SUPERVISOR_STOP_CMD')
SYSTEM_MAINTENANCE_WARNING = env('SYSTEM_MAINTENANCE_WARNING', 24) # hours
DISABLE_EMAIL = env('DISABLE_EMAIL', False)
MEDIA_APP_DIR = env('MEDIA_APP_DIR', 'das')
MEDIA_APIARY_DIR = env('MEDIA_APIARY_DIR', 'apiary')
SPATIAL_DATA_DIR = env('SPATIAL_DATA_DIR', 'spatial_data')
ANNUAL_RENTAL_FEE_GST_EXEMPT = True
FILE_UPLOAD_MAX_MEMORY_SIZE = env('FILE_UPLOAD_MAX_MEMORY_SIZE', 15728640)
APIARY_MIGRATED_LICENCES_APPROVER = env('APIARY_MIGRATED_LICENCES_APPROVER', 'jacinta.overman@dbca.wa.gov.au')
SHOW_ROOT_API = env('SHOW_ROOT_API', False)
SSO_SETTING_URL=env('SSO_SETTING_URL','')
TIME_ZONE = "Australia/Perth"

INSTALLED_APPS += [
    'reversion',
    'reversion_compare',
    'disturbance',
    'taggit',
    'rest_framework',
    'rest_framework_datatables',
    'rest_framework_gis',
    'reset_migrations',
    'ckeditor',
    'smart_selects',
    'ledger_api_client',
    'webtemplate_dbca',
    "django_vite",
    "appmonitor_client",
]

ADD_REVERSION_ADMIN=True

# maximum number of days allowed for a booking
WSGI_APPLICATION = 'disturbance.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework_datatables.renderers.DatatablesRenderer',
    ),
    "EXCEPTION_HANDLER": "disturbance.exceptions.custom_exception_handler",
}

USE_DJANGO_JQUERY= True

MIDDLEWARE_CLASSES += [
    'disturbance.middleware.FirstTimeNagScreenMiddleware',
    'disturbance.middleware.RevisionOverrideMiddleware',
    'disturbance.middleware.CacheControlMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance', 'templates'))
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance', 'components','ap_payments', 'templates'))
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance', 'components','approvals', 'templates'))
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance', 'components','compliances', 'templates'))
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance', 'components','emails', 'templates'))
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance', 'components','organisations', 'templates'))
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance', 'components','proposals', 'templates'))
TEMPLATES[0]['OPTIONS']['context_processors'].append('disturbance.context_processors.apiary_url')

if 'css_url' in BOOTSTRAP3:
    del BOOTSTRAP3['css_url']

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'disturbance', 'cache'),
    }
}
STATIC_ROOT=os.path.join(BASE_DIR, 'staticfiles_ds')
STATICFILES_DIRS.append(os.path.join(os.path.join(BASE_DIR, 'disturbance', 'static')))
STATICFILES_DIRS.append(os.path.join(os.path.join(BASE_DIR, 'disturbance', 'static', 'disturbance_vue')))
DATA_UPLOAD_MAX_NUMBER_FIELDS = None
STATIC_URL = '/static/'

# Department details
SYSTEM_NAME = env('SYSTEM_NAME', 'Disturbance Approval System')
APIARY_SYSTEM_NAME = env('APIARY_SYSTEM_NAME', 'Apiary System')
SYSTEM_NAME_SHORT = env('SYSTEM_NAME_SHORT', 'DAS')
SITE_PREFIX = env('SITE_PREFIX')
SITE_DOMAIN = env('SITE_DOMAIN')
SUPPORT_EMAIL = env('SUPPORT_EMAIL', SYSTEM_NAME_SHORT.lower() + '@' + SITE_DOMAIN).lower()
APIARY_SUPPORT_EMAIL = env('APIARY_SUPPORT_EMAIL', SUPPORT_EMAIL).lower()
DEP_URL = env('DEP_URL','www.' + SITE_DOMAIN)
DEP_PHONE = env('DEP_PHONE','(08) 9219 9000')
DEP_PHONE_SUPPORT = env('DEP_PHONE_SUPPORT','(08) 9219 9000')
DEP_FAX = env('DEP_FAX','(08) 9423 8242')
DEP_POSTAL = env('DEP_POSTAL','Locked Bag 104, Bentley Delivery Centre, Western Australia 6983')
DEP_NAME = env('DEP_NAME','Department of Biodiversity, Conservation and Attractions')
DEP_NAME_SHORT = env('DEP_NAME_SHORT','DBCA')
SITE_URL = env('SITE_URL', 'https://' + '.'.join([SITE_PREFIX, SITE_DOMAIN]).strip('.'))
PUBLIC_URL=env('PUBLIC_URL', SITE_URL)
EMAIL_FROM = env('EMAIL_FROM', 'no-reply@' + SITE_DOMAIN).lower()
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'no-reply@' + SITE_DOMAIN).lower()
APIARY_ADMIN_GROUP = 'Apiary Admin'
APIARY_PAYMENTS_OFFICERS_GROUP = 'Apiary Payments Officers'
APPROVED_APIARY_EXTERNAL_USERS_GROUP = env('APPROVED_APIARY_EXTERNAL_USERS_GROUP', 'Apiary Approved External Users')
CRON_EMAIL = env('CRON_EMAIL', 'cron@' + SITE_DOMAIN).lower()
TENURE_SECTION = env('TENURE_SECTION', None)
ASSESSMENT_REMINDER_DAYS = env('ASSESSMENT_REMINDER_DAYS', 15)
OSCAR_BASKET_COOKIE_OPEN = 'das_basket'
PAYMENT_SYSTEM_ID = env('PAYMENT_SYSTEM_ID', 'S517')
PS_PAYMENT_SYSTEM_ID = PAYMENT_SYSTEM_ID
PAYMENT_SYSTEM_PREFIX = env('PAYMENT_SYSTEM_PREFIX', PAYMENT_SYSTEM_ID.replace('S','0')) # '0517'
os.environ['LEDGER_PRODUCT_CUSTOM_FIELDS'] = "('ledger_description','quantity','price_incl_tax','price_excl_tax','oracle_code')"
APIARY_URL = env('APIARY_URL', [])
CRON_NOTIFICATION_EMAIL = env('CRON_NOTIFICATION_EMAIL', NOTIFICATION_EMAIL).lower()
VERSION_NO="1.0.1"

BASE_URL=env('BASE_URL')

CRON_CLASSES = [
    'appmonitor_client.cron.CronJobAppMonitorClient',
]

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
    },
    'awesome_ckeditor': {
        'toolbar': 'Basic',
    },
}

BUILD_TAG = env('BUILD_TAG', hashlib.md5(os.urandom(32)).hexdigest())  # URL of the Dev app.js served by webpack & express
GEOCODING_ADDRESS_SEARCH_TOKEN = env('GEOCODING_ADDRESS_SEARCH_TOKEN', 'ACCESS_TOKEN_NOT_FOUND')
RESTRICTED_RADIUS = 3000  # unit: [m]
DBCA_ABN = '38 052 249 024'
if env('CONSOLE_EMAIL_BACKEND', False):
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SITE_STATUS_DRAFT = 'draft'
SITE_STATUS_PENDING = 'pending'
SITE_STATUS_APPROVED = 'approved'  # This status 'approved' is assigned to the ApiarySiteOnProposal object once it's approved.  'current' is assigned to the ApiarySiteOnApproval object after that.
SITE_STATUS_DENIED = 'denied'
SITE_STATUS_CURRENT = 'current'
SITE_STATUS_NOT_TO_BE_REISSUED = 'not_to_be_reissued'
SITE_STATUS_SUSPENDED = 'suspended'
SITE_STATUS_TRANSFERRED = 'transferred'  # This status 'transferred' is assigned to the old relationship (ApiarySiteOnApproval object)
SITE_STATUS_VACANT = 'vacant'
SITE_STATUS_DISCARDED = 'discarded'
BASE_EMAIL_TEXT = 'disturbance/emails/base_email.txt'
BASE_EMAIL_HTML = 'disturbance/emails/base_email.html'
ORGANISATION_PERMISSION_MODULE = 'disturbance.permission'

HTTP_HOST_FOR_TEST = 'localhost:9061'

LOGGERS_TO_REMOVE = ['wildlifecompliance', 'wildlifelicensing', 'log', 'disturbance',]
for logger_name in LOGGERS_TO_REMOVE:
    if logger_name in LOGGING['loggers']:
        del LOGGING['loggers'][logger_name]

# Prevent dictConfig from disabling existing (module) loggers that aren't
# present in the LOGGING['loggers'] mapping. Some packages predefine
# loggers (eg. 'disturbance.*') and removing their entry above would
# otherwise leave them disabled when dictConfig runs. Ensure existing
# loggers remain active and propagate to the root handlers.
LOGGING['disable_existing_loggers'] = False
LOGGING['formatters']['verbose2'] = {"format": "%(levelname)s %(asctime)s %(name)s [Line:%(lineno)s][%(funcName)s] %(message)s"}
LOGGING['loggers']['']['level'] = 'DEBUG'
LOGGING['handlers']['console']['formatter'] = 'verbose2'
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['handlers']['file']['formatter'] = 'verbose2'
LOGGING['handlers']['file']['level'] = 'INFO'

KMI_SERVER_URL = env('KMI_SERVER_URL', 'https://kmi.dbca.wa.gov.au')

TEMPLATE_TITLE = "Apiary System"
TEMPLATE_HEADER_LOGO = "/static/disturbance/img/logo-park-stay-trunc.gif"
TEMPLATE_GROUP = "parkswildlifev2"

LEDGER_TEMPLATE = "bootstrap5"

# Use git commit hash for purging cache in browser for deployment changes
GIT_COMMIT_HASH = os.popen(
    f"cd {BASE_DIR}; git log -1 --format=%H"
).read()  
GIT_COMMIT_DATE = os.popen(
    f"cd {BASE_DIR}; git log -1 --format=%cd"
).read()  
if len(GIT_COMMIT_HASH) == 0:
    GIT_COMMIT_HASH = os.popen("cat /app/git_hash").read()
APPLICATION_VERSION = env("APPLICATION_VERSION", "1.0.0") + "-" + GIT_COMMIT_HASH[:7]

APIARY_EXTERNAL_URL = env('APIARY_EXTERNAL_URL', 'External url not configured')
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
if env('EMAIL_INSTANCE') is not None and env('EMAIL_INSTANCE','') != 'PROD':
    SESSION_FILE_PATH = env('SESSION_FILE_PATH', BASE_DIR+'/session_store/')
    if not os.path.isdir(SESSION_FILE_PATH):
        os.mkdir(SESSION_FILE_PATH)       
else:
    SESSION_FILE_PATH = env('SESSION_FILE_PATH', '/app/session_store/')

SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE', True)
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', True)
SESSION_COOKIE_AGE = env('SESSION_COOKIE_AGE',3600)
LEDGER_UI_ACCOUNTS_MANAGEMENT = [
    {'first_name': {'options' : {'view': True, 'edit': True}}},
    {'last_name': {'options' : {'view': True, 'edit': True}}},
    {'residential_address': {'options' : {'view': True, 'edit': True}}},
    {'postal_address': {'options' : {'view': True, 'edit': True}}},
    {'phone_number' : {'options' : {'view': True, 'edit': True}}},
    {'mobile_number' : {'options' : {'view': True, 'edit': True}}},
    {'dob' : {'options' : {'view': True, 'edit': True}}},
    {'postal_same_as_residential' : {'options' : {'view': True, 'edit': True}}},
    {'address_details' : {'options' : {'billing_address': {'show': False}}}},
]
LEDGER_UI_SYSTEM_ACCOUNTS_MANAGEMENT['address_details']['options']['billing_address']['show'] = False
LEDGER_UI_ORGANISATION_MANAGEMENT = [
        {'organisation_name': {'options' : {'view': True, 'edit': True}}},
        {'organisation_abn': {'options' : {'view': True, 'edit': True}}},
        {'postal_address': {'options' : {'view': True, 'edit': True}}}
]

LEDGER_UI_ACCOUNTS_MANAGEMENT_KEYS = []
for am in LEDGER_UI_ACCOUNTS_MANAGEMENT:
    LEDGER_UI_ACCOUNTS_MANAGEMENT_KEYS.append(list(am.keys())[0])

RUNNING_DEVSERVER = len(sys.argv) > 1 and sys.argv[1] == "runserver"

MIDDLEWARE = MIDDLEWARE_CLASSES 

# Make sure this returns true when in local development
# so you can use the vite dev server with hot module reloading
DJANGO_VITE_DEV_MODE = RUNNING_DEVSERVER and EMAIL_INSTANCE == "DEV" and DEBUG is True

STATIC_URL_PREFIX = "/static/disturbance_vue/" if DJANGO_VITE_DEV_MODE else "disturbance_vue/"

DJANGO_VITE = {
  "default": {
    "dev_mode": DJANGO_VITE_DEV_MODE,
    "manifest_path": os.path.join(
        BASE_DIR, "disturbance", "static", "disturbance_vue", "manifest.json"
    ),
    "dev_server_host": "localhost", # Default host for vite (can change if needed)
    "dev_server_port": 5173, # Default port for vite (can change if needed)
    "static_url_prefix": STATIC_URL_PREFIX,
  }
}
VUE3_ENTRY_SCRIPT = env(  # This is not a reserved keyword.
    "VUE3_ENTRY_SCRIPT",
    "src/main.js"  # This path will be auto prefixed with the static_url_prefix from DJANGO_VITE above
)  # Path of the vue3 entry point script served by vite

LEDGER_SYSTEM_ID = env('PAYMENT_INTERFACE_SYSTEM_PROJECT_CODE', 'PAYMENT_INTERFACE_SYSTEM_PROJECT_CODE not configured')
LEDGER_USER = env('LEDGER_USER', '')
LEDGER_PASS = env('LEDGER_PASS', '')
KB_USER = env('KB_USER', LEDGER_USER)
KB_PASSWORD = env('KB_PASSWORD', LEDGER_PASS)
KB_SERVER_URL = env('KB_SERVER_URL', 'https://kb.dbca.wa.gov.au/')