from rest_framework.permissions import BasePermission

from disturbance.helpers import (
    is_internal,
)

class InternalApprovalPermission(BasePermission):
    """
    Approval permission for internal users, essentially any member of 
    any of the existing internal system groups

    Intended to be non-specific with regards to the given approval type
    """

    def has_permission(self, request, view):
        return is_internal(request)