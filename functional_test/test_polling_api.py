"""
This file contains GREN Map Polling API tests.
"""

import requests
import time
from urllib.parse import urljoin
from constants import *
from framework import GrenMapTestingFramework
import pytest

TEST_DATA_FILE = '/home/grenmap_functional_test/test_files/test_import_grenml_no_address.xml'
TEST_URL_CUSTOM = 'https://websp1:8443/'


class TestPollingAPI(GrenMapTestingFramework):

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestPollingAPI)

    @pytest.fixture(autouse=True)
    def before_each(self):
        # Retry flush in case the task runner locks the database
        # because it is busy with a polling from the previous test.
        for _ in range(5):
            try:
                self.flush_db()
                break
            except Exception:
                time.sleep(2)

        self.add_super_user()
        self.create_import_token()
        self.load_fixture('test_app_configurations.json')
        self._import_data()

    def test_setup_polling_source(self):
        """
        Test setup polling source through API
        """
        for test_source in TEST_NODE_NAME_LIST:
            test_source_data = {
                "name": test_source,
                "protocol": "https",
                "hostname": test_source,
                "port": "8443",
                "path": "",
                "active": True
            }
            self.post(url=POLLING_SOURCE_URL, data=test_source_data)
        # Check polling source setup correctly
        polling_source_list = self.get(url=POLLING_SOURCE_URL)
        source_name_list = []
        for source in polling_source_list:
            source_name_list.append(source['hostname'])
        assert TEST_NODE_NAME_LIST == source_name_list

    def test_trigger_batch_polling_all_pass(self):
        """
        Test polling batch source, and all sources should pass
        """
        for test_source in TEST_NODE_NAME_LIST:
            test_source_data = {
                "name": test_source,
                "protocol": "https",
                "hostname": test_source,
                "port": "8443",
                "path": "",
                "active": True
            }
            self.post(url=POLLING_SOURCE_URL, data=test_source_data)
        # trigger the batch polling and check the batch polling log
        location, response = self.post(url=POLLING_BATCH_TRIGGER_URL)
        batch_log_location = urljoin(TEST_SITE_URL, location)
        response = self._wait_until_poll_completes(batch_log_location)
        host_name_list = []
        for polling_event in response['polls']:
            host_name_list.append(polling_event['polling_source']['hostname'])
            assert polling_event['status'], \
                f'Unexpected polling status, {response}'
        assert TEST_NODE_NAME_LIST.sort() == host_name_list.sort()

    def test_trigger_batch_polling_one_pass_one_fail(self):
        """
        Test polling batch source, and one source pass and one fail
        """
        expected_node_name_list = [
            TEST_NODE_NAME_LIST[0],
            TEST_NODE_NAME_LIST[1] + 'New'
        ]
        for test_source in expected_node_name_list:
            test_source_data = {
                "name": test_source,
                "protocol": "https",
                "hostname": test_source,
                "port": "8443",
                "path": "",
                "active": True
            }
            self.post(url=POLLING_SOURCE_URL, data=test_source_data)

        # trigger the batch polling and check the batch polling log
        location, response = self.post(
            url=POLLING_BATCH_TRIGGER_URL,
            expected_status_code=requests.codes.created
        )
        batch_log_location = urljoin(TEST_SITE_URL, location)
        response = self._wait_until_poll_completes(batch_log_location)
        host_name_list = []
        for polling_event in response['polls']:
            host_name_list.append(polling_event['polling_source']['hostname'])
            if polling_event['polling_source']['hostname'] == TEST_NODE_NAME_LIST[0]:
                # to understand status check PollImport
                # in polling.models.control
                assert polling_event['status'] == 4, \
                    f'Unexpected polling status, {response}'
            else:
                assert polling_event['status'] == -1, \
                    f'Unexpected polling status, {response}'
        assert expected_node_name_list.sort() == host_name_list.sort()

    def test_trigger_batch_polling_all_fail(self):
        """
        Test polling batch source fail, setup both not active source.
        """
        for test_source in TEST_NODE_NAME_LIST:
            test_source_data = {
                "name": test_source,
                "protocol": "https",
                "hostname": test_source,
                "port": "8441",
                "path": "",
                "active": True
            }
            self.post(url=POLLING_SOURCE_URL, data=test_source_data)

        # trigger the batch polling and check the batch polling log
        location, response = self.post(
            url=POLLING_BATCH_TRIGGER_URL,
            expected_status_code=requests.codes.created
        )
        batch_log_location = urljoin(TEST_SITE_URL, location)
        response = self._wait_until_poll_completes(batch_log_location)
        host_name_list = []
        for polling_event in response['polls']:
            host_name_list.append(polling_event['polling_source']['hostname'])
            assert polling_event['status'] == -1, \
                f'Unexpected polling status, {response}'
        assert TEST_NODE_NAME_LIST == host_name_list

    @pytest.mark.parametrize(
        'kwargs',
        (
            {
                "name": 'websp1',
                "protocol": "https",
                "hostname": 'websp1',
                "port": "8443",
                "path": "",
                "active": True
            },
            {
                "name": 'websp2',
                "protocol": "https",
                "hostname": 'websp2',
                "port": "8443",
                "path": "",
                "active": False
            },
        ),
        ids=['polling pass active source', 'polling pass not active source']
    )
    def test_single_source_polling_pass(self, kwargs):
        """
        Test polling single source pass situation.
        """
        location, response = self.post(url=POLLING_SOURCE_URL, data=kwargs)
        polling_id = str(response['id'])
        polling_single_trigger_url = f'{POLLING_TRIGGER_URL}{polling_id}/'
        # trigger the source polling and check the source polling log
        location, response = self.post(url=polling_single_trigger_url)
        source_log_location = urljoin(TEST_SITE_URL, location)
        response = self._wait_until_poll_completes(source_log_location)
        assert response['polls'][0]['polling_source']['hostname'] == kwargs['hostname']
        assert response['polls'][0]['polling_source']['active'] == kwargs['active']
        assert response['polls'][0]['status'] == 4, \
            f'Unexpected polling status, {response}'

    @pytest.mark.parametrize(
        'kwargs',
        (
            {
                "name": 'websp1',
                "protocol": "https",
                "hostname": 'websp1',
                "port": "8441",
                "path": "",
                "active": True
            },
            {
                "name": 'websp1',
                "protocol": "http",
                "hostname": 'websp1',
                "port": "8443",
                "path": "",
                "active": True
            },
            {
                "name": 'websp1',
                "protocol": "https",
                "hostname": 'websp1_1',
                "port": "8443",
                "path": "",
                "active": True
            },
            {
                "name": 'websp1',
                "protocol": "https",
                "hostname": 'websp1',
                "port": "8443",
                "path": "status/",
                "active": True
            },
        ),
        ids=[
            'incorrect port number',
            'incorrect host protocol',
            'incorrect hostname',
            'incorrect path'
        ]
    )
    def test_single_source_polling_fail(self, kwargs):
        """
        Test polling single source fail situation.
        """
        location, response = self.post(url=POLLING_SOURCE_URL, data=kwargs)
        polling_id = str(response['id'])
        polling_single_trigger_url = f'{POLLING_TRIGGER_URL}{polling_id}/'

        # trigger the source polling and check the source polling log
        location, response = self.post(
            url=polling_single_trigger_url,
            expected_status_code=requests.codes.created
        )
        source_log_location = urljoin(TEST_SITE_URL, location)
        response = self._wait_until_poll_completes(source_log_location)
        assert response['polls'][0]['polling_source']['hostname'] == kwargs['hostname']
        assert response['polls'][0]['polling_source']['active'] == kwargs['active']
        assert response['polls'][0]['status'] == -1, \
            f'Unexpected polling status, {response}'

    @pytest.mark.skip(reason="Need to figure out how to do short polling durations")
    def test_schedule_polling_pass(self):
        """
        Setup polling schedule and active, test the schedule polling
        """
        source_id_list = []
        for test_source in TEST_NODE_NAME_LIST:
            test_source_data = {
                "name": test_source,
                "protocol": "https",
                "hostname": test_source,
                "port": "8443",
                "path": "",
                "active": True
            }
            location, response = self.post(
                url=POLLING_SOURCE_URL,
                data=test_source_data
            )
            source_id_list.append(response['id'])
        # Set automatic polling enabled
        self.put(
            url=POLLING_AUTOMATIC_ENABLED,
            expected_status_code=requests.codes.ok
        )
        # Set schedule interval
        schedule_interval_data = {
            "interval": "@every 5s"
        }
        self.put(
            url=POLLING_SCHEDULE_INTERVAL,
            data=schedule_interval_data,
            expected_status_code=requests.codes.ok
        )
        time.sleep(6)
        # Set automatic polling disabled
        self.put(
            url=POLLING_AUTOMATIC_DISABLED,
            expected_status_code=requests.codes.ok
        )

        # Check the batch polling log and source polling log
        time.sleep(1)
        response = self.get(url=POLLING_SOURCE_ALL_LOG_URL)
        source_log_id_list = []
        for source_log in response:
            source_log_id_list.append(source_log['id'])
            if source_log['source']['id'] == source_id_list[0]:
                assert source_log['source']['hostname'] == TEST_NODE_NAME_LIST[0]
                batch_event_id_1 = source_log['batch_poll_event']
            if source_log['source']['id'] == source_id_list[1]:
                assert source_log['source']['hostname'] == TEST_NODE_NAME_LIST[1]
                source_log['batch_poll_event']

        batch_polling_log_url = f'{POLLING_BATCH_LOG_URL}{str(batch_event_id_1)}'
        response = self.get(url=batch_polling_log_url)
        assert response['was_scheduled'], \
            f'Fail to setup the schedule polling {response}'
        assert response['status'], f'Unexpected polling status, {response}'

    @pytest.mark.skip(reason="Need to figure out how to do short polling durations")
    def test_schedule_polling_not_enabled(self):
        """
        Test schedule will not start if it is not enabled
        """
        test_source_data = {
            "name": TEST_NODE_NAME_LIST[0],
            "protocol": "https",
            "hostname": TEST_NODE_NAME_LIST[0],
            "port": "8443",
            "path": "",
            "active": True
        }
        location, response = self.post(
            url=POLLING_SOURCE_URL,
            data=test_source_data
        )
        # Set schedule interval
        schedule_interval_data = {
            "interval": "@every 5s"
        }
        self.put(
            url=POLLING_SCHEDULE_INTERVAL,
            data=schedule_interval_data,
            expected_status_code=requests.codes.ok
        )
        self.put(
            url=POLLING_AUTOMATIC_DISABLED,
            expected_status_code=requests.codes.ok
        )
        time.sleep(6)
        source_log = self.get(url=POLLING_SOURCE_ALL_LOG_URL)
        assert source_log == []

    def _import_data(self):
        """
        This helper method is used to import test data existing import
        methods in the framework are not used as the source URL is
        different from the rest of the test suite
        """
        test_data = open(TEST_DATA_FILE, 'r')
        requests.post(
            url=TEST_URL_CUSTOM + 'grenml_import/upload/',
            files={'file': test_data},
            headers={'Authorization': 'Bearer ' + TEST_TOKEN},
            verify=False,
        )
        self.poll_then_delete()

    def _wait_until_poll_completes(self, api):
        """
        This helper method checks if the poll batch event is completed
        successfully by verifying the status flag of the batch
        polling job to True. if the value is False then it is
        still running
        """
        flag = True
        while flag:
            response = self.get(url=api)
            if response['status']:
                return response
