import logging

import django_cron
from django.core import management

log = logging.getLogger(__name__)


class CronJobProcessReportQueue(django_cron.CronJobBase):
    """Process pending report export jobs from the JobQueue every 2 minutes."""

    schedule = django_cron.Schedule(run_weekly_on_days=[0, 1, 2, 3, 4, 5, 6], run_every_mins=2)
    code = "apiary.process_report_queue"

    def do(self) -> None:
        log.info("Process report queue cron job triggered, running...")
        management.call_command("run_queue_job")
        return "Job Completed Successfully"
