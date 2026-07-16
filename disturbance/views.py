import base64
import json
import logging
import mimetypes
import os
import re
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.gis.geos import GEOSGeometry
from django.core.cache import cache
from django.core.management import call_command
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from rest_framework import serializers
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from wagov_utils.components.proxy.views import proxy_view

from disturbance.components.approvals.models import Approval
from disturbance.components.compliances.models import Compliance
from disturbance.components.main.decorators import timeit
from disturbance.components.main.models import JobQueue
from disturbance.components.main.serializers import (
    WaCoastOptimisedSerializer,
    WaCoastSerializer,
)
from disturbance.components.main.utils import (
    get_feature_in_wa_coastline_original,
    get_feature_in_wa_coastline_smoothed,
)
from disturbance.components.organisations.models import (
    Organisation,
    OrganisationContact,
)
from disturbance.components.proposals.mixins import ReferralOwnerMixin
from disturbance.components.proposals.models import Proposal, Referral
from disturbance.helpers import get_proxy_cache, is_internal

logger = logging.getLogger(__name__)


class InternalView(UserPassesTestMixin, TemplateView):
    template_name = "disturbance/dash/index.html"

    def test_func(self):
        return is_internal(self.request)


class ExternalView(LoginRequiredMixin, TemplateView):
    template_name = "disturbance/dash/index.html"


# TODO on-cleanup review and remove unused DetailView (they don't appear to be needed though that should be tested)
class ReferralView(ReferralOwnerMixin, DetailView):
    model = Referral
    template_name = "disturbance/dash/index.html"

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            if is_internal(self.request):
                return super(InternalComplianceView, self).get(*args, **kwargs)


class ExternalProposalView(DetailView):
    model = Proposal
    template_name = "disturbance/dash/index.html"


class ExternalComplianceView(DetailView):
    model = Compliance
    template_name = "disturbance/dash/index.html"


class InternalComplianceView(DetailView):
    model = Compliance
    template_name = "disturbance/dash/index.html"

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            if is_internal(self.request):
                return super(InternalComplianceView, self).get(*args, **kwargs)
            return redirect("external-compliance-detail")


class DisturbanceRoutingView(TemplateView):
    template_name = "disturbance/index.html"

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            if is_internal(self.request):
                return redirect("internal")
            return redirect("external")
        return super(DisturbanceRoutingView, self).get(*args, **kwargs)


class DisturbanceContactView(TemplateView):
    template_name = "disturbance/contact.html"


class DisturbanceFurtherInformationView(TemplateView):
    template_name = "disturbance/further_info.html"


class InternalProposalView(DetailView):
    model = Proposal
    template_name = "disturbance/dash/index.html"

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            if is_internal(self.request):
                return super(InternalProposalView, self).get(*args, **kwargs)
            return redirect("external-proposal-detail")


class ManagementCommandsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "disturbance/mgt-commands.html"

    def test_func(self):
        return is_internal(self.request)

    def post(self, request):
        data = {}
        command_script = request.POST.get("script", None)
        if command_script:
            print("running {}".format(command_script))
            call_command(command_script)
            data.update({command_script: "true"})

        return render(request, self.template_name, data)


@timeit
@api_view(("GET",))
@renderer_classes((JSONRenderer,))
def gisdata(request):
    layer = request.GET.get("layer", None)
    lat = request.GET.get("lat", None)
    lng = request.GET.get("lng", None)
    include_feature = request.GET.get(
        "include_feature", False
    )  # feature(polygon) data could be large

    geom_str = GEOSGeometry("POINT(" + lng + " " + lat + ")", srid=4326)

    if layer == "wa_coast_smoothed":
        feature = get_feature_in_wa_coastline_smoothed(geom_str)
    elif layer == "wa_coast_original":
        feature = get_feature_in_wa_coastline_original(geom_str)

    if include_feature:
        serializer = WaCoastSerializer(feature)
    else:
        serializer = WaCoastOptimisedSerializer(feature)

    return Response(serializer.data)


def is_authorised_to_access_proposal_document(request, document_id):
    if is_internal(request):
        return True
    elif request.user and request.user.is_authenticated:
        user = request.user
        user_orgs = [org.id for org in user.disturbance_organisations.all()]
        return (
            Proposal.objects.filter(id=document_id)
            .filter(
                Q(applicant_id__in=user_orgs)
                | Q(proxy_applicant=user)
                | Q(submitter=user)
            )
            .exists()
        )


def is_authorised_to_access_approval_document(request, document_id):
    if is_internal(request):
        return True
    elif request.user and request.user.is_authenticated:
        user = request.user
        user_orgs = [org.id for org in user.disturbance_organisations.all()]
        return (
            Approval.objects.filter(id=document_id)
            .filter(
                Q(applicant_id__in=user_orgs)
                | Q(proxy_applicant=user)
                | Q(proxy_applicant_id=user.id)
            )
            .exists()
        )


def is_authorised_to_access_organisation_document(request, document_id):
    if is_internal(request):
        return True
    elif request.user and request.user.is_authenticated:
        user = request.user
        org_contacts = OrganisationContact.objects.filter(is_admin=True).filter(
            email=user.email
        )
        user_admin_orgs = [org.organisation.id for org in org_contacts]
        return (
            Organisation.objects.filter(id=document_id)
            .filter(id__in=user_admin_orgs)
            .exists()
        )


def get_file_path_id(check_str, file_path):
    file_name_path_split = file_path.split("/")
    # if the check_str is in the file path, the next value should be the id
    if check_str in file_name_path_split:
        id_index = file_name_path_split.index(check_str) + 1
        if (
            len(file_name_path_split) > id_index
            and file_name_path_split[id_index].isnumeric()
        ):
            return int(file_name_path_split[id_index])
        else:
            return False
    else:
        return False


def is_authorised_to_access_document(request):

    if is_internal(request):
        return True
    elif request.user.is_authenticated:
        p_document_id = get_file_path_id("proposals", request.path)
        if p_document_id:
            return is_authorised_to_access_proposal_document(request, p_document_id)

        a_document_id = get_file_path_id("approvals", request.path)
        if a_document_id:
            return is_authorised_to_access_approval_document(request, a_document_id)

        # for organisation requests, this will fail and they are stored in a request subdir and by date (which is fine for current use cases)
        o_document_id = get_file_path_id("organisations", request.path)
        if o_document_id:
            return is_authorised_to_access_organisation_document(request, o_document_id)
    else:
        return False


def getPrivateFile(request):

    if is_authorised_to_access_document(request):
        file_name_path = request.path
        # norm path will convert any traversal or repeat / in to its normalised form
        full_file_path = os.path.normpath(settings.BASE_DIR + file_name_path)
        # we then ensure the normalised path is within the BASE_DIR (and the file exists)
        if full_file_path.startswith(settings.BASE_DIR) and os.path.isfile(
            full_file_path
        ):
            extension = file_name_path.split(".")[-1]
            the_file = open(full_file_path, "rb")
            the_data = the_file.read()
            the_file.close()
            if extension == "msg":
                return HttpResponse(the_data, content_type="application/vnd.ms-outlook")
            if extension == "eml":
                return HttpResponse(the_data, content_type="application/vnd.ms-outlook")

            return HttpResponse(
                the_data, content_type=mimetypes.types_map["." + str(extension.lower())]
            )

    return HttpResponse()


@csrf_exempt
def process_proxy(request, remoteurl, queryString, auth_user, auth_password):

    if request.user.is_authenticated:
        proxy_cache = None
        proxy_response = None
        proxy_response_content = None
        base64_json = {}
        query_string_remote_url = remoteurl + "?" + queryString

        cache_times_strings = get_proxy_cache()
        CACHE_EXPIRY = 300
        layer_allowed = False

        proxy_cache = cache.get(query_string_remote_url)
        query_string_remote_url_new = query_string_remote_url.replace("%3A", ":")
        for cts in cache_times_strings:
            layer_name = cts["layer_name"].split(":")[-1]
            if layer_name in query_string_remote_url:
                CACHE_EXPIRY = cts["cache_expiry"]

            if (
                "?layer=" + cts["layer_name"] in query_string_remote_url_new
                or "&LAYERS=" + cts["layer_name"] in query_string_remote_url_new
            ):
                layer_allowed = True
        if layer_allowed is True:
            if proxy_cache is None:
                auth_details = None
                if auth_user is None and auth_password is None:
                    auth_details = None
                else:
                    auth_details = {"user": auth_user, "password": auth_password}
                proxy_response = proxy_view(request, remoteurl, basic_auth=auth_details)
                proxy_response_content_encoded = base64.b64encode(
                    proxy_response.content
                )
                base64_json = {
                    "status_code": proxy_response.status_code,
                    "content_type": proxy_response.headers["content-type"][1],
                    "content": proxy_response_content_encoded.decode("utf-8"),
                    "cache_expiry": CACHE_EXPIRY,
                }
                if proxy_response.status_code == 200:
                    cache.set(
                        query_string_remote_url, json.dumps(base64_json), CACHE_EXPIRY
                    )
                else:
                    cache.set(query_string_remote_url, json.dumps(base64_json), 15)
            else:
                base64_json = json.loads(proxy_cache)
            proxy_response_content = base64.b64decode(base64_json["content"].encode())
            http_response = HttpResponse(
                proxy_response_content,
                content_type=base64_json["content_type"],
                status=base64_json["status_code"],
            )
            http_response["Django-Cache-Expiry"] = (
                str(base64_json["cache_expiry"]) + " seconds"
            )
            return http_response
        else:
            http_response = HttpResponse(
                "Access Denied", content_type="text/html", status=401
            )
            return http_response
    return


def _extract_single_layer_namespace(layers_value):
    """Return the namespace if all requested layers share the same namespace."""
    if not layers_value:
        return None

    namespaces = set()
    layers = [layer.strip() for layer in layers_value.split(",") if layer.strip()]
    if not layers:
        return None

    for layer in layers:
        if ":" not in layer:
            return None
        namespace = layer.split(":", 1)[0].strip()
        if not namespace:
            return None
        namespaces.add(namespace)

    return namespaces.pop() if len(namespaces) == 1 else None


def _ensure_workspace_in_geoserver_url(remoteurl, requested_layers):
    """Inject the workspace into /geoserver/<service> URLs when omitted by clients."""
    if not remoteurl:
        return remoteurl

    namespace = _extract_single_layer_namespace(requested_layers)
    if not namespace:
        return remoteurl

    if f"/geoserver/{namespace}/" in remoteurl:
        return remoteurl

    return re.sub(
        r"/geoserver/(wms|wfs|wcs|ows)(?=$|/)",
        rf"/geoserver/{namespace}/\1",
        remoteurl,
    )


def _build_kb_remote_url(path):
    """Join configured KB server URL with proxy path without duplicating /geoserver."""
    base_url = (settings.KB_SERVER_URL or "").rstrip("/") + "/"
    normalized_path = (path or "").lstrip("/")

    if base_url.rstrip("/").endswith("/geoserver") and normalized_path.startswith(
        "geoserver/"
    ):
        normalized_path = normalized_path[len("geoserver/") :]

    return urljoin(base_url, normalized_path)


@csrf_exempt
def mapProxyView(request, path):
    if request.user.is_authenticated:
        queryString = request.META["QUERY_STRING"]
        remoteurl = None
        auth_user = None
        auth_password = None
        if "kb-proxy" in request.path:
            remoteurl = _build_kb_remote_url(path)
            auth_user = settings.KB_USER
            auth_password = settings.KB_PASSWORD

        requested_layers = request.GET.get("LAYERS", "") or request.GET.get(
            "layers", ""
        )
        remoteurl = _ensure_workspace_in_geoserver_url(remoteurl, requested_layers)

        # Basemap layers are not registered in MapLayer DB, so bypass the layer check
        basemap_layers = [
            settings.KB_BASEMAP_STREET_LAYER,
            settings.KB_BASEMAP_SATELLITE_LAYER,
        ]
        if requested_layers in basemap_layers:
            auth_details = (
                {"user": auth_user, "password": auth_password} if auth_user else None
            )
            return proxy_view(request, remoteurl, basic_auth=auth_details)

        response = process_proxy(
            request, remoteurl, queryString, auth_user, auth_password
        )
        return response
    else:
        raise serializers.ValidationError("User is not authenticated")


class EmailExportsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "disturbance/email_exports.html"

    def test_func(self):
        return is_internal(self.request)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request):
        context = self.get_context_data()
        export_model = request.POST.get("export_model", None)
        filters = request.POST.get("filters", None)
        format = request.POST.get("format", "csv")
        num_records = request.POST.get(
            "num_records", settings.MAX_NUM_ROWS_MODEL_EXPORT
        )

        try:
            num_records = min(int(num_records), settings.MAX_NUM_ROWS_MODEL_EXPORT)
        except Exception:
            num_records = settings.MAX_NUM_ROWS_MODEL_EXPORT

        if export_model:
            parameters = {
                "model": export_model,
                "filters": filters,
                "format": format,
                "num_records": num_records,
            }
            parameters_json = parameters
            # check if job with same params that is not completed/failed already exists - prevent needless duplicates
            if not JobQueue.objects.filter(
                job_cmd="email_exports",
                status__lt=2,
                parameters_json=parameters_json,
                user=request.user.id,
            ):
                JobQueue.objects.create(
                    job_cmd="email_exports",
                    status=0,
                    parameters_json=parameters_json,
                    user=request.user.id,
                )
                context.update(
                    {
                        "message": "{} data export shall be emailed to {} when ready.".format(
                            export_model, request.user.email
                        ).capitalize()
                    }
                )
            else:
                context.update(
                    {
                        "message": "{} data export for {} already in progress.".format(
                            export_model, request.user.email
                        ).capitalize()
                    }
                )
        else:
            context.update({"message": "Export request failed."})

        return self.render_to_response(context)
