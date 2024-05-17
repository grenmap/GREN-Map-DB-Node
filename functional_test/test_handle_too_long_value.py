"""
This file contains tests of import grenml function
which tests the long value handled during import
"""

import pytest
import time
from framework import GrenMapTestingFramework
from constants import *
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

expected_response = 'Data successfully imported'
QUERY = gql(
    '''
    query{
        institutions {
            id
            name
            shortName
            unlocode
            properties{
                name
                value
            }
        }
    }
    '''
)
PROPERTY_512 = "A book is a medium for recording information in the form of " \
               "writing or images, typically composed of many pages " \
               "(made of papyrus, parchment, vellum, or paper) " \
               "bound together and protected by a cover.[1] The technical " \
               "term for this physical arrangement is codex " \
               "(plural, codices). In the history of hand-held physical " \
               "supports for extended written compositions or records, " \
               "the codex replaces its immediate predecessor, the scroll. " \
               "A single sheet in a codex is a leaf, and each side of " \
               "a leaf is a page. length 512"

PROPERTY_755 = "A book is a medium for recording information in the form of " \
               "writing or images, typically composed of many pages " \
               "(made of papyrus, parchment, vellum, or paper) bound " \
               "together and protected by a cover.[1] The technical term " \
               "for this physical arrangement is codex (plural, codices). " \
               "In the history of hand-held physical supports for extended " \
               "written compositions or records, the codex replaces its " \
               "immediate predecessor, the scroll. A single sheet in a " \
               "codex is a leaf, and each side of a leaf is a page.Calculat..."


class TestHandleTooLongValue(GrenMapTestingFramework):

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestHandleTooLongValue)

    @pytest.fixture(autouse=True)
    def before_each(self):
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')
        time.sleep(1)

    def test_short_name(self):
        """
        This test uses grenml test file with one institution has short
        name more than 40 chars, expected trimmed short name
        with message.
        """
        expected_short_name = 'short_name_10_short_name_25_s...'
        test_grenml_name = 'test_short_name_40_chars.xml'
        self.import_xml_file(test_grenml_name)
        client = self._setup_visualization_http_request()
        institution = client.execute(QUERY)
        inst_found = False
        for inst in institution['institutions']:
            if inst['name'] == 'Institution 1':
                assert inst['shortName'] == expected_short_name
                inst_found = True
                break

        assert inst_found

    def test_name(self):
        """
        This test uses grenml test file with one institution's name
        has more than 160 chars, expected trimmed name with message.
        """
        expected_name = 'Institution name is ' \
                        'abcdefghijklmnopqrstuvwxyz123456 ' \
                        'That\'s the name for testing and has a ' \
                        'length of 160 charachters Still ne...'
        test_grenml_name = 'test_name_as_160_chars.xml'
        self.import_xml_file(test_grenml_name)
        client = self._setup_visualization_http_request()
        institution = client.execute(QUERY)
        inst_found = False
        for inst in institution['institutions']:
            if inst['id'] == 'Inst_1':
                assert inst['name'] == expected_name
                inst_found = True
                break

        assert inst_found

    def test_locode(self):
        """
        This test uses grenml test file with one institution has locode
        more than 5 chars, expected trimmed locode with message.
        """
        expected_locode = 'CA...'
        test_grenml_name = 'test_locode.xml'
        response = self.import_xml_file(test_grenml_name)
        print(response.status_code)
        client = self._setup_visualization_http_request()
        institution = client.execute(QUERY)
        inst_found = False
        for inst in institution['institutions']:
            if inst['id'] == 'Inst_1':
                assert inst['unlocode'] == expected_locode
                inst_found = True
                break

        assert inst_found

    def test_property_512_chars(self):
        """
        This test uses grenml test file with one institution has
        property equal to 512 chars, expected property with 512 chars.
        """
        expected_property_name = 'city'
        expected_property_value = PROPERTY_512
        test_grenml_name = 'test_property_as_512_chars.xml'
        self.import_xml_file(test_grenml_name)
        client = self._setup_visualization_http_request()
        institution = client.execute(QUERY)
        inst_found = False
        property_found = False
        for inst in institution['institutions']:
            if inst['id'] == 'Inst_1':
                for property in inst['properties']:
                    if property['name'] == expected_property_name:
                        assert property['value'] == expected_property_value
                        property_found = True
                        break
                inst_found = True
                break

        assert property_found
        assert inst_found

    def test_property_755_chars(self):
        """
        This test uses grenml test file with one institution has
        property equal to 755 chars, expected trimmed property
        with message.
        """
        expected_property_name = 'city'
        expected_property_value = PROPERTY_755
        test_grenml_name = 'test_property_as_755_chars.xml'
        self.import_xml_file(test_grenml_name)
        client = self._setup_visualization_http_request()
        institution = client.execute(QUERY)
        inst_found = False
        property_found = False
        for inst in institution['institutions']:
            if inst['id'] == 'Inst_1':
                for property in inst['properties']:
                    if property['name'] == expected_property_name:
                        assert property['value'] == expected_property_value
                        property_found = True
                        break
                inst_found = True
                break

        assert property_found
        assert inst_found

    def test_multiple_properties(self):
        """
        This test uses grenml test file with one institution has
        multiple properties with same keyword,
        expected properties with message.
        """
        expected_property_name = 'country'
        expected_property_value1 = "CA"
        expected_property_value2 = "USA"
        test_grenml_name = 'test_multiple_properties.xml'
        self.import_xml_file(test_grenml_name)
        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                institutions {
                    id
                    name
                    properties{
                        name
                        value
                    }
                }
            }
            '''
        )
        institution = client.execute(query)
        inst_found = False
        property_value_1_found = False
        property_value_2_found = False
        for inst in institution['institutions']:
            if inst['id'] == 'Inst_1':
                for property in inst['properties']:
                    if property['name'] == expected_property_name:
                        if property['value'] == expected_property_value1:
                            print(property['value'])
                            property_value_1_found = True
                        if property['value'] == expected_property_value2:
                            property_value_2_found = True
                inst_found = True
                break

        assert property_value_1_found and property_value_2_found
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
