<template>
<div id="externalApproval">
    <div class="row">
        <h3>Licence: {{ approval.lodgement_number }}</h3>
        
        <div class="col-sm-12">
            <FormSection :formCollapse="false" label="Holder" Index="holder">
                <div v-if="organisationApplicant">
                    <form class="form-horizontal">
                        <div class="mb-3">
                            <div class="row mb-3">
                                <label for="" class="col-sm-3 col-form-label">Name</label>
                                <div class="col-sm-6">
                                    <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="approval.organisation.name">
                                </div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="row mb-3">
                                <label for="" class="col-sm-3 col-form-label" >ABN/ACN</label>
                                <div class="col-sm-6">
                                    <input disabled type="text" class="form-control" name="applicantABN" placeholder="" v-model="approval.organisation.abn">
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
                <div v-else>
                    <form class="form-horizontal">
                        <div class="mb-3">
                            <div class="row mb-3">
                                <label for="" class="col-sm-3 col-form-label">Given Name(s)</label>
                                <div class="col-sm-6">
                                    <input disabled type="text" class="form-control" name="applicantFirstName" placeholder="" v-model="approval.applicant_first_name">
                                </div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="row mb-3">
                                <label for="" class="col-sm-3 col-form-label" >Last Name</label>
                                <div class="col-sm-6">
                                    <input disabled type="text" class="form-control" name="applicantLastName" placeholder="" v-model="approval.applicant_last_name">
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </FormSection>

            <FormSection :formCollapse="false" label="Address Details" Index="address_details">
                <form v-if="approval.applicant_address" class="form-horizontal" action="index.html" method="post">
                    <div class="mb-3">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label">Street</label>
                            <div class="col-sm-6">
                                <input type="text" disabled class="form-control" name="street" placeholder="" v-model="approval.applicant_address.line1">
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label" >Town/Suburb</label>
                            <div class="col-sm-6">
                                <input type="text" disabled class="form-control" name="surburb" placeholder="" v-model="approval.applicant_address.locality">
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label">State</label>
                            <div class="col-sm-3">
                                <input type="text" disabled class="form-control" name="country" placeholder="" v-model="approval.applicant_address.state">
                            </div>
                            <label for="" class="col-sm-1 col-form-label">Postcode</label>
                            <div class="col-sm-2">
                                <input type="text" disabled class="form-control" name="postcode" placeholder="" v-model="approval.applicant_address.postcode">
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label" >Country</label>
                            <div class="col-sm-4">
                                <input type="text" disabled class="form-control" name="country" v-model="approval.applicant_address.country" />
                            </div>
                        </div>
                    </div>
                </form>
            </FormSection>

            <FormSection :formCollapse="false" label="Licence Details" Index="approval_details">
                <form class="form-horizontal" action="index.html" method="post">
                    <div class="mb-3">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label">Issue Date</label>
                            <div class="col-sm-6">
                                <label for="" class="col-form-label float-start">{{ formatDate(approval.issue_date) }}</label>
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label" >Start Date</label>
                            <div class="col-sm-6">
                                <label for="" class="col-form-label float-start">{{ formatDate(approval.start_date) }}</label>
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label">Expiry Date</label>
                            <div class="col-sm-3">
                                <label for="" class="col-form-label float-start">{{ formatDate(approval.expiry_date) }}</label>
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label" >Document</label>
                            <div class="col-sm-4">
                                <p><a target="_blank" :href="approval.latest_apiary_licence_document" class="col-form-label float-start">Licence.pdf</a></p>
                            </div>
                        </div>
                    </div>
                    <!--div class="mb-3">
                        <label for="" class="col-sm-3 col-form-label" >Document History</label>
                        <div class="col-sm-4">
                            <div v-for="doc in approval.apiary_licence_document_history">
                                <p><a target="_blank" :href="doc.url" class="col-form-label float-start">{{doc.name}}</a></p>
                            </div>
                        </div>
                    </div-->
                    </form>
            </FormSection>
            
            <FormSection :formCollapse="false" label="Site(s)" Index="site_avaiability">
                <template v-if="approval && approval.id">
                    <SiteAvailability
                        :approval_id="approval.id"
                        :is_internal="false"
                        :is_external="true"
                        :user_can_site_transfer="user_can_interact"
                        ref="site_availability"
                    />
                </template>
            </FormSection>
            
            <FormSection :formCollapse="false" label="Annual Site Fee" Index="annual_rental_fee">
                <template v-if="approval && approval.id">
                    <SectionAnnualRentalFee
                        :is_readonly="false"
                        :is_external="true"
                        :is_internal="false"
                        :approval_id="approval.id"
                        :annual_rental_fee_periods="approval.annual_rental_fee_periods"
                        :no_annual_rental_fee_until="approval.no_annual_rental_fee_until"
                    />
                </template>
            </FormSection>
            
            <FormSection :formCollapse="false" label="Temporary Use" Index="temporary_use">
                <template v-if="approval && approval.id">
                    <TemporaryUse
                        :approval_id="approval.id"
                        :is_internal="false"
                        :is_external="true"
                        :user_can_temporary_use="user_can_interact"
                        ref="tempoary_use"
                    />
                </template>
            </FormSection>
           
            <FormSection :formCollapse="false" label="On Site" Index="on_site">
                <template v-if="approval && approval.id">
                    <OnSiteInformation
                        :approval_id="approval.id"
                        :is_internal="false"
                        :is_external="true"
                        :user_can_interact="user_can_interact"
                        ref="on_site_information"
                    />
                </template>
            </FormSection>
        </div>
    </div>
</div>
</template>
<script>
import { v4 as uuid } from 'uuid';
// import datatable from '@vue-utils/datatable.vue'
// import CommsLogs from '@common-utils/comms_logs.vue'
import FormSection from "@/components/forms/section_toggle.vue"
import { api_endpoints, helpers } from '@/utils/hooks'
import OnSiteInformation from '@/components/common/apiary/section_on_site_information.vue'
import TemporaryUse from '@/components/common/apiary/section_temporary_use.vue'
import SiteAvailability from '@/components/common/apiary/section_site_availability.vue'
import SectionAnnualRentalFee from '@/components/common/apiary/section_annual_rental_fee.vue'

export default {
    name: 'ApiaryApprovalExternal',
    props:{
        is_external: {
            type: Boolean,
            default: false
        },
        is_internal: {
            type: Boolean,
            default: false
        },
        approvalId: {
            type: Number,
            default: null,
        }
    },
    data() {
        return {
            loading: [],
            approval: {
                applicant_id: null
            },
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            adBody: 'adBody'+uuid(),
            pBody: 'pBody'+uuid(),
            cBody: 'cBody'+uuid(),
            oBody: 'oBody'+uuid(),
            onBody: 'onBody'+uuid(),
            org: {
                address: {}
            },
        }
    },
    created: function() {
        if (this.approvalId) {
            this.loadApproval(this.approvalId)
        }
    },
    components: {
        SectionAnnualRentalFee,
        FormSection,
        OnSiteInformation,
        SiteAvailability,
        TemporaryUse,
    },
    computed: {
        isLoading: function () {
            return this.loading.length > 0;
        },
        proposal_apiary_id: function() {
            try {
                return this.approval.current_proposal.proposal_apiary.id;
            } catch(err) {
                console.error(err);
                return 0;
            }
        },
        organisationApplicant: function() {
            let oApplicant = false;
            if (this.approval && this.approval.organisation && this.approval.organisation.abn) {
                oApplicant = true;
            }
            return oApplicant;
        },
        user_can_interact: function() {
            return this.approval.status.toLowerCase() === 'current' ? true : false
        },
    },
    methods: {
        formatDate: function(data){
            return moment(data).format('DD/MM/YYYY');
        },
        loadApproval: function(approval_id){
            let vm = this
            console.log('in loadApproval')
            fetch(helpers.add_endpoint_json(api_endpoints.approvals,approval_id)).then(
                async (res) => {
                    if (!res.ok) {
                        return await res.json().then(err => { throw err });
                    }
                    let data = await res.json();
                    vm.approval = data;
                    vm.approval.applicant_id = data.applicant_id;
                    vm.fetchOrganisation(vm.approval.applicant_id)
                }).catch(error => {
                    console.log(error);
                });
        },
        commaToNewline(s){
            return s.replace(/[,;]/g, '\n');
        },
        fetchOrganisation(applicant_id){
            let vm=this;
            fetch(helpers.add_endpoint_json(api_endpoints.organisations,applicant_id)).then(
                async (response) => {
                    if (!response.ok) {
                        return await response.json().then(err => { throw err });
                    }
                    let data = await response.json();
                    vm.org = data;
                    vm.org.address = data.address;
                }).catch((error) => {
                    console.log(error);
                });

        },
    },
    mounted: function () {
    }
}
</script>
<style scoped>
.top-buffer-s {
    margin-top: 10px;
}
.actionBtn {
    cursor: pointer;
}
.hidePopover {
    display: none;
}
</style>
