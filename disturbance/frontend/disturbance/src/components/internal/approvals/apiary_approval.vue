<template>
<div id="internalApproval">
    <div class="row">
        <h3>Licence {{ approval.lodgement_number }}</h3>
        <div class="col-md-3">
            <CommsLogs :comms_url="comms_url" :logs_url="logs_url" :comms_add_url="comms_add_url" :disable_add_entry="false"/>
            <div class="mb-3">
                <div class="card card-default">
                    <div class="card-header">
                        Submission
                    </div>
                    <div class="card-body py-2">
                        <strong>Issued on</strong><br/>
                        {{ formatDate(approval.issue_date) }}
                    </div>
                    <div class="card-body border-top py-2">
                        <table class="table small-table">
                            <thead>
                                <tr>
                                    <th>Lodgement</th>
                                    <th>Date</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                        </table>
                    </div>
                </div>
            </div>
            <div class="mb-3">
                <div class="card card-default sticky-top">
                    <div class="card-header">Workflow</div>
                    <div class="card-body">
                        <strong>Status</strong><br/>
                        {{ approval.status }}
                    </div>                        
                </div>
            </div>
        </div>
        <div class="col-md-9">
            <FormSection :formCollapse="false" label="Holder" Index="holder">
                <div v-if="organisationApplicant">
                    <form class="form-horizontal">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label">Name</label>
                            <div class="col-sm-6">
                                <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="approval.organisation_name">
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label" >ABN/ACN</label>
                            <div class="col-sm-6">
                                <input disabled type="text" class="form-control" name="applicantABN" placeholder="" v-model="approval.organisation_abn">
                            </div>
                        </div>
                    </form>
                </div>
                <div v-else>
                    <form class="form-horizontal">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label">Given Name(s)</label>
                            <div class="col-sm-6">
                                <input disabled type="text" class="form-control" name="applicantFirstName" placeholder="" v-model="approval.applicant_first_name">
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label" >Last Name</label>
                            <div class="col-sm-6">
                                <input disabled type="text" class="form-control" name="applicantLastName" placeholder="" v-model="approval.applicant_last_name">
                            </div>
                        </div>
                    </form>
                </div>
            </FormSection>

            <FormSection :formCollapse="true" label="Address Details" Index="address_details">
                <div v-if="loading.length == 0 && approval && approval.applicant_address">
                    <form class="form-horizontal" action="index.html" method="post">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label">Street</label>
                            <div class="col-sm-6">
                                <input type="text" disabled class="form-control" name="street" placeholder="" v-model="approval.applicant_address.line1">
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label" >Town/Suburb</label>
                            <div class="col-sm-6">
                                <input type="text" disabled class="form-control" name="surburb" placeholder="" v-model="approval.applicant_address.locality">
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label">State</label>
                            <div class="col-sm-3">
                                <input type="text" disabled class="form-control" name="country" placeholder="" v-model="approval.applicant_address.state">
                            </div>
                            <label for="" class="col-sm-2 col-form-label">Postcode</label>
                            <div class="col-sm-2">
                                <input type="text" disabled class="form-control" name="postcode" placeholder="" v-model="approval.applicant_address.postcode">
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label" >Country</label>
                            <div class="col-sm-6">
                                <input type="text" disabled class="form-control" name="country" v-model="approval.applicant_address.country" />
                            </div>
                        </div>
                    </form>
                </div>
            </FormSection>

            <FormSection :formCollapse="true" label="Licence Details" Index="licence_details">
                <div v-if="loading.length == 0">
                    <form class="form-horizontal" action="index.html" method="post">
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label">Issue Date</label>
                            <div class="col-sm-6">
                                <label for="" class="col-form-label pull-left">{{ formatDate(approval.issue_date) }}</label>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label" >Start Date</label>
                            <div class="col-sm-6">
                                <label for="" class="col-form-label pull-left">{{ formatDate(approval.start_date) }}</label>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label">Expiry Date</label>
                            <div class="col-sm-3">
                                <label for="" class="col-form-label pull-left">{{ formatDate(approval.expiry_date) }}</label>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label" >Document</label>
                            <div class="col-sm-4">
                                <!-- <p><a target="_blank" :href="approval.licence_document" class="control-label pull-left">Approval.pdf</a></p> -->
                                <!--p><a :href="'#'+approval.id" class="control-label pull-left" @click="viewApprovalPDF(approval.id, approval.latest_apiary_licence_document)">Approval.pdf</a></p-->
                                <p><a target="_blank" :href="approval.latest_apiary_licence_document" class="col-form-label pull-left">Licence.pdf</a></p>
                            </div>
                        </div>
                        <!--div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label" >Document History</label>
                            <div class="col-sm-4">
                                <div v-for="doc in approval.apiary_licence_document_history">
                                    <p><a target="_blank" :href="doc.url" class="col-form-label pull-left">{{doc.name}}</a></p>
                                </div>
                            </div>
                        </div-->
                    </form>
                </div>
            </FormSection>

            <FormSection :formCollapse="false" label="Site(s)" Index="site_avaiability">
                <template v-if="approval && approval.id">
                    <ComponentSiteSelection
                        :show_col_checkbox="false"
                        :show_col_status="true"
                        :apiary_approval_id="approval.id"
                    />
                </template>
            </FormSection>
            
            <FormSection :formCollapse="false" label="Annual Site Fee" Index="annual_rental_fee">
                <template v-if="approval && approval.id">
                    <SectionAnnualRentalFee
                        :is_readonly="false"
                        :is_internal="true"
                        :is_external="false"
                        :approval_id="approval.id"
                        :annual_rental_fee_periods="approval.annual_rental_fee_periods"
                        :no_annual_rental_fee_until="approval.no_annual_rental_fee_until"
                    />
                </template>
            </FormSection>
            
            <!--TODO fix for segregation - fix this to load the temporary use records after request resolved-->
            <FormSection :formCollapse="false" label="Temporary Use" Index="temporary_use">
                <template v-if="approval && approval.id">
                    <TemporaryUse
                        :approval_id="approval.id"
                        :is_internal="true"
                        :is_external="false"
                        ref="tempoary_use"
                    />
                </template>
            </FormSection>
            
            <FormSection :formCollapse="false" label="On Site" Index="on_site">
                <template v-if="approval && approval.id">
                    <OnSiteInformation
                        :approval_id="approval.id"
                        :is_internal="true"
                        :is_external="false"
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
import CommsLogs from '@common-utils/comms_logs.vue'
import FormSection from "@/components/forms/section_toggle.vue"
import { api_endpoints, helpers } from '@/utils/hooks'
import OnSiteInformation from '@/components/common/apiary/section_on_site_information.vue'
import TemporaryUse from '@/components/common/apiary/section_temporary_use.vue'
import ComponentSiteSelection from '@/components/common/apiary/component_site_selection.vue'
import SectionAnnualRentalFee from '@/components/common/apiary/section_annual_rental_fee.vue'
export default {
  name: 'ApiaryApproval',
  data() {
    let vm = this;
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
        org: {
            address: {}
        },

        // Filters
        logs_url: helpers.add_endpoint_json(api_endpoints.approvals,vm.$route.params.approval_id+'/action_log'),
        comms_url: helpers.add_endpoint_json(api_endpoints.approvals,vm.$route.params.approval_id+'/comms_log'),
        comms_add_url: helpers.add_endpoint_json(api_endpoints.approvals,vm.$route.params.approval_id+'/add_comms_log'),
    }
  },
  props: {
        approvalId: {
            type: Number,
        },
    },
  created: function(){
    let url_approval = helpers.add_endpoint_json(api_endpoints.approvals,this.approvalId)

    //TODO make it so we NEVER load with apiary sites (always load separately)
    url_approval = url_approval + '?with_apiary_sites=false'

    fetch(url_approval).then(
        async (response) => {
            if (!response.ok) { return response.json().then(err => { throw err }); }
            let data = await response.json();
            this.approval = data;
            this.approval.applicant_id = data.applicant_id;
            this.fetchOrganisation(this.approval.applicant_id)
        }).catch((error) => {
            console.log(error);
        });
  },
  components: {
        SectionAnnualRentalFee,
        CommsLogs,
        FormSection,
        OnSiteInformation,
        TemporaryUse,
        ComponentSiteSelection,
  },
  computed: {
    isLoading: function () {
      return this.loading.length > 0;
    },
    organisationApplicant: function() {
        let oApplicant = false;
        if (this.approval && this.approval.organisation_abn) {
            oApplicant = true;
        }
        return oApplicant;
    },

  },
  methods: {
    formatDate: function(data){
        return moment(data).format('DD/MM/YYYY');
    },
    commaToNewline(s){
        return s.replace(/[,;]/g, '\n');
    },
    fetchOrganisation(applicant_id){
        let vm=this;
        fetch(helpers.add_endpoint_json(api_endpoints.organisations,applicant_id)).then(
            async (response) => {
                if (!response.ok) { return response.json().then(err => { throw err }); }
                let data = await response.json();
                vm.org = data;
                vm.org.address = data.address;
            }).catch((error) => {
                console.log(error);
            });
    },
    viewApprovalPDF: function(id,media_link){
            //console.log(approval);
            fetch(helpers.add_endpoint_json(api_endpoints.approvals,(id+'/approval_pdf_view_log')),{
                })
                .then(async (response) => {  
                    if (!response.ok) { return response.json().then(err => { throw err }); }
                }).catch((error) => {
                    console.log(error);
                });
            window.open(media_link, '_blank');
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
