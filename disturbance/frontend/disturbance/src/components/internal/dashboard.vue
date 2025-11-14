<template>
<div class="container" id="internalDash">
    <ProposalDashTable level="internal" :url="proposals_url"/>
    <ReferralDashTable :url="referrals_url"/>
</div>
</template>
<script>
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
            //proposals_url: api_endpoints.proposals,
            //proposals_url: api_endpoints.proposals_paginated_internal,
            //proposals_url: '/api/list_proposal/?format=datatables',
            //proposals_url: api_endpoints.list_proposals,
            proposals_url: api_endpoints.proposals_paginated_internal,
            referrals_url: api_endpoints.referrals_paginated_internal,
        }
    
    },
    components: {
        ProposalDashTable,
        ReferralDashTable
    },
    computed: {
    },
    methods: {},
    mounted: function () {
    }
}
</script>
