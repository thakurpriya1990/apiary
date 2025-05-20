from disturbance.settings import HTTP_HOST_FOR_TEST
from disturbance.tests.test_setup import APITestSetup
import json
from disturbance.components.proposals.models import (
        Proposal,
        ApiarySite,
        ProposalStandardRequirement,
        )
from disturbance.components.approvals.models import ApiarySiteOnApproval
from disturbance.management.commands.update_compliance_status import Command


class ApiarySiteTransferIntegrationTests(APITestSetup):
    def test_proposal_apiary_site_transfer_workflow(self):
        print("test_proposal_apiary_site_transfer_workflow")
        self.client.login(email=self.customer1, password='pass')
        self.client.enforce_csrf_checks=True
        # create proposal
        create_response_1 = self.client.post(
                '/api/proposal/', 
                self.create_proposal_data_customer1,
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                #content_type='application/json'
                )
        proposal_id_1 = create_response_1.data.get('id')
        # save draft proposal
        proposal_1 = Proposal.objects.get(id=proposal_id_1)
        draft_schema_1 = {
            "proposal_apiary": {
                "id": proposal_id_1,
                "title": "test_title",
                "applicant_checklist_answers": [
                        {
                        "id": proposal_1.proposal_apiary.apiary_checklist.order_by('id')[0].id,
                        "answer": True
                        },
                        {
                        "id": proposal_1.proposal_apiary.apiary_checklist.order_by('id')[1].id,
                        "answer": False
                        },
                        {
                        "id": proposal_1.proposal_apiary.apiary_checklist.order_by('id')[2].id,
                        "answer": True
                        },
                    ]
                }
            }

        draft_proposal_data_1 = {
                "schema": json.dumps(draft_schema_1),
                "all_the_features": self.all_the_features_1
                }
        draft_response_1 = self.client.post(
                '/api/proposal/{}/draft/'.format(proposal_id_1),
                draft_proposal_data_1, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        self.assertEqual(draft_response_1.status_code, 302)
        # Simulate Proposal submission by changing status instead of going through the payment gateway
        saved_proposal_1 = Proposal.objects.get(id=proposal_id_1)
        saved_proposal_1.processing_status = 'with_assessor'
        saved_proposal_1.customer_status = 'with_assessor'
        saved_proposal_1.save()
        #  bb 20201109 must run this after (fake) payment
        saved_proposal_1.proposal_apiary.post_payment_success()

        # Move status to 'With Assessor (Requirements)
        saved_proposal_1.processing_status = 'with_assessor_requirements'
        saved_proposal_1.save()

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
                "proposal": proposal_id_1,
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
                "proposal": proposal_id_1,
                "standard_requirement": str(proposal_standard_req_a1_id),
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
        apiary_sites_1 = []
        for site_1 in saved_proposal_1.proposal_apiary.apiary_sites.all():
            apiary_sites_1.append({
                "id": site_1.id,
                "checked": True
                })
        propose_to_approve_data_1 = {
                "details": "test details 1",
                "expiry_date": self.today_plus_26_weeks_str,
                "start_date": self.today_str,
                "apiary_sites": apiary_sites_1
                }
        print("propose_to_approve_data_1")
        print(propose_to_approve_data_1)
        propose_to_approve_response_1 = self.client.post(
                '/api/proposal/{}/proposed_approval/'.format(proposal_id_1), 
                propose_to_approve_data_1, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )

        self.assertEqual(propose_to_approve_response_1.status_code, 200)

        # Final approval with unchanged data
        final_approval_data_1 = propose_to_approve_data_1
        final_approval_response_1 = self.client.post(
                '/api/proposal_apiary/{}/final_approval/'.format(proposal_id_1), 
                final_approval_data_1, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )

        self.assertEqual(final_approval_response_1.status_code, 200)

        # Show properties of newly created approval
        proposal_1_obj = Proposal.objects.get(id=proposal_id_1)
        print("proposal_1_obj.id")
        print(proposal_1_obj.id)
        print(proposal_1_obj.approval)
        customer1_approval = proposal_1_obj.approval
        print(proposal_1_obj.approval.apiary_approval)
        print(proposal_1_obj.processing_status)
        for site_1_output in proposal_1_obj.proposal_apiary.apiary_sites.all():
            print(site_1_output)
        #print("APPROVAL SITES")
        #for approval_site in ApiarySite.objects.filter(approval=customer1_approval):
         #   print(approval_site)

        #######################################################
        self.client.login(email=self.customer2, password='pass')
        self.client.enforce_csrf_checks=True
        # create proposal
        create_response_2 = self.client.post(
                '/api/proposal/', 
                self.create_proposal_data_customer2,
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        proposal_id_2 = create_response_2.data.get('id')
        # save draft proposal
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
        self.assertEqual(add_requirements_response_4.status_code, 201)


        # Propose to approve
        apiary_sites_2 = []
        for site_2 in saved_proposal_2.proposal_apiary.apiary_sites.all():
            apiary_sites_2.append({
                "id": site_2.id,
                "checked": True
                })
        propose_to_approve_data_2 = {
                "details": "test details 2",
                "expiry_date": self.today_plus_26_weeks_str,
                "start_date": self.today_str,
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
        proposal_2_obj = Proposal.objects.get(id=proposal_id_2)
        print("proposal_2_obj.id")
        print(proposal_2_obj.id)
        print(proposal_2_obj.approval)
        customer2_approval = proposal_2_obj.approval
        print(proposal_2_obj.approval.apiary_approval)
        print(proposal_2_obj.processing_status)
        for site_2_output in proposal_2_obj.proposal_apiary.apiary_sites.all():
            print(site_2_output)
        #print("APPROVAL SITES")
        #for approval_site in ApiarySite.objects.filter(approval=customer2_approval):
         #   print(approval_site)
        ####################################################

        ## Start Site Transfer proposal
        print("Site transfer proposal")
        self.client.login(email=self.customer1, password='pass')
        self.client.enforce_csrf_checks=True
        # create proposal
        self.create_site_transfer_proposal_data['originating_approval_id'] = proposal_1_obj.approval.id
        create_response_site_transfer = self.client.post(
                '/api/proposal/',
                self.create_site_transfer_proposal_data,
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        print("create_response_site_transfer.status_code")
        print(create_response_site_transfer.status_code)
        site_transfer_proposal_id = create_response_site_transfer.data.get('id')
        # save draft proposal
        site_transfer_proposal = Proposal.objects.get(id=site_transfer_proposal_id)
        draft_schema_site_transfer = {
            "proposal_apiary": {
                "id": site_transfer_proposal_id,
                #"selected_licence": proposal_2_obj.approval.id,
                "title": "test_title",
                "applicant_checklist_answers": [
                        {
                        "id": site_transfer_proposal.proposal_apiary.apiary_checklist.order_by('id')[0].id,
                        "answer": True
                        },
                        {
                        "id": site_transfer_proposal.proposal_apiary.apiary_checklist.order_by('id')[1].id,
                        "answer": False
                        },
                        {
                        "id": site_transfer_proposal.proposal_apiary.apiary_checklist.order_by('id')[2].id,
                        "answer": True
                        },
                    ]
                }
            }
        #import ipdb; ipdb.set_trace()
        #selected_licence_holder_str = '{{"licence_holder":{0},"type":"individual","id":{1},"lodgement_number":{2}}}'.format(
        #        self.customer2.email, proposal_2_obj.approval.id, proposal_2_obj.approval.lodgement_number)
        selected_licence_holder_dict = {
            "licence_holder": self.customer2.email,
            "type":"individual",
            "id": proposal_2_obj.approval.id,
            "lodgement_number": proposal_2_obj.approval.lodgement_number,
            "transferee_id": self.customer2.id,
        }
        draft_site_transfer_proposal_data = {
                "schema": json.dumps(draft_schema_site_transfer),
                "apiary_sites_local": json.dumps([{
                    #"id": ApiarySite.objects.filter(approval=customer1_approval)[1].id,
                    "id": ApiarySiteOnApproval.objects.filter(approval=customer1_approval)[1].id,
                    "checked": True,
                    },
                    ]),
                "selected_licence_holder": json.dumps(selected_licence_holder_dict),
                "transferee_email_text": self.customer2.email,
                }
        draft_response_site_transfer = self.client.post(
                '/api/proposal/{}/draft/'.format(site_transfer_proposal_id),
                draft_site_transfer_proposal_data, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )
        self.assertEqual(draft_response_2.status_code, 302)
        # Simulate Proposal submission by changing status instead of going through the payment gateway
        saved_site_transfer_proposal = Proposal.objects.get(id=site_transfer_proposal_id)
        saved_site_transfer_proposal.processing_status = 'with_assessor'
        saved_site_transfer_proposal.customer_status = 'with_assessor'
        saved_site_transfer_proposal.save()

        # Move status to 'With Assessor (Requirements)
        saved_site_transfer_proposal.processing_status = 'with_assessor_requirements'
        saved_site_transfer_proposal.save()

        # login as internal 
        self.client.login(email=self.adminUser, password='pass')
        self.client.enforce_csrf_checks=True

        # Propose to approve
        site_transfer_apiary_sites = []
        for site_transfer_site in saved_site_transfer_proposal.proposal_apiary.site_transfer_apiary_sites.all():
            site_transfer_apiary_sites.append({
                "id": site_transfer_site.apiary_site_on_approval.id,
                "checked": True
                })
        site_transfer_propose_to_approve_data = {
                "details": "site transfer test details",
                "apiary_sites": site_transfer_apiary_sites
                }
        print(site_transfer_propose_to_approve_data)
        site_transfer_propose_to_approve_response = self.client.post(
                '/api/proposal/{}/proposed_approval/'.format(site_transfer_proposal_id),
                site_transfer_propose_to_approve_data,
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )

        self.assertEqual(site_transfer_propose_to_approve_response.status_code, 200)

        # Final approval with unchanged data
        site_transfer_final_approval_data = site_transfer_propose_to_approve_data
        site_transfer_final_approval_response = self.client.post(
                '/api/proposal_apiary/{}/final_approval/'.format(site_transfer_proposal_id),
                site_transfer_final_approval_data,
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
                )

        self.assertEqual(site_transfer_final_approval_response.status_code, 200)

        # Show properties of updated approvals
        proposal_1_obj = Proposal.objects.get(id=proposal_id_1)
        print(proposal_1_obj.approval.apiary_approval)
        print(proposal_1_obj.processing_status)
        for site_1_output in proposal_1_obj.proposal_apiary.apiary_sites.all():
            print(site_1_output)
        print("APPROVAL SITES customer 1")
        for approval_site in customer1_approval.get_current_apiary_sites:
            print(approval_site)
        print(customer1_approval.current_proposal)
        print(customer1_approval.current_proposal.application_type.name)

        self.assertEqual(len(customer1_approval.get_current_apiary_sites), 2)

        proposal_2_obj = Proposal.objects.get(id=proposal_id_2)
        print(proposal_2_obj.approval.apiary_approval)
        print(proposal_2_obj.processing_status)
        for site_2_output in proposal_2_obj.proposal_apiary.apiary_sites.all():
            print(site_2_output)
        print("APPROVAL SITES customer 2")
        for approval_site in customer2_approval.get_current_apiary_sites:
            print(approval_site)
        print(customer2_approval.current_proposal)
        print(customer2_approval.current_proposal.application_type.name)

        self.assertEqual(len(customer2_approval.get_current_apiary_sites), 3)

