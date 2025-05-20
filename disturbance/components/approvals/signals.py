from django.db.models.signals import post_save
from django.dispatch import receiver

from apiary.components.approvals.models import ApiarySiteOnApproval
from apiary.settings import SITE_STATUS_TRANSFERRED


class ApiarySiteOnApprovalListener(object):
    """
    Event listener for the ApiarySiteOnApproval
    """
    @staticmethod
    @receiver(post_save, sender=ApiarySiteOnApproval)
    def _post_save(sender, instance, **kwargs):
        if instance.site_status == SITE_STATUS_TRANSFERRED:
            # This instance (ApiarySiteOnApproval object) was updated because of the apiary site has been transferred.
            # In that case, we don't want to update apiary_site.latest_approval_link.
            pass
        else:
            instance.apiary_site.latest_approval_link = instance
            instance.apiary_site.save()
            print('ApiarySite: {} updated its latest_approval_link: {}'.format(instance.apiary_site.id, instance))

