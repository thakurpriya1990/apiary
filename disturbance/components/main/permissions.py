from rest_framework.permissions import BasePermission

from ledger_api_client.helpers import is_payment_admin

class PaymentOfficerPermission(BasePermission):
    """
    Approval permission for internal users, essentially any member of 
    any of the existing internal system groups

    Intended to be non-specific with regards to the given approval type
    """

    def has_permission(self, request, view):
        return request.user.is_superuser or is_payment_admin(request)