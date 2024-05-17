"""
This file contains tests for ID collision resolution function
"""

from framework import GrenMapTestingFramework
import pytest
from constants import (
    RESTORE_DEFAULT_ID_COLLISION_RULES,
    TEST_TOKEN,
    TEST_TOKEN_EXPORT,
    XML_HEADER
)

TEST_HEADER = {'Authorization': 'Bearer ' + TEST_TOKEN}
TEST_HEADER_EXPORT = XML_HEADER
TEST_HEADER_EXPORT["Authorization"] = "Bearer " + TEST_TOKEN_EXPORT
NODE_ID = 'node-1'
LINK_ID = 'link-1'
INSTITUTION_ID = 'inst-2'
NODE = 'node'
LINK = 'link'
INSTITUTION = 'institution'
IMPORT_BASE_XML = 'test_import_grenml_base.xml'
IMPORT_BASE_TOPOLOGY_GRENMLID = 'parent-topology'
PARENT_TOPOLOGY_XML = 'test_import_grenml.xml'
PARENT_TOPOLOGY_GRENMLID = 'topology-1'
PK = 'pk'


class TestIDCollision(GrenMapTestingFramework):

    @classmethod
    def setup_class(cls):
        """
        Check test docker server is connected before
        other tests
        """
        cls.check_test_server_status(TestIDCollision)

    @pytest.fixture(autouse=True)
    def before_each(self):
        self.flush_db()
        self.add_super_user()
        self.load_fixture('test_app_configurations.json')
        self.create_import_token()
        # create default catch-all ruleset
        self.post(
            url=RESTORE_DEFAULT_ID_COLLISION_RULES,
            auth=True,
            expected_status_code=200
        )

    def test_id_collision_of_node_after_import_parent_topology(self):
        """
        This test verifies that when multiple imports are performed then
        the latest version of the node is retained by the DB. this test
        checks if the primary key value is incremented after import
        """
        # 1st import
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=NODE,
            grenml_id=NODE_ID
        )
        # 2nd import
        final_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=NODE,
            grenml_id=NODE_ID
        )
        assert initial_value[0][PK] < final_value[0][PK]

    def test_id_collision_of_link_after_import_parent_topology(self):
        """
        This test verifies that when multiple imports are performed then
        the latest version of the link is retained by the DB. this test
        checks if the primary key value is incremented after import
        """
        # 1st import
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=LINK,
            grenml_id=LINK_ID
        )
        # 2nd import
        final_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=LINK,
            grenml_id=LINK_ID
        )
        assert initial_value[0][PK] < final_value[0][PK]

    def test_id_collision_of_institution_after_import_parent_topology(self):
        """
        This test verifies that when multiple imports are performed
        then the latest version of the institution is retained by DB.
        this test checks if the primary key value is
        incremented after import
        """
        # 1st import
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=INSTITUTION,
            grenml_id=INSTITUTION_ID
        )
        # 2nd import
        final_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=INSTITUTION,
            grenml_id=INSTITUTION_ID
        )
        assert initial_value[0][PK] < final_value[0][PK]

    def test_id_collision_of_node_after_import_child_topology(self):
        """
        This test verifies that when multiple imports are performed to
        child topology then the latest version of the node is
        retained by the DB. this test checks if the primary key value
        is incremented after import
        """
        # parent topology import
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=PARENT_TOPOLOGY_XML,
        )
        topology_details = self.get_topology_details(PARENT_TOPOLOGY_GRENMLID)
        # child import #1
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=NODE,
            grenml_id=NODE_ID,
            parent_topology_id=topology_details[0][PK]
        )
        # child import #2
        final_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=NODE,
            grenml_id=NODE_ID,
            parent_topology_id=topology_details[0][PK]
        )
        assert initial_value[0][PK] < final_value[0][PK]

    def test_id_collision_of_link_after_import_child_topology(self):
        """
        This test verifies that when multiple imports are performed to
        child topology then the latest version of the link is
        retained by the DB. this test checks if the primary key
        value is incremented after import
        """

        # parent topology import
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=PARENT_TOPOLOGY_XML,
        )
        topology_details = self.get_topology_details(PARENT_TOPOLOGY_GRENMLID)
        # child import #1
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=LINK,
            grenml_id=LINK_ID,
            parent_topology_id=topology_details[0][PK]
        )
        # child import #2
        final_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=LINK,
            grenml_id=LINK_ID,
            parent_topology_id=topology_details[0][PK]
        )
        assert initial_value[0][PK] < final_value[0][PK]

    def test_id_collision_of_institution_after_import_child_topology(self):
        """
        This test verifies that when multiple imports are performed to
        child topology then the latest version of the institution is
        retained by the DB. this test checks if the primary key value
        is incremented after import
        """

        # parent topology import
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=PARENT_TOPOLOGY_XML,
        )
        topology_details = self.get_topology_details(PARENT_TOPOLOGY_GRENMLID)
        # child import #1
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=INSTITUTION,
            grenml_id=INSTITUTION_ID,
            parent_topology_id=topology_details[0][PK]
        )
        # child import #2
        final_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=INSTITUTION,
            grenml_id=INSTITUTION_ID,
            parent_topology_id=topology_details[0][PK]
        )
        assert initial_value[0][PK] < final_value[0][PK]

    def test_id_collision_of_duplicate_ids_in_same_topology(self):
        """
        This test verifies that importing a topology in xml file with
        node and link having duplicate ID in the same topology
        should pass at grenml import
        """
        test_grenml_name = 'test_import_grenml_duplicate_ids.xml'
        node_details = self.import_and_retrieve_element_list(
            xml_file=test_grenml_name,
            element_type=NODE,
            grenml_id=NODE_ID,
        )
        link_details = self.get_link_details(NODE_ID)
        assert node_details[0]['grenml_id'] == link_details[0]['grenml_id'], \
            'Failed. Got node: %s. link: %s' % (node_details, link_details)

    def test_id_collision_of_node_id_and_link_id_in_same_topology(self):
        """
        Import a topology with Node ID A, and import into the same
        topology with a link ID A should allow duplication and
        creation of the Link.
        """
        # 1st import
        nodes_list = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=NODE,
            grenml_id=NODE_ID,
        )
        # 2nd import
        link_list = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_duplicate_node_link_id.xml',
            element_type=LINK,
            grenml_id=NODE_ID
        )
        assert nodes_list[0]['grenml_id'] == link_list[0]['grenml_id'], \
            'Failed. Got node: %s. link: %s' % (nodes_list, link_list)

    def test_id_collision_of_node_id_and_institution_id_in_same_topology(self):
        """
        import a topology with Node ID A, and import into the same
        topology with an institution ID A should allow duplication
        and creation of the institution.
        """
        # 1st import
        nodes_list = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=NODE,
            grenml_id=NODE_ID,
        )
        # 2nd import
        institution_list = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_duplicate_node_institution_id.xml',
            element_type=INSTITUTION,
            grenml_id=NODE_ID
        )

        assert nodes_list[0]['grenml_id'] == institution_list[0]['grenml_id'], \
            'Failed. Got node: %s. institution: %s' % (
                nodes_list, institution_list)

    def test_id_collision_of_link_id_and_institution_id_in_same_topology(self):
        """
        Import a topology with link ID A, and import into the same
        topology with an institution ID A should allow duplication and
        creation of the institution.
        """
        # 1st import
        link_list = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=LINK,
            grenml_id=LINK_ID,
        )
        # 2nd import
        institution_list = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_duplicate_link_institution_id.xml',
            element_type=INSTITUTION,
            grenml_id=LINK_ID
        )

        assert link_list[0]['grenml_id'] == institution_list[0]['grenml_id'], \
            'Failed. Got link: %s. institution: %s' % (
                link_list, institution_list)

    def test_id_collision_of_duplicate_node_ids_in_two_topologies(self):
        """
        Import a topology with node ID A, and importing into a child
        topology with the same node ID A should be allowed. Verify
        the node in first topology has a different name after the merge.
        """
        # 1st import
        nodes_list_import_1 = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=NODE,
            grenml_id=NODE_ID,
        )
        topology_details = self.get_topology_details(
            IMPORT_BASE_TOPOLOGY_GRENMLID)

        assert len(nodes_list_import_1) == 1, \
            'after import 1, node: %s does not exist. Got node: %s' % (
                NODE_ID, nodes_list_import_1)

        # 2nd import as a child
        nodes_list_import_2 = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_base_same_node.xml',
            element_type=NODE,
            grenml_id=NODE_ID,
            parent_topology_id=topology_details[0][PK]
        )
        assert len(nodes_list_import_2) == 1, \
            'after import 2, node: %s does not exist. Got node: %s' % (
                NODE_ID, nodes_list_import_2)
        assert nodes_list_import_1[0]['name'] != nodes_list_import_2[0]['name'], \
            'Failed. Got node: %s. node: %s' % (
                nodes_list_import_1, nodes_list_import_2)

    def test_id_collision_of_node_id_and_link_id_in_two_topologies(self):
        """
        Import a topology with node ID A, and importing into a child
        topology with the same link ID A should
        be allowed.
        """
        # 1st import
        nodes_list_import_1 = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=NODE,
            grenml_id=NODE_ID,
        )
        topology_details = self.get_topology_details(
            IMPORT_BASE_TOPOLOGY_GRENMLID)

        # 2nd import as a child
        link_list_import_2 = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_duplicate_node_link_id.xml',
            element_type=LINK,
            grenml_id=NODE_ID,
            parent_topology_id=topology_details[0][PK]
        )
        assert nodes_list_import_1[0]['grenml_id'] == link_list_import_2[0]['grenml_id'], \
            'Failed. Got node: %s. link: %s' % (
                nodes_list_import_1, link_list_import_2)

    def test_id_collision_of_node_id_and_institution_id_in_two_topologies(self):
        """
        Import a topology with node ID A, and importing into a child
        topology with the same institution ID A should
        be allowed.
        """
        # 1st import
        nodes_list_import_1 = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=NODE,
            grenml_id=NODE_ID,
        )
        topology_details = self.get_topology_details(
            IMPORT_BASE_TOPOLOGY_GRENMLID)

        # 2nd import as a child
        institution_list_import_2 = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_base_same_node_institution_id.xml',
            element_type=INSTITUTION,
            grenml_id=NODE_ID,
            parent_topology_id=topology_details[0][PK]
        )
        assert nodes_list_import_1[0]['grenml_id'] == \
            institution_list_import_2[0]['grenml_id'], \
            'Failed. Got node: %s. institution: %s' \
            % (nodes_list_import_1, institution_list_import_2)

    def test_id_collision_of_link_ids_with_non_match_nodes_in_two_topologies(self):
        """
        Import a topology with link ID A which connects node C and D,
        then import into a child topology with the same link ID A which
        connect to node E and F. The first link name should be updated.
        """
        # 1st import
        link_list_import_1 = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=LINK,
            grenml_id=LINK_ID
        )
        topology_details = self.get_topology_details(
            IMPORT_BASE_TOPOLOGY_GRENMLID)
        # 2nd import should pass
        link_list_import_2 = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_base_same_link.xml',
            element_type=LINK,
            grenml_id=LINK_ID,
            parent_topology_id=topology_details[0][PK]
        )
        assert link_list_import_1[0]['name'] != link_list_import_2[0]['name'], \
            'Failed. Got link: %s. link: %s' % (
                link_list_import_1, link_list_import_2)

    def test_id_collision_of_link_ids_with_matched_nodes_in_two_topologies(self):
        """
        Import a topology with link ID A, and importing into a child
        topology with the same link ID A and
        matched nodes should pass.
        The first link name should be updated.
        """
        # 1st import
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=LINK,
            grenml_id=LINK_ID
        )
        # 2nd import
        final_value = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_base_same_link_matched_nodes.xml',
            element_type=LINK,
            grenml_id=LINK_ID
        )
        assert len(initial_value) == 1, \
            'after import 1, link: %s does not exist. Got link: %s' % (
                LINK_ID, initial_value)

        assert len(final_value) == 1, \
            'after import 2, link: %s does not exist. Got link: %s' % (
                LINK_ID, final_value)

        assert initial_value[0]['name'] != final_value[0]['name'], \
            'Failed. Got link: %s. link: %s' % (initial_value, final_value)

    def test_id_collision_of_link_id_and_node_id_in_two_topologies(self):
        """
        Import a topology with link ID A, and importing into a child
        topology with the same node ID A should be allowed.
        """
        # 1st import
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=LINK,
            grenml_id=LINK_ID
        )
        topology_details = self.get_topology_details(
            IMPORT_BASE_TOPOLOGY_GRENMLID)
        # 2nd import
        final_value = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_base_same_link_node_id.xml',
            element_type=NODE,
            grenml_id=LINK_ID,
            parent_topology_id=topology_details[0][PK]
        )

        assert len(initial_value) == 1, \
            'after import 1, link: %s does not exist. Got link: %s' % (
                LINK_ID, initial_value)

        assert len(final_value) == 1, \
            'after import 2, node: %s does not exist. Got node: %s' % (
                LINK_ID, final_value)

        assert initial_value[0]['grenml_id'] == final_value[0]['grenml_id'], \
            'Failed. Got link: %s. node: %s' % (
                initial_value, final_value)

    def test_id_collision_of_duplicate_institution_ids_in_two_topologies(self):
        """
        Import a topology with institution ID A, and importing into
        a child topology with the same institution ID A should be
        allowed. Verify the institution in first topology has a
        different name after the merge.
        (verify if the latest value is retained)
        """
        # 1st import
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=LINK,
            grenml_id=LINK_ID
        )
        # 2nd import
        final_value = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_base_same_link_node_id.xml',
            element_type=NODE,
            grenml_id=LINK_ID
        )
        assert len(initial_value) == 1, \
            'after import 1, link: %s does not exist. Got link: %s' % (
                LINK_ID, initial_value)

        assert len(final_value) == 1, \
            'after import 2, node: %s does not exist. Got node: %s' % (
                LINK_ID, final_value)

        assert initial_value[0]['grenml_id'] == final_value[0]['grenml_id'], \
            'Failed. Got link: %s. node: %s' % (initial_value, final_value)

    def test_id_collision_of_link_id_and_institution_id_in_two_topologies(self):
        """
        Import a topology with link ID A, and importing into a child
        topology with the same institution ID A should
        be allowed.
        """
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=LINK,
            grenml_id=LINK_ID
        )

        topology_details = self.get_topology_details(
            IMPORT_BASE_TOPOLOGY_GRENMLID)

        # 2nd import
        final_value = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_base_same_link_institution_id.xml',
            element_type=INSTITUTION,
            grenml_id=LINK_ID,
            parent_topology_id=topology_details[0][PK]
        )
        # 1st import
        assert len(initial_value) == 1, \
            'after import 1, link: %s does not exist. Got link: %s' % (
                LINK_ID, initial_value)

        assert len(final_value) == 1, \
            'after import 2, institution: %s does not exist. ' \
            'Got institution: %s' % (LINK_ID, final_value)
        assert initial_value[0]['grenml_id'] == final_value[0]['grenml_id'], \
            'Failed. Got link: %s. institution: %s' % (
                initial_value, final_value)

    def test_id_collision_of_institution_id_and_node_id_in_two_topologies(self):
        """
        Import a topology with institution ID A, and importing into
        a child topology with the same node ID A should be allowed.
        """
        # 1st import
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=INSTITUTION,
            grenml_id=INSTITUTION_ID
        )

        topology_details = self.get_topology_details(
            IMPORT_BASE_TOPOLOGY_GRENMLID)

        # 2nd import
        final_value = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_base_same_institution_node_id.xml',
            element_type=NODE,
            grenml_id=INSTITUTION_ID,
            parent_topology_id=topology_details[0][PK]
        )

        assert len(initial_value) == 1, \
            'after import 1, institution: %s does not exist. ' \
            'Got institution: %s' % (INSTITUTION_ID, initial_value)

        assert len(final_value) == 1, \
            'after import 2, node: %s does not exist. ' \
            'Got node: %s' % (INSTITUTION_ID, final_value)

        assert initial_value[0]['grenml_id'] == final_value[0]['grenml_id'], \
            'Failed. Got institution: %s. node: %s' % (initial_value, final_value)

    def test_id_collision_of_institution_id_and_link_id_in_two_topologies(self):
        """
        Import a topology with institution ID A, and importing into
        a child topology with the same link ID A should be allowed.
        """
        # 1st import
        initial_value = self.import_and_retrieve_element_list(
            xml_file=IMPORT_BASE_XML,
            element_type=INSTITUTION,
            grenml_id=INSTITUTION_ID
        )

        topology_details = self.get_topology_details(
            IMPORT_BASE_TOPOLOGY_GRENMLID)

        # 2nd import
        final_value = self.import_and_retrieve_element_list(
            xml_file='test_import_grenml_base_same_institution_link_id.xml',
            element_type=LINK,
            grenml_id=INSTITUTION_ID,
            parent_topology_id=topology_details[0][PK]
        )
        assert len(initial_value) == 1, \
            'after import 1, institution: %s does not exist. ' \
            'Got institution: %s' % (INSTITUTION_ID, initial_value)

        assert len(final_value) == 1, \
            'after import 2, link: %s does not exist. Got link: %s' % (INSTITUTION_ID, final_value)

        assert initial_value[0]['grenml_id'] == final_value[0]['grenml_id'], \
            'Failed. Got institution: %s. link: %s' % (initial_value, final_value)

    def _retrieve_element_details(self, element_type, grenml_id):
        """
        This helper method retrieves element details depending on
        the type provided
        """

        if element_type == NODE:
            node_list = self.get_node_details(grenml_id)
            return node_list
        elif element_type == LINK:
            link_list = self.get_link_details(grenml_id)
            return link_list
        elif element_type == INSTITUTION:
            institution_list = self.get_institution_details(grenml_id)
            return institution_list

    def import_and_retrieve_element_list(
            self,
            xml_file,
            grenml_id,
            element_type,
            parent_topology_id=None,
    ):
        """
        this helper method imports xml and retrieves from DB the
        details of the element with the provided grenml_id
        """
        self.import_xml_file_with_import_type_and_topology_name(
            test_grenml_name=xml_file,
            topology_id=parent_topology_id,
        )
        element_details_after_import = self._retrieve_element_details(
            element_type, grenml_id)
        assert len(element_details_after_import) == 1, \
            'after import, element: %s does not exist in the list: %s' % (
                grenml_id, element_details_after_import)
        return element_details_after_import
