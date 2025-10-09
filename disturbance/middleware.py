from django.urls import reverse
from django.shortcuts import redirect

import re
import logging

from django.conf import settings
from disturbance.components.ap_payments.models import ApplicationFee
from reversion.middleware  import RevisionMiddleware
from reversion.views import _request_creates_revision
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

CHECKOUT_PATH = re.compile('^/ledger/checkout/checkout')

class FirstTimeNagScreenMiddleware(object):
    '''
    Generic FirstTimeNagScreenMiddleware.
    '''
    
    def __init__(self, get_response):
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):
        return None

    def __call__(self, request):
        
        if 'static' in request.path:
            return self.get_response(request)
        
        first_time_nag = FirstTimeDefaultNag()
        response = first_time_nag.process_request(request)
        if not response:
            return self.get_response(request)
        else:
            return response

class FirstTimeDefaultNag(object):
    '''
    A specialised FirstTimeNagScreenMiddleware for non WildlifeLicensing.
    '''

    def process_request(self, request):

        if 'static' in request.path:
            return None

        if (request.method == 'GET' 
            and request.user.is_authenticated
            and 'api' not in request.path 
            and 'admin' not in request.path 
            and 'ledger-private' not in request.path
            and 'static' not in request.path
            and "/ledger-ui/" not in request.get_full_path()
            and "/firsttime/" not in request.get_full_path()):

            path_first_time = '/ledger-ui/accounts-firsttime'

            if (not request.user.first_name) or \
                (not request.user.last_name) or \
                (not request.user.legal_first_name) or \
                (not request.user.legal_last_name) or \
                (not request.user.dob and not request.user.legal_dob) or \
                (not request.user.residential_address) or \
                (not (
                    request.user.phone_number or request.user.mobile_number
                )):
                path_logout = reverse('logout')
                if request.path not in (path_first_time, path_logout):
                    return redirect(path_first_time + "?next=" + quote_plus(request.get_full_path()))
                
        return None


class RevisionOverrideMiddleware(RevisionMiddleware):

    """
        Wraps the entire request in a revision.

        override venv/lib/python2.7/site-packages/reversion/middleware.py
    """

    # exclude ledger payments/checkout from revision - hack to overcome basket (lagging status) issue/conflict with reversion
    def request_creates_revision(self, request):
        return _request_creates_revision(request) and 'checkout' not in request.get_full_path()


class CacheControlMiddleware(object):
    def process_response(self, request, response):
        if request.path[:5] == '/api/' or request.path == '/':
            response['Cache-Control'] = 'private, no-store'
        elif request.path[:8] == '/static/':
            response['Cache-Control'] = 'public, max-age=86400'
        else:
            response['Cache-Control'] = 'private, no-store'
        return response


