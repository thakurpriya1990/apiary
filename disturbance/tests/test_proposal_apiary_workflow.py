from disturbance.settings import HTTP_HOST_FOR_TEST
from disturbance.tests.test_setup import APITestSetup
import json
from disturbance.components.proposals.models import (
        Proposal,
        ApiarySite,
        ProposalStandardRequirement,
        )
from disturbance.management.commands.update_compliance_status import Command


class ApiaryIntegrationTests(APITestSetup):
    def test_proposal_apiary_workflow(self):
        print("test_proposal_apiary_workflow")
        self.client.login(email=self.customer, password='pass')
        self.client.enforce_csrf_checks=True
        # create proposal
        create_response = self.client.post(
                '/api/proposal/', 
                self.create_proposal_data,
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        proposal_id = create_response.data.get('id')
        # get proposal
        url = 'http://localhost:8071/api/proposal_apiary/{}.json'.format(proposal_id)
        get_response = self.client.get(url, HTTP_HOST=HTTP_HOST_FOR_TEST,)

        self.assertEqual(get_response.status_code, 200)
        #######################
        proposal = Proposal.objects.get(id=proposal_id)
        draft_schema = {
            "proposal_apiary": {
                "id": proposal_id,
                "title": "test_title",
                "applicant_checklist_answers": [
                        {
                        "id": proposal.proposal_apiary.apiary_checklist.order_by('id')[0].id,
                        "answer": True
                        },
                        {
                        "id": proposal.proposal_apiary.apiary_checklist.order_by('id')[1].id,
                        "answer": False
                        },
                        {
                        "id": proposal.proposal_apiary.apiary_checklist.order_by('id')[2].id,
                        "answer": True
                        },
                    ]
                }
            }

        draft_proposal_data = {
                "schema": json.dumps(draft_schema),
                "all_the_features": self.all_the_features_1
                }
        draft_response = self.client.post(
                '/api/proposal/{}/draft/'.format(proposal_id),
                draft_proposal_data, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        self.assertEqual(draft_response.status_code, 302)

        # Simulate Proposal submission by changing status instead of going through the payment gateway
        saved_proposal = Proposal.objects.get(id=proposal_id)
        saved_proposal.processing_status = 'with_assessor'
        saved_proposal.customer_status = 'with_assessor'
        saved_proposal.save()
        #  bb 20201109 must run this after (fake) payment
        saved_proposal.proposal_apiary.post_payment_success()

        # referrals testing goes here

        # Move status to 'With Assessor (Requirements)
        saved_proposal.processing_status = 'with_assessor_requirements'
        saved_proposal.save()

        # login as internal 
        self.client.login(email=self.adminUser, password='pass')
        self.client.enforce_csrf_checks=True

        # add requirements
        proposal_standard_req_r1_id = ProposalStandardRequirement.objects.get(code='R1').id
        add_requirements_data_1 = {
                "due_date": self.today_plus_1_week_str,
                "standard": True,
                "recurrence": True,
                "recurrence_pattern": "1",
                "proposal": proposal_id,
                "standard_requirement": str(proposal_standard_req_r1_id),
                "recurrence_schedule": "1",
                "free_requirement": ""
                }
        add_requirements_response_1 = self.client.post(
                '/api/proposal_requirements.json', 
                add_requirements_data_1, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        self.assertEqual(add_requirements_response_1.status_code, 201)

        proposal_standard_req_a1_id = ProposalStandardRequirement.objects.get(code='A1').id
        add_requirements_data_2 = {
                "due_date": self.today_plus_1_week_str,
                "standard": True,
                "recurrence": False,
                "recurrence_pattern": "1",
                "proposal": proposal_id,
                "standard_requirement": str(proposal_standard_req_a1_id),
                #"recurrence_schedule": "1",
                "free_requirement": ""
                }
        add_requirements_response_2 = self.client.post(
                '/api/proposal_requirements.json', 
                add_requirements_data_2, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        self.assertEqual(add_requirements_response_2.status_code, 201)

        # Propose to approve
        apiary_sites = []
        for site in saved_proposal.proposal_apiary.apiary_sites.all():
            apiary_sites.append({
                "id": site.id,
                "checked": True
                })
        propose_to_approve_data = {
                "details": "test details",
                "expiry_date": self.today_plus_26_weeks_str,
                "start_date": self.today_str,
                "apiary_sites": apiary_sites
                }
        print(propose_to_approve_data)
        propose_to_approve_response = self.client.post(
                '/api/proposal/{}/proposed_approval/'.format(proposal_id), 
                propose_to_approve_data, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )

        self.assertEqual(propose_to_approve_response.status_code, 200)

        # Final approval with unchanged data
        final_approval_data = propose_to_approve_data
        final_approval_response = self.client.post(
                '/api/proposal_apiary/{}/final_approval/'.format(proposal_id), 
                final_approval_data, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        self.assertEqual(final_approval_response.status_code, 200)
        #proposal_1 = Proposal.objects.get(id=proposal_id)
        #import ipdb; ipdb.set_trace()

        print("new apiary proposal for same licence")
        self.client.login(email=self.customer, password='pass')
        self.client.enforce_csrf_checks=True
        # create proposal
        create_response_2 = self.client.post(
                '/api/proposal/', 
                self.create_proposal_data,
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        proposal_id_2 = create_response_2.data.get('id')
        # get proposal
        url = 'http://localhost:8071/api/proposal_apiary/{}.json'.format(proposal_id_2)
        get_response_2 = self.client.get(url, HTTP_HOST = HTTP_HOST_FOR_TEST,)

        self.assertEqual(get_response_2.status_code, 200)
        #######################
        proposal_2 = Proposal.objects.get(id=proposal_id_2)
        draft_schema_2 = {
            "proposal_apiary": {
                "id": proposal_id_2,
                "title": "test_title",
                "applicant_checklist_answers": [
                        {
                        "id": proposal_2.proposal_apiary.apiary_checklist.order_by('id')[0].id,
                        "answer": True
                        },
                        {
                        "id": proposal_2.proposal_apiary.apiary_checklist.order_by('id')[1].id,
                        "answer": False
                        },
                        {
                        "id": proposal_2.proposal_apiary.apiary_checklist.order_by('id')[2].id,
                        "answer": True
                        },
                    ]
                }
            }

        draft_proposal_data_2 = {
                "schema": json.dumps(draft_schema_2),
                "all_the_features": self.all_the_features_2
                }
        draft_response_2 = self.client.post(
                '/api/proposal/{}/draft/'.format(proposal_id_2),
                draft_proposal_data_2, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        self.assertEqual(draft_response_2.status_code, 302)

        # Simulate Proposal submission by changing status instead of going through the payment gateway
        saved_proposal_2 = Proposal.objects.get(id=proposal_id_2)
        saved_proposal_2.processing_status = 'with_assessor'
        saved_proposal_2.customer_status = 'with_assessor'
        saved_proposal_2.save()
        #  bb 20201109 must run this after (fake) payment
        saved_proposal_2.proposal_apiary.post_payment_success()

        # referrals testing goes here

        # Move status to 'With Assessor (Requirements)
        saved_proposal_2.processing_status = 'with_assessor_requirements'
        saved_proposal_2.save()

        # login as internal 
        self.client.login(email=self.adminUser, password='pass')
        self.client.enforce_csrf_checks=True

        # add requirements
        proposal_standard_req_r2_id = ProposalStandardRequirement.objects.get(code='R2').id
        add_requirements_data_3 = {
                "due_date": self.today_plus_1_week_str,
                "standard": True,
                "recurrence": True,
                "recurrence_pattern": "1",
                "proposal": proposal_id_2,
                "apiary_approval": Proposal.objects.get(id=proposal_id).approval.id,
                "standard_requirement": str(proposal_standard_req_r2_id),
                "recurrence_schedule": "1",
                "free_requirement": ""
                }
        add_requirements_response_3 = self.client.post(
                '/api/proposal_requirements.json', 
                add_requirements_data_3, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        self.assertEqual(add_requirements_response_3.status_code, 201)

        proposal_standard_req_a2_id = ProposalStandardRequirement.objects.get(code='A2').id
        add_requirements_data_4 = {
                "due_date": self.today_plus_1_week_str,
                "standard": True,
                "recurrence": False,
                "recurrence_pattern": "1",
                "proposal": proposal_id_2,
                "apiary_approval": Proposal.objects.get(id=proposal_id).approval.id,
                "standard_requirement": str(proposal_standard_req_a2_id),
                #"recurrence_schedule": "1",
                "free_requirement": ""
                }
        add_requirements_response_4 = self.client.post(
                '/api/proposal_requirements.json', 
                add_requirements_data_4, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        #proposal_requirement_4_id = add_requirements_response_4.data.get('id')
        self.assertEqual(add_requirements_response_4.status_code, 201)

        ## delete requirement
        #import ipdb; ipdb.set_trace()
        requirement_to_delete_id = Proposal.objects.get(id=proposal_id_2).requirements.filter(standard_requirement__code="A1")[0].id
        delete_requirement_response_2 = self.client.get(
                '/api/proposal_requirements/{}/discard.json'.format(requirement_to_delete_id),
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        self.assertEqual(delete_requirement_response_2.status_code, 200)

        # Propose to approve
        apiary_sites_2 = []
        for site in saved_proposal_2.proposal_apiary.apiary_sites.all():
            apiary_sites_2.append({
                "id": site.id,
                "checked": True
                })
        propose_to_approve_data_2 = {
                "details": "test details",
                "apiary_sites": apiary_sites_2
                }
        print(propose_to_approve_data_2)
        propose_to_approve_response_2 = self.client.post(
                '/api/proposal/{}/proposed_approval/'.format(proposal_id_2), 
                propose_to_approve_data_2, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )

        self.assertEqual(propose_to_approve_response_2.status_code, 200)

        # Final approval with unchanged data
        final_approval_data_2 = propose_to_approve_data_2
        final_approval_response_2 = self.client.post(
                '/api/proposal_apiary/{}/final_approval/'.format(proposal_id_2), 
                final_approval_data_2, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        self.assertEqual(final_approval_response_2.status_code, 200)


        # Show properties of newly created approval
        final_proposal = Proposal.objects.get(id=proposal_id_2)
        final_proposal_proposal_apiary_id = final_proposal.proposal_apiary.id
        print(Proposal.objects.get(id=proposal_id).approval.apiary_approval)
        print(Proposal.objects.get(id=proposal_id).processing_status)
        print("APPROVAL SITES")
        for approval_site in final_proposal.approval.get_current_apiary_sites:
            print(approval_site)
        #for approval_site in ApiarySite.objects.filter(approval=final_proposal.approval):
            #print(approval_site)
        # Compliance creation test
        approval_standard_requirements = []
        for compliance in final_proposal.approval.compliances.all():
            approval_standard_requirements.append(compliance.requirement.standard_requirement_id)
        self.assertIn(proposal_standard_req_r1_id, approval_standard_requirements)
        # This requirement is deleted earlier
        self.assertNotIn(proposal_standard_req_a1_id, approval_standard_requirements)
        self.assertIn(proposal_standard_req_r2_id, approval_standard_requirements)
        self.assertIn(proposal_standard_req_a2_id, approval_standard_requirements)

        # check Reversion endpoint
        url = '/api/proposal_apiary/{}/proposal_history/'.format(final_proposal_proposal_apiary_id)
        reversion_response = self.client.get(url, HTTP_HOST = HTTP_HOST_FOR_TEST,)
        self.assertEqual(reversion_response.status_code, 200)

        # Update newly created Compliance status values
        cron_job = Command()
        cron_job.handle()
        # Compliance with standard_requirement code "A2" should now have status "due"
        compliance_a2 = Proposal.objects.get(id=proposal_id_2).approval.compliances.filter(requirement__standard_requirement__code="A2")[0]
        self.assertEqual(compliance_a2.processing_status, "due")

        # Reissue approval with new expiry date
        reissue_payload = {"status": "with_approver"}
        #url = '/api/proposal_apiary/{}/reissue_approval.json'.format(final_proposal_proposal_apiary_id)
        #import ipdb; ipdb.set_trace()
        reissue_response = self.client.post(
                '/api/proposal/{}/reissue_approval/'.format(final_proposal.id),
                reissue_payload,
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        self.assertEqual(reissue_response.status_code, 200)

        reissue_final_approval_data = {
                "details": "reissued details",
                "expiry_date": self.today_plus_1_week_str,
                "start_date": self.today_str,
                "apiary_sites": apiary_sites_2
                }
        #import ipdb; ipdb.set_trace()
        reissue_final_approval_response = self.client.post(
                '/api/proposal_apiary/{}/final_approval/'.format(final_proposal.id),
                #final_approval_data, 
                reissue_final_approval_data,
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        self.assertEqual(reissue_final_approval_response.status_code, 200)

        # Renew approval
        renewal_response = self.client.get('/api/proposal/{}/renew_approval/'.format(final_proposal.id), HTTP_HOST = HTTP_HOST_FOR_TEST,)
        self.assertEqual(renewal_response.status_code, 200)

