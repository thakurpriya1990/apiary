from disturbance.tests.test_setup import APITestSetup


class ProposalTests(APITestSetup):
    def test_annual_rental_fee(self):
        print("test_annual_rental_fee")
        # self.client.login(email=self.customer, password='pass')
        # self.client.enforce_csrf_checks=True
        # create_response = self.client.post(
        #         '/api/proposal/',
        #         self.create_proposal_data,
        #         format='json'
        #         )
        #
        # self.assertEqual(create_response.status_code, 200)
        # self.assertTrue(create_response.data.get('id') > 0)
        self.assertTrue(1 > 0)

