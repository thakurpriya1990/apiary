<template>
<div class="container" id="externalDash">
    <div class="row">
        <div class="col-sm-12">
            <div class="well well-sm">
                <span v-html="welcomeMessage"></span>
                <!--p>
                    Welcome to the {{system_name}} online system dashboard.<br/><br/> Here you can access your existing approvals/licences, view any proposals/applications in progress, lodge new<br/> proposals/applications or submit information required to comply with requirements listed on your approval/license
                </p-->
            </div>
        </div>
    </div>
    <ProposalDashTable level='external' :url='proposals_url'/>
    <ApprovalDashTable level='external' :url='approvals_url'/>
    <ComplianceDashTable level='external' :url='compliances_url'/>
</div>
</template>
<script>

import datatable from '@/utils/vue/datatable.vue'
import ProposalDashTable from '@common-utils/proposals_dashboard.vue'
import ApprovalDashTable from '@common-utils/approvals_dashboard.vue'
import ComplianceDashTable from '@common-utils/compliances_dashboard.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
export default {
    name: 'ExternalDashboard',
    data() {
        let vm = this;
        return {
            proposals_url: api_endpoints.proposals_paginated_external,
            approvals_url: api_endpoints.approvals_paginated_external,
            compliances_url: api_endpoints.compliances_paginated_external,

            system_name: api_endpoints.system_name,
            apiaryTemplateGroup: false,
            dasTemplateGroup: false,
            // from env var?
            apiarySystemName: 'Apiary System',
            dasSystemName: 'Disturbance Approval System',
        }
    },
    components:{
        ProposalDashTable,
        ApprovalDashTable,
        ComplianceDashTable
    },
    watch: {},
    computed: {
        welcomeMessage: function() {
            let welcomeText = ``;
            if (this.dasTemplateGroup) {
                welcomeText = `Welcome to the ${this.dasSystemName} online system dashboard.<p/><p/>
                    Here you can access your existing approvals, view any proposals in progress, lodge new
                    proposals or submit information required to comply with requirements listed on your approval.`
            } else if (this.apiaryTemplateGroup) {
                welcomeText = `Welcome to the ${this.apiarySystemName} online dashboard.<p/><p/>
                    Here you can access your existing apiary authorities, view any applications in progress, lodge new
                    applications or submit information required to comply with requirements listed on your authority.`
            }
            return welcomeText;
        },

    },
    methods: {
    },
    mounted: function () {
    },
    created: function() {
        // retrieve template group
        this.$http.get('/template_group',{
            emulateJSON:true
            }).then(res=>{
                //this.template_group = res.body.template_group;
                if (res.body.template_group === 'apiary') {
                    this.apiaryTemplateGroup = true;
                } else {
                    this.dasTemplateGroup = true;
                }
        },err=>{
        console.log(err);
        });
    },

}
</script>
