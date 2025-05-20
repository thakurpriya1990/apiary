import datetime
import json
import logging
import os

import pytz
from django.contrib.auth.models import Group
from django.contrib.gis.geos import GEOSGeometry, fromfile
from django.core.exceptions import MultipleObjectsReturned
import apiary.settings

from apiary import settings
from apiary.components.main.models import ApplicationType, GlobalSettings, ApiaryGlobalSettings, RegionDbca, \
    DistrictDbca, CategoryDbca, WaCoast
from apiary.components.main.utils import overwrite_districts_polygons, overwrite_regions_polygons
from apiary.components.proposals.models import ApiarySiteFeeType, SiteCategory, ApiarySiteFee, ProposalType, \
    ApiaryAnnualRentalFeePeriodStartDate, ApiaryAnnualRentalFeeRunDate, ApiaryAnnualRentalFee

logger = logging.getLogger(__name__)


class DefaultDataManager(object):

    def insert_wa_coast(self, file_path, smoothed):
        # WA coast line: store geometries
        count = WaCoast.objects.filter(smoothed=smoothed).count()
        if not count > 0:
            with open(file_path) as f:
                data = json.load(f)

                for region in data['features']:
                    json_str = json.dumps(region['geometry'])
                    geom = GEOSGeometry(json_str)
                    coast_obj = WaCoast.objects.create(
                        wkb_geometry=geom,
                        type=region['properties']['TYPE'],
                        source=region['properties']['SOURCE'],
                        smoothed=smoothed,
                    )
                    coast_obj.save()
                    logger.info(
                        "Created coast line record, id:{}, type:{}, smoothed:{}".format(coast_obj.id, coast_obj.type,
                                                                                        smoothed))
                logger.info("{} coastline polygons have been created".format(len(data['features'])))

    def __init__(self):
        # Groups
        CUSTOM_GROUPS = [settings.ADMIN_GROUP, settings.APIARY_ADMIN_GROUP, settings.DAS_APIARY_ADMIN_GROUP, settings.APIARY_PAYMENTS_OFFICERS_GROUP,]
        for group_name in CUSTOM_GROUPS:
            try:
                group, created = Group.objects.get_or_create(name=group_name)
                if created:
                    logger.info("Created group: {}".format(group_name))
            except Exception as e:
                logger.error('{}, Group name: {}'.format(e, group_name))

        # WA coast (original)
        file_path_original = os.path.join(settings.BASE_DIR, 'disturbance', 'static', 'disturbance', 'gis', 'wa_coast.geojson')
        self.insert_wa_coast(file_path_original, False)

        # WA coast (smoothed)
        file_path_smoothed = os.path.join(settings.BASE_DIR, 'disturbance', 'static', 'disturbance', 'gis', 'wa_coast_smoothed.geojson')
        self.insert_wa_coast(file_path_smoothed, True)

        # Category: store south west apiary zone
        path_to_zones = os.path.join(settings.BASE_DIR, 'disturbance', 'static', 'disturbance', 'gis', 'sw_apiary_zone.geojson')
        count = CategoryDbca.objects.all().count()
        if not count > 0:
            with open(path_to_zones) as f:
                data = json.load(f)

                for area in data['features']:
                    json_str = json.dumps(area['geometry'])
                    geom = GEOSGeometry(json_str)
                    region_obj = CategoryDbca.objects.create(
                        wkb_geometry=geom,
                        category_name='south_west',  # We only define 'south west' area.  The others are 'remote' category
                    )
                    region_obj.save()
                    logger.info("Category 'south west' created")

        # Region: store geometries
        count = RegionDbca.objects.filter(enabled=True).count()
        if not count > 0:
            # Only when there are no enabled polygons, load polygons from the default geojson file
            path_to_regions = os.path.join(
                settings.BASE_DIR, 'disturbance', 'static', 'disturbance', 'DBCA_Regions.geojson'
                )
            overwrite_regions_polygons(path_to_regions)

        # District: store geometries
        count = DistrictDbca.objects.filter(enabled=True).count()
        if not count > 0:
            # Only when there are no enabled polygons, load polygons from the default geojson file
            path_to_districts = os.path.join(
                settings.BASE_DIR, 'disturbance', 'static', 'disturbance', 'DBCA_Districts.geojson'
                )
            overwrite_districts_polygons(path_to_districts)

        # Store
        for item in GlobalSettings.default_values:
            try:
                obj, created = GlobalSettings.objects.get_or_create(key=item[0])
                if created:
                    obj.value = item[1]
                    obj.save()
                    logger.info("Created {}: {}".format(item[0], item[1]))
            except Exception as e:
                logger.error('{}, Key: {}'.format(e, item[0]))

        # Store
        for item in ApiaryGlobalSettings.default_values:
            try:
                obj, created = ApiaryGlobalSettings.objects.get_or_create(key=item[0])
                if created:
                    obj.value = item[1]
                    obj.save()
                    logger.info("Created {}: {}".format(item[0], item[1]))
            except Exception as e:
                logger.error('{}, Key: {}'.format(e, item[0]))

        # Store default ApiarySiteFeeType data
        for item in ApiarySiteFeeType.FEE_TYPE_CHOICES:
            try:
                obj, created = ApiarySiteFeeType.objects.get_or_create(name=item[0])
                if created:
                    logger.info("Created apiary site fee type: %s" % obj)
            except Exception as e:
                logger.error('{}, Name: {}'.format(e, item[0]))

        # Store default SiteCategory data
        for item in SiteCategory.CATEGORY_CHOICES:
            try:
                obj, created = SiteCategory.objects.get_or_create(name=item[0])
                if created:
                    logger.info("Created apiary site category: %s" % obj)
            except Exception as e:
                logger.error('{}, Name: {}'.format(e, item[0]))

        # Store default ApiarySiteFee
        today_local = datetime.datetime.now(pytz.timezone(settings.TIME_ZONE)).date()
        for type_choice in ApiarySiteFeeType.FEE_TYPE_CHOICES:
            fee_type = ApiarySiteFeeType.objects.get(name=type_choice[0])
            for cat_choice in SiteCategory.CATEGORY_CHOICES:
                cat = SiteCategory.objects.get(name=cat_choice[0])
                site_fees = ApiarySiteFee.objects.filter(apiary_site_fee_type=fee_type, site_category=cat, date_of_enforcement__lte=today_local)
                if not site_fees.count():
                    new_fee = ApiarySiteFee.objects.create(apiary_site_fee_type=fee_type, site_category=cat, date_of_enforcement=today_local)
                    if fee_type == ApiarySiteFeeType.FEE_TYPE_RENEWAL:
                        new_fee.amount = 0
                    else:
                        new_fee.amount = 100
                    new_fee.save()
                    logger.info("Created apiary site fee: %s" % new_fee)

        # Annual site fee period start date
        for item in ApiaryAnnualRentalFeePeriodStartDate.NAME_CHOICES:
            try:
                obj, created = ApiaryAnnualRentalFeePeriodStartDate.objects.get_or_create(name=item[0])
                if created:
                    obj.period_start_date = datetime.date(year=2020, month=7, day=1)
                    obj.save()
                    logger.info("Created the period start date for the annual site fee: %s" % obj)
            except Exception as e:
                logger.error('{}, Name: {}'.format(e, item[0]))

        # Run cron job date for the annual site fee
        for item in ApiaryAnnualRentalFeeRunDate.NAME_CHOICES:
            try:
                obj, created = ApiaryAnnualRentalFeeRunDate.objects.get_or_create(name=item[0])
                if created:
                    obj.date_run_cron = datetime.date(year=2020, month=6, day=17)
                    obj.save()
                    logger.info("Created the cron job run date for the annual site fee: %s" % obj)
            except Exception as e:
                logger.error('{}, Name: {}'.format(e, item[0]))

        # Annual Site Fee
        arfs = ApiaryAnnualRentalFee.objects.filter(date_from__lte=today_local)
        if arfs.count() <= 0:
            try:
                obj, created = ApiaryAnnualRentalFee.objects.get_or_create(amount_south_west=25.00, amount_remote=20, date_from=(today_local - datetime.timedelta(days=1000)))
                if created:
                    logger.info("Created an apiary_annual_rental_fee: %s" % obj)
            except Exception as e:
                logger.error(e)

        # Store default
        for type_name in ApplicationType.APPLICATION_TYPES:
            q_set = ApplicationType.objects.filter(name=type_name[0])
            if not q_set:
                domain_used = 'apiary' if type_name[0] in ApplicationType.APIARY_APPLICATION_TYPES else 'das'
                visibility = False if type_name[0] in ApplicationType.APIARY_APPLICATION_TYPES else True  # Apiary is hidden until Jan 2021
                obj = ApplicationType.objects.create(
                    name=type_name[0],
                    application_fee=0,
                    oracle_code_application='',
                    domain_used=domain_used,
                    visible=visibility,
                )
                logger.info("Created application type: %s" % obj)

        for name in [ApplicationType.APIARY, ApplicationType.TEMPORARY_USE, ApplicationType.SITE_TRANSFER]:
            qs = ProposalType.objects.filter(name=name)
            if not qs:
                obj = ProposalType.objects.create(name=name, schema=[{}])
                if obj:
                    logger.info("Created proposal type: %s" % obj)


