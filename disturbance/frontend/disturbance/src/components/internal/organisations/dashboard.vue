<template>
<div class="container" id="internalOrgAccessDash">
    <div class="row">
        <div class="col-sm-12">
            <FormSection :form-collapse="false" label="Organisation Access Requests">
                <div class="row">
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="">Role</label>
                            <select class="form-select" v-model="filterRole">
                                <option value="All">All</option>
                                <option v-for="r in roleChoices" :value="r" :key="r">{{r}}</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="">Status</label>
                            <select class="form-select" v-model="filterStatus">
                                <option value="All">All</option>
                                <option v-for="s in statusChoices" :value="s" :key="s">{{s}}</option>
                            </select>
                        </div>
                    </div>
                </div>
                <template v-if="table_id">
                    <datatable
                        ref="org_access_table"
                        id="org-access-table"
                        :dtOptions="dtOptions"
                        :dtHeaders="dtHeaders"
                        :key="table_id">
                    </datatable>
                </template>
            </FormSection>
        </div>
    </div>
</div>
</template>
<script>
import { v4 as uuid } from 'uuid';
import datatable from '@vue-utils/datatable.vue'
import FormSection from '@/components/forms/section_toggle.vue';
import {
  api_endpoints,
  helpers,
  constants
}
from '@/utils/hooks'
export default {
  name: 'OrganisationAccessDashboard',
  data() {
    let vm = this;
    return {
        // Filters
        pBody: 'pBody' + uuid(),
        filterOrganisation: 'All',
        filterApplicant : 'All',
        filterRole : 'All',
        filterStatus: 'All',
        organisationChoices: [],
        applicantChoices: [],
        statusChoices: [],
        roleChoices: [],
        members:[],
        profile: {},
        table_id: 0,
        dtOptions:{
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                processing:true,
                order: [[0, "desc"]],
                ajax: {
                    "url": helpers.add_endpoint_json(api_endpoints.organisation_requests,'datatable_list'),
                    "dataSrc": '',
                },
                columns:[
                    {
                        data:"id",
                        defaultContent: '',
                    },
                    {
                        data:"name",
                        defaultContent: '',
                    },
                    {
                        data:"requester",
                        defaultContent: '',
                    },
                    {
                        data:"role",
                        defaultContent: '',
                    },
                    {
                        data:"status",
                        defaultContent: '',
                    },
                    {
                        data:"lodgement_date",
                        mRender:function(data){
                            return moment(data).format('DD/MM/YYYY')
                        },
                        defaultContent: '',
                    },
                    {
                        data:"assigned_officer",
                        defaultContent: '',
                    },
                    {
                        data:"id",
                        mRender:function(data, type, full){
                            let column
                            if (full.status == 'Approved' || full.status == 'Declined'){
                                column = "<a href='/internal/organisations/access/__ID__' >View </a>";
                            }
                            else{
                                if(vm.is_assessor){
                                    column = "<a href='/internal/organisations/access/__ID__'> Process </a>";
                                }
                                else{
                                    column = "<a href='/internal/organisations/access/__ID__' >View </a>";
                                }
                            }
                            return column.replace(/__ID__/g, data);
                        },
                        defaultContent: '',
                    },
                ],
                initComplete: function(){
                    // Grab Organisation from the data in the table
                    var organisationColumn = vm.$refs.org_access_table.vmDataTable.columns(1);
                    organisationColumn.data().unique().sort().each( function ( d ) {
                        let organisationChoices = [];
                        $.each(d,(index,a) => {
                            a != null && organisationChoices.indexOf(a) < 0 ? organisationChoices.push(a): '';
                        })
                        vm.organisationChoices = organisationChoices;
                    });
                    // Grab Applicant from the data in the table
                    var applicantColumn = vm.$refs.org_access_table.vmDataTable.columns(2);
                    applicantColumn.data().unique().sort().each( function ( d ) {
                        let applicationChoices = [];
                        $.each(d,(index,a) => {
                            a != null && applicationChoices.indexOf(a) < 0 ? applicationChoices.push(a): '';
                        })
                        vm.applicantChoices = applicationChoices;
                    });
                    // Grab Role from the data in the table
                    var roleColumn = vm.$refs.org_access_table.vmDataTable.columns(3);
                    roleColumn.data().unique().sort().each( function ( d ) {
                        let roleChoices = [];
                        $.each(d,(index,a) => {
                            a != null && roleChoices.indexOf(a) < 0 ? roleChoices.push(a): '';
                        })
                        vm.roleChoices = roleChoices;
                    });
                    // Grab Status from the data in the table
                    var statusColumn = vm.$refs.org_access_table.vmDataTable.columns(4);
                    statusColumn.data().unique().sort().each( function ( d ) {
                        let statusChoices = [];
                        $.each(d,(index,a) => {
                            a != null && statusChoices.indexOf(a) < 0 ? statusChoices.push(a): '';
                        })
                        vm.statusChoices = statusChoices;
                    });
                }
            },
            dtHeaders:["Request Number","Organisation","Applicant","Role","Status","Lodged on","Assigned To","Action"],
        }
    },
    watch: {
        filterOrganisation: function() {
            let vm = this;
            if (vm.filterOrganisation!= 'All') {
                vm.$refs.org_access_table.vmDataTable.columns(1).search(vm.filterOrganisation).draw();
            } else {
                vm.$refs.org_access_table.vmDataTable.columns(1).search('').draw();
            }
        },
        filterApplicant: function() {
            let vm = this;
            if (vm.filterApplicant != 'All') {
                vm.$refs.org_access_table.vmDataTable.columns(2).search(vm.filterApplicant).draw();
            } else {
                vm.$refs.org_access_table.vmDataTable.columns(2).search('').draw();
            }
        },
        filterRole: function() {
            let vm = this;
            if (vm.filterRole != 'All') {
                vm.$refs.org_access_table.vmDataTable.columns(3).search(vm.filterRole).draw();
            } else {
                vm.$refs.org_access_table.vmDataTable.columns(3).search('').draw();
            }
        },
        filterStatus: function() {
            let vm = this;
            if (vm.filterStatus!= 'All') {
                vm.$refs.org_access_table.vmDataTable.columns(4).search(vm.filterStatus).draw();
            } else {
                vm.$refs.org_access_table.vmDataTable.columns(4).search('').draw();
            }
        },
    },
    components: {
        datatable,
        FormSection
    },
    computed: {
        isLoading: function () {
            return this.loading.length == 0;
        },
        is_assessor: function(){
            return this.check_assessor()
        },
    },
    methods: {
        fetchAccessGroupMembers: async function(){
            let url = api_endpoints.apiary_organisation_access_group_members;
            const response = await fetch(url)
            if (!response.ok) { return response.json().then(err => { throw err }); }
            this.members = await response.json();
            this.table_id = uuid()
        },
        fetchProfile: async function(){
            const response = await fetch(api_endpoints.profile);
            if (!response.ok) { return response.json().then(err => { throw err }); }
            this.profile = await response.json();
        },

        check_assessor: function(){
            let vm = this
            let assessor = vm.members.filter(elem => elem.id == vm.profile.id)
            if (assessor.length > 0)
                return true;
            else
                return false;
        },
    },
    created: async function() {
        await this.fetchProfile();
        await this.fetchAccessGroupMembers();
    },

}
</script>
