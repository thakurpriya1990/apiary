from django.db.models import Func, FloatField, Value, F
from django.db.models import CharField
from django.contrib.postgres.fields import ArrayField
from django.db.models.functions import JSONObject, Concat

def annotate_apiary_site_on_approval_processed_geometry(qs):
    
    annotated = qs.annotate(
            lat=Func("wkb_geometry", function="ST_Y", output_field=FloatField()),
            lng=Func("wkb_geometry", function="ST_X", output_field=FloatField()),
        ).annotate(
            stable_coords=JSONObject(
                lng=F('lng'),
                lat=F('lat'),
            )
        ).annotate(
            site_guid=F("apiary_site__site_guid")
        ).annotate(
            status=F("site_status")
        ).annotate(
            is_vacant=F("apiary_site__is_vacant")
        ).annotate(
            geometry=JSONObject(
                type=Value("Point"), #we only serve points from here
                coordinates=Func(
                    Concat(F('lng'),Value(","),F('lat'),output_field=CharField()),
                    Value(','),
                    function='string_to_array',
                    output_field=ArrayField(FloatField()),
                )
            )
        ).annotate(
            type=Value("Feature") #we are returning a list of features
        ).annotate(
            properties=JSONObject(
                stable_coords=F('stable_coords'),
                site_guid=F('site_guid'),
                is_vacant=F('is_vacant'),
                available=F('available'),
                wkb_geometry=F('wkb_geometry'),
                site_category=F('site_category__name'),
                status=F('status'),
                licensed_site=F('licensed_site'),
                batch_no=F('batch_no'),
                approval_cpc_date=F('approval_cpc_date'),
                approval_minister_date=F('approval_minister_date'),
                map_ref=F('map_ref'),
                forest_block=F('forest_block'),
                cog=F('cog'),
                roadtrack=F('roadtrack'),
                zone=F('zone'),
                catchment=F('catchment'),
                dra_permit=F('dra_permit'),
            )
        ).values(
            'id',
            'type',
            'geometry',
            'properties',
        )

    return annotated