"""
This is an file contains tests for the visualization cors API
"""

import requests
import pytest
from constants import VISUALIZATION_ORIGIN_URL, VISUALIZATION_API_URL
from constants import DISABLE_VISUALIZATION_SETTING, ENABLE_VISUALIZATION_SETTING
from framework import GrenMapTestingFramework

ALLOW_ORIGIN = 'https://grenmap-sp.myisp.com:8443'


class TestVisualizationCORS(GrenMapTestingFramework):

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestVisualizationCORS)
        cls.allow_origin_name_list = []

    @pytest.fixture(autouse=True)
    def before_each(self):
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')

    def test_cors_connection_with_valid_origin(self):
        """
        Test the cors connection with a valid origin
        """
        self.put(
            url=DISABLE_VISUALIZATION_SETTING,
            expected_status_code=requests.codes.ok
        )
        test_origin = {
            'name': 'test',
            'origin': ALLOW_ORIGIN,
            'active': 'True',
        }
        self.post(url=VISUALIZATION_ORIGIN_URL, data=test_origin)
        test_header = {'origin': ALLOW_ORIGIN}
        response = requests.get(
            url=VISUALIZATION_API_URL,
            headers=test_header,
            verify=False,
        )
        assert response.status_code == requests.codes.ok, \
            'Expected connect to the correct allow origin'

    def test_cors_connection_with_invalid_origin(self):
        """
        Test the cors connection with an invalid origin
        """
        self.put(
            url=ENABLE_VISUALIZATION_SETTING,
            expected_status_code=requests.codes.ok
        )
        test_origin = {
            'name': 'test',
            'origin': ALLOW_ORIGIN,
            'active': 'True',
        }
        self.post(url=VISUALIZATION_ORIGIN_URL, data=test_origin)
        test_header = {'origin': 'http://www.example.com'}

        response = requests.get(
            url=VISUALIZATION_API_URL,
            headers=test_header,
            verify=False,
        )
        assert response.status_code == requests.codes.unauthorized, \
            'Expected fail with incorrect visualization origin'

    def test_cors_connection_with_inactive_origin(self):
        """
        Test the cors connection with an inactive origin
        """
        self.put(
            url=ENABLE_VISUALIZATION_SETTING,
            expected_status_code=requests.codes.ok
        )
        test_origin = {
            'name': 'test',
            'origin': ALLOW_ORIGIN,
            'active': '',
        }
        self.post(url=VISUALIZATION_ORIGIN_URL, data=test_origin)
        test_header = {'origin': ALLOW_ORIGIN}

        response = requests.get(
            url=VISUALIZATION_API_URL,
            headers=test_header,
            verify=False,
        )

        assert response.status_code == requests.codes.unauthorized, \
            'Expected fail with inactive visualization origin'

    def test_cors_connection_with_visualization_disabled(self):
        """
        Test the cors connection when visualization is disabled
        """
        self.put(
            url=DISABLE_VISUALIZATION_SETTING,
            expected_status_code=requests.codes.ok
        )
        test_origin = {
            'name': 'test',
            'origin': ALLOW_ORIGIN,
            'active': 'True',
        }
        self.post(url=VISUALIZATION_ORIGIN_URL, data=test_origin)
        response = self.get(
            url=VISUALIZATION_API_URL,
            expected_status_code=requests.codes.ok
        )
        assert \
            response['errors'][0]['message'] == 'Visualization is disabled', \
            'Got unexpected message when visualization is disabled'
