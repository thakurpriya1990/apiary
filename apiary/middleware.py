from confy import env
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.http import urlquote_plus

import re
import datetime
import logging

from django.http import HttpResponseRedirect
from django.utils import timezone

from django.conf import settings
from apiary.components.das_payments.models import ApplicationFee
from reversion.middleware  import RevisionMiddleware
from reversion.views import _request_creates_revision


logger = logging.getLogger(__name__)


CHECKOUT_PATH = re.compile('^/ledger/checkout/checkout')

class FirstTimeNagScreenMiddleware(object):
    def process_request(self, request):
        #print ("FirstTimeNagScreenMiddleware: REQUEST SESSION")
        if 'static' in request.path:
            return
        if request.user.is_authenticated() and request.method == 'GET' and 'api' not in request.path and 'admin' not in request.path:
            #print('DEBUG: {}: {} == {}, {} == {}, {} == {}'.format(request.user, request.user.first_name, (not request.user.first_name), request.user.last_name, (not request.user.last_name), request.user.dob, (not request.user.dob) ))
            if (not request.user.first_name) or (not request.user.last_name):# or (not request.user.dob):
                path_ft = reverse('first_time')
                path_logout = reverse('accounts:logout')
                if request.path not in (path_ft, path_logout):
                    return redirect(reverse('first_time')+"?next="+urlquote_plus(request.get_full_path()))


class BookingTimerMiddleware(object):
    def process_request(self, request):
        #print ("BookingTimerMiddleware: REQUEST SESSION")
        #print request.session['ps_booking']
        if 'das_app_invoice' in request.session:
            #print ("BOOKING SESSION : "+str(request.session['ps_booking']))
            try:
                application_fee = ApplicationFee.objects.get(pk=request.session['das_app_invoice'])
            except:
                # no idea what object is in self.request.session['ps_booking'], ditch it
                del request.session['das_app_invoice']
                return
            if application_fee.payment_type != 3:
                # booking in the session is not a temporary type, ditch it
                del request.session['das_app_invoice']
        if 'db_process' in request.session:
            #print ("BOOKING SESSION : "+str(request.session['ps_booking']))
            try:
                application_fee = ApplicationFee.objects.get(pk=request.session['db_process'])
            except:
                # no idea what object is in self.request.session['ps_booking'], ditch it
                del request.session['db_process']
                return
            if application_fee.payment_type != 3:
                # booking in the session is not a temporary type, ditch it
                del request.session['db_process']

        return


class RevisionOverrideMiddleware(RevisionMiddleware):

    """
        Wraps the entire request in a revision.

        override venv/lib/python2.7/site-packages/reversion/middleware.py
    """

    # exclude ledger payments/checkout from revision - hack to overcome basket (lagging status) issue/conflict with reversion
    def request_creates_revision(self, request):
        return _request_creates_revision(request) and 'checkout' not in request.get_full_path()


class DomainDetectMiddleware(object):
    def __init__(self, next_layer=None):
        """
        We allow next_layer to be None because old-style middlewares
        won't accept any argument.
        """
        self.get_response = next_layer

    def process_request(self, request):
        """
        Handle old-style request processing here, as usual.
        Any request goes through this function
        """
        # Do something with request
        # Probably return None
        # Or return an HttpResponse in some cases
        settings.DOMAIN_DETECTED = 'das'
        settings.SYSTEM_NAME = env('SYSTEM_NAME', 'Disturbance Approval System')
        settings.SYSTEM_NAME_SHORT = 'DAS'
        settings.BASE_EMAIL_TEXT = 'disturbance/emails/base_email.txt'
        settings.BASE_EMAIL_HTML = 'disturbance/emails/base_email.html'

        http_host = request.META.get('HTTP_HOST', None)

        logger.debug(f'http_host: {http_host}')
        
        if http_host and http_host in settings.APIARY_URL:
            settings.DOMAIN_DETECTED = 'apiary'
            settings.SYSTEM_NAME = settings.APIARY_SYSTEM_NAME
            settings.SYSTEM_NAME_SHORT = 'Apiary'
            settings.BASE_EMAIL_TEXT = 'disturbance/emails/apiary_base_email.txt'
            settings.BASE_EMAIL_HTML = 'disturbance/emails/apiary_base_email.html'

        return None

    def process_response(self, request, response):
        """
        Handle old-style response processing here, as usual.
        """
        # Do something with response, possibly using request.

        return response

    def __call__(self, request):
        """
        Handle new-style middleware here.
        """
        response = self.process_request(request)
        if response is None:
            # If process_request returned None, we must call the next middleware or
            # the view. Note that here, we are sure that self.get_response is not
            # None because this method is executed only in new-style middlewares.
            response = self.get_response(request)
        response = self.process_response(request, response)
        return response


class CacheControlMiddleware(object):
    def process_response(self, request, response):
        if request.path[:5] == '/api/' or request.path == '/':
            response['Cache-Control'] = 'private, no-store'
        elif request.path[:8] == '/static/':
            response['Cache-Control'] = 'public, max-age=86400'
        else:
            response['Cache-Control'] = 'private, no-store'
        return response


