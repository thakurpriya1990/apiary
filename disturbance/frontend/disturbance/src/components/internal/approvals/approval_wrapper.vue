<template>
<div class="container">
    <div v-if="approvalId">
        <div v-if="apiaryApproval">
            <ApiaryApproval :approvalId="approvalId"/>
        </div>
    </div>

</div>
</template>
<script>

import ApiaryApproval from './apiary_approval.vue';
import {
//   api_endpoints,
//   helpers
}
from '@/utils/hooks'
export default {
    name: 'ApprovalWrapper',
    data() {
        return {
            approvalId: null,
            apiaryApproval: false,
        }
    },
    components:{
        ApiaryApproval,
    },
    computed: {
    },
    methods: {
    },
    mounted: function () {
    },
    beforeRouteEnter: function(to, from, next) {
          fetch(`/api/approvals/${to.params.approval_id}/approval_wrapper.json`).then(
            async (res) => {
                if (!res.ok) { return res.json().then(err => { throw err }); }
                let data = await res.json();
                next(vm => {
                  vm.approvalId = data.id;
                  vm.apiaryApproval = data.apiary_approval;
                });
            }).catch(err => {
              console.log(err);
            });
    },
}
</script>
