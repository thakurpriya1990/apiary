import os

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from pathlib import Path

from apiary.settings import BASE_DIR
from apiary.utils.migration_utils_pd import ApiaryLicenceReader
from apiary.components.proposals.models import Proposal
from apiary.components.approvals.models import Approval
import datetime
import time

import itertools
import subprocess

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the Apiary Migrations Script \n' \
           'python manage_ds.py apiary_migration_script --filename disturbance/utils/csv/apiary_migration_file_20May2022.xlsx'

    def add_arguments(self, parser):
        parser.add_argument('--filename', type=str)

    def handle(self, *args, **options):
        filename = options['filename']

        if not filename:
            filename = os.path.join(BASE_DIR, 'tmp', 'test.xlsx')
        exists = os.path.isfile(filename)

        if exists:
            t_start = time.time()

            alr=ApiaryLicenceReader(filename)
            alr.run_migration()

            t_end = time.time()
            print('TIME TAKEN: {}'.format(t_end - t_start))

            # proposals = Proposal.objects.filter(migrated=True).count()
            # approvals = Approval.objects.filter(migrated=True).count()
            # print(f'Proposals {proposals}, Approvals {approvals}')
        else:
            print('File: {} does not exist.'.format(filename))
