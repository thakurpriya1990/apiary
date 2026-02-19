"""
Check which Approvals are linked to the target ApiarySites.

Run with:
    python manage.py shell_plus < scripts/check_sites_approval.py
"""

from disturbance.components.proposals.models import ApiarySite
from disturbance.components.approvals.models import ApiarySiteOnApproval, Approval

TARGET_SITE_IDS = [
    7805, 7806, 7807, 7808, 7809,
    8179, 8196, 8199, 8213, 8303,
    8535, 8577, 8580, 8617, 8620,
    8684, 8685, 8686, 8690, 8691,
    8789, 8946, 8967, 9074, 9088,
    9111, 9112, 9113, 9114, 9115,
    9116, 9117, 9118,
]

print("=" * 90)
print(f"{'Site ID':<10} {'Approval ID':<14} {'Site Status (on approval)':<30} {'Authority Holder'}")
print("=" * 90)

approval_to_target_sites = {}  # approval_id -> [site_ids]

for site_id in sorted(TARGET_SITE_IDS):
    try:
        site = ApiarySite.objects.get(id=site_id)
        link = site.latest_approval_link
        if link:
            approval = link.approval
            holder = approval.relevant_applicant_name
            print(f"{site_id:<10} {approval.id:<14} {link.site_status:<30} {holder}")
            approval_to_target_sites.setdefault(approval.id, []).append(site_id)
        else:
            print(f"{site_id:<10} {'(no approval link)'}")
    except ApiarySite.DoesNotExist:
        print(f"{site_id:<10} {'(site not found)'}")

print()
print("=" * 90)
print("Impact check: other sites on the same Approval that are NOT in the target list")
print("=" * 90)
print(f"{'Approval ID':<14} {'Target sites':<16} {'All sites on approval':<24} {'Side effects?':<16} {'Authority Holder'}")
print("-" * 90)

for approval_id, target_sites in sorted(approval_to_target_sites.items()):
    approval = Approval.objects.get(id=approval_id)
    all_links = ApiarySiteOnApproval.objects.filter(approval=approval).exclude(site_status='transferred')
    all_site_ids = list(all_links.values_list('apiary_site_id', flat=True))
    non_target = [s for s in all_site_ids if s not in TARGET_SITE_IDS]
    side_effects = "YES - WARNING" if non_target else "none"
    holder = approval.relevant_applicant_name
    print(f"{approval_id:<14} {len(target_sites):<16} {len(all_site_ids):<24} {side_effects:<16} {holder}")
    if non_target:
        print(f"  -> Non-target sites also on this approval: {non_target}")

print()
print("Done.")
