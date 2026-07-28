import decimal

import orjson
from django.db.models.query import QuerySet
from rest_framework.renderers import BaseRenderer


def django_fallback(obj):
    """Converts types that orjson cannot natively process."""
    # Force QuerySets into standard Python lists
    if isinstance(obj, QuerySet):
        return list(obj)

    # Safely convert Django functional proxies / lazy strings
    if isinstance(obj, decimal.Decimal) or hasattr(obj, "str"):
        return str(obj)

    raise TypeError(f"Type {type(obj)} is not JSON serializable")


class ORJSONRenderer(BaseRenderer):
    media_type = "application/json"
    format = "json"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""

        return orjson.dumps(
            data,
            default=django_fallback,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
        )
