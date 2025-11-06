import Vue from 'vue'
import Router from 'vue-router'
import LedgerPay from '@/components/ledgerpay'
import Profile from '@/components/user/profile.vue'
import external_routes from '@/components/external/routes'
import internal_routes from '@/components/internal/routes'
import ManageOrganisation from '@/components/external/organisations/manage.vue'
import Organisations from '@/components/user/manage_organisation.vue'
Vue.use(Router)

export default new Router({
    mode: 'history',
    routes: [
        {
          path: '/firsttime',
          name: 'first-time',
          component: Profile
        },
        {
          path: '/account',
          name: 'account',
          component: Profile

        },
        {
          path: '/ledgerpay/:payment_item',
          name: 'ledgerpay',
          component: LedgerPay
        },
        {
          path: '/ledger-ui/accounts',
          name: 'organisation',
          component: Organisations
        },
        {
          path: '/ledger-ui/organisation/:org_id',
          name: 'manage_organisation',
          component: ManageOrganisation
        },
        external_routes,
        internal_routes,
    ]
})
