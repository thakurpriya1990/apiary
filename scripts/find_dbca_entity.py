"""
Find the DBCA Organisation and/or EmailUser records in the database.

Run with:
    python manage.py shell_plus < scripts/find_dbca_entity.py
"""

from ledger.accounts.models import EmailUser
from disturbance.components.organisations.models import Organisation

print("=" * 70)
print("Organisations containing 'dbca' or 'biodiversity' or 'conservation'")
print("=" * 70)
orgs = Organisation.objects.filter(
    organisation__name__icontains='dbca'
) | Organisation.objects.filter(
    organisation__name__icontains='biodiversity'
) | Organisation.objects.filter(
    organisation__name__icontains='conservation'
)
for org in orgs:
    abn = getattr(org, 'abn', 'N/A')
    print(f"  Organisation id={org.id}  abn={abn}")

if not orgs.exists():
    print("  (none found)")

print()
print("=" * 70)
print("EmailUsers with @dbca.wa.gov.au domain")
print("=" * 70)
users = EmailUser.objects.filter(email__icontains='dbca.wa.gov.au')
print(f"  Total count: {users.count()}")

print()
print("=" * 70)
print("EmailUsers matching service account patterns (das@, apiary@, system@, admin@, noreply@)")
print("=" * 70)
service_users = EmailUser.objects.filter(email__iregex=r'(das|apiary|system|admin|noreply|no-reply)@dbca')
print(f"  Total count: {service_users.count()}")
for u in service_users:
    # Show only the local part of the email (before @) and the user id, no full name
    local_part = u.email.split('@')[0]
    print(f"  EmailUser id={u.id}  email_local_part={local_part!r}")
if not service_users.exists():
    print("  (none found)")

print()
print("Done.")
