<template>
<div class="container" id="internalDash">
    <div class="row">
        <div class="col-sm-12">
            <FormSection :form-collapse="false" label="Applications" Index="proposals">
                <ProposalDashTable level="internal" :url="proposals_url"/>
            </FormSection>
            <FormSection :form-collapse="false" label="Applications referred to me" Index="referrals">
                <ReferralDashTable :url="referrals_url"/>
            </FormSection>
        </div>
    </div>
</div>
</template>
<script>
import FormSection from '@/components/forms/section_toggle.vue';
import ProposalDashTable from '@common-utils/proposals_dashboard.vue'
import ReferralDashTable from '@common-utils/referrals_dashboard.vue'
import {
  api_endpoints,
}
from '@/utils/hooks'
export default {
    name: 'InternalDashboard',
    data() {
        return {
            proposals_url: api_endpoints.proposals_paginated_internal,
            referrals_url: api_endpoints.referrals_paginated_internal,
        }
    
    },
    components: {
        ProposalDashTable,
        ReferralDashTable,
        FormSection,
    },
    computed: {
    },
    methods: {},
    mounted: function () {
    }
}
</script>
