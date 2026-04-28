<template>
<div class="container" id="externalDash">
    <div class="row">
        <div class="col-sm-12">
            <div class="card mb-2 bg-light">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-9">
                            <span v-html="welcomeMessage"></span>
                        </div>
                    </div>
                </div>
            </div>
            <FormSection :form-collapse="false" label="Applications" Index="proposals" subtitle="View existing applications and lodge new ones">
                <ProposalDashTable level='external' :url='proposals_url'/>
            </FormSection>
            <FormSection :form-collapse="false" label="Licences" Index="proposals" subtitle="View existing licences and amend or renew them">
                <ApprovalDashTable level='external' :url='approvals_url'/>
            </FormSection>
            <FormSection :form-collapse="false" label="Compliance with requirements" Index="proposals" subtitle="View submitted compliances and submit new ones">
                <ComplianceDashTable level='external' :url='compliances_url'/>
            </FormSection>
        </div>
    </div>
</div>
</template>
<script>

import FormSection from '@/components/forms/section_toggle.vue';
import ProposalDashTable from '@common-utils/proposals_dashboard.vue'
import ApprovalDashTable from '@common-utils/approvals_dashboard.vue'
import ComplianceDashTable from '@common-utils/compliances_dashboard.vue'
import {
  api_endpoints,
}
from '@/utils/hooks'
export default {
    name: 'ExternalDashboard',
    data() {
        return {
            proposals_url: api_endpoints.proposals_paginated_external,
            approvals_url: api_endpoints.approvals_paginated_external,
            compliances_url: api_endpoints.compliances_paginated_external,
            system_name: api_endpoints.system_name,
            apiarySystemName: 'Apiary System',
        }
    },
    components:{
        ProposalDashTable,
        ApprovalDashTable,
        ComplianceDashTable,
        FormSection,
    },
    watch: {},
    computed: {
        welcomeMessage: function() {
            return `Welcome to the ${this.apiarySystemName} online dashboard.<p/><p/>
                Here you can access your existing apiary authorities, view any applications in progress, lodge new
                applications or submit information required to comply with requirements listed on your authority.`
        },
    },
}
</script>
