"""
This is an file contains GREN Map visualization API tests.
"""

import requests
import time
from constants import *
from framework import GrenMapTestingFramework
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import pytest

TEST_DATA_FILE = 'test_full_network_data.xml'


class TestVisualizationAPI(GrenMapTestingFramework):

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestVisualizationAPI)

    @pytest.fixture(scope="class", autouse=True)
    def before_each(self):
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')
        # import test network data
        self.import_xml_file(TEST_DATA_FILE)
        time.sleep(1)

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """
        Enable visualization setting for the tests
        """
        self.put(
            url=ENABLE_VISUALIZATION_SETTING,
            expected_status_code=requests.codes.ok
        )

    def test_toggle_visualization_api_setting(self):
        """
        Toggle visualization setting, check the visualization
        response as expected.
        """
        response = self.get(VISUALIZATION_SETTING_URL)
        assert response == 'True', 'Get unexpected visualization setting.'
        _, response = self.put(
            url=DISABLE_VISUALIZATION_SETTING,
            expected_status_code=requests.codes.ok
        )
        assert response == 'False', 'Get unexpected visualization setting.'
        visualization_response = self.get(url=VISUALIZATION_API_URL)
        error_message = visualization_response['errors'][0]['message']
        assert error_message == 'Visualization is disabled', \
            'Unexpected error message when visualization API is disabled'

    def test_visualization_api_query_institution_none(self):
        """
        Test visualization API to query institution expect empty result
        """
        expected_response = {'institution': None}
        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                institution(name:"Fake Name", id:"Fake ID") {
                    name
                    id
                }
            }
            '''
        )
        result = client.execute(query)
        assert result == expected_response, 'Unexpected institution response'

    def test_visualization_api_query_all_institutions(self):
        """
        Query all institution from visualization API.
        Check the total number of response institutions.
        """
        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                institutions {
                    id
                    name
                }
            }
            '''
        )
        institution_list = client.execute(query)
        print(institution_list)

        assert len(institution_list['institutions']) == 8, \
            'Got unexpected number of institutions'

    def test_visualization_api_query_one_institution_with_all_fields(self):
        """
        Query one institution with all fields from visualization API.
        """

        expected_institution_fields = [
            'id',
            'name',
            'shortName',
            'version',
            'longitude',
            'latitude',
            'address',
        ]

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                institutions {
                    id
                    name
                    shortName
                    version
                    longitude
                    latitude
                    address
                }
            }
            '''
        )
        institutions = client.execute(query)
        for institution in institutions['institutions']:
            for key, value in institution.items():
                assert key in expected_institution_fields, \
                    'Got unexpected data fields from institution'

    def test_visualization_api_query_node_none(self):
        """
        Test visualization API to query node and expect empty result
        """
        expected_response = {'node': None}
        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                node(name:"Fake Name", id:"Fake ID") {
                    name
                    id
                }
            }
            '''
        )
        result = client.execute(query)
        assert result == expected_response, 'Unexpected node response'

    def test_visualization_api_query_all_nodes(self):
        """
        Query all nodes from visualization API.
        Check the total number of response nodes.
        """
        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                nodes {
                    name
                    id
                }
            }
            '''
        )
        result = client.execute(query)
        assert len(result['nodes']) == 11, 'Got unexpected number of nodes'

    def test_visualization_api_query_one_node_with_all_fields(self):
        """
        Query one node with all fields from visualization API.
        Check the response node data correct.
        """
        exepected_fields = [
            'name',
            'id',
            'shortName',
            'version',
            'start',
            'end',
            'longitude',
            'latitude',
            'address',
        ]

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                nodes {
                    name
                    id
                    version
                    start
                    end
                    shortName
                    longitude
                    latitude
                    address
                }
            }
            '''
        )
        nodes = client.execute(query)
        for node in nodes['nodes']:
            for key, value in node.items():
                assert key in exepected_fields, 'Got unexpected node fields'

    def test_visualization_api_query_link_none(self):
        """
        Test visualization API to query link and expect empty result
        """
        expected_response = {'link': None}
        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                link(name:"Fake Name", id:"Fake ID") {
                    name
                    id
                }
            }
            '''
        )
        result = client.execute(query)
        assert result == expected_response, 'Unexpected link response'

    def test_visualization_api_query_all_links(self):
        """
        Query all links from visualization API.
        Check the total number of response links.
        """
        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                links {
                    name
                    id
                }
            }
            '''
        )
        result = client.execute(query)
        assert len(result['links']) == 5, 'Got unexpected number of links'

    def test_visualization_api_query_one_link_with_all_fields(self):
        """
        Query one link with all fields from visualization API.
        Check the response link data correct.
        """
        exepected_fields = [
            'name',
            'id',
            'version',
            'start',
            'end',
            'shortName',
            'nodeA',
            'nodeB'
        ]

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                links {
                    name
                    id
                    shortName
                    version
                    start
                    end
                    nodeA{
                        id
                    }
                    nodeB{
                        id
                    }
                }
            }
            '''
        )
        links = client.execute(query)
        for link in links['links']:
            for key, value in link.items():
                assert key in exepected_fields, 'Got unexpected link fields'

    def test_visualization_api_information_of_node_with_a_owner(self):
        """
        Query one node with a owner from visualization API.
        Check the additional information of node is correct.
        """
        expected_fields = {
            'name': 'Node 1',
            'owners': ['Institution test 6', 'GREN'],
        }

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                nodes {
                    name
                    owners{
                        name
                    }
                }
            }
            '''
        )
        node_found = False
        nodes = client.execute(query)
        for dic in nodes['nodes']:
            if dic['name'] == expected_fields['name']:
                for owners_name in dic['owners']:
                    assert owners_name['name'] in expected_fields['owners']
                node_found = True
                break
        assert node_found

    def test_visualization_api_information_of_node_with_multiple_owners(self):
        """
        Query one node with multiple owner from visualization API.
        Check the additional information of node is correct.
        """
        expected_fields = {
            'name': 'Node 3',
            'owners': ['Institution test 3', 'Institution test 4', 'GREN'],
        }

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                nodes {
                    name
                    owners{
                        name
                    }
                }
            }
            '''
        )
        node_found = False
        nodes = client.execute(query)
        for dic in nodes['nodes']:
            if dic['name'] == expected_fields['name']:
                for owner_name in dic['owners']:
                    assert owner_name['name'] in expected_fields['owners']
                node_found = True
                break
        assert node_found

    def test_visualization_api_information_of_node_with_properties(self):
        """
        Query one node with multiple properties from visualization API.
        Check the additional information of node is correct.
        """
        expected_fields = {
            'name': 'Node 1',
            'properties': [
                {
                    'name': 'description',
                    'value': 'This is Test University Node'
                },
                {
                    'name': 'note',
                    'value': 'This is a test node'
                }
            ]
        }

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                nodes {
                    name
                    properties{
                        name,
                        value
                    }
                }
            }
            '''
        )
        node_found = False
        nodes = client.execute(query)
        for dic in nodes['nodes']:
            if dic['name'] == expected_fields['name']:
                assert dic['properties'] == expected_fields['properties']
                node_found = True
                break
        assert node_found

    def test_visualization_api_information_of_node_with_short_name(self):
        """
        Query one node with short name field from visualization API.
        Check the additional information of node is correct.
        """
        expected_fields = {
            'name': 'Node 1',
            'shortName': 'NDE1'
        }

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                nodes {
                    name
                    shortName
                }
            }
            '''
        )
        node_found = False
        nodes = client.execute(query)
        for dic in nodes['nodes']:
            if dic['name'] == expected_fields['name']:
                assert dic['shortName'] == expected_fields['shortName']
                node_found = True
                break
        assert node_found

    def test_visualization_api_information_of_node_with_version(self):
        """
        Query one node with version field from visualization API.
        Check the additional information of node is correct.
        """
        expected_fields = {
            'name': 'Node 1',
            'version': '2020-01-01T10:10:00+00:00'
        }

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                nodes {
                    name
                    version
                }
            }
            '''
        )
        node_found = False
        nodes = client.execute(query)
        for dic in nodes['nodes']:
            if dic['name'] == expected_fields['name']:
                assert dic['version'] == expected_fields['version']
                node_found = True
                break
        assert node_found

    def test_visualization_api_information_of_node_with_start_end_time(self):
        """
        Query one node with start and end time field from
        visualization API.
        Check the additional information of node is correct.
        """
        expected_fields = {
            'name': 'Node 1',
            'start': '2020-05-07T00:00:01+00:00',
            'end': '2022-05-01T23:59:59+00:00'
        }

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                nodes {
                    name
                    start
                    end
                }
            }
            '''
        )
        node_found = False
        nodes = client.execute(query)
        for dic in nodes['nodes']:
            if dic['name'] == expected_fields['name']:
                assert dic['start'] == expected_fields['start']
                assert dic['end'] == expected_fields['end']
                node_found = True
                break
        assert node_found

    def test_visualization_api_information_of_link_with_multiple_owners(self):
        """
        Query one link with multiple owners from visualization API.
        Check the additional information of link is correct.
        """
        expected_fields = {
            'name': 'Link 1',
            'owners': ['Institution test 1', 'Institution test 2',
                       'Institution test 3', 'GREN']
        }

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                links {
                    name
                    owners{
                        name
                    }
                }
            }
            '''
        )
        link_found = False
        links = client.execute(query)
        for dic in links['links']:
            if dic['name'] == expected_fields['name']:
                for owner_name in dic['owners']:
                    assert owner_name['name'] in expected_fields['owners']
                link_found = True
                break
        assert link_found

    # @pytest.mark.skip('Unstable test that temporarily skipped')
    def test_visualization_api_information_of_link_with_properties(self):
        """
        Query one link with multiple properties from visualization API.
        Check the additional information of node is correct.
        """
        expected_fields = {
            'name': 'Link 2',
            'properties': [
                {'name': 'desc', 'value': 'link description'},
                {'name': 'linkspeed', 'value': '100000'}
            ]
        }

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                links {
                    name
                    properties{
                        name,
                        value
                    }
                }
            }
            '''
        )
        link_found = False
        links = client.execute(query)
        for dic in links['links']:
            if dic['name'] == expected_fields['name']:
                assert dic['properties'] == expected_fields['properties'], \
                    f'the result is {dic}, and links are {links["links"]}'
                link_found = True
                break
        assert link_found

    def test_visualization_api_information_of_link_with_short_name(self):
        """
        Query one link with short name field from visualization API.
        Check the additional information of node is correct.
        """
        expected_fields = {
            'name': 'Link 2',
            'shortName': 'LNK2',
        }

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                links {
                    name
                    shortName
                }
            }
            '''
        )
        link_found = False
        links = client.execute(query)
        for dic in links['links']:
            if dic['name'] == expected_fields['name']:
                assert dic['shortName'] == expected_fields['shortName']
                link_found = True
                break
        assert link_found

    def test_visualization_api_information_of_link_with_version(self):
        """
        Query one link with version field from visualization API.
        Check the additional information of node is correct.
        """
        expected_fields = {
            'name': 'Link 5',
            'version': '2020-01-01T10:10:00+00:00',
        }

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                links {
                    name
                    version
                }
            }
            '''
        )
        link_found = False
        links = client.execute(query)
        for dic in links['links']:
            if dic['name'] == expected_fields['name']:
                assert dic['version'] == expected_fields['version'], \
                    f'The dict is {dic}'
                link_found = True
                break
        assert link_found

    def test_visualization_api_information_of_link_start_end_time(self):
        """
        Query one link with start and end time field from
        visualization API.
        Check the additional information of node is correct.
        """
        expected_fields = {
            'name': 'Link 5',
            'start': '2020-01-01T10:10:00+00:00',
            'end': '2030-01-01T10:10:00+00:00'
        }

        client = self._setup_visualization_http_request()
        query = gql(
            '''
            query{
                links {
                    name
                    start
                    end
                }
            }
            '''
        )
        link_found = False
        links = client.execute(query)
        for dic in links['links']:
            if dic['name'] == expected_fields['name']:
                assert dic['start'] == expected_fields['start']
                assert dic['end'] == expected_fields['end']
                link_found = True
                break
        assert link_found

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
            retries=4,
            transport=visualization_transport,
            fetch_schema_from_transport=True,
        )
        return client
