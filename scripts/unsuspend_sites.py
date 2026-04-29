"""
Unsuspend target ApiarySites by setting site_status='current' on their
current latest_approval_link (ApiarySiteOnApproval record).

Run (dry run first):
    python manage_ds.py shell -c "exec(open('disturbance/scripts/unsuspend_sites.py').read())"

Then for real (requires explicit ACTUAL_RUN=true):
    ACTUAL_RUN=true python manage_ds.py shell -c "exec(open('disturbance/scripts/unsuspend_sites.py').read())"
"""

import os
from django.db import transaction
from disturbance.components.proposals.models import ApiarySite
from disturbance.settings import SITE_STATUS_SUSPENDED, SITE_STATUS_CURRENT

# --- Configuration -----------------------------------------------------------

TARGET_SITE_IDS = [
    8912, 8913, 8914, 8915, 8916, 8917, 8918,
    8929, 8930, 8931,
    8941, 8942,
    9155, 9156, 9157, 9158, 9159, 9163,
]

# Safe by default: only runs actual changes when ACTUAL_RUN=true is explicitly set
DRY_RUN = os.environ.get('ACTUAL_RUN', '').lower() != 'true'

# -----------------------------------------------------------------------------

print("=" * 70)
print("unsuspend_sites.py  |  DRY_RUN={}".format(DRY_RUN))
print("=" * 70)

hard_errors = []   # Genuine errors that must abort the run
warnings = []      # Skippable issues (e.g. site already not suspended)
actions = []

for site_id in sorted(TARGET_SITE_IDS):
    try:
        site = ApiarySite.objects.get(id=site_id)
    except ApiarySite.DoesNotExist:
        hard_errors.append("  ERROR: ApiarySite id={} does not exist".format(site_id))
        continue

    link = site.latest_approval_link
    if not link:
        hard_errors.append("  ERROR: ApiarySite id={} has no latest_approval_link".format(site_id))
        continue

    approval = link.approval
    if link.site_status != SITE_STATUS_SUSPENDED:
        warnings.append(
            "  WARNING: ApiarySite id={} site_status is {!r} (expected 'suspended') — skipping".format(
                site_id, link.site_status
            )
        )
        continue

    actions.append({
        'site_id': site_id,
        'link_id': link.id,
        'approval_id': approval.id,
        'approval_lodgement': approval.lodgement_number,
        'approval_status': approval.status,
        'current_status': link.site_status,
    })

print("=" * 70)
print("Planned actions")
print("=" * 70)
print("  Sites to update: {}".format(len(actions)))
print()
for a in actions:
    print("  Site {}: ApiarySiteOnApproval id={} (Approval {} / {}  approval_status={!r}) "
          "site_status {!r} -> {!r}".format(
              a['site_id'], a['link_id'], a['approval_id'],
              a['approval_lodgement'], a['approval_status'],
              a['current_status'], SITE_STATUS_CURRENT))

if warnings:
    print()
    print("=" * 70)
    print("WARNINGS (sites skipped)")
    print("=" * 70)
    for w in warnings:
        print(w)

if hard_errors:
    print()
    print("=" * 70)
    print("ERRORS — aborting")
    print("=" * 70)
    for e in hard_errors:
        print(e)
    raise SystemExit(1)

if not actions:
    print()
    print("No actions to perform — exiting.")
    raise SystemExit(0)

if DRY_RUN:
    print()
    print("DRY RUN complete - no changes made.")
    print("Set ACTUAL_RUN=true to apply changes.")
else:
    print()
    print("Applying changes inside a transaction...")
    # Note: saving an ApiarySiteOnApproval triggers a post_save signal
    # (disturbance/components/approvals/signals.py) which automatically
    # updates apiary_site.latest_approval_link to this instance and re-saves
    # the ApiarySite.  Since link IS already the latest_approval_link, this
    # is a no-op on that field and causes no data corruption.
    with transaction.atomic():
        for a in actions:
            site = ApiarySite.objects.get(id=a['site_id'])
            link = site.latest_approval_link
            link.site_status = SITE_STATUS_CURRENT
            link.save()
            print("  Done: Site {} — ApiarySiteOnApproval id={} site_status -> {!r}".format(
                a['site_id'], a['link_id'], SITE_STATUS_CURRENT))

    print()
    print("All changes committed successfully.")

print()
print("Done.")
