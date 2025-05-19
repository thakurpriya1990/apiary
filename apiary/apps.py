from __future__ import unicode_literals

from django.apps import AppConfig

class ApiaryConfig(AppConfig):
    name = 'apiary'

    run_once = False
    def ready(self):
        if not self.run_once:
            from apiary.components.organisations import signals
            from apiary.components.proposals import signals
            from apiary.components.approvals import signals

        self.run_once = True
