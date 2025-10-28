from django.conf import settings
from django.contrib import admin
from django.urls import re_path, include
from django.conf.urls.static import static
from rest_framework import routers
from disturbance import views
from disturbance.components.main.views import deed_poll_url, GeocodingAddressSearchTokenView
from disturbance.components.proposals import views as proposal_views
from disturbance.components.organisations import views as organisation_views
from disturbance.components.ap_payments import views as payment_views
from disturbance.components.proposals.views import ExternalProposalTemporaryUseSubmitSuccessView

from disturbance.components.users import api as users_api
from disturbance.components.organisations import api as org_api
from disturbance.components.proposals import api as proposal_api
from disturbance.components.approvals import api as approval_api
from disturbance.components.compliances import api as compliances_api
from disturbance.components.main import api as main_api
from disturbance.components.history import api as history_api

from ledger_api_client.urls import urlpatterns as ledger_patterns
from django_media_serv.urls import urlpatterns as media_serv_patterns

# API patterns
from disturbance.management.default_data_manager import DefaultDataManager
from disturbance.utils import are_migrations_running

router = routers.DefaultRouter()
router.include_root_view = settings.SHOW_ROOT_API
router.register(r'organisations',org_api.OrganisationViewSet,"organisations")
router.register(r'proposal',proposal_api.ProposalViewSet,"proposal")
router.register(r'proposal_apiary', proposal_api.ProposalApiaryViewSet,"proposal_apiary")
router.register(r'on_site_information', proposal_api.OnSiteInformationViewSet,"on_site_information")
router.register(r'apiary_site', proposal_api.ApiarySiteViewSet,"apiary_site")
router.register(r'proposal_paginated',proposal_api.ProposalPaginatedViewSet,"proposal_paginated")
router.register(r'approval_paginated',approval_api.ApprovalPaginatedViewSet,"approval_paginated_view")
router.register(r'compliance_paginated',compliances_api.CompliancePaginatedViewSet,"compliance_paginated")
router.register(r'referrals',proposal_api.ReferralViewSet,"referrals")
router.register(r'approvals',approval_api.ApprovalViewSet,"approvals")
router.register(r'compliances',compliances_api.ComplianceViewSet,"compliances")
router.register(r'proposal_requirements',proposal_api.ProposalRequirementViewSet,"proposal_requirements")
router.register(r'proposal_standard_requirements',proposal_api.ProposalStandardRequirementViewSet,"proposal_standard_requirements")
router.register(r'organisation_requests',org_api.OrganisationRequestsViewSet,"organisation_requests")
router.register(r'organisation_contacts',org_api.OrganisationContactViewSet,"organisation_contacts")
router.register(r'my_organisations',org_api.MyOrganisationsViewSet,"my_organisations")
router.register(r'users',users_api.UserViewSet,"users")
router.register(r'amendment_request',proposal_api.AmendmentRequestViewSet,"amendment_request")
router.register(r'compliance_amendment_request',compliances_api.ComplianceAmendmentRequestViewSet,"compliance_amendment_request")
router.register(r'regions', main_api.RegionViewSet,"regions")
router.register(r'activity_matrix', main_api.ActivityMatrixViewSet,"activity_matrix")
router.register(r'application_types', main_api.ApplicationTypeViewSet,"application_types")
router.register(r'apiary_referral_groups', proposal_api.ApiaryReferralGroupViewSet,"apiary_referral_groups")
router.register(r'apiary_referrals',proposal_api.ApiaryReferralViewSet,"apiary_referrals")
router.register(r'apiary_site_fees',proposal_api.ApiarySiteFeeViewSet,"apiary_site_fees")
router.register(r'proposal_type_sections', proposal_api.ProposalTypeSectionViewSet,"proposal_type_sections")

router.register(
    r'schema_question_paginated', proposal_api.SchemaQuestionPaginatedViewSet,"schema_question_paginated")

router.register(
    r'schema_question', proposal_api.SchemaQuestionViewSet,"schema_question")

router.register(
    r'schema_masterlist',
    proposal_api.SchemaMasterlistViewSet,
    "schema_masterlist"
)
router.register(
    r'schema_masterlist_paginated', proposal_api.SchemaMasterlistPaginatedViewSet,"schema_masterlist_paginated")
router.register(
    r'schema_proposal_type', proposal_api.SchemaProposalTypeViewSet,"schema_proposal_type")
router.register(
    r'schema_proposal_type_paginated', proposal_api.SchemaProposalTypePaginatedViewSet,"schema_proposal_type_paginated")
router.register(r'map_layers', main_api.MapLayerViewSet,"map_layers")

api_patterns = [
    re_path(r'^api/profile$', users_api.GetProfile.as_view(), name='get-profile'),
    re_path(r'^api/countries$', users_api.GetCountries.as_view(), name='get-countries'),
    re_path(r'^api/proposal_type$', proposal_api.GetProposalType.as_view(), name='get-proposal-type'),
    re_path(r'^api/organisation_access_group_members',org_api.OrganisationAccessGroupMembers.as_view(),name='organisation-access-group-members'),
    re_path(r'^api/apiary_organisation_access_group_members',org_api.ApiaryOrganisationAccessGroupMembers.as_view(),name='apiary-organisation-access-group-members'),
    re_path(r'^api/',include(router.urls)),
    re_path(r'^api/amendment_request_reason_choices',proposal_api.AmendmentRequestReasonChoicesView.as_view(),name='amendment_request_reason_choices'),
    re_path(r'^api/compliance_amendment_reason_choices',compliances_api.ComplianceAmendmentReasonChoicesView.as_view(),name='amendment_request_reason_choices'),
    re_path(r'^api/search_keywords',proposal_api.SearchKeywordsView.as_view(),name='search_keywords'),
    re_path(r'^api/search_reference',proposal_api.SearchReferenceView.as_view(),name='search_reference'),
    re_path(r'^api/search_sections',proposal_api.SearchSectionsView.as_view(),name='search_sections'),
    re_path(r'^api/deed_poll_url', deed_poll_url, name='deed_poll_url'),
    re_path(r'^api/history/compare/serialized/(?P<app_label>[\w-]+)/(?P<component_name>[\w-]+)/(?P<model_name>[\w-]+)/(?P<serializer_name>[\w-]+)/(?P<pk>\d+)/(?P<newer_version>\d+)/(?P<older_version>\d+)/$',
            history_api.GetCompareSerializedVersionsView.as_view(), name='get-compare-serialized-versions'),
    re_path(r'^api/history/compare/root/fields/(?P<app_label>[\w-]+)/(?P<model_name>[\w-]+)/(?P<pk>\d+)/(?P<newer_version>\d+)/(?P<older_version>\d+)/$',
            history_api.GetCompareRootLevelFieldsVersionsView.as_view(), name='get-compare-root-level-fields-versions'),
    re_path(r'^api/history/compare/field/(?P<app_label>[\w-]+)/(?P<model_name>[\w-]+)/(?P<pk>\d+)/(?P<newer_version>\d+)/(?P<older_version>\d+)/(?P<compare_field>[\w-]+)/$',
            history_api.GetCompareFieldVersionsView.as_view(), name='get-compare-field-versions'),
    re_path(r'^api/history/compare/(?P<app_label>[\w-]+)/(?P<model_name>[\w-]+)/(?P<pk>\d+)/(?P<newer_version>\d+)/(?P<older_version>\d+)/$',
            history_api.GetCompareVersionsView.as_view(), name='get-compare-versions'),
    re_path(r'^api/history/versions/(?P<app_label>[\w-]+)/(?P<component_name>[\w-]+)/(?P<model_name>[\w-]+)/(?P<pk>\d+)/(?P<reference_id_field>[\w-]+)/$',
            history_api.GetVersionsView.as_view(), name='get-versions'),
    re_path(r'^api/history/version/(?P<app_label>[\w-]+)/(?P<component_name>[\w-]+)/(?P<model_name>[\w-]+)/(?P<serializer_name>[\w-]+)/(?P<pk>\d+)/(?P<version_number>\d+)/$',
            history_api.GetVersionView.as_view(), name='get-version'),
    re_path(r'^api/geocoding_address_search_token', GeocodingAddressSearchTokenView.as_view(), name='geocoding_address_search_token'),
]

# URL Patterns
# You have to be careful about the order of the urls below.
# Django searches matching url from the top of the list, and once found a matching url, it never goes through the urls below it.
urlpatterns = [
    re_path(r'^admin/', admin.site.urls, name='admin'),
    re_path(r'^chaining/', include('smart_selects.urls')),
    re_path(r'', include(api_patterns)),
    re_path(r'^$', views.DisturbanceRoutingView.as_view(), name='home'),
    re_path(r'^contact/', views.DisturbanceContactView.as_view(), name='ds_contact'),
    re_path(r'^further_info/', views.DisturbanceFurtherInformationView.as_view(), name='ds_further_info'),
    re_path(r'^internal/', views.InternalView.as_view(), name='internal'),
    re_path(r'^internal/proposal/(?P<proposal_pk>\d+)/referral/(?P<referral_pk>\d+)/$', views.ReferralView.as_view(), name='internal-referral-detail'),
    re_path(r'^external/proposal/(?P<proposal_pk>\d+)/submit_temp_use_success/$', ExternalProposalTemporaryUseSubmitSuccessView.as_view(),),
    re_path(r'^external/', views.ExternalView.as_view(), name='external'),
    re_path(r'^firsttime/$', views.first_time, name='first_time'),
    re_path(r'^gisdata/$', views.gisdata, name='gisdata'),
    re_path(r'^account/$', views.ExternalView.as_view(), name='manage-account'),
    re_path(r'^help/(?P<application_type>[^/]+)/(?P<help_type>[^/]+)/$', views.HelpView.as_view(), name='help'),
    re_path(r'^mgt-commands/$', views.ManagementCommandsView.as_view(), name='mgt-commands'),

    #following url is used to include url path when sending Proposal amendment request to user.
    re_path(r'^proposal/$', proposal_views.ProposalView.as_view(), name='proposal'),
    re_path(r'^preview/licence-pdf/(?P<proposal_pk>\d+)',proposal_views.PreviewLicencePDFView.as_view(), name='preview_licence_pdf'),
    re_path(r'^ledgerpay/(?P<payment_item>.+)', views.LedgerPayView.as_view(), name='ledgerpay-view'),
    re_path(r'^validate_invoice_details/$', views.validate_invoice_details, name='validate-invoice-details'),
    re_path(r'^invoice_payment/(?P<invoice_reference>\d+)/$', payment_views.InvoicePaymentView.as_view(), name='invoice_payment'),
    re_path(r'^application_fee/(?P<proposal_pk>\d+)/$', payment_views.ApplicationFeeView.as_view(), name='application_fee'),
    re_path(r'^annual_rental_fee/(?P<annual_rental_fee_id>\d+)/$', payment_views.AnnualRentalFeeView.as_view(), name='annual_rental_fee'),
    re_path(r'^success/fee/$', payment_views.ApplicationFeeSuccessView.as_view(), name='fee_success'),
    re_path(r'^success_preload/fee/(?P<lodgement_number>.+)/', payment_views.ApplicationFeeSuccessViewPreload.as_view(), name='fee_success_preload'),
    # re_path(r'^success/site_transfer_fee/$', payment_views.SiteTransferApplicationFeeSuccessView.as_view(), name='site_transfer_fee_success'),
    re_path(r'^success/site_transfer_fee/(?P<lodgement_number>.+)/', payment_views.SiteTransferApplicationFeeSuccessView.as_view(), name='site_transfer_fee_success'),
    re_path(r'^success/annual_rental_fee/$', payment_views.AnnualRentalFeeSuccessView.as_view(), name='annual_rental_fee_success'),
    re_path(r'^success/invoice_payment/$', payment_views.InvoicePaymentSuccessView.as_view(), name='invoice_payment_success'),
    re_path(r'payments/invoice-pdf/(?P<reference>\d+)', payment_views.InvoicePDFView.as_view(), name='invoice-pdf'),
    re_path(r'payments/awaiting-payment-pdf/(?P<annual_rental_fee_id>\d+)', payment_views.AwaitingPaymentPDFView.as_view(), name='awaiting-payment-pdf'),
    re_path(r'payments/confirmation-pdf/(?P<reference>\d+)', payment_views.ConfirmationPDFView.as_view(), name='confirmation-pdf'),

    # following url is defined so that to include url path when sending Proposal amendment request to user.
    re_path(r'^external/proposal/(?P<proposal_pk>\d+)/$', views.ExternalProposalView.as_view(), name='external-proposal-detail'),
    re_path(r'^internal/proposal/(?P<proposal_pk>\d+)/$', views.InternalProposalView.as_view(), name='internal-proposal-detail'),
    re_path(r'^external/compliance/(?P<compliance_pk>\d+)/$', views.ExternalComplianceView.as_view(), name='external-compliance-detail'),
    re_path(r'^internal/compliance/(?P<compliance_pk>\d+)/$', views.InternalComplianceView.as_view(), name='internal-compliance-detail'),

    # reversion history-compare
    re_path(r'^history/proposal/latest/(?P<pk>\d+)/(?P<count>\d+)/$', proposal_views.ProposalHistoryLatestCompareView.as_view(), name='proposal_history_latest'),
    re_path(r'^history/proposal/(?P<pk>\d+)/$', proposal_views.ProposalHistoryCompareView.as_view(), name='proposal_history'),
    re_path(r'^history/proposal/filtered/(?P<pk>\d+)/$', proposal_views.ProposalFilteredHistoryCompareView.as_view(), name='proposal_filtered_history'),
    re_path(r'^history/referral/(?P<pk>\d+)/$', proposal_views.ReferralHistoryCompareView.as_view(), name='referral_history'),
    re_path(r'^history/approval/(?P<pk>\d+)/$', proposal_views.ApprovalHistoryCompareView.as_view(), name='approval_history'),
    re_path(r'^history/compliance/(?P<pk>\d+)/$', proposal_views.ComplianceHistoryCompareView.as_view(), name='compliance_history'),
    re_path(r'^history/proposaltype/(?P<pk>\d+)/$', proposal_views.ProposalTypeHistoryCompareView.as_view(), name='proposaltype_history'),
    re_path(r'^history/helppage/(?P<pk>\d+)/$', proposal_views.HelpPageHistoryCompareView.as_view(), name='helppage_history'),
    re_path(r'^history/organisation/(?P<pk>\d+)/$', organisation_views.OrganisationHistoryCompareView.as_view(), name='organisation_history'),
    re_path(r'^template_group$', views.TemplateGroupView.as_view(), name='template-group'),
    re_path(r'^private-media/', views.getPrivateFile, name='view_private_file'),

    # Reports
    re_path(r'^api/oracle_job$', main_api.OracleJob.as_view(), name='get-oracle'),
    re_path(r'^api/reports/booking_settlements$', main_api.BookingSettlementReportView.as_view(),
        name='booking-settlements-report'),
] + ledger_patterns #+ media_serv_patterns

if not are_migrations_running():
    DefaultDataManager()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
