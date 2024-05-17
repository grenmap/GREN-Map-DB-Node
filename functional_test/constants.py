"""
Synopsis: This file contains constants for API testing.

"""

import os

TEST_TOKEN = 'toketest1234'

TEST_TOKEN_EXPORT = "1213124145315"

TARGET_SERVER_ADDRESS = str(os.environ['TEST_DOCKER_NAME']).lower()

TARGET_SERVER_PORT = str(os.environ['TEST_DOCKER_PORT']).lower()

TEST_USER_NAME = os.environ['TEST_USER_NAME']

TEST_USER_PASSWORD = os.environ['TEST_USER_PASSWORD']

TEST_USER_DATA = {
    "username": TEST_USER_NAME,
    "password": TEST_USER_PASSWORD,
    "email": "grenmapadmin@myisp.com"
}

TEST_SITE_URL = f'https://{TARGET_SERVER_ADDRESS}:{TARGET_SERVER_PORT}/'

TEST_NODE_NAME_LIST = ['websp1', 'websp2']

STATUS_URL = TEST_SITE_URL + 'status/'

POLLING_SOURCE_URL = TEST_SITE_URL + 'polling/test/sources/'

POLLING_TRIGGER_URL = TEST_SITE_URL + 'polling/test/trigger/source/'

POLLING_SOURCE_LOG_URL = TEST_SITE_URL + 'polling/test/logs/sources/'

POLLING_SOURCE_ALL_LOG_URL = POLLING_SOURCE_LOG_URL + 'all/'

POLLING_BATCH_TRIGGER_URL = TEST_SITE_URL + 'polling/trigger/'

POLLING_BATCH_LOG_URL = TEST_SITE_URL + 'polling/test/logs/batches/'

FLUSH_DB_URL = TEST_SITE_URL + 'test/flushdb/'

LOAD_FIXTURE_URL = TEST_SITE_URL + 'test/loadfixture/'

CREATE_SUPER_USER = TEST_SITE_URL + 'test/create_superuser/'

CREATE_TEST_TOKEN_URL = TEST_SITE_URL + 'test/token/'

POLLING_AUTOMATIC_CONFIG = TEST_SITE_URL + 'polling/test/enabled/'

POLLING_AUTOMATIC_ENABLED = POLLING_AUTOMATIC_CONFIG + '1/'

POLLING_AUTOMATIC_DISABLED = POLLING_AUTOMATIC_CONFIG + '0/'

POLLING_SCHEDULE_INTERVAL = TEST_SITE_URL + 'polling/test/interval/'

POLL_COLLECTION_URL = TEST_SITE_URL + 'grenml_export/'

JSON_HEADER = {'Content-Type': 'application/json'}

XML_HEADER = {'Content-Type': 'application/xml'}

TEST_HEADER = {'Authorization': 'Bearer ' + TEST_TOKEN}

DEFAULT_SCHEDULE_INTERVAL = {"interval": "R */4 * * *"}

DEFAULT_INTERVAL = 5

DEFAULT_TIMEOUT = 300

VISUALIZATION_API_URL = TEST_SITE_URL + 'visualization/graphql/'

VISUALIZATION_SETTING_URL = TEST_SITE_URL + 'visualization/test/enabled_setting/'

DISABLE_VISUALIZATION_SETTING = VISUALIZATION_SETTING_URL + '0/'

ENABLE_VISUALIZATION_SETTING = VISUALIZATION_SETTING_URL + '1/'

VISUALIZATION_ORIGIN_URL = TEST_SITE_URL + 'visualization/test/allow_origin/'

IMPORT_GRENML_POLL_ATTEMPTS = 10

IMPORT_GRENML_POLL_SLEEP_SECONDS = 1

IMPORT_GRENML_URL = TEST_SITE_URL + 'grenml_import/upload/'

IMPORT_GRENML_STATUS_CODE_PENDING = 0

IMPORT_GRENML_URL_POLL_DELETE = TEST_SITE_URL + 'grenml_import/test/'

IMPORT_GRENML_URL_TEST = TEST_SITE_URL + 'grenml_import/test/upload/'

EXPORT_GRENML_URL = TEST_SITE_URL + 'grenml_export/test'

NODE_DATA_API = TEST_SITE_URL + 'network_topology/test/nodes/'

LINK_DATA_API = TEST_SITE_URL + 'network_topology/test/links/'

INSTITUTION_DATA_API = TEST_SITE_URL + 'network_topology/test/institutions/'

TOPOLOGY_DATA_API = TEST_SITE_URL + 'network_topology/test/topologies/'

RULE_TEST_API_URL = TEST_SITE_URL + 'collation/test/rules/'

RULESET_TEST_API_URL = TEST_SITE_URL + 'collation/test/rulesets/'

IMPORT_RULESETS_API_URL = TEST_SITE_URL + 'collation/test/import_rulesets'

EXPORT_RULESETS_API_URL = TEST_SITE_URL + 'collation/test/export_rulesets'

RESTORE_DEFAULT_ID_COLLISION_RULES = \
    TEST_SITE_URL + '/collation/test/rulesets/restore_default_collision_resolution/'

ACTION_TYPE_LIST = TEST_SITE_URL + 'collation/test/action_types/'

MATCH_TYPE_LIST = TEST_SITE_URL + 'collation/test/match_types/'

ACTION_API_URL = TEST_SITE_URL + 'collation/test/actions/'

ACTION_API_INFO_RUL = TEST_SITE_URL + 'collation/test/action_infos/'

MATCH_CRITERIA_API_URL = TEST_SITE_URL + 'collation/test/match_criteria/'

MATCH_INFO_API_URL = TEST_SITE_URL + 'collation/test/match_infos/'

TEST_DEFAULT_ROOT_TOPOLOGY_ID = '9b6d8d62-5b80-442d-b0b8-37f2bbc96b03'

TEST_FILE_FOLDER = '/home/grenmap_functional_test/test_files/'
