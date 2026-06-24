"""
Suspend ApiarySite id=8183 by setting site_status='suspended' on its
current latest_approval_link (ApiarySiteOnApproval record).

This site was omitted from the 33-site cancel batch (cancel_sites_to_dbca.py)
and requires a different action: suspend (not cancel/transfer to DBCA).

Run (dry run first):
    python manage.py shell -c "exec(open('disturbance/scripts/suspend_site_8183.py').read())"

Then for real (requires explicit ACTUAL_RUN=true):
    ACTUAL_RUN=true python manage.py shell -c "exec(open('disturbance/scripts/suspend_site_8183.py').read())"
"""

import os

from django.db import transaction

from disturbance.components.proposals.models import ApiarySite
from disturbance.settings import SITE_STATUS_SUSPENDED

# --- Configuration -----------------------------------------------------------

TARGET_SITE_ID = 8183

# Safe by default: only runs actual changes when ACTUAL_RUN=true is explicitly set
DRY_RUN = os.environ.get("ACTUAL_RUN", "").lower() != "true"

# -----------------------------------------------------------------------------

print("=" * 70)
print("suspend_site_8183.py  |  DRY_RUN={}".format(DRY_RUN))
print("=" * 70)

try:
    site = ApiarySite.objects.get(id=TARGET_SITE_ID)
except ApiarySite.DoesNotExist:
    print("ERROR: ApiarySite id={} does not exist".format(TARGET_SITE_ID))
    raise SystemExit(1)

link = site.latest_approval_link
if not link:
    print("ERROR: ApiarySite id={} has no latest_approval_link".format(TARGET_SITE_ID))
    raise SystemExit(1)

print("Site id          : {}".format(site.id))
print("latest_approval_link id : {}".format(link.id))
print("  approval id    : {}".format(link.approval_id))
print("  approval lodgement : {!r}".format(link.approval.lodgement_number))
print("  current site_status: {!r}".format(link.site_status))
print()

if link.site_status == SITE_STATUS_SUSPENDED:
    print("Site {} is already suspended — nothing to do.".format(TARGET_SITE_ID))
    raise SystemExit(0)

print(
    "Planned action: set ApiarySiteOnApproval id={} site_status {!r} -> {!r}".format(
        link.id, link.site_status, SITE_STATUS_SUSPENDED
    )
)
print()

if DRY_RUN:
    print("DRY RUN complete - no changes made.")
    print("Set ACTUAL_RUN=true to apply changes.")
else:
    print("Applying change inside a transaction...")
    with transaction.atomic():
        link.site_status = SITE_STATUS_SUSPENDED
        link.save()
        print(
            "  Done: ApiarySiteOnApproval id={} site_status -> {!r}".format(
                link.id, link.site_status
            )
        )
    print()
    print("Change committed successfully.")

print()
print("Done.")
