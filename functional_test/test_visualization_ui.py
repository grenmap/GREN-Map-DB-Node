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

Synopsis: Functional tests of the external topology element support
    supplied when exported and imported, for elements in related
    and unrelated topologies.
"""
import pytest

from framework import GrenMapUITestingFramework
from constants import TEST_SITE_URL
from selenium_testcase import BY_XPATH, BY_CLASS

TEST_DATA_FILE = 'test_import_grenml_base.xml'
CONTINUE_BUTTON_ID = 'idpSelectSelectButton'
INPUT_FIELD_ID = 'idpSelectInput'
TEST_IDP_VALUE = 'https://idp.example.org/idp/shibboleth'
NODE_LINK_ELEMENT_CLASS = "leaflet-interactive"
NODE_DRAWER_XPATH = "//mat-toolbar[contains(text(),'Node Details')]"
LINK_DRAWER_XPATH = "//mat-toolbar[contains(text(),'Link Details')]"


class TestUI(GrenMapUITestingFramework):
    """
    these tests are performed without login as map is expected to be
    embedded to external sites.
    """

    @pytest.fixture(autouse=True, scope="class")
    def before_each(self):
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')
        self.import_xml_file(TEST_DATA_FILE)

    def test_01_node_info_drawer_visible_in_ui(self):
        """
        Test the info drawer on the right is visible in the UI
        when a node is clicked. this has to be possible without login
        note: of the 3 elements received first 2 are nodes and the
        last one is a link
        """
        self.get_page(TEST_SITE_URL)
        self.wait_for_element_to_be_clickable(
            NODE_LINK_ELEMENT_CLASS,
            BY_CLASS
        )
        elements = self.find_elements(NODE_LINK_ELEMENT_CLASS, BY_CLASS)
        elements[0].click()
        node_drawer = self.find_element(NODE_DRAWER_XPATH, BY_XPATH)
        assert node_drawer is not None

    def test_02_link_info_drawer_visible_in_ui(self):
        """
        Test the info drawer on the right is visible in the UI when a
        link is clicked without login.
        note: of the 3 elements received first 2 are nodes and the
        last one is a link
        """
        self.get_page(TEST_SITE_URL)
        self.wait_for_element_to_be_clickable(
            NODE_LINK_ELEMENT_CLASS,
            BY_CLASS
        )
        elements = self.find_elements(NODE_LINK_ELEMENT_CLASS, BY_CLASS)
        elements[2].click()
        link_drawer = self.find_element(LINK_DRAWER_XPATH, BY_XPATH)
        assert link_drawer is not None
