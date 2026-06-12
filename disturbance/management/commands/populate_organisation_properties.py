from django.core.management.base import BaseCommand
from disturbance.components.organisations.models import Organisation
from django.db.models import Q

import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **options):
        
        logger.info("Checking for organisations that are missing Org name or ABN from property cache.")

        orgs_without_properties = Organisation.objects.filter(Q(property_cache__name__isnull=True)|Q(property_cache__abn__isnull=True))

        logger.info(f"{orgs_without_properties.count()} org records to be updated.")

        for org in orgs_without_properties:
            org.update_property_cache()

        logger.info(f"{orgs_without_properties.count()} org records updated.")