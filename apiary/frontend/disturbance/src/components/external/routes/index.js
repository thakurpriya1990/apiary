import ExternalDashboard from '../dashboard.vue'
//import Proposal from '../proposal_external.vue'
import Proposal from '../proposal_wrapper.vue'
import ProposalApply from '../proposal_apply.vue'
import ProposalSubmit from '../proposal_submit.vue'
import Organisation from '../organisations/manage.vue'
import Compliance from '../compliances/access.vue'
import ComplianceSubmit from '../compliances/submit.vue'
//import Approval from '../approvals/approval.vue'
import Approval from '../approvals/approval_wrapper.vue'
//import AvailableSites from '../available_sites.vue'
import AvailableSites from '@/components/common/apiary/available_sites.vue'

export default
{
    path: '/external',
    component:
    {
        render(c)
        {
            return c('router-view')
        }
    },
    children: [
        {
            path: '/',
            component: ExternalDashboard,
            name: 'external-proposals-dash'
        },
        {
            path: 'organisations/manage/:org_id',
            component: Organisation
        },
        {
            path: 'compliance/:compliance_id',
            component: Compliance
        },
        {
            path: 'compliance/submit',
            component: ComplianceSubmit,
            name:"submit_compliance"
        },
        {
            path: 'sites',
            component: AvailableSites,
            name: 'sites',
            props: { is_external: true }
        },
        {
            path: 'approval/:approval_id',
            component: Approval,
            name: "external-approval"
        },
        {
            path: 'proposal',
            component:
            {
                render(c)
                {
                    return c('router-view')
                }
            },
            children: [
                {
                    path: '/',
                    component: ProposalApply,
                    name:"apply_proposal"
                },
                {
                    path: 'submit',
                    component: ProposalSubmit,
                    name:"submit_proposal"
                },
                {
                    path: ':proposal_id',
                    component: Proposal,
                    name:"draft_proposal"
                },
            ]
        },
    ]
}
