from django.conf import settings
from apiary import helpers


def disturbance_url(request):
    template_group = 'disturbance'
    TERMS = "/know/online-disturbance-apiary-terms-and-conditions"

    is_officer = False
    is_admin = False
    is_customer = False

    if request.user.is_authenticated:
         is_admin = helpers.is_disturbance_admin(request)
         is_apiary_admin = helpers.is_disturbance_admin(request)
         is_customer = helpers.is_customer(request)

    return {
        'APIARY_SEARCH': '/external/payment',
        'APIARY_CONTACT': '/contact-us',
        'APIARY_TERMS': TERMS,
        'DEV_STATIC': settings.DEV_STATIC,
        'DEV_STATIC_URL': settings.DEV_STATIC_URL,
        'TEMPLATE_GROUP': template_group,
        'SYSTEM_NAME': settings.SYSTEM_NAME,
        'IS_OFFICER': is_officer,
        'IS_ADMIN': is_admin,
        'IS_APIARY_ADMIN': is_apiary_admin,
        'IS_CUSTOMER': is_customer,
        'PUBLIC_URL': settings.PUBLIC_URL
    }


def template_context(request):
    """Pass extra context variables to every template.
    """
    context = disturbance_url(request)
    return context



