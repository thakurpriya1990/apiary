import datetime
import pytz
from django.contrib import admin
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from disturbance.components.main.utils import custom_strftime
from disturbance.components.proposals import models, forms
from disturbance.components.main.models import SystemMaintenance, ApplicationType, ApiaryGlobalSettings
from reversion.admin import VersionAdmin
from django.urls import re_path
from django.http import HttpResponseRedirect
from disturbance.utils import create_helppage_object
from disturbance.helpers import is_apiary_admin, is_disturbance_admin, is_das_apiary_admin


@admin.register(models.ProposalType)
class ProposalTypeAdmin(admin.ModelAdmin):
    list_display = ['name','description', 'version']
    ordering = ('name', '-version')
    list_filter = ('name',)


class ProposalDocumentInline(admin.TabularInline):
    model = models.ProposalDocument
    extra = 0


@admin.register(models.AmendmentReason)
class AmendmentReasonAdmin(admin.ModelAdmin):
    list_display = ['reason']


@admin.register(models.ApiaryAnnualRentalFeePeriodStartDate)
class ApiaryAnnualRentalFeePeriodStartDateAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_month_date', 'end_month_date']
    readonly_fields = ['name',]
    fields = ('name', 'period_start_date',)

    def start_month_date(self, obj):
        return custom_strftime('{S} of %b', obj.period_start_date)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def end_month_date(self, obj):
        period_end_date = datetime.date(year=obj.period_start_date.year + 1, month=obj.period_start_date.month, day=obj.period_start_date.day) - datetime.timedelta(days=1)
        return custom_strftime('{S} of %b', period_end_date)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


@admin.register(models.ProposalApiary)
class ProposalApiaryAdmin(VersionAdmin):
    list_display = ['id', 'proposal']


#TODO show apiary only (?)
@admin.register(models.Proposal)
class ProposalAdmin(VersionAdmin):
    inlines =[ProposalDocumentInline,]
    list_display = ['lodgement_number', 'application_type', 'proposal_type', 'processing_status', 'proposal_apiary', 'approval', 'previous_app_lodgement_number', 'proxy_applicant', 'submitter', 'applicant']
    search_fields = ['lodgement_number', 'application_type__name', 'proposal_type', 'processing_status']
    raw_id_fields = ('applicant','proxy_applicant','submitter','previous_application', 'assigned_officer', 'assigned_approver', 'approval')
    readonly_fields = ['approval_level_document']
    list_filter = ['application_type',]

    @admin.display(description='Prev. App No.')
    def previous_app_lodgement_number(self, obj):
        if obj.previous_application:
            return obj.previous_application.lodgement_number
        else:
            return ''

@admin.register(models.ApiarySite)
class ApiarySite(admin.ModelAdmin):
    list_display = ['id', 'site_guid', 'latest_proposal_link', 'latest_approval_link', 'is_vacant', 'exempt_from_radius_restriction',]
    readonly_fields = ['site_guid','is_vacant','latest_proposal_link','latest_approval_link','proposal_link_for_vacant','approval_link_for_vacant', 'coordinates']
    search_fields = ['id']
    list_filter = ['is_vacant', 'exempt_from_radius_restriction',]


@admin.register(models.ApiarySiteOnProposal)
class ApiarySiteOnProposalAdmin(admin.ModelAdmin):
    list_display = ['apiary_site', 'proposal_apiary', 'site_status', 'for_renewal', 'making_payment', 'application_fee_paid', 'created_at', 'modified_at',]
    readonly_fields = ['apiary_site', 'proposal_apiary', 'site_status', 'created_at', 'modified_at',]


class ProposalAssessorGroupMembershipInline(admin.TabularInline):
    model = models.ProposalAssessorGroupMember
    extra = 1
    raw_id_fields = ('emailuser',)


@admin.register(models.ProposalAssessorGroup)
class ProposalAssessorGroupAdmin(admin.ModelAdmin):
    list_display = ['name','default']
    # filter_horizontal = ('members',)
    form = forms.ProposalAssessorGroupAdminForm
    readonly_fields = ['default']
    inlines = [ProposalAssessorGroupMembershipInline,]

    def has_delete_permission(self, request, obj=None):
        if obj and obj.default:
            return False
        return super(ProposalAssessorGroupAdmin, self).has_delete_permission(request, obj)


class ProposalApproverGroupMembershipInline(admin.TabularInline):
    model = models.ProposalApproverGroupMember
    extra = 1
    raw_id_fields = ('emailuser',)

#TODO check if need for apiary
@admin.register(models.ProposalApproverGroup)
class ProposalApproverGroupAdmin(admin.ModelAdmin):
    list_display = ['name','default']
    # filter_horizontal = ('members',)
    form = forms.ProposalApproverGroupAdminForm
    readonly_fields = ['default']
    inlines = [ProposalApproverGroupMembershipInline,]

    def has_delete_permission(self, request, obj=None):
        if obj and obj.default:
            return False
        return super(ProposalApproverGroupAdmin, self).has_delete_permission(request, obj)


class ApiaryReferralGroupMembershipInline(admin.TabularInline):
    model = models.ApiaryReferralGroupMember
    extra = 1
    raw_id_fields = ('emailuser',)


@admin.register(models.ApiaryReferralGroup)
class ApiaryReferralGroupAdmin(admin.ModelAdmin):
    # filter_horizontal = ('members',)
    list_display = ['name']
    exclude = ('site',)
    actions = None
    inlines = [ApiaryReferralGroupMembershipInline,]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
        return super(ApiaryReferralGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


class ApiaryAssessorGroupMembershipInline(admin.TabularInline):
    model = models.ApiaryAssessorGroupMember
    extra = 1
    raw_id_fields = ('emailuser',)

@admin.register(models.ApiaryAssessorGroup)
class ApiaryAssessorGroupAdmin(admin.ModelAdmin):
    # filter_horizontal = ('members',)
    exclude = ('site',)
    actions = None
    inlines = [ApiaryAssessorGroupMembershipInline,]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
        return super(ApiaryAssessorGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.ApiaryAssessorGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 

class ApiaryApproverGroupMembershipInline(admin.TabularInline):
    model = models.ApiaryApproverGroupMember
    extra = 1
    raw_id_fields = ('emailuser',)

@admin.register(models.ApiaryApproverGroup)
class ApiaryApproverGroupAdmin(admin.ModelAdmin):
    # filter_horizontal = ('members',)
    exclude = ('site',)
    actions = None
    inlines = [ApiaryApproverGroupMembershipInline,]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
        return super(ApiaryApproverGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.ApiaryApproverGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 

#TODO show apiary only
@admin.register(models.ProposalStandardRequirement)
class ProposalStandardRequirementAdmin(admin.ModelAdmin):
    list_display = ['code','text','system','obsolete']

    def get_queryset(self, request):
        qs = super(ProposalStandardRequirementAdmin, self).get_queryset(request)
        if request.user.is_superuser or is_das_apiary_admin(request):
            return qs
        group_list = []
        if is_apiary_admin(request):
            group_list.append('apiary')
        if is_disturbance_admin(request):
            group_list.append('disturbance')
        return qs.filter(system__in=group_list)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'system':
            if (request.user.is_superuser or is_das_apiary_admin(request) or 
                    (is_apiary_admin(request) and is_disturbance_admin(request))
                    ):
                # user will see both choices
                kwargs["choices"] = (
                        ('apiary', 'Apiary'),
                        ('disturbance', 'Disturbance'),
                        )
            elif is_apiary_admin(request):
                kwargs["choices"] = (('apiary', 'Apiary'),)
            elif is_disturbance_admin(request):
                kwargs["choices"] = (('disturbance', 'Disturbance'),)
        return super(ProposalStandardRequirementAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

#TODO is this needed?
@admin.register(models.HelpPage)
class HelpPageAdmin(admin.ModelAdmin):
    list_display = ['application_type','help_type', 'description', 'version']
    form = forms.DisturbanceHelpPageAdminForm
    change_list_template = "disturbance/help_page_changelist.html"
    ordering = ('application_type', 'help_type', '-version')
    list_filter = ('application_type', 'help_type')

    def get_urls(self):
        urls = super(HelpPageAdmin, self).get_urls()
        my_urls = [
            re_path('create_disturbance_help/', self.admin_site.admin_view(self.create_disturbance_help)),
            re_path('create_apiary_help/', self.admin_site.admin_view(self.create_apiary_help)),
            re_path('create_disturbance_help_assessor/', self.admin_site.admin_view(self.create_disturbance_help_assessor)),
            re_path('create_apiary_help_assessor/', self.admin_site.admin_view(self.create_apiary_help_assessor)),
        ]
        return my_urls + urls

    def create_disturbance_help(self, request):
        create_helppage_object(application_type='Disturbance', help_type=models.HelpPage.HELP_TEXT_EXTERNAL)
        return HttpResponseRedirect("../")

    def create_apiary_help(self, request):
        create_helppage_object(application_type='Apiary', help_type=models.HelpPage.HELP_TEXT_EXTERNAL)
        return HttpResponseRedirect("../")

    def create_disturbance_help_assessor(self, request):
        create_helppage_object(application_type='Disturbance', help_type=models.HelpPage.HELP_TEXT_INTERNAL)
        return HttpResponseRedirect("../")

    def create_apiary_help_assessor(self, request):
        create_helppage_object(application_type='Apiary', help_type=models.HelpPage.HELP_TEXT_INTERNAL)
        return HttpResponseRedirect("../")


@admin.register(SystemMaintenance)
class SystemMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'start_date', 'end_date', 'duration']
    ordering = ('start_date',)
    readonly_fields = ('duration',)
    form = forms.SystemMaintenanceAdminForm

#TODO show apiary only
@admin.register(ApplicationType)
class ApplicationTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'visible', 'domain_used',]
    ordering = ('order',)


@admin.register(ApiaryGlobalSettings)
class ApiaryGlobalSettingsAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        if obj.key in [ApiaryGlobalSettings.KEY_APIARY_LICENCE_TEMPLATE_FILE, ApiaryGlobalSettings.KEY_DBCA_REGIONS_FILE, ApiaryGlobalSettings.KEY_DBCA_DISTRICTS_FILE,]:
            return ['key', '_file',]
        else:
            return ['key', 'value',]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return ['key',]

    def get_form(self, request, obj=None, **kwargs):
        form = super(ApiaryGlobalSettingsAdmin, self).get_form(request, obj, **kwargs)
        if obj.key == ApiaryGlobalSettings.KEY_APIARY_SITES_LIST_TOKEN:
            link_to = '/api/apiary_site/export/?' + ApiaryGlobalSettings.KEY_APIARY_SITES_LIST_TOKEN + '=' + obj.value
            http_host = request.META['HTTP_HOST']
            display_link_to = http_host + link_to
            form.base_fields['value'].help_text = '<a href="' + link_to + '">' + display_link_to + '</a>'
        return form

    list_display = ['key', 'value', '_file',]
    ordering = ('key',)

#TODO determine where this is used
@admin.register(models.ApiaryAnnualRentalFee)
class ApiaryAnnualRentalFeeAdmin(admin.ModelAdmin):
    list_display = ['id', 'amount_south_west', 'amount_remote', 'date_from',]

#TODO determine where this is used
@admin.register(models.ApiaryAnnualRentalFeeRunDate)
class ApiaryAnnualRentalFeeRunDateAdmin(admin.ModelAdmin):
    list_display = ['name', 'run_month_date', 'enabled', 'enabled_for_new_site', 'period_to_be_charged_for']
    readonly_fields = ['name',]
    fields = ('name', 'date_run_cron', 'enabled', 'enabled_for_new_site')

    def run_month_date(self, obj):
        return custom_strftime('{S} of %b', obj.date_run_cron)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def period_to_be_charged_for(self, obj):
        from disturbance.management.commands.send_annual_rental_fee_invoice import get_annual_rental_fee_period

        today_now_local = datetime.datetime.now(pytz.timezone(settings.TIME_ZONE))
        today_date_local = today_now_local.date()
        period_start_date, period_end_date = get_annual_rental_fee_period(today_date_local)
        return '{} --- {}'.format(period_start_date.strftime('%Y/%m/%d'), period_end_date.strftime('%Y/%m/%d'))

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    run_month_date.short_description = 'Date on which start billing for the next annual site fee'


class ApiarySiteFeeInline(admin.TabularInline):
    model = models.ApiarySiteFee
    extra = 0
    can_delete = True
    fields = ('apiary_site_fee_type', 'amount', 'date_of_enforcement',)


@admin.register(models.ApiarySiteFeeType)
class ApiarySiteFeeTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description',]


class SiteCategoryAdmin(admin.ModelAdmin):
    inlines = [ApiarySiteFeeInline,]
admin.site.register(models.SiteCategory, SiteCategoryAdmin)


@admin.register(models.ApiaryChecklistQuestion)
class ApiaryChecklistQuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'checklist_type', 'checklist_role',]
    ordering = ('order',)

#TODO is this needed for apiary?
@admin.register(models.QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['label',]
    fields = ('label',)

#TODO is this needed for apiary?
@admin.register(models.MasterlistQuestion)
class MasterlistQuestionAdmin(admin.ModelAdmin):
    list_display = ['question',]
    filter_horizontal = ('option',)
    form = forms.MasterlistQuestionAdminForm
    
#TODO fix for segregation (?) - only if needed for apiary
#@admin.register(models.SectionQuestion)
#class SectionQuestionAdmin(admin.ModelAdmin):
#    list_display = ['section', 'question','order', 'parent_question','parent_answer']
#    #list_display = ['section', 'question','parent_question',]
#    form = forms.SectionQuestionAdminForm