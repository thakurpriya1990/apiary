from __future__ import unicode_literals

from django.apps import AppConfig

class DisturbanceConfig(AppConfig):
    name = 'disturbance'

    run_once = False
    def ready(self):
        if not self.run_once:
            from disturbance.components.main import models
            from disturbance.components.organisations import models
            from disturbance.components.users import models
            from disturbance.components.proposals import models
            from disturbance.components.approvals import models
            from disturbance.components.compliances import models
            from disturbance.components.ap_payments import models
            # from disturbance.components.history import models

            from disturbance.components.organisations import signals
            from disturbance.components.proposals import signals
            from disturbance.components.approvals import signals

        self.run_once = True
