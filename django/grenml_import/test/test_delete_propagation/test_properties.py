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
from grenml.models import INSTITUTIONS, LINKS, NODES

import network_topology.models as m

from grenml_import.importer import GRENMLImporter

from .single_topology import DEFAULT_TOPOLOGY_ID, make_grenml_id, make_topology_fixture


@pytest.fixture
def topology_fixture():
    """ Wraps the make_topology_fixture into a pytest fixture. """
    return make_topology_fixture()


GET_METHODS = {
    INSTITUTIONS: GRENMLManager.get_institution,
    LINKS: GRENMLManager.get_link,
    NODES: GRENMLManager.get_node,
}


@pytest.mark.parametrize(
    'property_name, entity, model_class',
    [
        ('institution_property', INSTITUTIONS, m.Institution),
        ('link_property', LINKS, m.Link),
        ('node_property', NODES, m.Node),
    ],
)
@pytest.mark.django_db
def test_property(topology_fixture, property_name, entity, model_class):
    """
    This test checks that a property of a institution, link or node will
    disappear from the server's database when it imports a file in which
    the property doesn't exist.

    The steps in the test are: create an object with a property in the
    database by calling the import function with a GRENML manager (which
    contains the object); delete the property from the object in the
    manager; import again then verify the property is no longer in
    the database.
    """
    # create an object with a property
    manager = topology_fixture['import_manager']
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)
    obj_id = make_grenml_id(DEFAULT_TOPOLOGY_ID, entity, 1)

    # verify the object and property exist
    m.Topology.objects.get()
    db_obj = model_class.objects.get(grenml_id=obj_id)
    assert len(db_obj.properties.all()) > 0

    # delete property from the manager
    get_obj = GET_METHODS[entity]
    grenml_obj = get_obj(manager, id=obj_id)
    grenml_obj.del_property(property_name)

    # import again
    importer.from_grenml_manager(manager)

    # check the property is not in the database
    db_node = model_class.objects.get(grenml_id=obj_id)
    assert len(db_node.properties.all()) == 0
