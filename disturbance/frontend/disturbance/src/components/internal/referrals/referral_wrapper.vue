<template>
<!--div class="container" id="referralWrapper"-->
<div class="container">
       <!--ApplicationDashTable level='external' :url='applications_url'/>
    <div>
        <LicenceDashTable level='external' :url='licences_url'/>
        <ReturnDashTable level='external' :url='returns_url'/>
    </div-->
    <div v-if="referralId">
        <div v-if="apiaryReferral">
            <ApiaryReferral :referralId="referralId"/>
        </div>
        <div v-else>
            <Referral :referralId="referralId"/>
        </div>
    </div>

</div>
</template>
<script>

/*import datatable from '@/utils/vue/datatable.vue'
import ApplicationDashTable from '@common-components/applications_dashboard.vue'
import LicenceDashTable from '@common-components/licences_dashboard.vue'
import ReturnDashTable from '@common-components/returns_dashboard.vue'
*/
import Referral from './referral.vue';
import ApiaryReferral from './apiary_referral.vue';
export default {
    name: 'ReferralWrapper',
    data() {
        let vm = this;
        return {
            referralId: null,
            apiaryReferral: false,
        }
    },
    components:{
        /*
        ApplicationDashTable,
        LicenceDashTable,
        ReturnDashTable,
        */
        Referral,
        ApiaryReferral
    },
    watch: {},
    computed: {
        /*
        apiaryReferral: function() {
            let returnVal = false;
            if (this.referral && this.referral.apiary_referral && this.referral.apiary_referral.id) {
                returnVal = true;
            }
            return returnVal;
        },
        referralId: function() {
            let retVal = false;
            if (this.referral && this.referral.id) {
                retVal = true;
            }
            return retVal;
        },
        */
    },
    methods: {
    },
    mounted: function () {
    },
    beforeRouteEnter: function(to, from, next) {
          Vue.http.get(`/api/referrals/${to.params.referral_id}/referral_wrapper.json`).then(res => {
          //Vue.http.get(helpers.add_endpoint_json(api_endpoints.referrals,to.params.referral_id)).then(res => {
              next(vm => {
                  vm.referralId = res.body.id;
                  vm.apiaryReferral = res.body.apiary_referral_exists;
              });
            },
            err => {
              console.log(err);
            });
    },

}
</script>
