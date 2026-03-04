<template lang="html">
    <!--div v-if="proposal" class="container" id="internalReferral"-->
    <div v-if="proposal" class="container">
            <div class="row">
        <h3>Proposal: {{ proposal.lodgement_number }}</h3>
        <div class="col-md-3">
            <CommsLogs :comms_url="comms_url" :logs_url="logs_url" comms_add_url="test"/>
            <div class="mb-3">
                <div class="card card-default">
                    <div class="card-header">
                       Submission 
                    </div>
                    <div class="card-body py-2">
                        <strong>Submitted by</strong><br/>
                        {{ proposal.submitter }}
                    </div>
                    <div  class="card-body border-top py-2">
                        <strong>Lodged on</strong><br/>
                        {{ formatDate(proposal.lodgement_date) }}
                    </div>
                    <div  class="card-body border-top py-2">
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
                    <div class="card-header">
                        Workflow
                    </div>
                    <div class="card-body py-2">
                        <strong>Status</strong><br/>
                        {{ proposal.processing_status }}
                    </div>

                    <div v-if="!isFinalised" class="card-body py-2 border-top">
                        <div class="row">
                            <div class="col-sm-12 top-buffer-s">
                                <strong>Currently assigned to</strong><br/>
                                <div class="form-group">
                                    <select ref="assigned_officer_referral" :disabled="!canProcess" class="form-select" v-model="apiaryReferral.assigned_officer_id">
                                        <option :value="null"></option>
                                        <option v-for="member in apiaryReferral.allowed_assessors" :value="member.id" :key="member.id">{{member.first_name}} {{member.last_name}}</option>
                                    </select>
                                    <a 
                                        v-if="canAssign && apiaryReferral.assigned_officer_id != apiaryReferral.current_officer.id" 
                                        @click.prevent="assignRequestUser()" 
                                        class="actionBtn pull-right">Assign to me
                                    </a>
                                </div>
                            </div>
                        </div>
                        <div class="card-body border-top" v-if="!isFinalised && canAction">
                            <div class="col-sm-12 top-buffer-s" v-if="canAction">
                                <div class="row">
                                    <div class="col-sm-12">
                                        <strong>Action</strong><br/>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-12">
                                        <label class="control-label pull-left"  for="Name">Comments</label>
                                        <textarea class="form-control" name="name" v-model="referral_comment"></textarea>
                                        <button style="width:80%;" class="btn btn-primary top-buffer-s" :disabled="proposal.can_user_edit" @click.prevent="completeReferral">Complete Referral Task</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-1"></div>
        <div class="col-md-8">
            <div class="row">
                <div v-show="false" class="col-md-12">
                    <div class="row">
                        <div class="panel panel-default">
                            <div class="panel-heading">
                                <h3>Level of Approval</h3>
                            </div>
                            <div class="panel-body panel-collapse">
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-12">
                    <div class="row">
                        <FormSection :formCollapse="false" label="Applicant" Index="applicant">
                            <div v-if="organisationApplicant">
                                <form class="form-horizontal">
                                    <div class="form-group">
                                    <label for="" class="col-sm-3 control-label">Name</label>
                                    <div class="col-sm-6">
                                        <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="proposal.applicant.name">
                                    </div>
                                    </div>
                                    <div class="form-group">
                                    <label for="" class="col-sm-3 control-label" >ABN/ACN</label>
                                    <div class="col-sm-6">
                                        <input disabled type="text" class="form-control" name="applicantABN" placeholder="" v-model="proposal.applicant.abn">
                                    </div>
                                    </div>
                                </form>
                            </div>
                            <div v-else>
                                <form class="form-horizontal">
                                    <div class="form-group">
                                    <label for="" class="col-sm-3 control-label">Given Name(s)</label>
                                    <div class="col-sm-6">
                                        <input disabled type="text" class="form-control" name="applicantFirstName" placeholder="" v-model="proposal.applicant_first_name">
                                    </div>
                                    </div>
                                    <div class="form-group">
                                    <label for="" class="col-sm-3 control-label" >Last Name</label>
                                    <div class="col-sm-6">
                                        <input disabled type="text" class="form-control" name="applicantLastName" placeholder="" v-model="proposal.applicant_last_name">
                                    </div>
                                    </div>
                                </form>
                            </div>
                        </FormSection>
                    </div>
                </div>
                <div class="col-md-12">
                    <div class="row">
                        <FormSection :formCollapse="true" label="Address Details" Index="address_details">
                            <form class="form-horizontal">
                                <div class="form-group">
                                <label for="" class="col-sm-3 control-label">Street</label>
                                <div class="col-sm-6">
                                    <input disabled type="text" class="form-control" name="street" placeholder="" v-model="applicantAddress.line1">
                                </div>
                                </div>
                                <div class="form-group">
                                <label for="" class="col-sm-3 control-label" >Town/Suburb</label>
                                <div class="col-sm-6">
                                    <input disabled type="text" class="form-control" name="surburb" placeholder="" v-model="applicantAddress.locality">
                                </div>
                                </div>
                                <div class="form-group">
                                <label for="" class="col-sm-3 control-label">State</label>
                                <div class="col-sm-2">
                                    <input disabled type="text" class="form-control" name="country" placeholder="" v-model="applicantAddress.state">
                                </div>
                                <label for="" class="col-sm-2 control-label">Postcode</label>
                                <div class="col-sm-2">
                                    <input disabled type="text" class="form-control" name="postcode" placeholder="" v-model="applicantAddress.postcode">
                                </div>
                                </div>
                                <div class="form-group">
                                <label for="" class="col-sm-3 control-label" >Country</label>
                                <div class="col-sm-4">
                                    <input disabled type="text" class="form-control" name="country" v-model="applicantAddress.country"/>
                                </div>
                                </div>
                            </form>
                        </FormSection>
                    </div>
                </div>
                <div class="col-md-12">
                    <div class="row">
                        <FormSection :formCollapse="true" label="Contact Details" Index="contact_details">
                                <div v-if="organisationApplicant">
                                    <table ref="contacts_datatable" :id="contacts_table_id" class="hover table table-striped table-bordered dt-responsive" cellspacing="0" width="100%">
                                    </table>
                                </div>
                                <div v-else>
                                  <form class="form-horizontal">
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Phone (work)</label>
                                        <div class="col-md-8">
                                            <input disabled type="text" class="form-control" name="applicantWorkPhone" placeholder="" v-model="proposal.applicant_phone_number">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Mobile</label>
                                        <div class="col-md-8">
                                            <input disabled type="text" class="form-control" name="applicantMobileNumber" placeholder="" v-model="proposal.applicant_mobile_number">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Email</label>
                                        <div class="col-md-8">
                                            <input disabled type="text" class="form-control" name="applicantEmail" placeholder="" v-model="proposal.applicant_email">
                                        </div>
                                      </div>
                                  </form>
                                </div>
                        </FormSection>
                    </div>
                </div>

                <div class="col-md-12">
                    <div class="row">
                        <form :action="proposal_form_url" method="post" name="new_proposal" enctype="multipart/form-data">
                            <!--ProposalApiary form_width="inherit" :withSectionsSelector="false" v-if="proposal" :proposal="proposal"-->
                            <div v-if="proposal && proposal.application_type=='Apiary'">
                                <ProposalApiary 
                                v-if="proposal" 
                                :proposal="proposal" 
                                ref="proposal_apiary" 
                                :is_external="false" 
                                :is_internal="true" 
                                :hasAssessorMode="hasAssessorMode"
                                :referral="referral"
                                >
                                    <!--NewApply v-if="proposal" :proposal="proposal"></NewApply>
                                    <input type="hidden" name="csrfmiddlewaretoken" :value="csrf_token"/>
                                    <input type='hidden' name="schema" :value="JSON.stringify(proposal)" />
                                    <input type='hidden' name="proposal_id" :value="1" /-->
                                    <input type='hidden' name="referrer_checklist_answers" :value="JSON.stringify(proposalApiaryReferrerChecklistAnswers)" />
                                    <input type='hidden' name="referrer_checklist_answers_per_site" :value="JSON.stringify(proposalApiaryReferrerChecklistAnswersPerSite)" />
                                    <div class="navbar navbar-fixed-bottom" v-if="!proposal.can_user_edit && !isFinalised" style="background-color: #f5f5f5 ">
                                            <div class="navbar-inner">
                                                <div v-if="!isFinalised" class="container">
                                                <p class="pull-right">                       
                                                <button class="btn btn-primary pull-right" style="margin-top:5px;" @click.prevent="save()">Save Changes</button>
                                                </p>                      
                                                </div>                   
                                            </div>
                                    </div>      

                                </ProposalApiary>
                            </div>
                            <div v-else-if="proposal && proposal.application_type=='Site Transfer'">
                                <ApiarySiteTransfer
                                    v-if="proposal"
                                    :proposal="proposal"
                                    ref="site_transfer"
                                    :hasAssessorMode="hasAssessorMode"
                                    :is_external="false" 
                                    :is_internal="true" 
                                    :referral="referral"
                                >
                                    <input type='hidden' name="referrer_checklist_answers" :value="JSON.stringify(siteTransferProposalApiaryReferrerChecklistAnswers)" />
                                    <input type='hidden' name="referrer_checklist_answers_per_site" :value="JSON.stringify(siteTransferProposalApiaryReferrerChecklistAnswersPerSite)" />
                                    <div class="navbar navbar-fixed-bottom" v-if="!proposal.can_user_edit && !isFinalised" style="background-color: #f5f5f5 ">
                                            <div class="navbar-inner">
                                                <div v-if="!isFinalised" class="container">
                                                <p class="pull-right">                       
                                                <button class="btn btn-primary pull-right" style="margin-top:5px;" @click.prevent="save()">Save Changes</button>
                                                </p>                      
                                                </div>                   
                                            </div>
                                    </div>      
                                </ApiarySiteTransfer>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        </div>
    </div>
</template>
<script>
import { v4 as uuid } from 'uuid';
import ProposalApiary from '../../form_apiary.vue'
import ApiarySiteTransfer from '../../form_apiary_site_transfer.vue'
import CommsLogs from '@common-utils/comms_logs.vue'
import FormSection from "@/components/forms/section_toggle.vue"
import {
    api_endpoints,
    helpers,
    constants
}
from '@/utils/hooks'
export default {
    name: 'ApiaryReferral',
    data: function() {
        let vm = this;
        return {
            detailsBody: 'detailsBody'+uuid(),
            addressBody: 'addressBody'+uuid(),
            contactsBody: 'contactsBody'+uuid(),
            assigned_officer_id: null,
            referral_sent_list: null,
            "loading": [],
            selected_referral: '',
            referral_text: '',
            referral_comment: '',
            sendingReferral: false,
            form: null,
            members: [],
            department_users : [],
            contacts_table_initialised: false,
            initialisedSelects: false,
            contacts_table_id: uuid() +'contacts-table',
            contacts_options:{
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                ajax: {
                    "url": vm.contactsURL,
                    "dataSrc": ''
                },
                columns: [
                    {
                        title: 'Name',
                        data: 'id',
                        mRender:function (data,type,full) {
                            return full.first_name + " " + full.last_name;
                        }
                    },
                    {
                        title: 'Phone',
                        data:'phone_number'
                    },
                    {
                        title: 'Mobile',
                        data:'mobile_number'
                    },
                    {
                        title: 'Fax',
                        data:'fax_number'
                    },
                    {
                        title: 'Email',
                        data:'email'
                    },
                  ],
                  processing: true
            },
            contacts_table: null,
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            logs_url: helpers.add_endpoint_json(api_endpoints.proposals,vm.$route.params.proposal_id+'/action_log'),
            comms_url: helpers.add_endpoint_json(api_endpoints.proposals,vm.$route.params.proposal_id+'/comms_log'),
            panelClickersInitialised: false,
            referral: {},
            apiaryReferralGroups: [],
        }
    },
    components: {
        FormSection,
        ProposalApiary,
        // datatable,
        CommsLogs,
        //MoreReferrals,
        //NewApply,
        //ApiaryReferralsForProposal,
        ApiarySiteTransfer,
        //OriginatingApprovalRequirements,
        //TargetApprovalRequirements,
    },
    props:{
            referralId:{
                type:Number,
            },
    },
    computed: {
        canAssign: function() {
            let assign = false;
            if (this.apiaryReferral && this.apiaryReferral.can_assign) {
                assign = true;
            }
            return assign;
        },
        canProcess: function() {
            let assign = false;
            if (this.apiaryReferral && this.apiaryReferral.can_process) {
                assign = true;
            }
            return assign;
        },

        apiaryReferral: function() {
            if (this.referral && this.referral.apiary_referral) {
                return this.referral.apiary_referral;
            }
            return null;
        },


        proposal: function(){
            return this.referral != null && this.referral != 'undefined' ? this.referral.proposal : null;
        },
        proposalApiaryReferrerChecklistAnswers: function() {
            if (this.proposal && this.proposal.proposal_apiary) {
                return this.proposal.proposal_apiary.referrer_checklist_answers;
            }
            return null;
        },
        proposalApiaryReferrerChecklistAnswersPerSite: function() {
            if (this.proposal && this.proposal.proposal_apiary) {
                return this.proposal.proposal_apiary.referrer_checklist_answers_per_site;
            }
            return null;
        },
        siteTransferProposalApiaryReferrerChecklistAnswers: function() {
            if (this.proposal && this.proposal.proposal_apiary) {
                return this.proposal.proposal_apiary.site_transfer_referrer_checklist_answers;
            }
            return null;
        },
        siteTransferProposalApiaryReferrerChecklistAnswersPerSite: function() {
            if (this.proposal && this.proposal.proposal_apiary) {
                return this.proposal.proposal_apiary.site_transfer_referrer_checklist_answers_per_site;
            }
            return null;
        },
        contactsURL: function(){
            return this.proposal!= null ? helpers.add_endpoint_json(api_endpoints.organisations,this.proposal.applicant.id+'/contacts') : '';
        },
        isLoading: function() {
          return this.loading.length > 0
        },
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
        proposal_form_url: function() {
          return (this.proposal) ? `/api/proposal_apiary/${this.proposal.proposal_apiary.id}/assessor_save.json` : '';
        },
        isFinalised: function(){
            return !(this.referral != null  && this.referral.processing_status == 'Awaiting'); 
        },
        applicantAddress: function() {
            if (this.proposal && this.proposal.applicant_address) {
                return this.proposal.applicant_address;
            } else {
                return {}
            }
        },
        canAction: function() {
            let retVal = false;
            if (!this.isFinalised && this.referral.can_be_completed) {
                for (let member of this.referral.apiary_referral.referral_group.all_members_list) {
                    if (member.id === this.proposal.current_assessor.id) {
                        retVal = true;
                    }
                }
            }
            return retVal;
        },
        organisationApplicant: function() {
            let retVal = false;
            if (this.proposal && this.proposal.applicant_type === 'organisation') {
                retVal = true;
            }
            return retVal;
        },
        hasAssessorMode:function(){
            return this.proposal && this.proposal.assessor_mode.has_assessor_mode ? true : false;
        },
    },
    methods: {
        formatDate: function(data){
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss'): '';
        },
        updateAssignedOfficerSelect: function(){
            let vm = this;
            console.log(vm)
            $(vm.$refs.assigned_officer_referral).val(vm.apiaryReferral.assigned_officer_id);
            $(vm.$refs.assigned_officer_referral).trigger('change');
        },
        assignRequestUser: async function(){
            await this.$nextTick();
            const response = await fetch(helpers.add_endpoint_json(api_endpoints.apiary_referrals,this.referral.apiary_referral.id+'/assign_request_user'),
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const res = await response.json();
            this.referral = res;
            await this.$nextTick();
            this.updateAssignedOfficerSelect();
        },
        assignTo: async function() {
            await this.$nextTick();
            const data = {'assigned_officer_id': this.apiaryReferral.assigned_officer_id};
            const response = await fetch(helpers.add_endpoint_json(api_endpoints.apiary_referrals,this.referral.apiary_referral.id+'/assign_to'),{
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const res = await response.json();
            this.referral = res.body;
            await this.$nextTick();
            this.updateAssignedOfficerSelect();
        },
        unAssign: async function() {
            await this.$nextTick();
            const response = await fetch(helpers.add_endpoint_json(api_endpoints.apiary_referrals,this.referral.apiary_referral.id+'/unassign'),{
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const res = await response.json();
            this.referral = res;
            await this.$nextTick();
            this.updateAssignedOfficerSelect();
        },

        initialiseAssignedOfficerSelect:function(reinit=false){
            let vm = this;
            if (reinit){
                $(vm.$refs.assigned_officer_referral).data('select2') ? $(vm.$refs.assigned_officer_referral).select2('destroy'): '';
            }
            // Assigned officer select
            $(vm.$refs.assigned_officer_referral).select2({
                "theme": "bootstrap",
                allowClear: true,
                placeholder:"Select Officer"
            }).
            on("select2:select", async function (e) {
                var selected = $(e.currentTarget);
                vm.apiaryReferral.assigned_officer_id = selected.val();
                await vm.assignTo();
            }).on("select2:unselect", async function () {
                vm.apiaryReferral.assigned_officer_id = null;
                await vm.unAssign();
            });
        },

        refreshFromResponse:function(response){
            let vm = this;
            vm.proposal = helpers.copyObject(response);
            vm.proposal.applicant.address = vm.proposal.applicant.address != null ? vm.proposal.applicant.address : {};
        },
        initialiseOrgContactTable: function(){
            let vm = this;
            if (vm.proposal && !vm.contacts_table_initialised){
                vm.contacts_options.ajax.url = helpers.add_endpoint_json(api_endpoints.organisations,vm.proposal.applicant.id+'/contacts');
                vm.contacts_table = $('#'+vm.contacts_table_id).DataTable(vm.contacts_options);
                vm.contacts_table_initialised = true;
            }
        },
        commaToNewline(s){
            return s.replace(/[,;]/g, '\n');
        },
        proposedDecline: function(){
            this.$refs.proposed_decline.isModalOpen = true;
        },
        ammendmentRequest: function(){
            this.$refs.ammendment_request.isModalOpen = true;
        },
        save: function() {
          let vm = this;
          let formData = new FormData(vm.form);
          fetch(vm.proposal_form_url, {
            method: 'POST',
            body: formData
            })
            .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            //return response.json(); // or response.text(), depending on your backend
            })
            .then(() => {
                swal.fire({
                    title: 'Saved',
                    text: 'Your proposal has been saved',
                    icon: 'success',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                    },
                });
            })
            .catch(err => {
                console.log(err);
            });
        },
        fetchProposalGroupMembers: function(){
            let vm = this;
            vm.loading.push('Loading Proposal Group Members');
             fetch(api_endpoints.organisation_access_group_members)
            .then(async (response) => {
                if (!response.ok) { return response.json().then(err => { throw err }); }
                vm.members = await response.json();
                vm.loading.splice('Loading Proposal Group Members',1);
            }).catch((error) => {
                console.log(error);
                vm.loading.splice('Loading Proposal Group Members',1);
            })
        },
        fetchReferral: function(){
            let vm = this;
            fetch(helpers.add_endpoint_json(api_endpoints.referrals,vm.referral.id))
            .then(async (res) => {
                if (!res.ok) { return res.json().then(err => { throw err }); }
                vm.referral = await res.json();
                vm.referral.proposal.applicant.address = vm.proposal.applicant.address != null ? vm.proposal.applicant.address : {};
            }).catch(err => {
              console.log(err);
            });
        },
        completeReferral:function(){
            let vm = this;
            let data = {'referral_comment': this.referral_comment};
            
            swal.fire({
                title: "Complete Referral",
                text: "Are you sure you want to complete this referral?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: 'Submit',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
            }).then((swalresult) => {
                if (swalresult.isConfirmed) {
                    let formData = new FormData(this.form);
                    fetch(vm.proposal_form_url, {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => {
                        if (!response.ok) {
                        throw new Error(`Form save failed: ${response.status}`);
                        }
                    })
                    .then(() => {
                        // Second POST: Complete referral
                        return fetch(
                        helpers.add_endpoint_json(api_endpoints.apiary_referrals,this.referral.apiary_referral.id+'/complete'),{
                            method: 'POST',
                            headers: {
                            'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(data)
                        }) .then(response => {
                            if (!response.ok) {
                            throw new Error(`Referral completion failed: ${response.status}`);
                            }
                            return response.json();
                        })
                        .then(() => {
                            //this.referral = responseData;
                            this.$router.push({ path: '/internal' });
                         })
                        .catch(error => {
                            console.log(error);
                            swal.fire({
                                title: 'Referral Error',
                                text: error,
                                icon: 'error',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                        });
                    
                    }).catch(error => {
                        console.log(error);
                    });
                }
            }).catch(error => {
                console.log(error);
            });
        }
    },
    mounted: function() {
        let vm = this;
        vm.fetchProposalGroupMembers();        
    },
    updated: function(){
        let vm = this;
        if (!vm.panelClickersInitialised){
            $('.panelClicker[data-toggle="collapse"]').on('click', function () {
                var chev = $(this).children()[0];
                window.setTimeout(function () {
                    $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
                },100);
            }); 
            vm.panelClickersInitialised = true;
        }
        this.$nextTick(() => {
            vm.initialiseOrgContactTable();
            //vm.initialiseSelects();
            vm.form = document.forms.new_proposal;
        });
    },
    created: async function() {
       fetch(helpers.add_endpoint_json(api_endpoints.referrals,this.referralId))
        .then(async (res) => {
            if (!res.ok) { return res.json().then(err => { throw err }); }
            this.referral = await res.json();
            if (this.referral.proposal.applicant) {
                this.referral.proposal.applicant.address = this.proposal.applicant.address != null ? this.proposal.applicant.address : {};
            }
        })
        await this.$nextTick();
        this.initialiseAssignedOfficerSelect()
    },
    beforeRouteUpdate: function(to, from, next) {
           fetch(`/api/proposal/${to.params.proposal_id}/referral_proposal.json`)
          .then(async (res) => {
            if (!res.ok) { return res.json().then(err => { throw err }); }
            const data = await res.json();
              next(vm => {
                vm.referral = data;
                vm.referral.proposal.applicant.address = vm.referral.proposal.applicant.address != null ? vm.referral.proposal.applicant.address : {};
              });
            })
            .catch(err => {
              console.log(err);
            });
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
.separator {
    border: 1px solid;
    margin-top: 15px;
    margin-bottom: 10px;
    width: 100%;
}
</style>
