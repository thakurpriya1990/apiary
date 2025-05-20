import logging
from datetime import datetime

import requests
import json
import pytz
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import Distance
from django.core.cache import cache
from django.db import connection, transaction
from django.db.models.query_utils import Q
from rest_framework import serializers
from ledger_api_client.ledger_models import EmailUserRO as EmailUser

from disturbance.components.main.decorators import timeit
from disturbance.settings import SITE_STATUS_DRAFT, SITE_STATUS_APPROVED, SITE_STATUS_TRANSFERRED, RESTRICTED_RADIUS, \
    SITE_STATUS_PENDING, SITE_STATUS_DISCARDED, SITE_STATUS_VACANT, SITE_STATUS_DENIED, SITE_STATUS_CURRENT, \
    SITE_STATUS_NOT_TO_BE_REISSUED, SITE_STATUS_SUSPENDED

logger = logging.getLogger(__name__)


#def retrieve_department_users():
#    try:
#        res = requests.get('{}/api/users?minimal'.format(settings.CMS_URL), auth=(settings.LEDGER_USER,settings.LEDGER_PASS), verify=False)
#        res.raise_for_status()
#        cache.set('department_users',json.loads(res.content).get('objects'),10800)
#    except:
#        raise
#
#
#def get_department_user(email):
#    try:
#        res = requests.get('{}/api/users?email={}'.format(settings.CMS_URL,email), auth=(settings.LEDGER_USER,settings.LEDGER_PASS), verify=False)
#        res.raise_for_status()
#        data = json.loads(res.content).get('objects')
#        if len(data) > 0:
#            return data[0]
#        else:
#            return None
#    except:
#        raise
#


def get_department_user(email):
    if (EmailUser.objects.filter(email__iexact=email.strip()) and 
            EmailUser.objects.get(email__iexact=email.strip()).is_staff):
        return True
    return False


def to_local_tz(_date):
    local_tz = pytz.timezone(settings.TIME_ZONE)
    return _date.astimezone(local_tz)


def check_db_connection():
    """  check connection to DB exists, connect if no connection exists """
    try:
        if not connection.is_usable():
            connection.connect()
    except Exception as e:
        connection.connect()


def convert_utc_time_to_local(utc_time_str_with_z):
    """
    This function converts datetime str like '', which is in UTC, to python datetime in local
    """
    if utc_time_str_with_z:
        # Serialized moment obj is supposed to be sent. Which is UTC timezone.
        date_utc = datetime.strptime(utc_time_str_with_z, '%Y-%m-%dT%H:%M:%S.%fZ')
        # Add timezone (UTC)
        date_utc = date_utc.replace(tzinfo=pytz.UTC)
        # Convert the timezone to TIME_ZONE
        date_perth = date_utc.astimezone(pytz.timezone(settings.TIME_ZONE))
        return date_perth
    else:
        return utc_time_str_with_z


def get_template_group(request):
    web_url = request.META.get('HTTP_HOST', None)
    template_group = None
    if web_url in settings.APIARY_URL:
       template_group = 'apiary'
    else:
       template_group = 'das'
    return template_group


@timeit
def get_category(wkb_geometry):
    from disturbance.components.proposals.models import SiteCategory
    from disturbance.components.main.models import CategoryDbca

    category = SiteCategory.objects.get(name=SiteCategory.CATEGORY_REMOTE)
    zones = CategoryDbca.objects.filter(wkb_geometry__contains=wkb_geometry)
    if zones:
        category_name = zones[0].category_name.lower()
        if 'south' in category_name:
            category = SiteCategory.objects.get(name=SiteCategory.CATEGORY_SOUTH_WEST)
    return category


def _get_params(layer_name, coords):
    return {
        'SERVICE': 'WMS',
        'VERSION': '1.1.1',
        'REQUEST': 'GetFeatureInfo',
        'FORMAT': 'image/png',
        'TRANSPARENT': True,
        'QUERY_LAYERS': layer_name,
        'STYLES': '',
        'LAYERS': layer_name,
        'INFO_FORMAT': 'application/json',
        'FEATURE_COUNT': 1,  # Features should not be overwrapped
        'X': 50,
        'Y': 50,
        'SRS': 'EPSG:4283',
        'WIDTH': 101,
        'HEIGHT': 101,
        'BBOX': str(coords[0] - 0.0001) + ',' + str(coords[1] - 0.0001) + ',' + str(coords[0] + 0.0001) + ',' + str( coords[1] + 0.0001),
    }

def get_feature_in_wa_coastline_original(wkb_geometry):
    return get_feature_in_wa_coastline(wkb_geometry, False)


@timeit
def get_feature_in_wa_coastline_smoothed(wkb_geometry):
    return get_feature_in_wa_coastline(wkb_geometry, True)


def get_feature_in_wa_coastline(wkb_geometry, smoothed):
    from disturbance.components.main.models import WaCoast

    try:
        features = WaCoast.objects.filter(wkb_geometry__contains=wkb_geometry, smoothed=smoothed)
        if features:
            return features[0]
        else:
            return None
    except:
        return None


def get_feature_in_wa_coastline_kmi(wkb_geometry):
    try:
        URL = 'https://kmi.dpaw.wa.gov.au/geoserver/public/wms'
        coords = wkb_geometry.get_coords()
        PARAMS = _get_params('public:wa_coast_pub', coords)
        res = requests.get(url=URL, params=PARAMS)
        geo_json = res.json()
        feature = None
        if len(geo_json['features']) > 0:
            feature = geo_json['features'][0]
        return feature
    except:
        return None


def get_tenure(wkb_geometry):
    try:
        URL = 'https://kmi.dpaw.wa.gov.au/geoserver/public/wms'
        coords = wkb_geometry.get_coords()
        PARAMS = _get_params('public:dpaw_lands_and_waters', coords)
        res = requests.get(url=URL, params=PARAMS)
        geo_json = res.json()
        tenure_name = ''
        if len(geo_json['features']) > 0:
            tenure_name = geo_json['features'][0]['properties']['tenure']
        return tenure_name
    except:
        return ''


def get_region_district(wkb_geometry):
    from disturbance.components.main.models import RegionDbca
    from disturbance.components.main.models import DistrictDbca

    try:
        regions = RegionDbca.objects.filter(wkb_geometry__contains=wkb_geometry, enabled=True)
        districts = DistrictDbca.objects.filter(wkb_geometry__contains=wkb_geometry, enabled=True)
        text_arr = []
        if regions:
            text_arr.append(regions.first().region_name)
        if districts:
            text_arr.append(districts.first().district_name)

        ret_text = '/'.join(text_arr)
        return ret_text
    except:
        return ''


def _get_vacant_apiary_site(search_text=''):
    from disturbance.components.proposals.models import ApiarySite
    queries = Q(is_vacant=True)
    if search_text:
        # queries &= Q(id__icontains=search_text)
        queries &= Q(id=search_text)
    qs_vacant_site = ApiarySite.objects.filter(queries).distinct()
    return qs_vacant_site


def get_qs_vacant_site(search_text=''):
    from disturbance.components.proposals.models import ApiarySiteOnProposal
    from disturbance.components.approvals.models import ApiarySiteOnApproval

    qs_vacant_site = _get_vacant_apiary_site(search_text)

    # apiary_site_proposal_ids = qs_vacant_site.all().values('proposal_link_for_vacant__id')
    # apiary_site_proposal_ids = qs_vacant_site.all().values('latest_proposal_link__id')
    # When the 'vacant' site is selected, saved, deselected and then saved again, the latest_proposal_link gets None
    # That's why we need following line too to pick up all the vacant sites
    # apiary_site_proposal_ids2 = qs_vacant_site.filter(latest_proposal_link__isnull=True).values('proposal_link_for_vacant__id')
    apiary_site_proposal_ids = qs_vacant_site.all().values('proposal_link_for_vacant__id')
    qs_vacant_site_proposal = ApiarySiteOnProposal.objects.select_related(
            'apiary_site', 
            'proposal_apiary', 
            'proposal_apiary__proposal', 
            'proposal_apiary__proposal__proxy_applicant', 
            'proposal_apiary__transferee', 
            'proposal_apiary__target_approval_organisation', 
            'proposal_apiary__target_approval', 
            'proposal_apiary__originating_approval', 
            'site_category_draft', 
            'site_category_processed', 
            'apiary_site__latest_proposal_link', 
            'apiary_site__proposal_link_for_vacant',
            # ).filter(Q(id__in=apiary_site_proposal_ids) | Q(id__in=apiary_site_proposal_ids2))
            ).filter(Q(id__in=apiary_site_proposal_ids))

    # At any moment, either approval_link_for_vacant or proposal_link_for_vacant is True at most.  Never both are True.  (See make_vacant() method of the ApiarySite model)
    # Therefore qs_vacant_site_proposal and qs_vacant_site_approval shouldn't overlap each other
    apiary_site_approval_ids = qs_vacant_site.all().values('approval_link_for_vacant__id')
    #qs_vacant_site_approval = ApiarySiteOnApproval.objects.filter(id__in=apiary_site_approval_ids)
    qs_vacant_site_approval = ApiarySiteOnApproval.objects.select_related(
            'apiary_site', 
            'approval', 
            'site_category', 
            'apiary_site__latest_approval_link', 
            'apiary_site__approval_link_for_vacant',
            'approval__applicant',
            'approval__applicant__organisation',
            'approval__proxy_applicant',
            # 'approval__lodgement_number',
            ).filter(id__in=apiary_site_approval_ids)

    return qs_vacant_site_proposal, qs_vacant_site_approval


def get_qs_denied_site(search_text=''):
    from disturbance.components.proposals.models import ApiarySite, ApiarySiteOnProposal

    q_include_proposal = Q()
    q_exclude_proposal = Q()

    # ApiarySite condition
    q_include_apiary_site = Q()
    q_include_apiary_site &= Q(latest_proposal_link__isnull=False)
    if search_text:
        # q_include_apiary_site &= Q(id__icontains=search_text)
        q_include_apiary_site &= Q(id=search_text)
    qs_apiary_sites = ApiarySite.objects.filter(q_include_apiary_site)

    # ApiarySiteOnProposal conditions for include
    q_include_proposal &= Q(id__in=(qs_apiary_sites.values_list('latest_proposal_link__id', flat=True)))
    q_include_proposal &= Q(site_status__in=(SITE_STATUS_DENIED,))

    # ApiarySiteOnProposal conditions for exclude
    qs_vacant_site = _get_vacant_apiary_site()
    q_exclude_proposal |= Q(apiary_site__in=qs_vacant_site)
    q_exclude_proposal |= Q(site_status=SITE_STATUS_TRANSFERRED)

    qs_on_proposal = ApiarySiteOnProposal.objects.select_related(
        'site_category_processed',
        'apiary_site__latest_proposal_link',
    ).filter(q_include_proposal).exclude(q_exclude_proposal).exclude(wkb_geometry_processed=None).values(
        'wkb_geometry_processed',
        'apiary_site__id',
        'site_status',
        'application_fee_paid',
        'site_category_processed__name',
        'apiary_site__is_vacant',
        'for_renewal',
    )
    return qs_on_proposal


def get_qs_pending_site(search_text=''):
    from disturbance.components.proposals.models import ApiarySite, ApiarySiteOnProposal, Proposal

    q_include_proposal = Q()
    q_exclude_proposal = Q()

    # ApiarySite condition
    q_include_apiary_site = Q()
    q_include_apiary_site &= Q(latest_proposal_link__isnull=False)
    if search_text:
        # q_include_apiary_site &= Q(id__icontains=search_text)
        q_include_apiary_site &= Q(id=search_text)
    qs_apiary_sites = ApiarySite.objects.filter(q_include_apiary_site)

    # ApiarySiteOnProposal conditions for include
    q_include_proposal &= Q(id__in=(qs_apiary_sites.values_list('latest_proposal_link__id', flat=True)))
    q_include_proposal &= Q(site_status__in=(SITE_STATUS_PENDING,))

    # ApiarySiteOnProposal conditions for exclude
    qs_vacant_site = _get_vacant_apiary_site()
    q_exclude_proposal |= Q(apiary_site__in=qs_vacant_site)
    q_exclude_proposal |= Q(site_status=SITE_STATUS_TRANSFERRED)

    qs_on_proposal = ApiarySiteOnProposal.objects.select_related(
        'site_category_processed',
        'apiary_site__latest_proposal_link',
    ).filter(q_include_proposal).exclude(q_exclude_proposal).exclude(wkb_geometry_processed=None).values(
        'wkb_geometry_processed',
        'apiary_site__id',
        'site_status',
        'application_fee_paid',
        'site_category_processed__name',
        'apiary_site__is_vacant',
        'for_renewal',
    )
    return qs_on_proposal


def get_qs_suspended_site(search_text=''):
    from disturbance.components.proposals.models import ApiarySite
    from disturbance.components.approvals.models import ApiarySiteOnApproval

    q_include_approval = Q()
    q_exclude_approval = Q()

    # ApiarySite
    q_include_apiary_site = Q()
    q_include_apiary_site &= Q(latest_approval_link__isnull=False)
    if search_text:
        # q_include_apiary_site &= Q(id__icontains=search_text)
        q_include_apiary_site &= Q(id=search_text)
    qs_apiary_sites = ApiarySite.objects.filter(q_include_apiary_site)

    # 2.1. Include
    q_include_approval &= Q(
        id__in=(qs_apiary_sites.values_list('latest_approval_link__id', flat=True))
    )  # Include only the intermediate objects which are on the ApiarySite.latest_proposal_links
    q_include_approval &= Q(site_status__in=(SITE_STATUS_SUSPENDED,))

    # 2.2. Exclude
    qs_vacant_site = _get_vacant_apiary_site()
    q_exclude_approval |= Q(apiary_site__in=qs_vacant_site)  # We don't want to pick up the vacant sites already retrieved above
    q_exclude_approval |= Q(site_status=SITE_STATUS_TRANSFERRED)  # Exclude 'transferred' sites just in case

    # 2.3. Issue query
    qs_on_approval = ApiarySiteOnApproval.objects.select_related(
        'approval__lodgement_number',
        'approval__id',
        'apiary_site__id',
        'apiary_site__site_guid',
        'apiary_site__is_vacant',
        'site_category__name',
    ).filter(q_include_approval).exclude(q_exclude_approval).values(
        'approval__lodgement_number',
        'approval__id',
        'wkb_geometry',
        'apiary_site__id',
        'apiary_site__site_guid',
        'site_status',
        'site_category__name',
        'apiary_site__is_vacant',
        'available',
    )
    return qs_on_approval


def get_qs_current_site(search_text='', available=None):
    from disturbance.components.proposals.models import ApiarySite
    from disturbance.components.approvals.models import ApiarySiteOnApproval

    q_include_approval = Q()
    q_exclude_approval = Q()

    # ApiarySite
    q_include_apiary_site = Q()
    q_include_apiary_site &= Q(latest_approval_link__isnull=False)
    if search_text:
        # q_include_apiary_site &= Q(id__icontains=search_text)
        q_include_apiary_site &= Q(id=search_text)
    qs_apiary_sites = ApiarySite.objects.filter(q_include_apiary_site)

    # 2.1. Include
    q_include_approval &= Q(id__in=(qs_apiary_sites.values_list('latest_approval_link__id', flat=True)))  # Include only the intermediate objects which are on the ApiarySite.latest_proposal_links
    q_include_approval &= Q(site_status__in=(SITE_STATUS_CURRENT,))
    if available is None:
        pass  # Include both available and unavailable
    elif available:
        q_include_approval &= Q(available=True)
    else:
        q_include_approval &= Q(available=False)

    # 2.2. Exclude
    qs_vacant_site = _get_vacant_apiary_site()
    q_exclude_approval |= Q(apiary_site__in=qs_vacant_site)  # We don't want to pick up the vacant sites already retrieved above
    q_exclude_approval |= Q(site_status=SITE_STATUS_TRANSFERRED)  # Exclude 'transferred' sites just in case

    # 2.3. Issue query
    qs_on_approval = ApiarySiteOnApproval.objects.select_related(
        'approval__lodgement_number',
        'approval__id',
        'apiary_site__id',
        'apiary_site__site_guid',
        'apiary_site__is_vacant',
        'site_category__name',
    ).filter(q_include_approval).exclude(q_exclude_approval).values(
        'approval__lodgement_number',
        'approval__id',
        'wkb_geometry',
        'apiary_site__id',
        'apiary_site__site_guid',
        'site_status',
        'site_category__name',
        'apiary_site__is_vacant',
        'available',
    )
    return qs_on_approval


def get_qs_discarded_site(search_text=''):
    from disturbance.components.proposals.models import ApiarySite, ApiarySiteOnProposal

    # ApiarySiteOnProposal conditions to be included
    q_include_proposal = Q()
    # ApiarySiteOnProposal conditions to be excluded
    q_exclude_proposal = Q()

    # ApiarySite conditions
    q_include_apiary_site = Q()
    q_include_apiary_site &= Q(latest_proposal_link__isnull=False)
    if search_text:
        q_include_apiary_site &= Q(id__icontains=search_text)
    qs_apiary_sites = ApiarySite.objects.filter(q_include_apiary_site)

    q_include_proposal &= Q(id__in=(qs_apiary_sites.values_list('latest_proposal_link__id', flat=True)))
    q_include_proposal &= Q(site_status__in=(SITE_STATUS_DISCARDED,))

    # 2.2. Exclude
    qs_vacant_site = _get_vacant_apiary_site()
    q_exclude_proposal |= Q(apiary_site__in=qs_vacant_site)  # Exclude 'vacant' sites
    q_exclude_proposal |= Q(site_status=SITE_STATUS_TRANSFERRED)  # Exclude 'transferred' sites

    qs_on_proposal = ApiarySiteOnProposal.objects.select_related(
        'site_category_processed',
        'apiary_site__latest_proposal_link',
    ).filter(q_include_proposal).exclude(q_exclude_proposal).exclude(wkb_geometry_processed=None).values(
        'wkb_geometry_processed',
        'apiary_site__id',
        'site_status',
        'application_fee_paid',
        'site_category_processed__name',
        'apiary_site__is_vacant',
        'for_renewal',
    )
    return qs_on_proposal


def get_qs_not_to_be_reissued_site(search_text=''):
    from disturbance.components.proposals.models import ApiarySite
    from disturbance.components.approvals.models import ApiarySiteOnApproval

    q_include_approval = Q()
    q_exclude_approval = Q()

    # ApiarySite
    q_include_apiary_site = Q()
    q_include_apiary_site &= Q(latest_approval_link__isnull=False)
    if search_text:
        # q_include_apiary_site &= Q(id__icontains=search_text)
        q_include_apiary_site &= Q(id=search_text)
    qs_apiary_sites = ApiarySite.objects.filter(q_include_apiary_site)

    # 2.1. Include
    q_include_approval &= Q(
        id__in=(qs_apiary_sites.values_list('latest_approval_link__id', flat=True))
    )  # Include only the intermediate objects which are on the ApiarySite.latest_proposal_links
    q_include_approval &= Q(site_status__in=(SITE_STATUS_NOT_TO_BE_REISSUED,))

    # 2.2. Exclude
    qs_vacant_site = _get_vacant_apiary_site()
    q_exclude_approval |= Q(
        apiary_site__in=qs_vacant_site
    )  # We don't want to pick up the vacant sites already retrieved above
    q_exclude_approval |= Q(site_status=SITE_STATUS_TRANSFERRED)  # Exclude 'transferred' sites just in case

    # 2.3. Issue query
    qs_on_approval = ApiarySiteOnApproval.objects.select_related(
        'approval__lodgement_number',
        'approval__id',
        'apiary_site__id',
        'apiary_site__site_guid',
        'apiary_site__is_vacant',
        'site_category__name',
    ).filter(q_include_approval).exclude(q_exclude_approval).values(
        'approval__lodgement_number',
        'approval__id',
        'wkb_geometry',
        'apiary_site__id',
        'apiary_site__site_guid',
        'site_status',
        'site_category__name',
        'apiary_site__is_vacant',
        'available',
    )
    return qs_on_approval


def get_qs_proposal(draft_processed, proposal=None, search_text='', include_pure_draft_site=False):
    from disturbance.components.proposals.models import ApiarySite, ApiarySiteOnProposal, Proposal

    # 1. ApiarySiteOnProposal
    q_include_proposal = Q()
    q_exclude_proposal = Q()

    # 1.1. Include
    q_include_apiary_site = Q()
    q_include_apiary_site &= Q(latest_proposal_link__isnull=False)
    if search_text:
        q_include_apiary_site &= Q(id__icontains=search_text)
    qs_apiary_sites = ApiarySite.objects.filter(q_include_apiary_site)
    q_include_proposal &= Q(id__in=(qs_apiary_sites.values_list('latest_proposal_link__id', flat=True)))  # Include only the intermediate objects which are on the ApiarySite.latest_proposal_links

    # 1.2. Exclude
    if include_pure_draft_site:
        pass
    else:
        q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_DRAFT,)) & Q(making_payment=False)  # Exclude pure 'draft' site
    q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_DISCARDED,))
    q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_APPROVED,))  # 'approved' site should be included in the approval as a 'current'
    q_exclude_proposal |= Q(apiary_site__in=ApiarySite.objects.filter(is_vacant=True))  # Vacant sites are already picked up above.  We don't want to pick up them again here.

    # 1.3. Exculde the apairy sites which are on the proposal apiary currently being accessed
    # (incorporated into 1.4)
    proposal_apiary = None
    if proposal:
        proposal_apiary = proposal.proposal_apiary
    # 1.4. Issue query
    if draft_processed == 'draft':
        qs_on_proposal = ApiarySiteOnProposal.objects.select_related(
                'site_category_draft', 
                'apiary_site__latest_proposal_link', 
                ).filter(q_include_proposal).exclude(q_exclude_proposal).filter(wkb_geometry_processed=None).exclude(
                        proposal_apiary=proposal_apiary).values(
                                                        'wkb_geometry_draft',
                                                        'apiary_site__id',
                                                        'site_status',
                                                        'application_fee_paid',
                                                        'site_category_draft__name',
                                                        'apiary_site__is_vacant',
                                                        'for_renewal',
                                                        )
    elif draft_processed == 'processed':
        qs_on_proposal = ApiarySiteOnProposal.objects.select_related(
                'site_category_processed', 
                'apiary_site__latest_proposal_link', 
                ).filter(q_include_proposal).exclude(q_exclude_proposal).exclude(wkb_geometry_processed=None).exclude(
                                                proposal_apiary=proposal_apiary).values(
                                                        'wkb_geometry_processed',
                                                        'apiary_site__id',
                                                        'site_status',
                                                        'application_fee_paid',
                                                        'site_category_processed__name',
                                                        'apiary_site__is_vacant',
                                                        'for_renewal',
                                                        )
    return qs_on_proposal


def get_qs_approval():
    from disturbance.components.proposals.models import ApiarySite
    from disturbance.components.approvals.models import ApiarySiteOnApproval

    q_include_approval = Q()
    q_exclude_approval = Q()

    qs_vacant_site = _get_vacant_apiary_site()

    # 2.1. Include
    q_include_approval &= Q(id__in=(ApiarySite.objects.filter(latest_approval_link__isnull=False).values_list('latest_approval_link__id', flat=True)))  # Include only the intermediate objects which are on the ApiarySite.latest_proposal_links

    # 2.2. Exclude
    q_exclude_approval |= Q(apiary_site__in=qs_vacant_site)  # We don't want to pick up the vacant sites already retrieved above
    q_exclude_approval |= Q(site_status=SITE_STATUS_TRANSFERRED)

    # 2.3. Issue query
    qs_on_approval = ApiarySiteOnApproval.objects.select_related(
            'approval__lodgement_number',
            'approval__id',
            'apiary_site__id',
            'apiary_site__site_guid',
            'apiary_site__is_vacant',
            'site_category__name',
            ).filter(q_include_approval).exclude(q_exclude_approval).values(
                    'approval__lodgement_number',
                    'approval__id',
                    'wkb_geometry',
                    'apiary_site__id',
                    'apiary_site__site_guid',
                    'site_status',
                    'site_category__name',
                    'apiary_site__is_vacant',
                    'available',
                    )
    return qs_on_approval


@timeit
def validate_buffer(wkb_geometry, apiary_sites_to_exclude=None):
    """
    This function checks if the wkb_geometry (point) is at least 3km away from the other apiary sites
    @param wkb_geometry: WKB geometry of a point
    @param apiary_sites_to_exclude: List or queryset of the apiary sites to be excluded when validation
    """
    if not apiary_sites_to_exclude:
        from disturbance.components.proposals.models import ApiarySite
        apiary_sites_to_exclude = ApiarySite.objects.none()

    site_too_close_error = serializers.ValidationError(
        ['Apiary Site: (lat: {}, lng: {}) is too close to another apiary site.'.format(
            wkb_geometry.coords[1],
            wkb_geometry.coords[0],
        )])

    qs_vacant_site_proposal, qs_vacant_site_approval = get_qs_vacant_site()
    sites = qs_vacant_site_proposal.exclude(apiary_site__in=apiary_sites_to_exclude).filter(Q(wkb_geometry_processed__distance_lte=(wkb_geometry, Distance(m=RESTRICTED_RADIUS))))
    if sites:
        raise site_too_close_error
    sites = qs_vacant_site_approval.exclude(apiary_site__in=apiary_sites_to_exclude).filter(Q(wkb_geometry__distance_lte=(wkb_geometry, Distance(m=RESTRICTED_RADIUS))))
    if sites:
        raise site_too_close_error

    qs_on_proposal_draft = get_qs_proposal('draft')
    qs_on_proposal_processed = get_qs_proposal('processed')
    sites = qs_on_proposal_draft.exclude(apiary_site__in=apiary_sites_to_exclude).filter(Q(wkb_geometry_draft__distance_lte=(wkb_geometry, Distance(m=RESTRICTED_RADIUS))))
    if sites:
        raise site_too_close_error
    sites = qs_on_proposal_processed.exclude(apiary_site__in=apiary_sites_to_exclude).filter(Q(wkb_geometry_processed__distance_lte=(wkb_geometry, Distance(m=RESTRICTED_RADIUS))))
    if sites:
        raise site_too_close_error

    qs_on_approval = get_qs_approval()
    sites = qs_on_approval.exclude(apiary_site__in=apiary_sites_to_exclude).filter(Q(wkb_geometry__distance_lte=(wkb_geometry, Distance(m=RESTRICTED_RADIUS))))
    if sites:
        raise site_too_close_error


def get_status_for_export(relation):
    if relation.apiary_site.is_vacant:
        return_status = SITE_STATUS_VACANT
    else:
        if hasattr(relation, 'making_payment') and relation.making_payment:
            return_status = SITE_STATUS_PENDING
        else:
            if relation.site_status in (
                    SITE_STATUS_DRAFT, SITE_STATUS_APPROVED, SITE_STATUS_TRANSFERRED, SITE_STATUS_DISCARDED,):
                raise Exception('Apiary site with wrong status: {} is picked up'.format(relation.site_status))
            else:
                return_status = relation.site_status
    return return_status


def handle_validation_error(e):
    # if hasattr(e, 'error_dict'):
    #     raise serializers.ValidationError(repr(e.error_dict))
    # else:
    #     raise serializers.ValidationError(repr(e[0].encode('utf-8')))
    if hasattr(e, 'error_dict'):
        raise serializers.ValidationError(repr(e.error_dict))
    else:
        if hasattr(e, 'message'):
            raise serializers.ValidationError(e.message)
        else:
            raise


def get_qs_vacant_site_for_export():
    from disturbance.components.proposals.models import ApiarySiteOnProposal
    from disturbance.components.approvals.models import ApiarySiteOnApproval

    qs_vacant_site = _get_vacant_apiary_site()

    # apiary_site_proposal_ids = qs_vacant_site.all().values('proposal_link_for_vacant__id')
    apiary_site_proposal_ids = qs_vacant_site.all().values('latest_proposal_link__id')
    # When the 'vacant' site is selected, saved, deselected and then saved again, the latest_proposal_link gets None
    # That's why we need following line too to pick up all the vacant sites
    apiary_site_proposal_ids2 = qs_vacant_site.filter(latest_proposal_link__isnull=True).values('proposal_link_for_vacant__id')
    qs_vacant_site_proposal = ApiarySiteOnProposal.objects.filter(Q(id__in=apiary_site_proposal_ids) | Q(id__in=apiary_site_proposal_ids2))

    # At any moment, either approval_link_for_vacant or proposal_link_for_vacant is True at most.  Never both are True.  (See make_vacant() method of the ApiarySite model)
    # Therefore qs_vacant_site_proposal and qs_vacant_site_approval shouldn't overlap each other
    apiary_site_approval_ids = qs_vacant_site.all().values('approval_link_for_vacant__id')
    qs_vacant_site_approval = ApiarySiteOnApproval.objects.filter(id__in=apiary_site_approval_ids)

    return qs_vacant_site_proposal, qs_vacant_site_approval


def get_qs_proposal_for_export():
    from disturbance.components.proposals.models import ApiarySite, ApiarySiteOnProposal, Proposal

    # 1. ApiarySiteOnProposal
    q_include_proposal = Q()
    q_exclude_proposal = Q()

    # 1.1. Include
    q_include_proposal &= Q(id__in=(ApiarySite.objects.all().values('latest_proposal_link__id')))  # Include only the intermediate objects which are on the ApiarySite.latest_proposal_links

    # 1.2. Exclude
    # q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_DRAFT,)) & Q(making_payment=False)  # Exclude pure 'draft' site
    q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_DRAFT,))  # For this purpose, we don't want 'draft' sites.
    q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_DISCARDED,))
    q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_PENDING,))  # For this purpose, we don't want 'pending' sites.
    q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_APPROVED,))  # 'approved' site is included in the approval as a 'current'
    # The followings should not exclude any records because ApiarySiteOnProposal should not be in these statuses, but added just in case there are.
    # Otherwise, sites might be picked up multiple times.
    q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_CURRENT,))
    q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_NOT_TO_BE_REISSUED,))
    q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_SUSPENDED,))
    q_exclude_proposal |= Q(site_status__in=(SITE_STATUS_TRANSFERRED,))
    q_exclude_proposal |= Q(apiary_site__in=ApiarySite.objects.filter(is_vacant=True))  # Vacant sites are already picked up above.  We don't want to pick up them again here.

    # 1.4. Issue query
    qs_on_proposal = ApiarySiteOnProposal.objects.filter(q_include_proposal).exclude(q_exclude_proposal).distinct('apiary_site')
    qs_on_proposal_processed = qs_on_proposal.exclude(wkb_geometry_processed=None)
    qs_on_proposal_draft = qs_on_proposal.filter(wkb_geometry_processed=None)  # For the 'draft' apiary sites with the making_payment=True attribute

    return qs_on_proposal_draft, qs_on_proposal_processed


def get_qs_approval_for_export():
    from disturbance.components.proposals.models import ApiarySite
    from disturbance.components.approvals.models import ApiarySiteOnApproval

    q_include_approval = Q()
    q_exclude_approval = Q()

    qs_vacant_site = _get_vacant_apiary_site()

    # 2.1. Include
    q_include_approval &= Q(id__in=(ApiarySite.objects.all().values('latest_approval_link__id')))  # Include only the intermediate objects which are on the ApiarySite.latest_approval_links

    # 2.2. Exclude
    q_exclude_approval |= Q(apiary_site__in=qs_vacant_site)  # We don't want to pick up the vacant sites already retrieved above
    q_exclude_approval |= Q(site_status=SITE_STATUS_TRANSFERRED)
    # The followings should not exclude any records because ApiarySiteOnApproval should not be in these statuses, but added just in case there are.
    # Otherwise, sites might be picked up multiple times.
    q_exclude_approval |= Q(site_status=SITE_STATUS_DRAFT)
    q_exclude_approval |= Q(site_status=SITE_STATUS_PENDING)
    q_exclude_approval |= Q(site_status=SITE_STATUS_APPROVED)
    q_exclude_approval |= Q(site_status=SITE_STATUS_DENIED)
    q_exclude_approval |= Q(site_status=SITE_STATUS_DISCARDED)

    # 2.3. Issue query
    qs_on_approval = ApiarySiteOnApproval.objects.filter(q_include_approval).exclude(q_exclude_approval).distinct('apiary_site')

    return qs_on_approval


def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def custom_strftime(format_str, t):
    return t.strftime(format_str).replace('{S}', str(t.day) + suffix(t.day))


def overwrite_districts_polygons(path_to_geojson_file):
    from disturbance.components.main.models import DistrictDbca
    try:
        with transaction.atomic():
            # Disable all the existing polygons
            all_districts = DistrictDbca.objects.all()
            all_districts.update(enabled=False)

            with open(path_to_geojson_file) as f:
                data = json.load(f)
                for district in data['features']:
                    json_str = json.dumps(district['geometry'])
                    geom = GEOSGeometry(json_str)
                    district_obj = DistrictDbca.objects.create(
                        wkb_geometry=geom,
                        district_name=district['properties']['DDT_DISTRICT_NAME'],
                        office=district['properties']['DDT_OFFICE'],
                        object_id=district['properties']['OBJECTID'],
                    )
                    district_obj.save()
                    logger.info("Created District: {}".format(district['properties']['DDT_DISTRICT_NAME']))
    except Exception as e:
        logger.error('Error overwriting districts polygons: {}'.format(e))


def overwrite_regions_polygons(path_to_geojson_file):
    from disturbance.components.main.models import RegionDbca

    try:
        with transaction.atomic():
            # Disable all the existing polygons
            all_regions = RegionDbca.objects.all()
            all_regions.update(enabled=False)

            with open(path_to_geojson_file) as f:
                data = json.load(f)
                for region in data['features']:
                    json_str = json.dumps(region['geometry'])
                    geom = GEOSGeometry(json_str)
                    region_obj = RegionDbca.objects.create(
                        wkb_geometry=geom,
                        region_name=region['properties']['DRG_REGION_NAME'],
                        office=region['properties']['DRG_OFFICE'],
                        object_id=region['properties']['OBJECTID'],
                    )
                    region_obj.save()
                    logger.info("Created Region: {}".format(region['properties']['DRG_REGION_NAME']))
    except Exception as e:
        logger.error('Error overwriting regions polygons: {}'.format(e))
