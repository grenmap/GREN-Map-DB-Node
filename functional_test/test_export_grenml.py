"""
This file contains tests of exporting grenml function
"""

from constants import EXPORT_GRENML_URL, XML_HEADER, TEST_TOKEN_EXPORT
from framework import GrenMapTestingFramework
import pytest
import requests

TEST_HEADER = XML_HEADER
TEST_HEADER["Authorization"] = "Bearer " + TEST_TOKEN_EXPORT
TEST_DATA_FILE = 'test_full_network_data.xml'


class TestImportAPI(GrenMapTestingFramework):

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestImportAPI)

    @pytest.fixture(autouse=True)
    def before_each(self):
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')
        self.create_grenml_export_token()

        # import test network data
        self.import_xml_file(TEST_DATA_FILE)

    def test_grenml_export(self):
        """
        Test export grenml file API endpoint. Expected
        response file contains same data as test_fixture.json
        """

        xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER
        )

        expected_institution_list = [
            '36bd28d2-b882-479b-a98b-d884aacb9712',
            '4d88927b-c3ac-4637-85ed-711c6c50be73',
            '597c764d-a955-4b3d-b4f0-1dd95fd9f50d',
            '68e41179-695e-4fce-b0db-ecaaf9819c24',
            'bf833723-c9d1-43bf-b3c7-5e8f646dc9e0',
            'de00a1cd-d0a9-4b02-ad95-d7495ddc4959',
            'df777906-622c-432d-b2ae-ad42b08cc65b'
        ]

        for institution_id in expected_institution_list:
            assert institution_id in xml_data, \
                'Fail to find expecting institution in exported xml data.'

        expected_node_list = [
            '245382d3-2a5a-43a8-b10c-a80431d18b50',
            '3b2a4b82-5f6b-41f4-a361-f608234c03cc',
            '578d5f1c-4b58-4462-84e4-031b8cadb552',
            '5e491083-3a75-4316-a228-f021185659b0',
            '779b5571-0f68-4a61-b92d-6fed6777058e',
            'ac770ef7-27d3-4203-afef-92ac86b9c1ce',
            'bcb593f5-402f-4c72-afdc-0840dc26b43c',
            'c3182ad1-f3c5-44d4-b073-0dfcbfdc19d6',
            'cdf346f4-45c1-4b5b-9942-95d418aaf1f8',
            'd13a9ec9-e3db-4715-85f8-32d352b2d448',
            'fcb714fe-56e8-436c-a07c-3dc3c10991d0'
        ]

        for node_id in expected_node_list:
            assert node_id in xml_data, \
                'Fail to find expecting node in exported xml data.'

        expected_link_list = [
            '3b2a4b82-5f6b-41f4-a361-l123456c0000',
            '3b2a4b82-5f6b-41f4-a361-l123456c0001',
            '3b2a4b82-5f6b-41f4-a361-l123456c0002',
            '3b2a4b82-5f6b-41f4-a361-l123456c0003',
            '3b2a4b82-5f6b-41f4-a361-l123456c0004',
        ]

        for link_id in expected_link_list:
            assert link_id in xml_data, \
                'Fail to find expecting link in exported xml data.'

        expected_topology_name_list = [
            'Topology Test 2',
        ]

        for topology_name in expected_topology_name_list:
            assert topology_name in xml_data, \
                'Fail to find the root topology name in the xml data'

    def test_grenml_export_fail_without_token(self):
        """
        Test export grenml file API endpoint should fail
        without token string.
        """
        response = requests.get(
            url=EXPORT_GRENML_URL,
            verify=False,
        )
        assert response.status_code == requests.codes.forbidden

    def test_grenml_export_fail_with_invalid_token(self):
        """
        Test export grenml file API endpoint should fail with
        invalid string.
        """
        invalid_token = 'invalidtoken1234'
        response = requests.get(
            url=EXPORT_GRENML_URL,
            verify=False,
            headers={'Authorization': 'Bearer ' + invalid_token}
        )
        assert response.status_code == requests.codes.forbidden
