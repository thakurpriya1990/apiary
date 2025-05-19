from django.core.management.base import BaseCommand
from apiary.components.proposals.models import ProposalType


class Command(BaseCommand):
    help = 'Change the status of Compliances from future to due when they are close to due date'

    def handle(self, *args, **options):
        proposal_type = ProposalType.objects.filter(name='Disturbance').latest('version')
        print('latest version {}'.format(proposal_type))
