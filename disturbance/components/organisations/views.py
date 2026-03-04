from disturbance.components.organisations.models import Organisation
from reversion_compare.views import HistoryCompareDetailView

#TODO on-cleanup (fix or remove all history compare views (they are not secured!))
#class OrganisationHistoryCompareView(HistoryCompareDetailView):
#    """
#    View for reversion_compare
#    """
#    model = Organisation
#    template_name = 'disturbance/reversion_history.html'
