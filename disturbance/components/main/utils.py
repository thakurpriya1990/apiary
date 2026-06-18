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

import csv
import xlsxwriter
import uuid

from disturbance.settings import MAX_NUM_ROWS_MODEL_EXPORT

import re
import os

from disturbance.components.main.decorators import timeit
from disturbance.settings import SITE_STATUS_DRAFT, SITE_STATUS_APPROVED, SITE_STATUS_TRANSFERRED, RESTRICTED_RADIUS, \
    SITE_STATUS_PENDING, SITE_STATUS_DISCARDED, SITE_STATUS_VACANT, SITE_STATUS_DENIED, SITE_STATUS_CURRENT, \
    SITE_STATUS_NOT_TO_BE_REISSUED, SITE_STATUS_SUSPENDED

logger = logging.getLogger(__name__)

def remove_html_tags(text):

    if text is None:
        return None

    HTML_TAGS_WRAPPED = re.compile(r'<[^>]+>.+</[^>]+>')
    HTML_TAGS_NO_WRAPPED = re.compile(r'<[^>]+>')

    text = HTML_TAGS_WRAPPED.sub('', text)
    text = HTML_TAGS_NO_WRAPPED.sub('', text)
    return text

def remove_script_tags(text):

    if text is None:
        return None

    SCRIPT_TAGS_WRAPPED = re.compile(r'(?i)<script[^>]+>.+</script[^>]+>')
    SCRIPT_TAGS_NO_WRAPPED = re.compile(r'(?i)<script[^>]+>')

    text = SCRIPT_TAGS_WRAPPED.sub('', text)
    text = SCRIPT_TAGS_NO_WRAPPED.sub('', text)

    ATTR_BLACKLIST = ['onresize','onvolumechange','onsuspend','onpopstate','onbeforeunload','oncontextmenu',
        'ondragstart','oncuechange','onselect','onafterprint','onmouseover','ondragleave','onstorage',
        'onbeforeprint','onhashchange','onabort','ondragover','onwaiting','onclick','onmousemove','onkeyup',
        'onmousedown','ononline','onsearch','onprogress','onfocus','onmouseup','onplaying','onstalled','oninvalid',
        'ontimeupdate','onkeypress','onseeked','onreset','onwheel','onemptied','oninput','onpagehide','onpause',
        'onloadeddata','onseeking','onunload','onpageshow','onerror','ondrop','oncanplay','oncopy','onended','oncut',
        'onsubmit','ondrag','onblur','ondragend','onplay','onratechange','onloadedmetadata','oncanplaythrough',
        'ondurationchange','onchange','ondblclick','onmousewheel','onpaste','onload','onscroll','onkeydown',
        'ontoggle','onmouseout','onoffline','onloadstart','ondragenter']
    ATTR_BLACKLIST_STR=('|').join(ATTR_BLACKLIST)

    HTML_TAGS_WITH_ATTR_WRAPPED = re.compile(r'(?i)<[^>]+('+ATTR_BLACKLIST_STR+')[\\s]*=[^>]+>.+</[^>]+>')
    HTML_TAGS_WITH_ATTR_NO_WRAPPED = re.compile(r'(?i)<[^>]+('+ATTR_BLACKLIST_STR+')[\\s]*=[^>]+>')

    text = HTML_TAGS_WITH_ATTR_WRAPPED.sub('', text)
    text = HTML_TAGS_WITH_ATTR_NO_WRAPPED.sub('', text)

    return text

def is_json(value):
    try:
        json.loads(value)
    except:
        return False
    return True

def sanitise_fields(instance, exclude=[], error_on_change=[]):
    if hasattr(instance,"__dict__"):
        for i in instance.__dict__:
            #remove html tags for all string fields not in the exclude list
            if not i in exclude and (isinstance(instance.__dict__[i], dict)):
                instance.__dict__[i] = sanitise_fields(instance.__dict__[i])
            
            elif isinstance(instance.__dict__[i], list) and not i in exclude:
                for j in range(0, len(instance.__dict__[i])):
                    check = instance.__dict__[i][j]
                    if isinstance(instance.__dict__[i][j],str):
                        instance.__dict__[i][j] = remove_html_tags(instance.__dict__[i][j])
                    elif isinstance(instance.__dict__[i][j], list) or isinstance(instance.__dict__[i][j], dict):
                        instance.__dict__[i][j] = sanitise_fields(instance.__dict__[i][j])
                    if i in error_on_change and check != instance.__dict__[i][j]:
                        raise serializers.ValidationError("html tags included in field")
            
            elif isinstance(instance.__dict__[i], str) and not i in exclude:
                check = instance.__dict__[i]
                setattr(instance, i, remove_html_tags(instance.__dict__[i]))
                if i in error_on_change and check != instance.__dict__[i]:
                    #only fields that cannot be allowed to change through sanitisation just before saving will throw an error
                    raise serializers.ValidationError("html tags included in field")
            elif isinstance(instance.__dict__[i], str) and i in exclude:
                check = instance.__dict__[i]
                #even though excluded, we still check to remove script tags
                setattr(instance, i, remove_script_tags(instance.__dict__[i]))
                if i in error_on_change and check != instance.__dict__[i]:
                    #only fields that cannot be allowed to change through sanitisation just before saving will throw an error
                    raise serializers.ValidationError("script tags included in field")
            elif (isinstance(instance.__dict__[i], list) or isinstance(instance.__dict__[i], dict)) and i in exclude:
                #if we have reached this point, it means we have a json object with fields that are allowed to contain tags
                #we'll use . notation to identify sub fields that should be carried over to the exclude and error on change lists
                #NOTE: to allow sub fields to be sanitised, the parent field should be included in both lists required for their respective children
                sub_exclude_list = list(filter(lambda e:e.startswith(i+"."), exclude))
                exclude_list = list(map(lambda e:e.replace(i+".","",1), sub_exclude_list))
                #NOTE: a sub error on change list will require the parent field to be in the exclude list, to reach this point (but not necessarily in the error_on_change list)
                sub_error_on_change_list = list(filter(lambda e:e.startswith(i+"."), error_on_change))
                error_on_change_list = list(map(lambda e:e.replace(i+".","",1), sub_error_on_change_list))

                if isinstance(instance.__dict__[i], dict):
                    check = instance.__dict__[i]
                    instance.__dict__[i] = sanitise_fields(instance.__dict__[i], exclude=exclude_list, error_on_change=error_on_change_list)
                    if i in error_on_change and check != instance.__dict__[i]:
                        raise serializers.ValidationError("html tags included in field")
                elif isinstance(instance.__dict__[i], list):
                    for j in range(0, len(instance.__dict__[i])):
                        check = instance.__dict__[i][j]
                        if isinstance(instance.__dict__[i][j],str):
                            #strings in an excluded list will be treated as excluded
                            instance.__dict__[i][j] = remove_script_tags(instance.__dict__[i][j])
                        elif isinstance(instance.__dict__[i][j], list) or isinstance(instance.__dict__[i][j], dict):
                            instance.__dict__[i][j] = sanitise_fields(instance.__dict__[i][j], exclude=exclude_list, error_on_change=error_on_change_list)
                        if i in error_on_change and check != instance.__dict__[i][j]:
                            raise serializers.ValidationError("html tags included in field")
    else:
        remove_keys = []
        for i in instance:
            #for dicts we also check the keys - they are removed completely if not sanitary (should not change keys)
            original_key = i
            if isinstance(original_key, str):
                sanitised_key = remove_html_tags(i)
                if original_key != sanitised_key:
                    remove_keys.append(original_key)
                    continue

            #remove html tags for all string fields not in the exclude list
            if not i in exclude and (isinstance(instance[i], dict)):
                instance[i] = sanitise_fields(instance[i])

            elif isinstance(instance[i], list) and not i in exclude:
                for j in range(0, len(instance[i])):
                    check = instance[i][j]
                    if isinstance(instance[i][j],str):
                        instance[i][j] = remove_html_tags(instance[i][j])
                    elif isinstance(instance[i][j], list) or isinstance(instance[i][j], dict):
                        instance[i][j] = sanitise_fields(instance[i][j])
                    if i in error_on_change and check != instance[i][j]:
                        raise serializers.ValidationError("html tags included in field")

            else:
                if isinstance(instance[i], str) and not i in exclude:
                    check = instance[i]
                    instance[i] = remove_html_tags(instance[i])
                    if i in error_on_change and check != instance[i]:
                        #only fields that cannot be allowed to change through sanitisation just before saving will throw an error
                        raise serializers.ValidationError("html tags included in field")
                elif isinstance(instance[i], str) and i in exclude:
                    #even though excluded, we still check to remove script tags
                    instance[i] = remove_script_tags(instance[i])
                    if i in error_on_change and check != instance[i]:
                        #only fields that cannot be allowed to change through sanitisation just before saving will throw an error
                        raise serializers.ValidationError("script tags included in field")
                elif (isinstance(instance[i], list) or isinstance(instance[i], dict)) and i in exclude:
                    #if we have reached this point, it means we have a json object with fields that are allowed to contain tags
                    #we'll use . notation to identify sub fields that should be carried over to the exclude and error on change lists
                    #NOTE: to allow sub fields to be sanitised, the parent field should be included in both lists required for their respective children
                    sub_exclude_list = list(filter(lambda e:e.startswith(i+"."), exclude))
                    exclude_list = list(map(lambda e:e.replace(i+".","",1), sub_exclude_list))
                    #NOTE: a sub error on change list will require the parent field to be in the exclude list, to reach this point (but not necessarily in the error_on_change list)
                    sub_error_on_change_list = list(filter(lambda e:e.startswith(i+"."), error_on_change))
                    error_on_change_list = list(map(lambda e:e.replace(i+".","",1), sub_error_on_change_list))

                    if isinstance(instance[i], dict):
                        check = instance[i]
                        instance[i] = sanitise_fields(instance[i], exclude=exclude_list, error_on_change=error_on_change_list)
                        if i in error_on_change and check != instance[i]:
                            raise serializers.ValidationError("script tags included in field")
                    elif isinstance(instance[i], list):                        
                        for j in range(0, len(instance[i])):
                            check = instance[i][j]
                            if isinstance(instance[i][j],str):
                                #strings in an excluded list will be treated as excluded
                                instance[i][j] = remove_script_tags(instance[i][j])
                            elif isinstance(instance[i][j], list) or isinstance(instance[i][j], dict):
                                instance[i][j] = sanitise_fields(instance[i][j], exclude=exclude_list, error_on_change=error_on_change_list)
                            if i in error_on_change and check != instance[i][j]:
                                raise serializers.ValidationError("script tags included in field")
                    
        for i in remove_keys:
            del instance[i]
    return instance

def file_extension_valid(file, whitelist, model):
    _, extension = os.path.splitext(file)
    extension = extension.replace(".", "").lower()

    check = whitelist.filter(name=extension).filter(
        Q(model="all") | Q(model__iexact=model)
    )
    valid = check.exists()

    return valid

def check_file(file, model_name):
    from disturbance.components.main.models import FileExtensionWhitelist

    # check if extension in whitelist
    cache_key = settings.CACHE_KEY_FILE_EXTENSION_WHITELIST
    whitelist = cache.get(cache_key)
    if whitelist is None:
        whitelist = FileExtensionWhitelist.objects.all()
        cache.set(cache_key, whitelist, settings.CACHE_TIMEOUT_2_HOURS)

    valid = file_extension_valid(str(file), whitelist, model_name)

    if not valid:
        raise serializers.ValidationError("File type/extension not supported")

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
    template_group = 'apiary'
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
        coords = {'lng': wkb_geometry.x, 'lat': wkb_geometry.y}
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
        coords = {'lng': wkb_geometry.x, 'lat': wkb_geometry.y}
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

#NOTE: according to prior commit messages there was an explicit decision to only return an exact match on the site id - I have added better validation in line with this decision
def _get_vacant_apiary_site(search_text=''):
    from disturbance.components.proposals.models import ApiarySite
    queries = Q(is_vacant=True)
    if search_text and isinstance(search_text, int):
        queries &= Q(id=search_text)
    qs_vacant_site = ApiarySite.objects.filter(queries).distinct()
    return qs_vacant_site


def get_qs_vacant_site(search_text=''):
    from disturbance.components.proposals.models import ApiarySiteOnProposal
    from disturbance.components.approvals.models import ApiarySiteOnApproval

    qs_vacant_site = _get_vacant_apiary_site(search_text)
    apiary_site_proposal_ids = qs_vacant_site.all().values('proposal_link_for_vacant__id')
    
    qs_vacant_site_proposal = ApiarySiteOnProposal.objects.select_related(
            'apiary_site', 
            'proposal_apiary', 
            'proposal_apiary__proposal', 
            'proposal_apiary__target_approval_organisation', 
            'proposal_apiary__target_approval', 
            'proposal_apiary__originating_approval', 
            'site_category_draft', 
            'site_category_processed', 
            'apiary_site__latest_proposal_link', 
            'apiary_site__proposal_link_for_vacant',
            ).filter(Q(id__in=apiary_site_proposal_ids))

    # At any moment, either approval_link_for_vacant or proposal_link_for_vacant is True at most.  Never both are True.  (See make_vacant() method of the ApiarySite model)
    # Therefore qs_vacant_site_proposal and qs_vacant_site_approval shouldn't overlap each other
    apiary_site_approval_ids = qs_vacant_site.all().values('approval_link_for_vacant__id')
    qs_vacant_site_approval = ApiarySiteOnApproval.objects.select_related(
            'apiary_site', 
            'approval', 
            'site_category', 
            'apiary_site__latest_approval_link', 
            'apiary_site__approval_link_for_vacant',
            'approval__applicant',
            ).filter(id__in=apiary_site_approval_ids)

    return qs_vacant_site_proposal, qs_vacant_site_approval


def get_qs_denied_site(search_text=''):
    from disturbance.components.proposals.models import ApiarySite, ApiarySiteOnProposal

    q_include_proposal = Q()
    q_exclude_proposal = Q()

    # ApiarySite condition
    q_include_apiary_site = Q()
    q_include_apiary_site &= Q(latest_proposal_link__isnull=False)
    if search_text and isinstance(search_text, int):
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
    if search_text and isinstance(search_text, int):
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
    if search_text and isinstance(search_text, int):
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
    if search_text and isinstance(search_text, int):
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
    if search_text and isinstance(search_text, int):
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

def get_first_name(obj):

    if hasattr(obj,"legal_first_name") and obj.legal_first_name:
        return obj.legal_first_name
    elif hasattr(obj,"first_name") and obj.first_name:
        return obj.first_name

    return ""

def get_last_name(obj):

    if hasattr(obj,"legal_last_name") and obj.legal_last_name:
        return obj.legal_last_name
    elif hasattr(obj,"last_name") and obj.last_name:
        return obj.last_name

    return ""

def get_full_name(obj):
    return get_first_name(obj)+" "+get_last_name(obj)

def get_dob(obj):

    if hasattr(obj,"legal_dob") and obj.legal_dob:
        return obj.legal_dob
    if hasattr(obj,"dob") and obj.dob:
        return obj.dob

    return ""

def csvExportData(model, header, columns):
    
    csv_file = str(settings.BASE_DIR)+'/tmp/{}_{}_{}.csv'.format(model,uuid.uuid4(),int(datetime.now().timestamp()*100000))
    with open(csv_file, 'w', newline='') as new_file:
        writer = csv.writer(new_file)
        writer.writerow(header)
        for i in columns:
            writer.writerow(i)
    return csv_file

def excelExportData(model, header, columns):
    excel_file = str(settings.BASE_DIR)+'/tmp/{}_{}_{}.xlsx'.format(model,uuid.uuid4(),int(datetime.now().timestamp()*100000))
    workbook = xlsxwriter.Workbook(excel_file) 
    worksheet = workbook.add_worksheet("{} Report".format(model.capitalize()))
    format = workbook.add_format()

    col = 0 
    row = 0

    col_lens = [0]*len(header)

    for i in header:
        worksheet.write(row, col, str(i), format)
        col_lens[col] = len(str(i))+2
        worksheet.set_column(col, col, col_lens[col])
        col += 1
    col = 0 
    row += 1
    for i in columns:
        for j in i:
            worksheet.write(row, col, str(j), format)
            if len(str(j)) > col_lens[col]:
                col_lens[col] = len(str(j))+2
                worksheet.set_column(col, col, col_lens[col])
            col += 1
        col = 0
        row += 1

    workbook.close() 

    return excel_file

def getProposalExport(filters, num):
    from disturbance.components.proposals.models import Proposal

    qs = Proposal.objects.order_by("-lodgement_date")
    if filters:
        #lodged_on_from
        if "lodged_on_from" in filters and filters["lodged_on_from"]:
            qs = qs.filter(lodgement_date__gte=filters["lodged_on_from"])
        #lodged_on_to
        if "lodged_on_to" in filters and filters["lodged_on_to"]:
            qs = qs.filter(lodgement_date__lte=filters["lodged_on_to"])

    return qs[:num]

def getApprovalExport(filters, num):
    from disturbance.components.approvals.models import Approval

    qs = Approval.objects.order_by("-issue_date")
    if filters:
        #lodged_on_from
        if "issued_from" in filters and filters["issued_from"]:
            qs = qs.filter(issue_date__gte=filters["issued_from"])
        #lodged_on_to
        if "issued_to" in filters and filters["issued_to"]:
            qs = qs.filter(issue_date__lte=filters["issued_to"])

    return qs[:num]

def exportModelData(model, filters, num_records):

    if not num_records:
        num_records = MAX_NUM_ROWS_MODEL_EXPORT
    else:
        num_records = min(num_records, MAX_NUM_ROWS_MODEL_EXPORT)

    if model == "proposal":
        return getProposalExport(filters, num_records)
    if model == "approval":
        return getApprovalExport(filters, num_records)
    else:
        return

def getProposalExportFields(data):
    header = ["Lodgement Number", "Application Type", "Submitter", "Applicant", "Status", "Lodged On", "Assigned Officer", "Invoice Reference"]

    columns = list(
        data.values_list(
            "lodgement_number",
            "proposal_type",
            "submitter_id",
            "applicant__property_cache__name",
            "proxy_applicant_id",
            "processing_status",
            "lodgement_date",
            "assigned_officer_id",
            "fee_invoice_references"
        )
    )

    user_ids = {
        proposal[i]
        for proposal in columns
        for i in (2, 4, 7)
        if proposal[i] is not None
    }

    email_users = EmailUser.objects.filter(id__in=user_ids)
    
    user_map = {
        user.id: f"{user.first_name} {user.last_name}".strip()
        for user in email_users
    }

    columns = list(map(lambda proposal: (
        proposal[0],
        proposal[1].replace("_"," "),
        user_map.get(proposal[2]),
        proposal[3] if proposal[3] else user_map.get(proposal[4]) if user_map.get(proposal[4]) else user_map.get(proposal[2]),
        proposal[5].replace("_"," "),
        proposal[6] if proposal[6] else "",
        user_map.get(proposal[7]) if user_map.get(proposal[7]) else "",
        proposal[8] if proposal[8] else "",
    ),columns))

    return header, columns

def getApprovalExportFields(data):
    header = ["Number", "Holder", "Issue Date", "Start Date", "Expiry Date"]

    columns = list(
        data.values_list(
            "lodgement_number",
            "applicant__property_cache__name",
            "proxy_applicant_id",
            "issue_date",
            "start_date",
            "expiry_date",
        )
    )

    user_ids = {
        approval[i]
        for approval in columns
        for i in (2,)
        if approval[i] is not None
    }

    email_users = EmailUser.objects.filter(id__in=user_ids)
    
    user_map = {
        user.id: f"{user.first_name} {user.last_name}".strip()
        for user in email_users
    }
    columns = list(map(lambda approval: (
        approval[0],
        approval[1] if approval[1] else user_map.get(approval[2]),
        approval[3],
        approval[4],
        approval[5],
    ),columns))

    return header, columns

def formatExportData(model, data, format):
    
    if model == "proposal":
        header, columns = getProposalExportFields(data)
    if model == "approval":
        header, columns = getApprovalExportFields(data)
    else:
        return

    if os.path.isdir(str(settings.BASE_DIR)+'/tmp/') is False:
        os.makedirs(str(settings.BASE_DIR)+'/tmp/')

    if format == "excel":
        file_name = excelExportData(model, header, columns)
        file_buffer = None
        with open(file_name, 'rb') as f:
            file_buffer = f.read()    
        return ('Apiary - {} Report.xlsx'.format(model.capitalize()), file_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        file_name =  csvExportData(model, header, columns)
        file_buffer = None
        with open(file_name, 'rb') as f:
            file_buffer = f.read()    
        return ('Apiary - {} Report.csv'.format(model.capitalize()), file_buffer, 'application/csv')