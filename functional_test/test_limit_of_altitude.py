"""
This file contains tests of import grenml function
"""

import pytest
import time
from framework import GrenMapTestingFramework
from constants import *
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

QUERY = gql(
    '''
    query{
        institutions {
            id
            name
            altitude
        }
    }
    '''
)


class TestAltitudeLimit(GrenMapTestingFramework):

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestAltitudeLimit)

    @pytest.fixture(autouse=True)
    def before_each(self):
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')
        time.sleep(1)

    def test_altitude(self):
        """
        This test uses grenml test file with one institution has normal
        altitude, expected altitude with no message in the logs.
        """
        expected_alt = '1000.000000'
        test_grenml_name = 'test_alt.xml'
        self.import_xml_file(test_grenml_name)
        client = self._setup_visualization_http_request()
        institution = client.execute(QUERY)
        inst_found = False
        for inst in institution['institutions']:
            if inst['id'] == 'Inst_1':
                assert str(inst['altitude']) == expected_alt
                inst_found = True
                break

        assert inst_found

    def test_max_altitude(self):
        """
        This test uses grenml test file with one institution has
        maximum altitude, expected altitude with message.
        max altitude = 9000 as it is the highest point on earth
        """
        expected_alt = '9000.000000'
        test_grenml_name = 'test_max_alt.xml'
        self.import_xml_file(test_grenml_name)
        client = self._setup_visualization_http_request()
        institution = client.execute(QUERY)
        inst_found = False
        for inst in institution['institutions']:
            if inst['id'] == 'Inst_1':
                assert str(inst['altitude']) == expected_alt
                inst_found = True
                break

        assert inst_found

    def test_min_alt(self):
        """
        This test uses grenml test file with one institution has
        minimum altitude, expected altitude with message.
        min altitude = -11000 as it is the lowest point on ocean floor
        """
        expected_alt = '-11000.000000'
        test_grenml_name = 'test_min_alt.xml'
        self.import_xml_file(test_grenml_name)
        client = self._setup_visualization_http_request()
        institution = client.execute(QUERY)
        inst_found = False
        for inst in institution['institutions']:
            if inst['id'] == 'Inst_1':
                assert str(inst['altitude']) == expected_alt
                inst_found = True
                break

        assert inst_found

    def test_alt_beyond_limit(self):
        """
        This test uses grenml test file with one institution has
        altitude beyond limit, expected altitude with message.
        """
        expected_alt = '9000.000000'
        test_grenml_name = 'test_beyond_limit_alt.xml'
        self.import_xml_file(test_grenml_name)
        client = self._setup_visualization_http_request()
        institution = client.execute(QUERY)
        inst_found = False
        for inst in institution['institutions']:
            if inst['id'] == 'Inst_1':
                assert str(inst['altitude']) == expected_alt
                inst_found = True
                break

        assert inst_found

    def _setup_visualization_http_request(self):
        """
        Set up the visualization http requests
        """
        visualization_transport = RequestsHTTPTransport(
            url=VISUALIZATION_API_URL,
            use_json=True,
            headers=JSON_HEADER,
            verify=False,
        )
        client = Client(
            # retries=4,
            transport=visualization_transport,
            fetch_schema_from_transport=True,
        )
        return client
