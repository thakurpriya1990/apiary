"""
Check if a DBCA Approval already exists, and inspect Approval 1173's proposal.

Run with:
    python manage.py shell_plus < scripts/check_dbca_approval.py
"""

from disturbance.components.approvals.models import Approval
from disturbance.components.organisations.models import Organisation

DBCA_ORG_ID = 2
SOURCE_APPROVAL_ID = 1173

print("=" * 70)
print(f"Existing Approvals for Organisation id={DBCA_ORG_ID} (DBCA)")
print("=" * 70)
dbca_approvals = Approval.objects.filter(applicant_id=DBCA_ORG_ID, apiary_approval=True)
if dbca_approvals.exists():
    for a in dbca_approvals:
        site_count = a.apiary_sites.count()
        print(f"  Approval id={a.id}  lodgement_number={a.lodgement_number!r}  status={a.status!r}  sites={site_count}")
else:
    print("  (none found)")

print()
print("=" * 70)
print(f"Approval {SOURCE_APPROVAL_ID} - key fields")
print("=" * 70)
try:
    a = Approval.objects.get(id=SOURCE_APPROVAL_ID)
    print(f"  lodgement_number : {a.lodgement_number!r}")
    print(f"  status           : {a.status!r}")
    print(f"  apiary_approval  : {a.apiary_approval}")
    print(f"  current_proposal : id={a.current_proposal_id}  type={a.current_proposal.application_type.name!r}")
    print(f"  issue_date       : {a.issue_date}")
    print(f"  start_date       : {a.start_date}")
    print(f"  expiry_date      : {a.expiry_date}")
    print(f"  migrated         : {a.migrated}")
except Approval.DoesNotExist:
    print(f"  Approval {SOURCE_APPROVAL_ID} not found")

print()
print("Done.")
