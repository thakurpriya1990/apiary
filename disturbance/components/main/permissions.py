from rest_framework.permissions import BasePermission

from ledger_api_client.helpers import is_payment_admin

class PaymentOfficerPermission(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_superuser or is_payment_admin(request)