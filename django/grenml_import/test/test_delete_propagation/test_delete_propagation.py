"""
Copyright 2022 GRENMap Authors

SPDX-License-Identifier: Apache License 2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import pytest

from grenml.managers import GRENMLManager
from grenml.models import INSTITUTIONS, LINKS, NODES, TOPOLOGIES

from .single_topology import TEST_CASES as SINGLE_TOPOLOGY
from .shared_object import TEST_CASES as SHARED_OBJECT
from .shared_object_with_properties import TEST_CASES as SHARED_OBJECT_WITH_PROPERTIES

from grenml_import.importer import GRENMLImporter


def delete_topologies(manager, **match_kwargs):
    """
    Removes child topologies from the topology contained
    in a GRENML manager.
    """
    topologies = manager.topology.get_elements(TOPOLOGIES, **match_kwargs)
    manager.topology.delete_elements(TOPOLOGIES, topologies)


DELETE_METHODS = {
    INSTITUTIONS: GRENMLManager.delete_institutions,
    LINKS: GRENMLManager.delete_links,
    NODES: GRENMLManager.delete_nodes,
    TOPOLOGIES: delete_topologies,
}


@pytest.mark.parametrize(
    'fixture, delete_list, query_list, assertion',
    SINGLE_TOPOLOGY + SHARED_OBJECT + SHARED_OBJECT_WITH_PROPERTIES,
)
@pytest.mark.django_db
def test_delete_propagation(fixture, delete_list, query_list, assertion):
    """
    This executes delete propagation tests.

    A test case consists of three steps: (1) populate the database
    by importing a file into the server, (2) delete a few objects
    from the file then import it again, (3) verify the database is in
    the expected state.

    Importing a file is in fact simulated with GRENML managers and
    the function GRENMLImporter.from_grenml_manager. The simulated
    import is equal to the actual import that happens with polling
    and through the admin page, except for the parsing of the XML
    file or Excel spreadsheet.

    The fixture parameter will be a dictionary with two keys:
    - import_manager is the GRENML manager that the function uses to
    initialize the database;
    - delete manager is the GRENML manager from which the function
    deletes objects.

    A GRENML manager keeps a single topology. A test case that checks
    deletion of an item in a child topology needs two managers:
    the one that holds the root topology to be imported and another
    with the child topology from which the item will be deleted.

    The items in delete_list are dictionaries with three keys:
    - entity is one of the four values imported from grenml.models
    (INSTITUTIONS, LINKS, NODES, TOPOLOGIES);
    - id is the identifier of an object that the function deletes
    from the fixture;
    - model_class is one of the Django models in the network_topology
    plugin.

    The assertion parameter receives a function that will pass or fail
    the test depending on the contents of the database.

    The test function (the one we are describing in this docstring)
    passes the query_list argument to the assertion function.

    The type of the items in query_list changes according to
    the assertion.
    """
    # create records in database
    import_manager = fixture['import_manager']
    importer = GRENMLImporter()
    importer.from_grenml_manager(import_manager)

    # verify objects exist
    for item in delete_list:
        model_class = item['model_class']
        assert model_class.objects.get(grenml_id=item['id'])

    # delete selected objects from the manager
    delete_manager = fixture['delete_manager']
    for item in delete_list:
        delete_item_in_manager = DELETE_METHODS[item['entity']]
        item_id = item['id']
        delete_item_in_manager(delete_manager, id__in=[item_id])

    # import again after deleting objects
    importer.from_grenml_manager(import_manager)

    # check the final contents of the database
    assertion(model_class, query_list or delete_list)
