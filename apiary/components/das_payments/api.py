import traceback
import os
import datetime
import base64
import geojson
from six.moves.urllib.parse import urlparse
from wsgiref.util import FileWrapper
from django.db.models import Q, Min
from django.db import transaction
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework import viewsets, serializers, status, generics, views
from rest_framework.decorators import action, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, BasePermission
from rest_framework.pagination import PageNumberPagination
from datetime import datetime, timedelta
from collections import OrderedDict
from django.core.cache import cache
from ledger_api_client.ledger_models import EmailUserRO as EmailUser, Address
from ledger.address.models import Country
from datetime import datetime, timedelta, date
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from apiary.components.proposals.models import Proposal, ApplicationType
#from apiary.components.das_payments.models import
#from apiary.components.bookings.serializers import
from apiary.helpers import is_customer, is_internal
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from apiary.components.proposals.api import ProposalFilterBackend, ProposalRenderer


#class PaymentViewSet(viewsets.ModelViewSet):
#    queryset = Payment.objects.none()
#    serializer_class = PaymentSerializer
#
#    def get_queryset(self):
#        user = self.request.user
#        if is_internal(self.request):
#            return Payment.objects.all().exclude(payment_type=Payment.PAYMENT_TYPE_TEMPORARY)
#        elif is_customer(self.request):
#            user_orgs = [org.id for org in user.disturbance_organisations.all()]
#            return  Payment.objects.filter( Q(proposal__org_applicant_id__in = user_orgs) | Q(proposal__submitter = user) ).exclude(payment_type=Payment.PAYMENT_TYPE_TEMPORARY)
#        return Payment.objects.none()


