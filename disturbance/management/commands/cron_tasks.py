import logging
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

LOGFILE = "logs/cron_tasks.log"


class Command(BaseCommand):
    help = "Run the Disturbance Cron tasks"

    def handle(self, *args, **options):
        stdout_redirect = " | tee -a {}".format(LOGFILE)
        subprocess.call(
            "cat /dev/null > {}".format(LOGFILE), shell=True
        )  # empty the log file

        logger.info("Running command {}".format(__name__))
        subprocess.call(
            "python manage.py update_compliance_status" + stdout_redirect, shell=True
        )
        subprocess.call(
            "python manage.py send_compliance_reminder" + stdout_redirect, shell=True
        )
        subprocess.call(
            "python manage.py update_approval_status" + stdout_redirect, shell=True
        )
        subprocess.call(
            "python manage.py expire_approvals" + stdout_redirect, shell=True
        )
        subprocess.call(
            "python manage.py approval_renewal_notices" + stdout_redirect, shell=True
        )
        subprocess.call(
            "python manage.py send_assessment_reminder" + stdout_redirect, shell=True
        )
        subprocess.call(
            "python manage.py weekly_assessment_reminder" + stdout_redirect, shell=True
        )
        subprocess.call(
            "python manage.py send_annual_rental_fee_invoice" + stdout_redirect,
            shell=True,
        )
        subprocess.call(
            "python manage.py save_apiary_sites" + stdout_redirect, shell=True
        )

        logger.info("Command {} completed".format(__name__))
        self.send_email()

    def send_email(self):
        log_txt = Path(LOGFILE).read_text()
        # subject = '{} - Cronjob'.format(settings.SYSTEM_NAME_SHORT)
        subject = "DAS-Apiary - Cronjob"
        body = ""
        to = (
            settings.CRON_NOTIFICATION_EMAIL
            if isinstance(settings.NOTIFICATION_EMAIL, list)
            else [settings.CRON_NOTIFICATION_EMAIL]
        )
        send_mail(
            subject,
            body,
            settings.EMAIL_FROM,
            to,
            fail_silently=False,
            html_message=log_txt,
        )
