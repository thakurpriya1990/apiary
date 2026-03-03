from django.db.models import JSONField, Func, FloatField, Value, F
from django.db.models.functions import JSONObject, Cast

def annotate_apiary_site_on_approval_geometry(qs):
    
    annotated = qs.annotate(
            lat=Func("wkb_geometry", function="ST_Y", output_field=FloatField()),
            lng=Func("wkb_geometry", function="ST_X", output_field=FloatField()),
        ).annotate(
            stable_coords=JSONObject(
                lng=F('lng'),
                lat=F('lat'),
            )
        ).annotate(
            site_id=F("apiary_site__id")
        ).annotate(
            site_guid=F("apiary_site__site_guid")
        ).annotate(
            status=F("site_status")
        ).annotate(
            is_vacant=F("apiary_site__is_vacant")
        ).annotate(
            geometry=JSONObject(
                type=Value("Point"),
                coordinates=Func(
                    Cast(F('lng'), FloatField()),
                    Cast(F('lat'), FloatField()),
                    function='jsonb_build_array',
                    output_field=JSONField(),
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
            'site_id',
            'type',
            'geometry',
            'properties',
        )
    
    #transform site_id to id NOTE: this is not ideal, but the original serializer overwrote id so for now we have to as well...
    #TODO on cleanup - change all references to this dataset to site_id instead of id
    for row in annotated:
        row["id"] = row.pop("site_id")

    return annotated

def annotate_apiary_site_on_approval_min_geometry(qs):
    
    annotated = qs.annotate(
            lat=Func("wkb_geometry", function="ST_Y", output_field=FloatField()),
            lng=Func("wkb_geometry", function="ST_X", output_field=FloatField()),
        ).annotate(
            stable_coords=JSONObject(
                lng=F('lng'),
                lat=F('lat'),
            )
        ).annotate(
            site_id=F("apiary_site__id")
        ).annotate(
            site_guid=F("apiary_site__site_guid")
        ).annotate(
            status=F("site_status")
        ).annotate(
            is_vacant=F("apiary_site__is_vacant")
        ).annotate(
            lodgement_number=F("approval__lodgement_number")
        ).annotate(
            geometry=JSONObject(
                type=Value("Point"),
                coordinates=Func(
                    Cast(F('lng'), FloatField()),
                    Cast(F('lat'), FloatField()),
                    function='jsonb_build_array',
                    output_field=JSONField(),
                )
            )
        ).annotate(
            type=Value("Feature") #we are returning a list of features
        ).annotate(
            properties=JSONObject(
                stable_coords=F('stable_coords'),
                site_guid=F('site_guid'),
                is_vacant=F('is_vacant'),
                site_category=F('site_category__name'),
                status=F('status'),
                available=F('available'),
                approval_id=F('approval_id'),
                approval_lodgement_number=F('lodgement_number'),
            )
        ).values(
            'site_id',
            'type',
            'geometry',
            'properties',
        )
    
    for row in annotated:
        row["id"] = row.pop("site_id")

    return annotated