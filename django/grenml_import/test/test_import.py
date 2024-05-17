"""
Copyright 2023 GRENMap Authors

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

------------------------------------------------------------------------

Synopsis: unit tests for the import procedure.

These are the steps taken by the tests that check the
GRENMLImporter.from_grenml_manager method:

1. Start with a dictionary containing the attributes of a network
element (institution, link or node).
2. Use the dictionary to create the element in a GRENML manager.
3. Pass the manager to the import function; this creates a record in
the database.
4. Run test assertions: the element should exist, the attributes stored
in the database should match those passed to the GRENML manager.
"""

import pytest
import re
from io import BytesIO

from grenml.managers import GRENMLManager
from grenml.models import NODES
from network_topology.models import Institution, Link, Node
from network_topology.test.utils import make_set_of_ids

from grenml_import.importer import GRENMLImporter
from grenml_import.utils.import_exceptions import StreamParseError


def make_grenml_manager():
    """
    Helper function that initializes a GRENML manager
    which will contain test data for import.
    """
    manager = GRENMLManager(name='test topology')
    owner_institution = manager.add_institution(
        name='owner institution',
        short_name='ownerinst',
        longitude=0.0,
        latitude=0.0,
    )
    manager.set_primary_owner(owner_institution)
    return manager


def orm_model_to_dict(model, attributes, conversions):
    """
    Converts a Django ORM model to a dictionary. Takes the model,
    an attributes dictionary and a conversions dictionary.

    The attributes dictionary maps names of attributes in the ORM object
    to keys in the output dicitonary.

    The conversion dictionary associates attributes to functions
    that take an ORM field and return a value that the function stores
    in the object it returns.
    """
    orm_dict = {
        attributes[attr]: getattr(model, attr)
        for attr in attributes.keys()
    }
    for k, conversion_fn in conversions.items():
        orm_dict[k] = conversion_fn(orm_dict[k])
    return orm_dict


INSTITUTION_ATTRIBUTES = {
    'name': 'test institution',
    'short_name': 'testinst',
    'longitude': 1.2,
    'latitude': 3.4,
    'altitude': 5.6,
    'address': 'test institution in Ottawa',
    'unlocode': 'CAOTT',
    'version': '2022-11-15',
}


def datetime_to_str(datetime_field):
    """ Simple date-time to string conversion. """
    return datetime_field.strftime('%Y-%m-%d')


INSTITUTION_CONVERSIONS = {
    'longitude': float,
    'latitude': float,
    'altitude': float,
    'version': datetime_to_str,
}


def orm_institution_to_dict(orm_institution):
    """ Converts a Django ORM institution model to a dictionary. """

    attribute_names = INSTITUTION_ATTRIBUTES.keys()
    orm_fields_to_dict_keys = dict(zip(attribute_names, attribute_names))
    return orm_model_to_dict(
        orm_institution,
        orm_fields_to_dict_keys,
        INSTITUTION_CONVERSIONS,
    )


def element_assertions(model_class, input_dict, orm_to_dict, topology_ids):
    """
    Verifies an element exists in the database.
    Parameters:
    - model_class is the element's Django ORM model class;
    - input_dict is the arguments passed to the GRENML manager method
      that creates the element;
    - orm_to_dict is a function that takes an ORM model object and
      returns a dictionary that this function compares to input_dict;
    - topology_ids is the set of ids of topologies the element
      is associated with.
    """
    items = model_class.objects.filter(name=input_dict['name'])
    assert len(items) == 1

    orm_object = items[0]
    db_dict = orm_to_dict(orm_object)
    assert input_dict == db_dict

    db_topology_ids = list(set([t.grenml_id for t in orm_object.topologies.all()]))
    assert len(db_topology_ids) == len(topology_ids)
    for db_topology_id in db_topology_ids:
        assert db_topology_id in topology_ids


@pytest.mark.django_db
def test_import_institution():
    """
    Imports one institution.
    Loads the record created in the database.
    Compares its contents to the attributes in the imported institution.
    """
    manager = make_grenml_manager()
    manager.add_institution(**INSTITUTION_ATTRIBUTES)

    # This will raise an exception in case the input data we created
    # with the manager is incorrect.
    manager.validate()

    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)
    element_assertions(
        Institution,
        INSTITUTION_ATTRIBUTES,
        orm_institution_to_dict,
        {manager.topology.id},
    )


PROPERTY_NAME = 'test_property_name'
PROPERTY_VALUE = 'test_property_value'


def property_assertions(orm_properties):
    """
    Takes a property queryset. Verifies it contains a single property
    with the known name and value.
    """
    assert len(orm_properties) == 1
    test_property = orm_properties[0]
    assert test_property.name == PROPERTY_NAME
    assert test_property.value == PROPERTY_VALUE


@pytest.mark.django_db
def test_import_institution_with_property():
    """
    Creates an institution in a GRENML manager, adds a test property
    to it. Imports the topology in the manager. Verifies that the
    institution in the database has the test property.
    """
    manager = make_grenml_manager()
    institution_id = manager.add_institution(**INSTITUTION_ATTRIBUTES)
    institution = manager.get_institution(id=institution_id)
    institution.add_property(PROPERTY_NAME, PROPERTY_VALUE)

    manager.validate()
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)

    institutions = Institution.objects.filter(name=INSTITUTION_ATTRIBUTES['name'])
    orm_institution = institutions[0]
    properties = orm_institution.properties.all()
    property_assertions(properties)


def make_parent_child_managers():
    """
    Returns a tuple containing two GRENML managers.
    The topology in the child manager is the child of the topology
    in the parent manager.
    """
    parent_manager = GRENMLManager(name='parent topology')
    parent_owner_institution = parent_manager.add_institution(
        name='parent owner institution',
        short_name='p-owner-inst',
        longitude=0.0,
        latitude=0.0,
    )
    parent_manager.set_primary_owner(parent_owner_institution)

    child_manager = GRENMLManager(name='child topology')
    child_owner_institution = child_manager.add_institution(
        name='child owner institution',
        short_name='c-owner-inst',
        longitude=0.0,
        latitude=0.0,
    )
    child_manager.set_primary_owner(child_owner_institution)
    parent_manager.topology.add_topology(child_manager.topology)

    return (parent_manager, child_manager)


@pytest.mark.django_db
def test_import_institution_in_child_topology():
    """
    Starts with an empty GRENML manager and creates a topology
    under the manager's topology (the child). Adds an institution
    to the child topology. Imports the root topology. Verifies
    the child topology and the institution in it exist in the database.
    """
    parent_manager, child_manager = make_parent_child_managers()
    child_manager.add_institution(**INSTITUTION_ATTRIBUTES)

    parent_manager.validate()
    importer = GRENMLImporter()
    importer.from_grenml_manager(parent_manager)
    element_assertions(
        Institution,
        INSTITUTION_ATTRIBUTES,
        orm_institution_to_dict,
        {child_manager.topology.id},
    )


@pytest.mark.django_db
def test_import_institution_in_parent_and_child_topology():
    """
    Creates two topologies, in a parent-child relationship.
    Adds the same institution to both.
    Imports the topologies using the GRENML manager associated
    to the parent.
    Checks that the institution exists in the database and is not
    duplicated. Checks also that it is associated to the two topologies.
    """
    parent_manager, child_manager = make_parent_child_managers()
    parent_manager.add_institution(**INSTITUTION_ATTRIBUTES)
    child_manager.add_institution(**INSTITUTION_ATTRIBUTES)

    parent_manager.validate()
    importer = GRENMLImporter()
    importer.from_grenml_manager(parent_manager)
    element_assertions(
        Institution,
        INSTITUTION_ATTRIBUTES,
        orm_institution_to_dict,
        {parent_manager.topology.id, child_manager.topology.id},
    )


NODE_ATTRIBUTES = {
    'name': 'test node',
    'short_name': 'testnode',
    'longitude': 7.8,
    'latitude': 9.0,
    'altitude': 0.9,
    'unlocode': 'CAMTR',
    'address': 'test node in Montreal',
    'lifetime_start': '2022-11-16',
    'lifetime_end': '2022-12-16',
    'version': '2022-11-16',
}


def attribute_names_to_dict_keys(keys, substitutions):
    """
    Creates the dictionary that maps the name of a field
    in the ORM object to a key in the dictionary that contains
    the attributes passed to the GRENML manager.
    """
    attributes_to_keys = dict(zip(keys, keys))
    for s in substitutions:
        key = substitutions[s]
        del attributes_to_keys[key]
        attributes_to_keys[s] = key
    return attributes_to_keys


def add_node(manager):
    """ Creates a node in the GRENML manager's topology. """

    institution_id = manager.add_institution(**INSTITUTION_ATTRIBUTES)
    node_id = manager.add_node(**NODE_ATTRIBUTES)
    manager.add_owner_to_node(institution_id, node_id)
    return manager.get_node(id=node_id)


def orm_node_to_dict(orm_node):
    """ Converts an ORM node model to a dictionary. """

    attributes_to_keys = attribute_names_to_dict_keys(
        NODE_ATTRIBUTES.keys(),
        {'start': 'lifetime_start', 'end': 'lifetime_end'},
    )
    node_conversions = {
        **INSTITUTION_CONVERSIONS,
        'lifetime_start': datetime_to_str,
        'lifetime_end': datetime_to_str,
    }
    node_dict = orm_model_to_dict(
        orm_node,
        attributes_to_keys,
        node_conversions,
    )
    return node_dict


@pytest.mark.django_db
def test_import_node():
    """
    Imports a node, loads it from the database, compares
    the imported node to the database contents.
    """
    manager = make_grenml_manager()
    add_node(manager)
    manager.validate()
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)
    element_assertions(
        Node,
        NODE_ATTRIBUTES,
        orm_node_to_dict,
        {manager.topology.id},
    )


@pytest.mark.django_db
def test_import_node_with_property():
    """
    Creates a node in a GRENML manager, adds a property to it.
    Imports the topology in the manager. Fetches the node
    from the database. Checks that the property exists.
    """
    manager = make_grenml_manager()
    node = add_node(manager)
    node.add_property(PROPERTY_NAME, PROPERTY_VALUE)
    manager.validate()
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)

    nodes = Node.objects.filter(name=NODE_ATTRIBUTES['name'])
    orm_node = nodes[0]
    properties = orm_node.properties.all()
    property_assertions(properties)


@pytest.mark.django_db
def test_import_node_in_child_topology():
    """
    Creates parent and child topologies, puts a node in the child,
    imports them, verifies the node exists in the database.
    """
    parent_manager, child_manager = make_parent_child_managers()
    add_node(child_manager)
    parent_manager.validate()
    importer = GRENMLImporter()
    importer.from_grenml_manager(parent_manager)
    element_assertions(
        Node,
        NODE_ATTRIBUTES,
        orm_node_to_dict,
        {child_manager.topology.id},
    )


@pytest.mark.django_db
def test_import_node_in_parent_and_child_topology():
    """
    Adds a node to two topologies, parent and child.
    Verifies the existence of a single node in the database,
    associated to both topologies.
    """
    parent_manager, child_manager = make_parent_child_managers()
    add_node(parent_manager)
    add_node(child_manager)

    parent_manager.validate()
    importer = GRENMLImporter()
    importer.from_grenml_manager(parent_manager)
    element_assertions(
        Node,
        NODE_ATTRIBUTES,
        orm_node_to_dict,
        {parent_manager.topology.id, child_manager.topology.id},
    )


@pytest.mark.django_db
def test_import_node_with_two_owners_in_different_topologies():
    """
    Sets up a GRENML manager with two topologies, parent and child.
    Adds a node that appears in both topologies. The node has two
    owner institutions. Each institution appears in only one of the
    topologies. Verifies that the node in the database has two owners
    and is part of the parent and child topologies.
    """
    parent_manager, child_manager = make_parent_child_managers()

    node_id = parent_manager.add_node(**NODE_ATTRIBUTES)
    parent_topology_owner_institution_id = parent_manager.topology.primary_owner
    parent_manager.add_owner_to_node(
        parent_topology_owner_institution_id,
        node_id,
    )

    node_attributes = {
        **NODE_ATTRIBUTES,
        'id': node_id,
    }
    child_manager.add_node(**node_attributes)
    child_topology_owner_institution_id = child_manager.topology.primary_owner
    child_manager.add_owner_to_node(
        child_topology_owner_institution_id,
        node_id,
    )

    importer = GRENMLImporter()
    importer.from_grenml_manager(parent_manager)

    assert Node.objects.count() == 1
    orm_node = Node.objects.first()

    # We are not sure which copy is kept by the default "Keep Newest"
    # ActionType, but whichever one it is, it should retain only its
    # original owner and Topology.
    owner_ids = make_set_of_ids(orm_node.owners)
    assert len(owner_ids) == 2
    topology_ids = make_set_of_ids(orm_node.topologies)
    assert len(topology_ids) == 2
    assert parent_manager.topology.id in topology_ids and child_manager.topology.id in topology_ids


def add_link(manager):
    """
    Adds a link (also its two endpoint nodes and an owner institution)
    to the GRENML manager's topology.

    Returns the GRENML link object and a dictionary containing
    the link's attributes.
    """
    institution_id = manager.add_institution(**INSTITUTION_ATTRIBUTES)

    endpoint1_id = manager.add_node(**NODE_ATTRIBUTES)
    manager.add_owner_to_node(institution_id, endpoint1_id)
    endpoint1 = manager.get_node(id=endpoint1_id)

    endpoint2_attributes = dict(NODE_ATTRIBUTES)
    endpoint2_attributes['name'] = 'test node 2'
    endpoint2_attributes['short_name'] = 'testnode2'
    endpoint2_id = manager.add_node(**endpoint2_attributes)
    manager.add_owner_to_node(institution_id, endpoint2_id)
    endpoint2 = manager.get_node(id=endpoint2_id)

    link_attributes = {
        'name': 'test link',
        'short_name': 'testlink',
        'lifetime_start': '2022-11-17',
        'lifetime_end': '2022-12-17',
        'version': '2022-11-17',
        'nodes': {endpoint1, endpoint2},
    }
    link_id = manager.add_link(**link_attributes)
    manager.add_owner_to_link(institution_id, link_id)
    link = manager.get_link(id=link_id)
    return (link, link_attributes)


def orm_link_to_dict(orm_link, attribute_names, manager):
    """ Converts an ORM link model to a dictionary. """

    attributes_to_keys = attribute_names_to_dict_keys(
        attribute_names,
        {'start': 'lifetime_start', 'end': 'lifetime_end'},
    )
    del attributes_to_keys['nodes']
    link_conversions = {
        'lifetime_start': datetime_to_str,
        'lifetime_end': datetime_to_str,
        'version': datetime_to_str,
    }
    link_dict = orm_model_to_dict(
        orm_link,
        attributes_to_keys,
        link_conversions,
    )
    link_dict['nodes'] = manager.topology.get_elements(
        NODES,
        id__in=[orm_link.node_a.grenml_id, orm_link.node_b.grenml_id],
    )
    return link_dict


def link_assertions(link_attributes, manager, topology_ids):
    """ Verifies the link imported by a test exists in the database. """

    links = Link.objects.filter(name=link_attributes['name'])
    assert len(links) == 1

    orm_link = links[0]
    link_dict = orm_link_to_dict(orm_link, link_attributes.keys(), manager)
    assert link_attributes == link_dict

    db_topology_ids = list(set([t.grenml_id for t in orm_link.topologies.all()]))
    assert len(db_topology_ids) == len(topology_ids)
    for db_topology_id in db_topology_ids:
        assert db_topology_id in topology_ids


@pytest.mark.django_db
def test_import_link():
    """
    Imports a link, finds it in the database, verifies that
    the link imported and the one in the database are equal.
    """
    manager = make_grenml_manager()
    _, link_attributes = add_link(manager)
    manager.validate()
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)
    link_assertions(link_attributes, manager, {manager.topology.id})


@pytest.mark.django_db
def test_import_link_with_property():
    """
    Creates a link with a property. Imports it. Verifies
    the property exists in the database.
    """
    manager = make_grenml_manager()
    link, link_attributes = add_link(manager)
    link.add_property(PROPERTY_NAME, PROPERTY_VALUE)
    manager.validate()
    importer = GRENMLImporter()
    importer.from_grenml_manager(manager)

    links = Link.objects.filter(name=link_attributes['name'])
    orm_link = links[0]
    properties = orm_link.properties.all()
    property_assertions(properties)


@pytest.mark.django_db
def test_import_link_in_child_topology():
    """
    Creates parent and child topologies, then a link in the child.
    Calls the import function passing the manager associated to the
    parent topology. Checks the link is present in the database.
    """
    parent_manager, child_manager = make_parent_child_managers()
    _, link_attributes = add_link(child_manager)
    parent_manager.validate()
    importer = GRENMLImporter()
    importer.from_grenml_manager(parent_manager)
    link_assertions(
        link_attributes,
        child_manager,
        {child_manager.topology.id},
    )


@pytest.mark.django_db
def test_import_link_in_parent_and_child_topology():
    """
    Imports a topology that is the parent of another. A single link
    exists in both. Checks that the database contains a single record
    for the link. Checks also that it is associated to the parent and
    child topologies.
    """
    parent_manager, child_manager = make_parent_child_managers()
    _, link_attributes = add_link(parent_manager)
    add_link(child_manager)
    parent_manager.validate()
    importer = GRENMLImporter()
    importer.from_grenml_manager(parent_manager)

    # The function uses the manager below to find the ids
    # of the link's endpoints. The nodes exist in the parent and
    # the child topologies. It doesn't matter which manager we use.
    link_assertions(
        link_attributes,
        parent_manager,
        {parent_manager.topology.id, child_manager.topology.id},
    )


VALID_GRENML = '''<?xml version="1.0" encoding="utf-8"?>
<grenml:Topology
    id="ad127b32c13cec329c83719dd6abc96523a95002460d087d746b85145dfac9e6"
    xmlns:grenml="http://schemas.ogf.org/nml/2020/01/grenml"
    xmlns:nml="http://schemas.ogf.org/nml/2013/05/base#"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://schemas.ogf.org/nml/2020/01/grenml validation/grenml.xsd http://schemas.ogf.org/nml/2013/05/base# validation/nmlbase.xsd">
  <grenml:name>test topology</grenml:name>
  <grenml:owner>b71ea9d3162e6f873c30b5e8379c4f8616467c0cebaeaed0a0b756323c4525e3</grenml:owner>
  <grenml:Institution id="urn:ogf:networking:global">
    <grenml:name>GREN</grenml:name>
    <grenml:Property name="tag">global</grenml:Property>
  </grenml:Institution>
  <grenml:Institution id="b71ea9d3162e6f873c30b5e8379c4f8616467c0cebaeaed0a0b756323c4525e3">
    <grenml:name>owner institution</grenml:name>
    <grenml:short-name>ownerinst</grenml:short-name>
  </grenml:Institution>
  <grenml:Institution id="eb7ccff482821f1849208204df40c95adcebd13db1852488720c595113bce711" version="2022-11-15T00:00:00+00:00">
    <grenml:name>test institution</grenml:name>
    <grenml:short-name>testinst</grenml:short-name>
    <grenml:Location>
      <grenml:long>1.2</grenml:long>
      <grenml:lat>3.4</grenml:lat>
      <grenml:alt>5.6</grenml:alt>
      <grenml:unlocode>CAOTT</grenml:unlocode>
      <grenml:address>test institution in Ottawa</grenml:address>
    </grenml:Location>
  </grenml:Institution>
  <grenml:Link id="9a1c2d8232592961f4b9aa92bb23ca71f564dbe1d9896a193d8f707c5bb6455e" version="2022-11-17T00:00:00+00:00">
    <grenml:name>test link</grenml:name>
    <grenml:short-name>testlink</grenml:short-name>
    <grenml:owner>b71ea9d3162e6f873c30b5e8379c4f8616467c0cebaeaed0a0b756323c4525e3</grenml:owner>
    <grenml:owner>eb7ccff482821f1849208204df40c95adcebd13db1852488720c595113bce711</grenml:owner>
    <grenml:Lifetime>
      <nml:start>2022-11-17T00:00:00+00:00</nml:start>
      <nml:end>2022-12-17T00:00:00+00:00</nml:end>
    </grenml:Lifetime>
    <grenml:node>33e2ab210e9fda6f6299e1ecca3c1d9105bb46ecf631abbf6b6f45a0c8fc5ef6</grenml:node>
    <grenml:node>75f50310641cfc3deb964e95c4c35dd650eedc27a372e3f41cd1560467b4e911</grenml:node>
  </grenml:Link>
  <grenml:Node id="33e2ab210e9fda6f6299e1ecca3c1d9105bb46ecf631abbf6b6f45a0c8fc5ef6" version="2022-11-16T00:00:00+00:00">
    <grenml:name>test node</grenml:name>
    <grenml:short-name>testnode</grenml:short-name>
    <grenml:owner>b71ea9d3162e6f873c30b5e8379c4f8616467c0cebaeaed0a0b756323c4525e3</grenml:owner>
    <grenml:owner>eb7ccff482821f1849208204df40c95adcebd13db1852488720c595113bce711</grenml:owner>
    <grenml:Lifetime>
      <nml:start>2022-11-16T00:00:00+00:00</nml:start>
      <nml:end>2022-12-16T00:00:00+00:00</nml:end>
    </grenml:Lifetime>
    <grenml:Location>
      <grenml:long>7.8</grenml:long>
      <grenml:lat>9.0</grenml:lat>
      <grenml:alt>0.9</grenml:alt>
      <grenml:unlocode>CAMTR</grenml:unlocode>
      <grenml:address>test node in Montreal</grenml:address>
    </grenml:Location>
  </grenml:Node>
  <grenml:Node id="75f50310641cfc3deb964e95c4c35dd650eedc27a372e3f41cd1560467b4e911" version="2022-11-16T00:00:00+00:00">
    <grenml:name>test node 2</grenml:name>
    <grenml:short-name>testnode2</grenml:short-name>
    <grenml:owner>b71ea9d3162e6f873c30b5e8379c4f8616467c0cebaeaed0a0b756323c4525e3</grenml:owner>
    <grenml:owner>eb7ccff482821f1849208204df40c95adcebd13db1852488720c595113bce711</grenml:owner>
    <grenml:Lifetime>
      <nml:start>2022-11-16T00:00:00+00:00</nml:start>
      <nml:end>2022-12-16T00:00:00+00:00</nml:end>
    </grenml:Lifetime>
    <grenml:Location>
      <grenml:long>7.8</grenml:long>
      <grenml:lat>9.0</grenml:lat>
      <grenml:alt>0.9</grenml:alt>
      <grenml:unlocode>CAMTR</grenml:unlocode>
      <grenml:address>test node in Montreal</grenml:address>
    </grenml:Location>
  </grenml:Node>
</grenml:Topology>
'''  # noqa: E501


def import_stream_assertions(model_class):
    """
    Checks that elements appearing in the GRENML input string
    exist in the database.
    """
    element_ids = re.findall(
        '<grenml:{} id="([^"]+)"'.format(model_class._meta.object_name),
        VALID_GRENML,
    )
    elements_in_input = len(element_ids)
    elements_in_db = model_class.objects.filter(grenml_id__in=element_ids).count()
    assert elements_in_input == elements_in_db


@pytest.mark.django_db
def test_import_stream():
    """ Tests the import_stream function. """

    stream = BytesIO(VALID_GRENML.encode())
    importer = GRENMLImporter()
    importer.from_stream(stream)

    import_stream_assertions(Institution)
    import_stream_assertions(Link)
    import_stream_assertions(Node)


@pytest.mark.django_db
def test_import_invalid_stream():
    """ Tests the import_stream function with an invalid XML input. """

    invalid_xml = VALID_GRENML.replace('grenml:', '')
    stream = BytesIO(invalid_xml.encode())

    with pytest.raises(StreamParseError):
        importer = GRENMLImporter()
        importer.from_stream(stream)

    assert Institution.objects.count() == 0
    assert Link.objects.count() == 0
    assert Node.objects.count() == 0
