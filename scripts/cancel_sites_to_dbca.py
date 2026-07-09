"""
Cancel target ApiarySites by:
  1. Creating ApiarySiteOnApproval records on the DBCA Approval (id=1137)
     with site_status='not_to_be_reissued'
  2. Updating ApiarySite.latest_approval_link to the new records
  3. Setting the old ApiarySiteOnApproval records on Approval 1173
     to site_status='transferred'

The 'make vacant' button remains available because site_status is
'not_to_be_reissued' on the new latest_approval_link.

Run (dry run first):
    python manage.py shell -c "exec(open('scripts/cancel_sites_to_dbca.py').read())"

Then for real (requires explicit ACTUAL_RUN=true):
    ACTUAL_RUN=true python manage.py shell -c "exec(open('scripts/cancel_sites_to_dbca.py').read())"
"""

import os

from django.db import transaction

from disturbance.components.approvals.models import ApiarySiteOnApproval, Approval
from disturbance.components.proposals.models import ApiarySite
from disturbance.settings import SITE_STATUS_NOT_TO_BE_REISSUED, SITE_STATUS_TRANSFERRED

# --- Configuration -----------------------------------------------------------

TARGET_SITE_IDS = [
    7805,
    7806,
    7807,
    7808,
    7809,
    8179,
    8196,
    8199,
    8213,
    8303,
    8535,
    8577,
    8580,
    8617,
    8620,
    8684,
    8685,
    8686,
    8690,
    8691,
    8789,
    8946,
    8967,
    9074,
    9088,
    9111,
    9112,
    9113,
    9114,
    9115,
    9116,
    9117,
    9118,
]

DBCA_APPROVAL_ID = 1137  # Approval for Organisation id=2 (DBCA), lodgement A000793
SOURCE_APPROVAL_ID = 1173  # Current approval holding the target sites

# Safe by default: only runs actual changes when ACTUAL_RUN=true is explicitly set
DRY_RUN = os.environ.get("ACTUAL_RUN", "").lower() != "true"

# -----------------------------------------------------------------------------

print("=" * 70)
print("cancel_sites_to_dbca.py  |  DRY_RUN={}".format(DRY_RUN))
print("=" * 70)

dbca_approval = Approval.objects.get(id=DBCA_APPROVAL_ID)
source_approval = Approval.objects.get(id=SOURCE_APPROVAL_ID)

print(
    "DBCA Approval   : id={}  lodgement={!r}  status={!r}".format(
        dbca_approval.id, dbca_approval.lodgement_number, dbca_approval.status
    )
)
print(
    "Source Approval : id={}  lodgement={!r}  status={!r}".format(
        source_approval.id, source_approval.lodgement_number, source_approval.status
    )
)
print()

errors = []
actions = []

for site_id in sorted(TARGET_SITE_IDS):
    try:
        site = ApiarySite.objects.get(id=site_id)
    except ApiarySite.DoesNotExist:
        errors.append("  ERROR: ApiarySite id={} does not exist".format(site_id))
        continue

    try:
        old_link = ApiarySiteOnApproval.objects.get(
            apiary_site=site, approval=source_approval
        )
    except ApiarySiteOnApproval.DoesNotExist:
        errors.append(
            "  ERROR: Site {} has no ApiarySiteOnApproval on Approval {}".format(
                site_id, SOURCE_APPROVAL_ID
            )
        )
        continue

    existing_dbca_link = ApiarySiteOnApproval.objects.filter(
        apiary_site=site, approval=dbca_approval
    ).first()

    if existing_dbca_link:
        actions.append(
            {
                "site_id": site_id,
                "action": "update_existing_dbca_link",
                "dbca_link_id": existing_dbca_link.id,
                "old_link_id": old_link.id,
                "old_link_status": old_link.site_status,
                "existing_dbca_status": existing_dbca_link.site_status,
            }
        )
    else:
        actions.append(
            {
                "site_id": site_id,
                "action": "create_new_dbca_link",
                "old_link_id": old_link.id,
                "old_link_status": old_link.site_status,
                "wkb_geometry": old_link.wkb_geometry,
                "site_category_id": old_link.site_category_id,
                "licensed_site": old_link.licensed_site,
            }
        )

print("=" * 70)
print("Planned actions")
print("=" * 70)
create_count = sum(1 for a in actions if a["action"] == "create_new_dbca_link")
update_count = sum(1 for a in actions if a["action"] == "update_existing_dbca_link")
print("  Sites to process           : {}".format(len(actions)))
print("  New ApiarySiteOnApproval   : {}".format(create_count))
print("  Update existing (on DBCA)  : {}".format(update_count))
print()

for a in actions:
    if a["action"] == "create_new_dbca_link":
        print(
            "  Site {}: CREATE new link on Approval {} (site_status='{}'), "
            "set old link {} -> '{}', update latest_approval_link".format(
                a["site_id"],
                DBCA_APPROVAL_ID,
                SITE_STATUS_NOT_TO_BE_REISSUED,
                a["old_link_id"],
                SITE_STATUS_TRANSFERRED,
            )
        )
    else:
        print(
            "  Site {}: UPDATE existing DBCA link {} (was '{}') -> '{}', "
            "set old link {} -> '{}', update latest_approval_link".format(
                a["site_id"],
                a["dbca_link_id"],
                a["existing_dbca_status"],
                SITE_STATUS_NOT_TO_BE_REISSUED,
                a["old_link_id"],
                SITE_STATUS_TRANSFERRED,
            )
        )

if errors:
    print()
    print("=" * 70)
    print("ERRORS - aborting")
    print("=" * 70)
    for e in errors:
        print(e)
    raise SystemExit(1)

if DRY_RUN:
    print()
    print("DRY RUN complete - no changes made.")
    print("Set ACTUAL_RUN=true to apply changes.")
else:
    print()
    print("Applying changes inside a transaction...")
    with transaction.atomic():
        for a in actions:
            site = ApiarySite.objects.get(id=a["site_id"])
            old_link = ApiarySiteOnApproval.objects.get(id=a["old_link_id"])

            if a["action"] == "create_new_dbca_link":
                new_link = ApiarySiteOnApproval.objects.create(
                    apiary_site=site,
                    approval=dbca_approval,
                    site_status=SITE_STATUS_NOT_TO_BE_REISSUED,
                    wkb_geometry=a["wkb_geometry"],
                    site_category_id=a["site_category_id"],
                    licensed_site=a["licensed_site"],
                    available=False,
                )
            else:
                new_link = ApiarySiteOnApproval.objects.get(id=a["dbca_link_id"])
                new_link.site_status = SITE_STATUS_NOT_TO_BE_REISSUED
                new_link.save()

            old_link.site_status = SITE_STATUS_TRANSFERRED
            old_link.save()

            site.latest_approval_link = new_link
            site.save()

            print("  Done: Site {}".format(a["site_id"]))

    print()
    print("All changes committed successfully.")

print()
print("Done.")
