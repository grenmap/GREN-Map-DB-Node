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
import requests

from constants import EXPORT_GRENML_URL, TEST_TOKEN, XML_HEADER, TEST_TOKEN_EXPORT, \
    IMPORT_GRENML_URL, NODE_DATA_API, LINK_DATA_API, TOPOLOGY_DATA_API
from framework import GrenMapTestingFramework
from .mock_file import MockFile


TEST_HEADER = {'Authorization': 'Bearer ' + TEST_TOKEN}
TEST_HEADER_EXPORT = XML_HEADER
TEST_HEADER_EXPORT["Authorization"] = "Bearer " + TEST_TOKEN_EXPORT
PARENT_TOPOLOGY = 'parent-topology'
CHILD_TOPOLOGY = 'test-topology-1'
NODE_IN_PARENT_TOPOLOGY = 'node-1'
NODE_IN_CHILD_TOPOLOGY = 'node:1'
LINK_IN_PARENT_TOPOLOGY = 'link-1'
LINK_IN_CHILD_TOPOLOGY = 'link:1'
INSTITUTION_IN_PARENT_TOPOLOGY = 'inst-1'
INSTITUTION_IN_CHILD_TOPOLOGY = 'Test-Institution-1'
INSTITUTION = 'institution'
NODE = 'node'
LINK = 'link'
TOPOLOGY = 'topology'


class TestCrossTopologyRelationships(GrenMapTestingFramework):

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestCrossTopologyRelationships)

    @pytest.fixture(autouse=True)
    def before_each(self):
        """
        sets up testing database for exports and imports.
        Imports the contents of test_import_grenml_base.xml as the
        main/root Topology.
        Adds the contents of test_delete_propagation_full_data.xml
        as a child Topology of the above.
        """
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')
        self.create_import_token()
        self.create_grenml_export_token()
        self.import_xml_file_with_import_type_and_topology_name(
            'test_import_grenml_base.xml'
        )
        topology_details = self.get_topology_details(PARENT_TOPOLOGY)
        self.import_xml_file_with_import_type_and_topology_name(
            'test_delete_propagation_full_data.xml',
            topology_details[0]['pk'],
        )

    def test_link_has_endpoint_node_in_same_topology(self):
        """
        Verify link has an endpoint node in the same topology,
        and it is exportable.  This is a sort of "control" case.
        """
        self._verify_element_before_export_and_after_import(
            NODE_IN_PARENT_TOPOLOGY,
            NODE,
        )

    def test_link_has_endpoint_node_in_parent_topology(self):
        """
        link in a child topology having an endpoint
        node in parent topology
        """
        # The element node:1 is part of child topology so a patch
        # request is sent to change it as part of parent.
        endpoint_node = self.get_node_details(NODE_IN_CHILD_TOPOLOGY)[0]
        topology_details = self.get_topology_details(PARENT_TOPOLOGY)[0]

        # change topology of the end point node from child to parent
        self.patch(
            url=f"{NODE_DATA_API}{str(endpoint_node['pk'])}/",
            auth=True,
            data={'topologies': [topology_details['pk']]},
        )

        endpoint_node_after_change = \
            self.get_node_details(NODE_IN_CHILD_TOPOLOGY)[0]
        assert len(endpoint_node_after_change['topologies']) == 1
        assert endpoint_node_after_change['topologies'][0]['grenml_id'] != \
            endpoint_node['topologies'][0]['grenml_id']
        self._verify_element_before_export_and_after_import(
            LINK_IN_CHILD_TOPOLOGY,
            LINK,
        )

    def test_link_has_endpoint_node_in_child_topology(self):
        """
        link in a parent topology having an endpoint node
        in child topology
        """
        # The element node-1 is part of parent topology so a patch
        # request is sent to change to be in child topology.
        endpoint_node = self.get_node_details(NODE_IN_PARENT_TOPOLOGY)[0]
        topology_details = self.get_topology_details(CHILD_TOPOLOGY)[0]

        self.patch(
            url=f"{NODE_DATA_API}{str(endpoint_node['pk'])}/",
            auth=True,
            data={'topologies': [topology_details['pk']]},
        )

        endpoint_node_after_change = \
            self.get_node_details(NODE_IN_PARENT_TOPOLOGY)[0]
        assert len(endpoint_node_after_change['topologies']) == 1
        assert endpoint_node_after_change['topologies'][0]['grenml_id'] != \
            endpoint_node['topologies'][0]['grenml_id']
        self._verify_element_before_export_and_after_import(
            LINK_IN_PARENT_TOPOLOGY,
            LINK
        )

    def test_link_has_endpoint_node_in_unrelated_topology(self):
        """
        link in the main topology having an endpoint node in
        unrelated root level topology
        """
        self._make_topologies_unrelated()
        # The element node-1 is part of parent topology so a patch
        # request is sent to change to be an unrelated topology.
        endpoint_node = self.get_node_details(NODE_IN_PARENT_TOPOLOGY)[0]
        child_topology_details = self.get_topology_details(CHILD_TOPOLOGY)[0]

        self.patch(
            url=f"{NODE_DATA_API}{str(endpoint_node['pk'])}/",
            auth=True,
            data={'topologies': [child_topology_details['pk']]},
        )

        endpoint_node_after_change = \
            self.get_node_details(NODE_IN_PARENT_TOPOLOGY)[0]
        assert len(endpoint_node_after_change['topologies']) == 1
        assert endpoint_node_after_change['topologies'][0]['grenml_id'] != \
            endpoint_node['topologies'][0]['grenml_id']
        self._verify_element_before_export_and_after_import(
            LINK_IN_PARENT_TOPOLOGY,
            LINK
        )

    def test_node_has_owner_in_parent_topology(self):
        """
        Node in child topology having owner institution
        in parent topology
        """
        node_child_topology = self.get_node_details(NODE_IN_CHILD_TOPOLOGY)[0]
        inst_in_parent = self.get_institution_details(INSTITUTION_IN_PARENT_TOPOLOGY)[0]
        inst_in_child = self.get_institution_details(INSTITUTION_IN_CHILD_TOPOLOGY)[0]
        self.patch(
            url=f"{NODE_DATA_API}{str(node_child_topology['pk'])}/",
            auth=True,
            data={
                'owners': [
                    inst_in_parent['pk'],
                    # Because the GRENML library enforces ownership
                    # by the containing Topology's primary owner, this
                    # will end up in there, so let's expect it.
                    inst_in_child['pk'],
                ]
            }
        )
        node_after_owner_change = self.get_node_details(NODE_IN_CHILD_TOPOLOGY)[0]
        assert len(node_after_owner_change['owners']) == 2
        self._verify_element_before_export_and_after_import(
            NODE_IN_CHILD_TOPOLOGY,
            NODE
        )

    def test_link_has_owner_in_child_topology(self):
        """
        Link in parent topology having owner institution
        in child topology
        """
        link_parent_topology = self.get_link_details(LINK_IN_PARENT_TOPOLOGY)[0]
        inst_in_child = self.get_institution_details(INSTITUTION_IN_CHILD_TOPOLOGY)[0]
        inst_in_parent = self.get_institution_details(INSTITUTION_IN_PARENT_TOPOLOGY)[0]
        self.patch(
            url=f"{LINK_DATA_API}{str(link_parent_topology['pk'])}/",
            auth=True,
            data={
                'owners': [
                    inst_in_child['pk'],
                    # Because the GRENML library enforces ownership
                    # by the containing Topology's primary owner, this
                    # will end up in there, so let's expect it.
                    inst_in_parent['pk'],
                ]
            }
        )
        link_after_owner_change = self.get_link_details(LINK_IN_PARENT_TOPOLOGY)[0]
        assert len(link_after_owner_change['owners']) == 2
        new_owners = [inst['grenml_id'] for inst in link_after_owner_change['owners']]
        assert set(new_owners) == {
            inst_in_child['grenml_id'],
            inst_in_parent['grenml_id']
        }
        self._verify_element_before_export_and_after_import(
            LINK_IN_PARENT_TOPOLOGY,
            LINK
        )

    def test_node_has_owner_in_unrelated_topology(self):
        """
        Node in main topology having owner institution in
        unrelated topology
        """
        self._make_topologies_unrelated()
        node_parent_topology = self.get_node_details(NODE_IN_PARENT_TOPOLOGY)[0]
        inst_in_child = self.get_institution_details(INSTITUTION_IN_CHILD_TOPOLOGY)[0]
        inst_in_parent = self.get_institution_details(INSTITUTION_IN_PARENT_TOPOLOGY)[0]
        self.patch(
            url=f"{NODE_DATA_API}{str(node_parent_topology['pk'])}/",
            auth=True,
            data={
                'owners': [
                    inst_in_child['pk'],
                    # Because the GRENML library enforces ownership
                    # by the containing Topology's primary owner, this
                    # will end up in there, so let's expect it.
                    inst_in_parent['pk'],
                ]
            }
        )
        node_after_owner_change = self.get_node_details(NODE_IN_PARENT_TOPOLOGY)[0]
        assert len(node_after_owner_change['owners']) == 2
        new_owners = [inst['grenml_id'] for inst in node_after_owner_change['owners']]
        assert set(new_owners) == {
            inst_in_child['grenml_id'],
            inst_in_parent['grenml_id']
        }
        self._verify_element_before_export_and_after_import(
            NODE_IN_PARENT_TOPOLOGY,
            NODE
        )

    def test_topology_has_owner_in_parent(self):
        """
        Child topology having owner institution in parent topology
        """
        child_topology = self.get_topology_details(CHILD_TOPOLOGY)[0]
        inst_in_parent = self.get_institution_details(INSTITUTION_IN_PARENT_TOPOLOGY)[0]
        self.patch(
            url=f"{TOPOLOGY_DATA_API}{str(child_topology['pk'])}/",
            auth=True,
            data={
                'owner': inst_in_parent['pk'],
            }
        )
        # Refresh these objects after the change
        inst_in_parent = self.get_institution_details(INSTITUTION_IN_PARENT_TOPOLOGY)[0]
        child_topology = self.get_topology_details(CHILD_TOPOLOGY)[0]
        assert child_topology['owner'] == inst_in_parent['pk']
        assert len(inst_in_parent['topologies']) == 1
        assert inst_in_parent['topologies'][0]['pk'] != child_topology['pk']
        self._verify_element_before_export_and_after_import(
            CHILD_TOPOLOGY,
            TOPOLOGY
        )

    def test_topology_has_owner_in_child(self):
        """
        Parent topology having owner institution in child topology
        """
        parent_topology = self.get_topology_details(PARENT_TOPOLOGY)[0]
        inst_in_child = self.get_institution_details(INSTITUTION_IN_CHILD_TOPOLOGY)[0]
        self.patch(
            url=f"{TOPOLOGY_DATA_API}{str(parent_topology['pk'])}/",
            auth=True,
            data={
                'owner': inst_in_child['pk'],
            }
        )
        # Refresh these objects after the change
        inst_in_child = self.get_institution_details(INSTITUTION_IN_CHILD_TOPOLOGY)[0]
        parent_topology = self.get_topology_details(PARENT_TOPOLOGY)[0]
        assert parent_topology['owner'] == inst_in_child['pk']
        assert len(inst_in_child['topologies']) == 1
        assert inst_in_child['topologies'][0]['pk'] != parent_topology['pk']
        self._verify_element_before_export_and_after_import(
            PARENT_TOPOLOGY,
            TOPOLOGY
        )

    def test_topology_has_owner_in_unrelated_topology(self):
        """
        Main topology having owner institution in unrelated
        root level topology
        """
        parent_topology = self.get_topology_details(PARENT_TOPOLOGY)[0]
        inst_in_child = self.get_institution_details(INSTITUTION_IN_CHILD_TOPOLOGY)[0]
        self._make_topologies_unrelated()
        self.patch(
            url=f"{TOPOLOGY_DATA_API}{str(parent_topology['pk'])}/",
            auth=True,
            data={
                'owner': inst_in_child['pk'],
            }
        )
        parent_topology = self.get_topology_details(PARENT_TOPOLOGY)[0]
        inst_in_unrelated = self.get_institution_details(INSTITUTION_IN_CHILD_TOPOLOGY)[0]
        assert parent_topology['owner'] == inst_in_unrelated['pk']
        assert len(inst_in_unrelated['topologies']) == 1
        assert inst_in_unrelated['topologies'][0]['pk'] != parent_topology['pk']
        self._verify_element_before_export_and_after_import(
            PARENT_TOPOLOGY,
            TOPOLOGY
        )

    def test_multiple_import_export_cycles_converge_in_behaviour(self):
        """
        test data consistency over multiple import export cycles for
        the same data this current version of the test does not verify
        the entire DB but checks individual elements from the DB
        via API.
        """
        topology_details = self.get_topology_details(PARENT_TOPOLOGY)
        self.import_xml_file_with_import_type_and_topology_name(
            'test_cross_topologies_full_data.xml',
            topology_details[0]['pk'],
        )
        self.import_xml_file_with_import_type_and_topology_name(
            'test_cross_topologies_secondary_data.xml',
        )

        # Export and import cycle #1
        self._export_and_import_cycle()
        # Export and import cycle #2
        self._export_and_import_cycle()
        # Export and import cycle #3
        self._export_and_import_cycle()
        # By now it should have converged!
        inst_in_topo_3_initial = self._get_element_details(
            'Test-Topo-3-Inst:1',
            INSTITUTION,
        )
        inst_in_parent_initial = self._get_element_details(
            INSTITUTION_IN_PARENT_TOPOLOGY,
            INSTITUTION,
        )
        node_in_child_initial = self._get_element_details(
            NODE_IN_CHILD_TOPOLOGY,
            NODE,
        )
        link_in_child_initial = self._get_element_details(
            LINK_IN_CHILD_TOPOLOGY,
            LINK,
        )
        parent_topo_initial = self._get_element_details(
            PARENT_TOPOLOGY,
            TOPOLOGY,
        )

        # Export and import cycle #4
        self._export_and_import_cycle()
        inst_in_topo_3_final = self._get_element_details(
            'Test-Topo-3-Inst:1',
            INSTITUTION,
        )
        inst_in_parent_final = self._get_element_details(
            INSTITUTION_IN_PARENT_TOPOLOGY,
            INSTITUTION,
        )
        node_in_child_final = self._get_element_details(
            NODE_IN_CHILD_TOPOLOGY,
            NODE,
        )
        link_in_child_final = self._get_element_details(
            LINK_IN_CHILD_TOPOLOGY,
            LINK,
        )
        parent_topo_final = self._get_element_details(
            PARENT_TOPOLOGY,
            TOPOLOGY,
        )

        self._compare_except_primary_keys(inst_in_topo_3_initial, inst_in_topo_3_final)
        self._compare_except_primary_keys(inst_in_parent_initial, inst_in_parent_final)
        self._compare_except_primary_keys(node_in_child_initial, node_in_child_final)
        self._compare_except_primary_keys(link_in_child_initial, link_in_child_final)
        self._compare_except_primary_keys(parent_topo_initial, parent_topo_final)

    def _make_topologies_unrelated(self):
        """
        This helper method makes the 2 test topologies at the root level
        """
        topology_details = self.get_topology_details(CHILD_TOPOLOGY)
        self.patch(
            url=f"{TOPOLOGY_DATA_API}{str(topology_details[0]['pk'])}/",
            auth=True,
            data={
                'parent': None,
            }
        )

    def _verify_element_before_export_and_after_import(
            self,
            grenml_id,
            element,
    ):
        """
        this method checks the element remains the same after an
        export and import into the DB
        """
        element_data_1 = self._get_element_details(
            grenml_id=grenml_id,
            element=element,
        )
        self._export_and_import_cycle()
        element_data_2 = self._get_element_details(
            grenml_id=grenml_id,
            element=element,
        )
        self._compare_except_primary_keys(element_data_1, element_data_2)

    def _delete_all_topologies(self):
        self.delete(
            url=TOPOLOGY_DATA_API + 'delete/',
            auth=True,
        )

    def _get_element_details(self, grenml_id, element):
        if element == LINK:
            element_data = self.get_link_details(grenml_id)
        elif element == NODE:
            element_data = self.get_node_details(grenml_id)
        elif element == TOPOLOGY:
            element_data = self.get_topology_details(grenml_id)
        else:
            element_data = self.get_institution_details(grenml_id)
        return element_data

    def _export_and_import_cycle(self):
        """
        this method performs a grenml export and then imports the same
        grenml data
        """
        xml_data = self.get(
            url=EXPORT_GRENML_URL,
            headers=TEST_HEADER_EXPORT
        )

        self._delete_all_topologies()

        mock_file_to_upload = MockFile('import.xml', xml_data)
        response = requests.post(
            url=IMPORT_GRENML_URL,
            files={'file': mock_file_to_upload},
            headers=TEST_HEADER,
            verify=False,
        )
        assert 200 <= response.status_code < 300

        topologies = []
        while not topologies:
            topologies = self.get(
                url=TOPOLOGY_DATA_API,
                auth=True,
            )

        return xml_data

    def _compare_except_primary_keys(self, list_a, list_b):
        """
        When comparing before-and-after lists of Topologies,
        where a recent import of recently exported data
        is meant to resemble its prior self, the primary keys
        will of course differ as they get auto-incremented.
        Remove all integers and replace with 0.  This may
        obliterate any non-primary-key integers, but it may
        suffice for simple basic testing regardless.
        If it is desired to confirm particular items, best to
        check them explicitly.
        """
        def _sort_func(item):
            """
            Returns a key to sort lists where list items may be
            dictionaries of common models, but also may not be.
            Prefers 'grenml_id' key, then 'name' key.
            (For uncommon models without those, it returns 0,
            so order may be nondeterministic.)
            """
            if not item:
                return item
            if isinstance(item, dict):
                if item.get('grenml_id', False):
                    return item['grenml_id']
                elif item.get('name', False):
                    return item['name']
                else:
                    return 0

        def _sanitize_for_easy_simple_comparison(input_value):
            """
            Recursive function to identify integers in lists and
            dictionaries and replace them with zeroes.  Also
            sorts lists for easier comparison, in case they are
            randomly out of order.
            """
            # Lists (sets)
            if isinstance(input_value, list):
                new_list = []
                for item in input_value:
                    if isinstance(item, int):
                        new_list.append(0)
                    elif isinstance(item, dict) or isinstance(item, list):
                        new_list.append(_sanitize_for_easy_simple_comparison(item))
                    else:
                        new_list.append(item)
                return sorted(new_list, key=_sort_func)
            # Dictionaries
            elif isinstance(input_value, dict):
                new_dict = {}
                for key, val in input_value.items():
                    if isinstance(val, int):
                        new_dict[key] = 0
                    elif isinstance(val, dict) or isinstance(val, list):
                        new_dict[key] = _sanitize_for_easy_simple_comparison(val)
                    else:
                        new_dict[key] = val
                return new_dict
            # Single items
            else:
                if isinstance(input_value, int):
                    return 0
                else:
                    return input_value

        sanitized_list_a = _sanitize_for_easy_simple_comparison(list_a)
        sanitized_list_b = _sanitize_for_easy_simple_comparison(list_b)
        assert sanitized_list_b == sanitized_list_a, \
            str(sanitized_list_a) + '\n' + str(sanitized_list_b)
