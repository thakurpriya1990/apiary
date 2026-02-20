<template>
<div class="container">
    <div v-if="proposalId">
        <div v-if="apiaryGroupApplication">
            <ProposalApiary :proposalId="proposalId"/>
        </div>
        <div v-else-if="temporaryUseApplication">
            <ProposalTemporaryUse :proposalId="proposalId" />
        </div>
        <div v-else>
            <Proposal :proposalId="proposalId"/>
        </div>
    </div>
</div>
</template>
<script>


import ProposalApiary from './proposal_apiary.vue';
import ProposalTemporaryUse from '@/components/internal/proposals/proposal_temporary_use.vue'
import Proposal from './proposal.vue';

export default {
    name: 'InternalProposalWrapper',
    data() {
        return {
            proposalId: null,
            applicationTypeName: '',
        }
    },
    components:{
        Proposal,
        ProposalApiary,
        ProposalTemporaryUse,
    },
    computed: {
        apiaryGroupApplication: function() {
            let retVal = false;
            if (['Apiary', 'Site Transfer'].includes(this.applicationTypeName)) {
                retVal = true;
            }
            return retVal;
        },
        temporaryUseApplication: function() {
            let retVal = false;
            if (this.applicationTypeName === 'Temporary Use'){
                retVal = true;
            }
            return retVal;
        },
    },
    beforeRouteEnter: function(to, from, next) {
        fetch(`/api/proposal/${to.params.proposal_id}/internal_proposal_wrapper.json`)
        .then(async res => {
            if (!res.ok) { return res.json().then(err => { throw err }); }
            const data = await res.json();
            next(vm => {
                vm.proposalId = data.id;
                vm.applicationTypeName = data.application_type_name;
            });
        }).catch(err => {
            console.log(err);
        });
    },
}
</script>
