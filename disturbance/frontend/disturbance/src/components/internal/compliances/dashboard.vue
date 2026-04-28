<template>
<div class="container" id="internalDash">
    <div class="row">
        <div class="col-sm-12">
            <FormSection :form-collapse="false" label="Compliances with requirements" Index="compliances">
                <ComplianceDashTable level="internal" :url="compliances_url"/>
            </FormSection>
        </div>
    </div>
</div>
</template>
<script>
import ComplianceDashTable from '@common-utils/compliances_dashboard.vue'
import {
  api_endpoints,
//   helpers
}
from '@/utils/hooks'
import FormSection from '@/components/forms/section_toggle.vue';
export default {
    name: 'InternalCompliancesDashboard',
    data() {
        return {
            compliances_url: api_endpoints.compliances_paginated_external,
        }
    
    },
    components: {
        ComplianceDashTable,
        FormSection
    },
    computed: {
    },
    methods: {},
    mounted: function () {
    }
}
</script>
