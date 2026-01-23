<template id="approvals_dashboard">
    <div class="row">
        <div class="col-sm-12">
            <div class="row">
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Status</label>
                        <select class="form-select" v-model="filterProposalStatus">
                            <option value="All">All</option>
                            <option v-for="s in approval_status" :value="s" :key="s">{{s}}</option>
                        </select>
                    </div>
                </div>

                <div class="col-md-3">
                    <label for="">Start From</label>
                    <input
                        id="proposal-start-from"
                        type="date"
                        class="form-control"
                        v-model="proposal_start_from"
                        placeholder="DD/MM/YYYY"
                        :max="proposal_start_to"
                    >
                </div>
                <div class="col-md-3">
                    <label for="">Start To</label>
                    <input
                        id="proposal-start-to"
                        type="date"
                        class="form-control"
                        v-model="proposal_start_to"
                        placeholder="DD/MM/YYYY"
                        :min="proposal_start_from"
                    >
                </div>
            </div>
            <div class="row">
                <div class="col-md-3">
                    <label for="">Expiry From</label>
                    <input
                        id="proposal-expiry-from"
                        type="date"
                        class="form-control"
                        v-model="proposal_expiry_from"
                        placeholder="DD/MM/YYYY"
                        :max="proposal_expiry_to"
                    >
                </div>
                <div class="col-md-3">
                    <label for="">Expiry To</label>
                    <input
                        id="proposal-expiry-to"
                        type="date"
                        class="form-control"
                        v-model="proposal_expiry_to"
                        placeholder="DD/MM/YYYY"
                        :min="proposal_expiry_from"
                    >
                </div>
            </div>
            <div class="row">
                <div class="col-lg-12" style="margin-top:25px;">
                    <div v-if="datatableReady">
                        <datatable ref="proposal_datatable" :id="datatable_id" :dtOptions="proposal_options" :dtHeaders="proposal_headers"/>
                    </div>
                </div>
            </div>
        </div>
        <ApprovalCancellation ref="approval_cancellation"  @refreshFromResponse="refreshFromResponse"></ApprovalCancellation>
        <ApprovalSuspension ref="approval_suspension"  @refreshFromResponse="refreshFromResponse"></ApprovalSuspension>
        <ApprovalSurrender ref="approval_surrender"  @refreshFromResponse="refreshFromResponse"></ApprovalSurrender>
        <ApprovalHistory ref="approval_history" />

    </div>
</template>
<script>
import { v4 as uuid } from 'uuid';
import datatable from '@/utils/vue/datatable.vue'
import ApprovalCancellation from '../internal/approvals/approval_cancellation.vue'
import ApprovalSuspension from '../internal/approvals/approval_suspension.vue'
import ApprovalSurrender from '../internal/approvals/approval_surrender.vue'
import ApprovalHistory from './approval_history_modal.vue';
import {
    api_endpoints,
    helpers,
    constants
}from '@/utils/hooks'
export default {
    name: 'ApprovalsTableDash',
    props: {
        level:{
            type: String,
            required: true,
            validator:function(val) {
                let options = ['internal','referral','external'];
                return options.indexOf(val) != -1 ? true: false;
            }
        },
        url:{
            type: String,
            required: true
        }
    },
    data() {
        // let vm = this;
        return {
            pBody: 'pBody' + uuid(),
            datatable_id: 'approvals-datatable-'+uuid(),
            uuid: 0,
            //datatable_id: 'proposal-datatable-'+vm.uuid,
            //Profile to check if user has access to process Proposal
            profile: {},
            approval_history: {
                isModalOpen: false,
                approval_history_id: null,
            },
            // Filters for Proposals
            filterProposalRegion: 'All',
            filterProposalActivity: 'All',
            filterProposalStatus: 'All',
            // filterProposalStartFrom: '',
            // filterProposalStartTo: '',
            proposal_start_from: '',
            proposal_start_to: '',
            // filterProposalExpiryFrom: '',
            // filterProposalExpiryTo: '',
            proposal_expiry_from: '',
            proposal_expiry_to: '',
            filterProposalSubmitter: 'All',
            dashboardTitle: '',
            dashboardDescription: '',
            dateFormat: 'DD/MM/YYYY',
            datepickerOptions:{
                format: 'DD/MM/YYYY',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            approval_status:[],
            proposal_activityTitles : [],
            proposal_regions: [],
            proposal_submitters: [],
            select2Applied: false,
            proposal_options: {},
            datatableReady: false,
        }
    },
    components:{
        datatable,
        ApprovalCancellation,
        ApprovalSuspension,
        ApprovalSurrender,
        ApprovalHistory
    },
    watch:{
        filterProposalRegion: function(){
            //this.$refs.proposal_datatable.vmDataTable.draw();
            let vm = this;
            if (vm.filterProposalRegion!= 'All') {
                vm.$refs.proposal_datatable.vmDataTable.column('current_proposal__region__name:name').search(vm.filterProposalRegion).draw();
            } else {
                vm.$refs.proposal_datatable.vmDataTable.column('current_proposal__region__name:name').search('').draw();
            }
        },
        filterProposalActivity: function() {
            let vm = this;
            if (vm.filterProposalActivity!= 'All') {
                vm.$refs.proposal_datatable.vmDataTable.column('current_proposal__activity:name').search(vm.filterProposalActivity).draw();
            } else {
                vm.$refs.proposal_datatable.vmDataTable.column('current_proposal__activity:name').search('').draw();
            }
        },
        filterProposalSubmitter: function(){
            //this.$refs.proposal_datatable.vmDataTable.draw();
            let vm = this;
            if (vm.filterProposalSubmitter!= 'All') {
                vm.$refs.proposal_datatable.vmDataTable.columns(4).search(vm.filterProposalSubmitter).draw();
            } else {
                vm.$refs.proposal_datatable.vmDataTable.columns(4).search('').draw();
            }
        },
        filterProposalStatus: function() {
            let vm = this;
            if (vm.filterProposalStatus!= 'All') {
                vm.$refs.proposal_datatable.vmDataTable.column('status:name').search(vm.filterProposalStatus).draw();
            } else {
                vm.$refs.proposal_datatable.vmDataTable.column('status:name').search('').draw();
            }
        },
        // filterProposalStartFrom: function(){
        //     this.$refs.proposal_datatable.vmDataTable.draw();
        // },
        // filterProposalStartTo: function(){
        //     this.$refs.proposal_datatable.vmDataTable.draw();
        // },
        // filterProposalExpiryFrom: function(){
        //     this.$refs.proposal_datatable.vmDataTable.draw();
        // },
        // filterProposalExpiryTo: function(){
        //     this.$refs.proposal_datatable.vmDataTable.draw();
        // }
        dateRangeIdentifierForReloadProposalTable: function(){
            this.$refs.proposal_datatable.vmDataTable.draw();
        },
    },
    computed: {
        filterProposalExpiryFrom: {
            get() {
                // If our internal date exists, convert it for submission, etc
                if (this.proposal_expiry_from) {
                    return moment(this.proposal_expiry_from, 'YYYY-MM-DD').format('DD/MM/YYYY');
                }
                return ''; // Otherwise, return an empty string.
            }
        },
        filterProposalExpiryTo : {
            get() {
                // If our internal date exists, convert it for submission, etc
                if (this.proposal_expiry_to) {
                    return moment(this.proposal_expiry_to, 'YYYY-MM-DD').format('DD/MM/YYYY');
                }
                return ''; // Otherwise, return an empty string.
            }
        },
        dateRangeIdentifierForReloadProposalTable() {
            return `${this.proposal_expiry_from}|${this.proposal_expiry_to}|${this.proposal_start_from}|${this.proposal_start_to}`;
        },
        filterProposalStartFrom: {
            get() {
                // If our internal date exists, convert it for submission, etc
                if (this.proposal_start_from) {
                    return moment(this.proposal_start_from, 'YYYY-MM-DD').format('DD/MM/YYYY');
                }
                return ''; // Otherwise, return an empty string.
            }
        },
        filterProposaStartTo : {
            get() {
                // If our internal date exists, convert it for submission, etc
                if (this.proposal_start_to) {
                    return moment(this.proposal_start_to, 'YYYY-MM-DD').format('DD/MM/YYYY');
                }
                return ''; // Otherwise, return an empty string.
            }
        },
        status: function(){
            //return this.is_external ? this.external_status : this.internal_status;
            return [];
        },
        is_external: function(){
            return this.level == 'external';
        },
        is_referral: function(){
            return this.level == 'referral';
        },
        proposal_headers: function() {
            let columnHeaders = [
                "Number",
                "Holder",
                "Status",
                "Start Date",
                "Expiry Date",
                "Licence",
                "Action"
            ];
            return columnHeaders;
        },
        tableColumns: function() {
            let vm = this;
            let columnList = [
                {
                    data: "id",
                    'render':function(data,type,full){
                    if(!vm.is_external){
                        var result = '';
                        var popTemplate = '';
                        var message = '';
                        let tick = '';
                        tick = "<i class='fa fa-exclamation-triangle' style='color:red'></i>"
                        result = '<span>' + full.lodgement_number + '</span>';
                        if (full.migrated){
                            result = '<span>' + full.lodgement_number + ' (M)</span>';
                        } else {
                            result = '<span>' + full.lodgement_number + '</span>';
                        }

                        if(full.can_reissue){
                            if(!full.can_action){
                                if(full.set_to_cancel){
                                    message = 'This Approval is marked for cancellation to future date';
                                }
                                if(full.set_to_suspend){
                                    message = 'This Approval is marked for suspension to future date';
                                }
                                if(full.set_to_surrender){
                                    message = 'This Approval is marked for surrendering to future date';
                                }
                                popTemplate = _.template('<a href="#" ' +
                                        'role="button" ' +
                                        'data-toggle="popover" ' +
                                        'data-trigger="hover" ' +
                                        'data-placement="top auto"' +
                                        'data-html="true" ' +
                                        'data-content="<%= text %>" ' +
                                        '><%= tick %></a>');
                                result += popTemplate({
                                    text: message,
                                    tick: tick
                                });

                            }
                        }
                        return result;
                    }
                    else { 
                        if (full.migrated){
                            return full.lodgement_number + ' (M)'
                        } else {
                            return full.lodgement_number
                        }
                    }
                    },
                    'createdCell': helpers.dtPopoverCellFn,
                    name: "id, lodgement_number",
                    searchable: true,
                    defaultContent: '',
                }];
            columnList.push({
                    data: "applicant",
                    name: "applicant__organisation__name, proxy_applicant__first_name, proxy_applicant__last_name, proxy_applicant__email",
                    searchable: true,
                    defaultContent: '',
                },
                {
                    data: "status",
                    name: 'status',
                    defaultContent: '',
                },
                {
                    data: "start_date",
                    mRender:function (data) {
                        return data != '' && data != null ? moment(data).format(vm.dateFormat): '';
                    },
                    searchable: false,
                    defaultContent: '',
                },
                {
                    data: "expiry_date",
                    mRender:function (data) {
                        return data != '' && data != null ? moment(data).format(vm.dateFormat): '';
                    },
                    searchable: true,
                    defaultContent: '',
                },
                {
                    data: "licence_document",
                    mRender:function(data,type,full){
                        //let link='';
                        //return `<a href="${data}" target="_blank"><i style="color:red" class="fa fa-file-pdf-o"></i></a>`;
                        // link=`<a href='#${full.id}'<i style="color:red" class="fa fa-file-pdf-o"></i></a>`;
                        if (full.apiary_approval) {
                            return `<a href="${full.latest_apiary_licence_document}" target="_blank"><i style="color:red" class="fa fa-file-pdf-o"></i></a>`;
                        } else {
                            if(vm.is_external){
                                return `<a href="${data}" target="_blank"><i style="color:red" class="fa fa-file-pdf-o"></i></a>`;
                            }
                            else{
                                return `<a href="#${full.id}" data-pdf-approval='${full.id}' media-link='${data}'><i style="color:red" class="fa fa-file-pdf-o"></i></a>`;
                            }
                        }
                        //return link;
                    },
                    name: 'licence_document__name',
                    searchable: false,
                    //visible: false,
                    className: "noexport",
                    defaultContent: '',
                },
                {
                    data: '',
                    mRender:function (data,type,full) {
                        let links = '';
                        if (!vm.is_external){
                            //if(full.can_approver_reissue && full.current_proposal && full.current_proposal.application_type !== 'Site Transfer'){
                            if(full.can_approver_reissue && full.current_proposal){
                                    links +=  `<a href='#${full.id}' data-reissue-approval='${full.current_proposal_id}'>Reissue</a><br/>`;
                            }
                            if(vm.check_assessor(full)){
                                // if(full.can_approver_reissue){
                                //     links +=  `<a href='#${full.id}' data-reissue-approval='${full.current_proposal}'>Reissue</a><br/>`;
                                // }
                                if(full.can_reissue && full.can_action){
                                    links +=  `<a href='#${full.id}' data-cancel-approval='${full.id}'>Cancel</a><br/>`;
                                    links +=  `<a href='#${full.id}' data-surrender-approval='${full.id}'>Surrender</a><br/>`;
                                }
                                if(full.status == 'Current' && full.can_action){
                                    links +=  `<a href='#${full.id}' data-suspend-approval='${full.id}'>Suspend</a><br/>`;
                                }
                                if(full.can_reinstate)
                                {
                                    links +=  `<a href='#${full.id}' data-reinstate-approval='${full.id}'>Reinstate</a><br/>`;
                                }
                                links +=  `<a href='/internal/approval/${full.id}'>View</a><br/>`;
                            }
                            else{
                                links +=  `<a href='/internal/approval/${full.id}'>View</a><br/>`;

                            }
                            if(full.renewal_document && full.renewal_sent){
                              links +=  `<a href='${full.renewal_document}' target='_blank'>Renewal Notice</a><br/>`;

                            }
                            // if(full.can_approver_reissue){
                            //         links +=  `<a href='#${full.id}' data-reissue-approval='${full.current_proposal}'>Reissue</a><br/>`;
                            // }
                        }
                        else{
                            if (full.can_reissue) {
                                links +=  `<a href='/external/approval/${full.id}'>View</a><br/>`;
                                if(full.can_action){
                                    links +=  `<a href='#${full.id}' data-surrender-approval='${full.id}'>Surrender</a><br/>`;
                                    if(full.can_amend){
                                       links +=  `<a href='#${full.id}' data-amend-approval='${full.current_proposal_id}'>Amend</a><br/>`;
                                   }
                                }
                                if(full.renewal_document && full.renewal_sent && full.can_renew) {
                                    links +=  `<a href='#${full.id}' data-renew-approval='${full.current_proposal_id}'>Renew</a><br/>`;
                                }
                            }
                            else {
                                links +=  `<a href='/external/approval/${full.id}'>View</a><br/>`;

                            }
                        }
                        if (full.apiary_approval) {
                            links +=  `<a href='#${full.id}' approval-history='${full.id}'>Licence History</a><br/>`;
                        } else {
                            links +=  `<a href='#${full.id}' approval-history='${full.id}'>Approval History</a><br/>`;
                        }
                        return links;
                    },
                    searchable: false,
                    orderable: false,
                    name: '',
                    className: "noexport",
                    defaultContent: '',
                },
                {
                    data: 'template_group',
                    searchable: false,
                    orderable: false,
                    visible: false,
                    className: "noexport",
                    defaultContent: '',
                }
                );
            return columnList;
        }
    },
    methods:{
        set_proposal_options: function() {
            this.datatableReady = false;
            let vm = this;
            this.uuid++;
            //$(vm.$refs.proposal_datatable.vmDataTable).DataTable().destroy();
            //$(vm.$refs.proposal_datatable.vmDataTable).DataTable({
            this.proposal_options = {
                destroy: true,
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                serverSide: true,
                lengthMenu: [ [10, 25, 50, 100], [10, 25, 50, 100] ],
                order: [
                    [0, 'desc']
                    ],
                ajax: {
                    "url": vm.url,
                    "dataSrc": 'data',
                    // adding extra GET params for Custom filtering
                    "data": function ( d ) {
                        //d.regions = vm.filterProposalRegion.join(); // no need to add this since we can filter normally (filter is not multi-select in Approval table)
                        // d.start_date_from = vm.filterProposalStartFrom != '' && vm.filterProposalStartFrom != null ? moment(vm.filterProposalStartFrom, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
                        // d.start_date_to = vm.filterProposalStartTo != '' && vm.filterProposalStartTo != null ? moment(vm.filterProposalStartTo, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
                        d.start_date_from = vm.proposal_start_from != '' && vm.proposal_start_from != null ? moment(vm.proposal_start_from, 'YYYY-MM-DD').format('YYYY-MM-DD'): '';
                        d.start_date_to = vm.proposal_start_to != '' && vm.proposal_start_to != null ? moment(vm.proposal_start_to, 'YYYY-MM-DD').format('YYYY-MM-DD'): '';
                        // d.expiry_date_from = vm.filterProposalExpiryFrom != '' && vm.filterProposalExpiryFrom != null ? moment(vm.filterProposalExpiryFrom, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
                        // d.expiry_date_to = vm.filterProposalExpiryTo != '' && vm.filterProposalExpiryTo != null ? moment(vm.filterProposalExpiryTo, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
                        d.expiry_date_from = vm.proposal_expiry_from != '' && vm.proposal_expiry_from != null ? moment(vm.proposal_expiry_from, 'YYYY-MM-DD').format('YYYY-MM-DD'): '';
                        d.expiry_date_to = vm.proposal_expiry_to != '' && vm.proposal_expiry_to != null ? moment(vm.proposal_expiry_to, 'YYYY-MM-DD').format('YYYY-MM-DD'): '';
                        d.region = vm.filterProposalRegion;
                        d.proposal_activity = vm.filterProposalActivity;
                        d.approval_status = vm.filterProposalStatus;
                    }
                },
                columnDefs: [
                    { responsivePriority: 1, targets: 0 }, // First visible column has top priority (e.g. proposal_number
                    { responsivePriority: 2, targets: -2 }, // If the actions is the last entry in columns then this will make it 2nd top priority soo as long as the screen is a decent size it will always be shown
                ],
                dom: "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                buttons:[
                    {
                        extend: 'excelHtml5',
                        className: 'btn btn-primary me-2 rounded',
                        exportOptions: {
                            //columns: ':not(:last-child)'
                            columns: ':not(.noexport)'
                        }
                    },
                    {
                        extend: 'csvHtml5',
                        className: 'btn btn-primary me-2 rounded',
                        exportOptions: {
                            //columns: ':not(:last-child)'
                            columns: ':not(.noexport)'
                        }
                    },
                ],
                columns: vm.tableColumns,
                processing: true,
                initComplete: function() {
                    //vm.showHideColumns()
                },
            };
            this.datatableReady = true;
            this.$nextTick(() => {
                this.initialiseSearch();
                this.addEventListeners();
            });
        },
        setDashboardText: function() {
            this.dashboardTitle = 'Licences';
            this.dashboardDescription = 'View existing licences and amend or renew them';
        },

        fetchFilterLists: function(){
            let vm = this;

            fetch(api_endpoints.filter_list_approvals).then(
                async (response) => {
                    if (!response.ok) { return response.json().then(err => { throw err }); }
                    const filter_lists_approval = await response.json();
                    vm.proposal_regions = filter_lists_approval.regions;
                    vm.proposal_activityTitles = filter_lists_approval.activities;
                    vm.proposal_submitters = filter_lists_approval.submitters;
                    vm.approval_status = filter_lists_approval.approval_status_choices;
                }).catch((error) => {
                    console.log(error);
                });
        },

        addEventListeners: function(){
            let vm = this;
            // Internal Reissue listener
            vm.$refs.proposal_datatable.vmDataTable.on('click', 'a[data-reissue-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-reissue-approval');
                vm.reissueApproval(id);
            });

            //Internal Cancel listener
            vm.$refs.proposal_datatable.vmDataTable.on('click', 'a[data-cancel-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-cancel-approval');
                vm.cancelApproval(id);
            });

            //Internal Suspend listener
            vm.$refs.proposal_datatable.vmDataTable.on('click', 'a[data-suspend-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-suspend-approval');
                vm.suspendApproval(id);
            });

            // Internal Reinstate listener
            vm.$refs.proposal_datatable.vmDataTable.on('click', 'a[data-reinstate-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-reinstate-approval');
                vm.reinstateApproval(id);
            });

            //Internal/ External Surrender listener
            vm.$refs.proposal_datatable.vmDataTable.on('click', 'a[data-surrender-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-surrender-approval');
                vm.surrenderApproval(id);
            });

            // External renewal listener
            vm.$refs.proposal_datatable.vmDataTable.on('click', 'a[data-renew-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-renew-approval');
                vm.renewApproval(id);
            });

            // External amend listener
            vm.$refs.proposal_datatable.vmDataTable.on('click', 'a[data-amend-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-amend-approval');
                vm.amendApproval(id);
            });

            // Internal view pdf listener
            vm.$refs.proposal_datatable.vmDataTable.on('click', 'a[data-pdf-approval]', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-pdf-approval');
                var media_link = $(this).attr('media-link');
                vm.viewApprovalPDF(id, media_link);
            });
            // Create Licence History Listener.
            vm.$refs.proposal_datatable.vmDataTable.on('click', 'a[approval-history]', function(e) {
                e.preventDefault();
                let approval_id = $(this).attr('approval-history');
                vm.$refs.approval_history.approval_history_id = approval_id;
                vm.$refs.approval_history.isModalOpen = true;
            });

        },
        initialiseSearch:function(){
            this.regionSearch();
            this.dateSearch();
        },
        regionSearch:function(){
            let vm = this;
            vm.$refs.proposal_datatable.table.dataTableExt.afnFiltering.push(
                function(settings,data,dataIndex,original){
                    let found = false;
                    let filtered_regions = vm.filterProposalRegion.split(',');
                    if (filtered_regions == 'All'){ return true; }

                    let regions = original.region != '' && original.region != null ? original.region.split(','): [];

                    $.each(regions,(i,r) => {
                        if (filtered_regions.indexOf(r) != -1){
                            found = true;
                            return false;
                        }
                    });
                    if  (found) { return true; }

                    return false;
                }
            );
        },
        submitterSearch:function(){
            let vm = this;
            vm.$refs.proposal_datatable.table.dataTableExt.afnFiltering.push(
                function(settings,data,dataIndex,original){
                    let filtered_submitter = vm.filterProposalSubmitter;
                    if (filtered_submitter == 'All'){ return true; }
                    return filtered_submitter == original.submitter.email;
                }
            );
        },
        dateSearch:function(){
            let vm = this;
            vm.$refs.proposal_datatable.table.dataTableExt.afnFiltering.push(
                function(settings,data,dataIndex,original){
                    let from = vm.filterProposalExpiryFrom;
                    let to = vm.filterProposalExpiryTo;
                    let val = original.expiry_date;

                    if ( from == '' && to == ''){
                        return true;
                    }
                    else if (from != '' && to != ''){
                        return val != null && val != '' ? moment().range(moment(from,vm.dateFormat),moment(to,vm.dateFormat)).contains(moment(val)) :false;
                    }
                    else if(from == '' && to != ''){
                        if (val != null && val != ''){
                            return moment(to,vm.dateFormat).diff(moment(val)) >= 0 ? true : false;
                        }
                        else{
                            return false;
                        }
                    }
                    else if (to == '' && from != ''){
                        if (val != null && val != ''){
                            return moment(val).diff(moment(from,vm.dateFormat)) >= 0 ? true : false;
                        }
                        else{
                            return false;
                        }
                    }
                    else{
                        return false;
                    }
                }
            );
        },

        fetchProfile: function(){
            let vm = this;
            fetch(api_endpoints.profile).then(
                async (response) => {
                    if (!response.ok) { return response.json().then(err => { throw err }); }
                    vm.profile = await response.json();
                }).catch((error) => {
                    console.log(error);
                });
        },

        check_assessor: function(proposal){
            let vm = this;
            //console.log(proposal.id, proposal.can_approver_reissue);
            var assessor = proposal.allowed_assessors.filter(function(elem){
                    return(elem.id==vm.profile.id)

                });

            if (assessor.length > 0){
                //console.log(proposal.id, assessor)
                return true;
            }
            else
                return false;

        },

        reissueApproval:function (proposal_id) {
            let vm = this;
            let status= 'with_approver'
            let data = {'status': status}
            swal.fire({
                title: "Reissue Approval",
                text: "Are you sure you want to reissue this approval?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Reissue approval',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
            }).then(
                (result) => {
                    if (result.isConfirmed) {
                        fetch(helpers.add_endpoint_json(api_endpoints.proposals,(proposal_id+'/reissue_approval')),{
                            headers: { 'Content-Type': 'application/json' },
                            method: 'POST',
                            body: JSON.stringify(data),
                        })
                        .then(async (response) => {

                            if (!response.ok) {
                                const data = await response.json();
                                swal.fire({
                                    title: "Reissue Approval",
                                    text: JSON.stringify(data),
                                    icon: "error",
                                    customClass: {
                                        confirmButton: 'btn btn-primary',
                                    },
                                });
                                return;
                            }
                            vm.$router.push({
                                name:"internal-proposal",
                                params:{proposal_id:proposal_id}
                            });
                        }).catch((error) => {
                            console.log(error);
                        })
                    }
                });
        },

        reinstateApproval:function (approval_id) {
            let vm = this;
            // let status= 'with_approver'
            //let data = {'status': status}
            swal.fire({
                title: "Reinstate Approval",
                text: "Are you sure you want to reinstate this approval?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Reinstate approval',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
            }).then((result) => {
                if (result.isConfirmed){
                    fetch(helpers.add_endpoint_json(api_endpoints.approvals,(approval_id+'/approval_reinstate')),{
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                    })
                    .then(async (response) => {
                    if (!response.ok) {
                            const data = await response.json();
                            swal.fire({
                                icon: "error",
                                title: "Reinstate Approval",
                                text: JSON.stringify(data),
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            return;
                        }
                        swal.fire({
                            title: 'Reinstate',
                            text: 'Your approval has been reinstated',
                            icon: 'success',
                            customClass: {
                                confirmButton: 'btn btn-primary',
                            },
                        })
                        vm.$refs.proposal_datatable.vmDataTable.ajax.reload();

                    }).catch((error) => {
                        console.log(error);
                    });
                }
            });
        },

        renewApproval:function (proposal_id) {
            let vm = this;
            // let status= 'with_approver'
            //let data = {'status': status}
            swal.fire({
                title: "Renew Approval",
                text: "Are you sure you want to renew this approval?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Renew approval',
                //confirmButtonColor:'#d9534f'
            }).then((result) => {
                if (result.isConfirmed){
                    fetch(helpers.add_endpoint_json(api_endpoints.proposals,(proposal_id+'/renew_approval')),{}).then(
                    async (response) => {
                        if (!response.ok) {
                            const data = await response.json();
                            swal.fire({
                                title: "Renew Approval",
                                text: JSON.stringify(data),
                                icon: "error",
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            return;
                        }
                        let proposal = {}
                        proposal = await response.json();
                        vm.$router.push({
                            name:"draft_proposal",
                            params:{proposal_id: proposal.id}
                        });

                    }).catch((error) => {
                        console.log(error);
                        swal.fire({
                            title: "Renew Approval",
                            text: error,
                            icon: "error",
                            customClass: {
                                confirmButton: 'btn btn-primary',
                            },
                        })
                    });
                }
            });
        },

        amendApproval:function (proposal_id) {
            let vm = this;
            swal.fire({
                title: "Amend Approval",
                text: "Are you sure you want to amend this approval?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Amend approval',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
            }).then((result) => {
                if(result.isConfirmed){
                    fetch(helpers.add_endpoint_json(api_endpoints.proposals,(proposal_id+'/amend_approval')))
                    .then(async (response) => {
                        if (!response.ok) {
                            const data = await response.json();
                            swal.fire({
                                title: "Ammend Approval",
                                text: JSON.stringify(data),
                                icon: "error",
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            return;
                        }
                        let proposal = {}
                        proposal = await response.json();
                        vm.$router.push({
                            name:"draft_proposal",
                            params:{proposal_id: proposal.id}
                        });

                    }).catch((error) => {
                            console.log(error);
                            swal.fire({
                                title: "Amend Approval",
                                text: error.text,
                                icon: "error",
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            })

                        }
                    );
                }
            });
        },

        cancelApproval: function(approval_id){

            this.$refs.approval_cancellation.approval_id = approval_id;
            this.$refs.approval_cancellation.isModalOpen = true;
        },

        suspendApproval: function(approval_id){
            this.$refs.approval_suspension.approval = {};
            this.$refs.approval_suspension.approval_id = approval_id;
            this.$refs.approval_suspension.isModalOpen = true;
        },

        surrenderApproval: function(approval_id){

            this.$refs.approval_surrender.approval_id = approval_id;
            this.$refs.approval_surrender.isModalOpen = true;
        },

        refreshFromResponse: function(){
            this.$refs.proposal_datatable.vmDataTable.ajax.reload();
        },

        viewApprovalPDF: function(id,media_link){
            fetch(helpers.add_endpoint_json(api_endpoints.approvals,(id+'/approval_pdf_view_log')))
            .then(async (response) => {
                if (!response.ok) {
                    return response.json().then(err => { throw err });
                }
                //console.log(response)
            }).catch((error) => {
                console.log(error);
            });
            window.open(media_link, '_blank');
        },
    },
    mounted: function(){
		this.fetchFilterLists();
        this.fetchProfile();
        $( 'a[data-toggle="collapse"]' ).on( 'click', function () {
            var chev = $( this ).children()[ 0 ];
            window.setTimeout( function () {
                $( chev ).toggleClass( "glyphicon-chevron-down glyphicon-chevron-up" );
            }, 100 );
        });
    },
    created: function() {
        this.set_proposal_options();
    },
}
</script>
<style scoped>
</style>
