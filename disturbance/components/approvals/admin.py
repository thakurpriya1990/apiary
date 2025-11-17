
from django.contrib import admin
from disturbance.components.approvals.models import ApiarySiteOnApproval, Approval

@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = [
        'lodgement_number',
        'status',
        'applicant',
        'proxy_applicant',
        'current_proposal',
        'issue_date',
        'original_issue_date',
        'start_date',
        'expiry_date',
        'set_to_cancel',
        'set_to_suspend',
        'set_to_surrender',
        'reissued',
        'no_annual_rental_fee_until',
        'migrated',
    ]
    raw_id_fields = ('applicant','proxy_applicant','current_proposal')
    readonly_fields = ['replaced_by', 'licence_document', 'cover_letter_document','renewal_document']
    search_fields = ['lodgement_number', 'current_proposal__lodgement_number', 'applicant__organisation__name', 'proxy_applicant__first_name', 'proxy_applicant__last_name']


@admin.register(ApiarySiteOnApproval)
class ApiarySiteOnApprovalAdmin(admin.ModelAdmin):
    list_display = ['id', 'apiary_site', 'approval', 'available', 'site_status', 'created_at', 'modified_at', 'site_category', 'licensed_site',]