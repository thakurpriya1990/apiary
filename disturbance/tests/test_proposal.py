from disturbance.settings import HTTP_HOST_FOR_TEST
from disturbance.tests.test_setup import APITestSetup


class ProposalTests(APITestSetup):
    def test_create_proposal_apiary(self):
        print("test_create_proposal_apiary")
        self.client.login(email=self.customer, password='pass')
        self.client.enforce_csrf_checks=True
        create_response = self.client.post(
            '/api/proposal/',
            self.create_proposal_data,
            format='json',
            HTTP_HOST=HTTP_HOST_FOR_TEST,
        )

        self.assertEqual(create_response.status_code, 200)
        self.assertTrue(create_response.data.get('id') > 0)

