<template>
<div class="container" id="schema-manager">
    <div class="col-md-12">

    <SchemaTabs :tabs="tabs" :initialTab="initialTab">

        <template slot="tab-panel-question"><SchemaQuestion /></template>
        <template slot="tab-panel-masterlist"><SchemaMasterlist /></template>
        <template slot="tab-panel-proposal-type"><SchemaProposalType /></template>
        <!-- <template slot="tab-panel-group"><SchemaGroup /></template> -->

    </SchemaTabs>

    </div>
</div>
</template>
<script>
import SchemaTabs from '@/components/forms/tab.vue'
import SchemaQuestion from '@/components/internal/main/schema_question.vue'
import SchemaMasterlist from '@/components/internal/main/schema_masterlist.vue'
import SchemaProposalType from '@/components/internal/main/schema_proposal_type.vue'
// import SchemaGroup from '@/components/internal/main/schema_group.vue'

export default {
    name: 'schema-manager',
    components: {
        SchemaTabs,
        SchemaQuestion,
        SchemaMasterlist,
        SchemaProposalType,
        // SchemaGroup,
    },
    data() {
        return {
            initialTab: 'masterlist',
            tabs: [
                {'masterlist': 'Schema Masterlist'},
                {'proposal-type': 'Proposal Type Sections'},
                // {'group': 'Section Groups'},
                {'question': 'Section Questions'},
            ],
        }
    },
}
</script>
