from rest_framework.permissions import BasePermission

from disturbance.helpers import (
    is_internal,
    is_apiary_assessor,
    is_apiary_approver,
    is_apiary_referrer,
)

class InternalProposalPermission(BasePermission):
    """
    Proposal permission for internal users, essentially any member of 
    any of the existing internal system groups

    Intended to be non-specific with regards to the given proposal type
    """

    def has_permission(self, request, view):
        return is_internal(request)

class ProposalAssessorPermission(BasePermission):

    def has_permission(self, request, view):
        return is_apiary_assessor(request)
    
class ProposalApproverPermission(BasePermission):

    def has_permission(self, request, view):
        return is_apiary_approver(request)
    
class ProposalReferrerPermission(BasePermission):

    def has_permission(self, request, view):
        return is_apiary_referrer(request)