"""
Copyright 2023 GRENMap Authors

SPDX-License-Identifier: Apache License 2.0

Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

------------------------------------------------------------------------

Synopsis: Contains functionality to support API tests of the GREN Map.
"""

import pytest
import requests
from requests.auth import HTTPBasicAuth
from constants import (
    DEFAULT_TIMEOUT,
    STATUS_URL,
    JSON_HEADER,
    FLUSH_DB_URL,
    CREATE_SUPER_USER,
    IMPORT_GRENML_POLL_ATTEMPTS,
    IMPORT_GRENML_POLL_SLEEP_SECONDS,
    IMPORT_GRENML_URL_POLL_DELETE,
    IMPORT_GRENML_URL,
    IMPORT_GRENML_STATUS_CODE_PENDING,
    TEST_TOKEN,
    TEST_TOKEN_EXPORT,
    CREATE_TEST_TOKEN_URL,
    LOAD_FIXTURE_URL,
    DEFAULT_INTERVAL,
    TEST_USER_NAME,
    TEST_USER_PASSWORD,
    TEST_USER_DATA,
    TEST_FILE_FOLDER,
    IMPORT_RULESETS_API_URL,
    NODE_DATA_API,
    TOPOLOGY_DATA_API,
    LINK_DATA_API,
    INSTITUTION_DATA_API,
)
from selenium_testcase import *

REMOTE_HUB_ADDRESS_VARIABLE_NAME = 'SELENIUM_HUB_ADDRESS'
DEFAULT_REMOTE_BROWSER_NAME = FIREFOX_BROWSER_IDENTIFIER


class GrenMapTestingFramework:

    def check_test_server_status(self):
        timeout = time.time() + DEFAULT_TIMEOUT
        while True:
            # Time out fail condition
            if time.time() > timeout:
                response = requests.get(
                    url=STATUS_URL,
                    headers=JSON_HEADER,
                    verify=False
                )

                raise pytest.fail(
                    f'Fail to connect to {STATUS_URL} in {DEFAULT_TIMEOUT} '
                    f'seconds with error \n {response.status_code}'
                )
            else:
                response = requests.get(
                    url=STATUS_URL,
                    headers=JSON_HEADER,
                    verify=False
                )
                if response.status_code == requests.codes.ok:
                    return

            # Setup retry interval using sleep function
            time.sleep(DEFAULT_INTERVAL)

    def flush_db(self):
        """
        Flushes the database. This should be called between tests
        """
        self.post(FLUSH_DB_URL, expected_status_code=200)

    def add_super_user(self, user_data=TEST_USER_DATA):
        """
        Create one super user for testing
        """
        self.post(
            CREATE_SUPER_USER,
            data=user_data,
            expected_status_code=200
        )

    def create_import_token(self):
        """
        This helper method creates an import token to enable
        authentication via api
        """
        self.post(
            url=CREATE_TEST_TOKEN_URL,
            data={
                "client_name": "test-upload",
                "token": TEST_TOKEN,
                "token_type": "grenml_import"},
            expected_status_code=requests.codes.ok
        )

    def create_grenml_export_token(self):
        """
        This helper method creates a grenml_export token to enable the
        grenml_export via api
        """
        self.post(
            url=CREATE_TEST_TOKEN_URL,
            data={
                "client_name": "test-export",
                "token": TEST_TOKEN_EXPORT,
                "token_type": "grenml_export"},
            expected_status_code=requests.codes.ok
        )

    def load_fixture(self, fixture_name):
        """
        Tells the server to load a fixture with a given name
        """
        self.post(
            LOAD_FIXTURE_URL,
            data={'fixture': fixture_name},
            expected_status_code=200
        )

    def poll_import_file(self):
        """
        Utility method to get an ImportFile object.
        Polls while the import status is "pending".
        Stops polling once the object has the success or failure
        status.
        """
        result = None
        for _ in range(IMPORT_GRENML_POLL_ATTEMPTS):
            time.sleep(IMPORT_GRENML_POLL_SLEEP_SECONDS)
            response = requests.get(
                IMPORT_GRENML_URL_POLL_DELETE,
                verify=False
            )
            entries = response.json()
            if len(entries) > 0:
                result = entries[-1]
                pending_code_len = IMPORT_GRENML_STATUS_CODE_PENDING
                status_code = result['import_status'][0:pending_code_len]
                if status_code != IMPORT_GRENML_STATUS_CODE_PENDING:
                    break
        return result

    def poll_then_delete(self):
        """
        Utility method to get an ImportFile object.
        Polls while the import status is "pending".
        Stops polling once the object has the success or failure
        status, then clears the database.
        """
        result = None
        for _ in range(IMPORT_GRENML_POLL_ATTEMPTS):
            time.sleep(IMPORT_GRENML_POLL_SLEEP_SECONDS)
            response = requests.get(
                verify=False, url=IMPORT_GRENML_URL_POLL_DELETE)
            entries = response.json()
            result = entries[0]
            pending_code_len = IMPORT_GRENML_STATUS_CODE_PENDING
            status_code = result['import_status'][0:pending_code_len]
            if status_code != IMPORT_GRENML_STATUS_CODE_PENDING:
                break
        requests.delete(IMPORT_GRENML_URL_POLL_DELETE, verify=False)
        return result

    def import_xml_file(
            self,
            file_name,
            topology_name=None,
    ):
        """
        Import xml file through import test API. This function will
        use a default test token to create an import token.
        This is used for the import of the parent topology only. use the
        import_xml_file_with_import_type_and_topology_name method
        to import child topologies without creating a token
        """
        self.create_import_token()
        test_file_path = TEST_FILE_FOLDER + file_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': test_data},
            headers={'Authorization': 'Bearer ' + TEST_TOKEN},
            verify=False,
            data={
                'topology_name': topology_name,
            },
        )
        self.poll_import_file()
        assert response.status_code == requests.codes.created, \
            'Failed to import grenml'

        return response

    def import_xml_file_with_import_type_and_topology_name(
            self,
            test_grenml_name,
            topology_id=None,
    ):
        """
        this helper method gets the file and posts it to the
        database via api this method specifies the import type
        and the topology name

        Note: If using the import method more than once in a test then
        provide the topology ID as it will change after the
        first import.
        """
        test_file_path = TEST_FILE_FOLDER + test_grenml_name
        test_data = open(test_file_path, 'r')
        response = requests.post(
            url=IMPORT_GRENML_URL,
            verify=False,
            files={'file': test_data},
            headers={'Authorization': 'Bearer ' + TEST_TOKEN},
            data={
                'parent_topology_id': topology_id,
            },
        )
        self.poll_import_file()
        assert response.status_code == requests.codes.created, \
            'Uploading the file should work'
        return response

    def import_ruleset(self, ruleset_json):
        test_file_path = TEST_FILE_FOLDER + ruleset_json
        with open(test_file_path, 'r') as json_data:
            data = json.load(json_data)
            # convert json object to string type for API
            data_string = json.dumps(data)
        # post ruleset to DB
        response = requests.post(
            url=IMPORT_RULESETS_API_URL,
            data=data_string,
            headers={"Content-Type": "application/json"},
            verify=False,
        )
        assert response.status_code == requests.codes.created, \
            'POST not successful via API'
        return response

    def get_topology_details(self, grenml_id=None):
        """
        This helper method returns a list of all topologies and
        their info from the DB
        """
        all_topology_data_list = self.get(
            url=TOPOLOGY_DATA_API,
            auth=True,
        )
        if grenml_id is None:
            return all_topology_data_list
        else:
            topology_list = []
            for topology in all_topology_data_list:
                if topology['grenml_id'] == grenml_id:
                    topology_list.append(topology)
            return topology_list

    def get_node_details(self, grenml_id=None):
        """
        This helper method returns a list of all  nodes and their
        info from the DB.
        if grenml_id of a node is provided then the data about that
        node is returned
        """

        all_nodes_data_list = self.get(
            url=NODE_DATA_API,
            auth=True,
        )
        if grenml_id is None:
            return all_nodes_data_list
        else:
            nodes_list = []
            for node in all_nodes_data_list:
                if node['grenml_id'] == grenml_id:
                    nodes_list.append(node)
            return nodes_list

    def get_link_details(self, grenml_id=None):
        """
        This helper method returns a list of all the links and their
        info from the DB
        """
        all_link_data_list = self.get(
            url=LINK_DATA_API,
            auth=True,
        )
        if grenml_id is None:
            return all_link_data_list
        else:
            link_list = []
            for link in all_link_data_list:
                if link['grenml_id'] == grenml_id:
                    link_list.append(link)
            return link_list

    def get_institution_details(self, grenml_id=None):
        """
        This helper method returns a list of all the institutions
        and their info from the DB
        """
        all_institution_data_list = self.get(
            url=INSTITUTION_DATA_API,
            auth=True,
        )
        if grenml_id is None:
            return all_institution_data_list
        else:
            institution_list = []
            for institution in all_institution_data_list:
                if institution['grenml_id'] == grenml_id:
                    institution_list.append(institution)
            return institution_list

    def post(self, url, data=None, auth=False, headers=JSON_HEADER,
             expected_status_code=requests.codes.created):
        """
        Use session to post data to API end point.
        Check the response status code is 201.
        Required to input, API end point URL and JSON format data.
        Output data posted location and response content.
        Input Example:
           data = {'name':'name'}
           url = 'https://test.myisp.com/api/'
        """
        if auth:
            if data is None:
                api_response = requests.post(
                    url=url,
                    headers=headers,
                    verify=False,
                    auth=HTTPBasicAuth(TEST_USER_NAME, TEST_USER_PASSWORD),
                )
            else:
                api_response = requests.post(
                    url=url,
                    data=json.dumps(data),
                    headers=headers,
                    verify=False,
                    auth=HTTPBasicAuth(TEST_USER_NAME, TEST_USER_PASSWORD),
                )
        else:
            if data is None:
                api_response = requests.post(
                    url=url,
                    headers=headers,
                    verify=False,
                )
            else:
                api_response = requests.post(
                    url=url,
                    data=json.dumps(data),
                    headers=headers,
                    verify=False,
                )

        assert expected_status_code == api_response.status_code, \
            'Post to URL {} failed with data {}. Expected status code {}, ' \
            'but got code {}, with error {}'.format(
                url,
                data,
                expected_status_code,
                api_response.status_code,
                api_response.content,
            )

        location = api_response.headers.get('location', None)

        content = self._get_content(api_response)

        return location, content

    def put(self, url, data=None, auth=False, headers=JSON_HEADER,
            expected_status_code=requests.codes.created):
        """
        Use session to put data to API end point.
        Check the response status code is 201.
        Required to input, API end point URL and JSON format data.
        Output data posted location and response content.
        Input Example:
           data = {'name':'name'}
           url = 'https://test.myisp.com/api/'
        """
        if auth:
            if data is None:
                api_response = requests.put(
                    url=url,
                    headers=headers,
                    verify=False,
                    auth=HTTPBasicAuth(TEST_USER_NAME, TEST_USER_PASSWORD),
                )
            else:
                api_response = requests.put(
                    url=url,
                    data=json.dumps(data),
                    headers=headers,
                    verify=False,
                    auth=HTTPBasicAuth(TEST_USER_NAME, TEST_USER_PASSWORD),
                )
        else:
            if data is None:
                api_response = requests.put(
                    url=url,
                    headers=headers,
                    verify=False,
                )
            else:
                api_response = requests.put(
                    url=url,
                    data=json.dumps(data),
                    headers=headers,
                    verify=False,
                )

        assert expected_status_code == api_response.status_code, \
            'Put to URL {} failed with data {}. Expected status code {}, ' \
            'but got code {}, with error {}'.format(
                url,
                data,
                expected_status_code,
                api_response.status_code,
                api_response.content,
            )

        location = api_response.headers.get('location', None)

        content = self._get_content(api_response)

        return location, content

    def patch(self, url, data=None, auth=False, headers=JSON_HEADER,
              expected_status_code=requests.codes.ok):
        """
        Use session to patch data to API end point.
        Check the response status code is 201.
        Required to input, API end point URL and JSON format data.
        Output data posted location and response content.
        Input Example:
           data = {'name':'name'}
           url = 'https://test.myisp.com/api/'
        """
        if auth:
            if data is None:
                api_response = requests.patch(
                    url=url,
                    headers=headers,
                    verify=False,
                    auth=HTTPBasicAuth(TEST_USER_NAME, TEST_USER_PASSWORD),
                )
            else:
                api_response = requests.patch(
                    url=url,
                    data=json.dumps(data),
                    headers=headers,
                    verify=False,
                    auth=HTTPBasicAuth(TEST_USER_NAME, TEST_USER_PASSWORD),
                )
        else:
            if data is None:
                api_response = requests.patch(
                    url=url,
                    headers=headers,
                    verify=False,
                )
            else:
                api_response = requests.patch(
                    url=url,
                    data=json.dumps(data),
                    headers=headers,
                    verify=False,
                )
        assert expected_status_code == api_response.status_code, \
            'Patch to URL {} failed with data {}. Expected status code {}, ' \
            'but got code {}, with error {}'.format(
                url,
                data,
                expected_status_code,
                api_response.status_code,
                api_response.content,
            )

        location = api_response.headers.get('location', None)

        content = self._get_content(api_response)

        return location, content

    def get(self, url, headers=JSON_HEADER, auth=False,
            expected_status_code=requests.codes.ok):
        """
        Use session to get data to API end point.
        Check the response status code is 200.
        Required to input API end point URL. Output response content.
        Input Example:
           url = 'https://test.myisp.com/api/23/'
        """
        if auth:
            api_response = requests.get(
                url=url,
                headers=headers,
                verify=False,
                auth=HTTPBasicAuth(TEST_USER_NAME, TEST_USER_PASSWORD),
            )
        else:
            api_response = requests.get(
                url=url,
                headers=headers,
                verify=False,
            )

        assert expected_status_code == api_response.status_code, \
            'Failed to get data from URL {}. Expected status code {}, ' \
            'but got code {}, with error {}'.format(
                url,
                expected_status_code,
                api_response.status_code,
                api_response.content,
            )
        location = api_response.headers.get('location', None)
        content = self._get_content(api_response)
        if location is not None:
            return location, content
        else:
            return content

    def delete(self, url, headers=JSON_HEADER, auth=False,
               expected_status_code=requests.codes.no_content):
        """
        Use session to remove data from API end point.
        Check the response status code is 204.
        Required to input created session, API end point URL. No output.
        Input Example:
           url = 'https://test.myisp.com/api/23/'
        """

        if auth:
            api_response = requests.delete(
                url=url,
                headers=headers,
                verify=False,
                auth=HTTPBasicAuth(TEST_USER_NAME, TEST_USER_PASSWORD),
            )
        else:
            api_response = requests.delete(
                url=url,
                headers=headers,
                verify=False,
            )

        assert expected_status_code == api_response.status_code, \
            'Failed to delete data from URL {}. Expected status code {}, ' \
            'but got code {}, with error {}'.format(
                url,
                expected_status_code,
                api_response.status_code,
                api_response.content,
            )

    def _get_content(self, api_response):
        """
        Get content from API response and try to convert to JSON format
        """

        api_content = api_response.text
        try:
            api_content = json.loads(api_content)
        except ValueError:
            pass

        return api_content


class GrenMapUITestingFramework(SeleniumTestCase, GrenMapTestingFramework):
    """
    This class contains the UI test help functions
    """
    @classmethod
    def setUpClass(cls) -> None:
        """
        Note: Always have calling this setUpClass the last
        instruction for any and all subclasses that use a
        setUpClass function
        """
        # Configure default browser setup for local
        # or remote Selenium testing.
        if REMOTE_HUB_ADDRESS_VARIABLE_NAME in os.environ:
            cls.node_url = os.environ[REMOTE_HUB_ADDRESS_VARIABLE_NAME]
            cls.browser_name = DEFAULT_REMOTE_BROWSER_NAME
        else:
            cls.browser_name = DEFAULT_LOCAL_BROWSER_NAME

        super(GrenMapUITestingFramework, cls).setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
