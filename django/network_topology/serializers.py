"""
SPDX-License-Identifier: Apache License 2.0

Copyright 2023 GRENMap Authors

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

Synopsis: Django REST Framework model serializers for network_topology
    models.
"""

from ast import literal_eval

from rest_framework import serializers as s

from .models import Node, Link, Institution, Topology, Property


class PropertySerializer(s.ModelSerializer):
    pk = s.ReadOnlyField()

    class Meta:
        model = Property
        fields = ['pk', 'name', 'value']


class PropertyListingField(s.RelatedField):
    """
    Use this in place of a regular PropertySerializer for
    deserialization, when for Properties, the primary key ID is
    generally not helpful.

    Output format:
        {"name": <string>, "value": <string>}
    Input format (unfortunately; see .to_internal_value):
        "{'name': <string>, 'value': <string>}"
    """

    def get_queryset(self):
        return Property.objects.all()

    def to_representation(self, value):
        """
        [Likely never used.]
        """
        return f'{{"name": {value.name}", "value": "{value.value}"}}'

    def to_internal_value(self, data):
        """
        Unfortunately, with ListFields when many=True,
        DRF gives us each entry dictionary as a string,
        in this case, each resembling a Python dictionary.
        Example:
            "{'name': <string>, 'value': <string>}"
                (Outer quotation marks denote the string;
                inner quotation marks are part of the string.)
        Since this should translate directly to Python, we can
        use eval.  However, eval raises serious security risks.
        ast.literal_eval is like eval but with reduced security
        exposure since only literals may be parsed, not arbitrary
        Python code.  Some additional factors to mitigate
        the security concerns typically associated with eval:
            - this API is not intended for production purposes,
            - this API requires authorization, and
            - the contents of the ListField may be sanitized by DRF.
        """
        parsed_data = literal_eval(data)
        name = parsed_data.get('name')
        value = parsed_data.get('value')
        return {
            'name': name,
            'value': value,
        }


def _add_properties(element, properties):
    """
    Adds Properties to a given element.
    Does not delete, edit, or clear existing Properties.
    Always allows duplicate Property names to coexist.
    'properties' argument should be a list of dictionaries:
        [
            {'name': <string>, 'value': <string>},
            {'name': <string>, 'value': <string>},
            {'name': <string>, 'value': <string>},
            ...
        ]
    """
    for property in properties:
        element.property(
            property['name'],
            value=property['value'],
            deduplicate=False,
        )


class TopologySerializer(s.ModelSerializer):
    pk = s.ReadOnlyField()
    properties = PropertySerializer(many=True, read_only=True)

    class Meta:
        model = Topology
        exclude = ['id']


class TopologyDeserializer(s.ModelSerializer):
    """
    Topologies contain Properties, a nested model.
    Writable nested serializers are not well-supported by Django
    REST Framework.  A common workaround is to provide two serializers,
    one simple one optimized for serialization (GET),
    the other for deserialization (POST, PUT, PATCH).
    The principle difference between this deserializer and the normal
    serializer above is that properties are deserialized using
    PropertyListingField.  This should validate incoming data,
    but writing is still not straightforward since DRF generally
    wants primary keys, but we'd like to let the database handle that
    and allow description of properties by name-value pairs only.
    The create and update methods pop the properties off the validated
    incoming data, inserts them separately, then DRF can take over.
    Note that this only supports adding properties!  They cannot be
    deleted by this particular set of API endpoints.
    https://www.django-rest-framework.org/topics/writable-nested-serializers  # noqa: W505
    """
    properties = PropertyListingField(many=True)

    class Meta:
        model = Topology
        fields = '__all__'

    def create(self, validated_data):
        properties = validated_data.pop('properties', [])
        topology = Topology.objects.create(**validated_data)
        _add_properties(topology, properties)
        return topology

    def update(self, instance, validated_data):
        properties = validated_data.pop('properties', [])
        _add_properties(instance, properties)
        return super().update(instance, validated_data)


class TopologyStubSerializer(s.ModelSerializer):
    pk = s.ReadOnlyField()

    class Meta:
        model = Topology
        fields = ['pk', 'grenml_id', 'name']


class TopologyListingField(s.RelatedField):
    """
    Use this in place of a regular TopologySerializer for
    deserialization, to allow specification of a Topology
    simply by its primary key.

    Output format:
        {"name": <string>, "value": <string>}
    Input format (unfortunately; see .to_internal_value):
        <primary key integer>
    """

    def get_queryset(self):
        return Topology.objects.all()

    def to_representation(self, value):
        """
        [Likely never used.]
        """
        return f'{{"id": {value.id}", "grenml_id": "{value.grenml_id}", "name": "{value.name}"}}'

    def to_internal_value(self, data):
        pk = data
        return pk


def _set_topologies(element, topologies):
    """
    Accepts a list of Topology primary keys in the 'topologies'
    parameter, and ensures that the given element belongs to
    exactly the corresponding set of Topologies.
    """
    element.topologies.clear()
    for topology_primary_key in topologies:
        topology = Topology.objects.get(pk=topology_primary_key)
        element.topologies.add(topology)


class InstitutionSerializer(s.ModelSerializer):
    pk = s.ReadOnlyField()
    topologies = TopologyStubSerializer(many=True, read_only=True)
    properties = PropertySerializer(many=True, read_only=True)
    owned_topologies = s.PrimaryKeyRelatedField(many=True, read_only=True)
    owned_elements = s.PrimaryKeyRelatedField(source='elements', many=True, read_only=True)

    class Meta:
        model = Institution
        exclude = ['id']


class InstitutionDeserializer(s.ModelSerializer):
    """
    Institutions contain Properties and belong to Topologies.
    These foreign keys and many-to-many relationships are nested models.
    Writable nested serializers are not well-supported by Django
    REST Framework.  A common workaround is to provide two serializers,
    one simple one optimized for serialization (GET),
    the other for deserialization (POST, PUT, PATCH).
    The principle difference between this deserializer and the normal
    serializer above is that nested models are deserialized using
    *ListingFields.  This should validate incoming data,
    but supplying data and writing is still not straightforward in DRF.
    We want to allow description of properties by name-value pairs only.
    We want to allow specification of Topologies by primary keys only.
    The create and update methods pop our related models off the
    validated incoming data, inserts them separately, then DRF can take
    over for the remaining fields.
    Note that this only supports adding properties!  They cannot be
    deleted by this particular set of API endpoints.
    """
    properties = PropertyListingField(many=True)
    topologies = TopologyListingField(many=True)

    class Meta:
        model = Institution
        fields = '__all__'

    def create(self, validated_data):
        properties = validated_data.pop('properties', [])
        topologies = validated_data.pop('topologies', [])
        institution = Institution.objects.create(**validated_data)
        _add_properties(institution, properties)
        _set_topologies(institution, topologies)
        return institution

    def update(self, instance, validated_data):
        properties = validated_data.pop('properties', [])
        topologies = validated_data.pop('topologies', None)
        _add_properties(instance, properties)
        if topologies is not None:
            _set_topologies(instance, topologies)
        return super().update(instance, validated_data)


class InstitutionStubSerializer(s.ModelSerializer):
    pk = s.ReadOnlyField()

    class Meta:
        model = Institution
        fields = ['pk', 'grenml_id', 'name', 'short_name']


class InstitutionListingField(s.RelatedField):
    """
    Use this in place of a regular InstitutionSerializer for
    deserialization, to allow specification of an owner
    Institution simply by its primary key.

    Output format:
        {"id": <string>, "grenmld_id": <string>, "name": <string>}
    Input format:
        <primary key integer>
    """

    def get_queryset(self):
        return Institution.objects.all()

    def to_representation(self, value):
        """
        [Likely never used.]
        """
        return f'{{"id": {value.id}", "grenml_id": "{value.grenml_id}", "name": "{value.name}"}}'

    def to_internal_value(self, data):
        pk = data
        return pk


def _set_owners(element, owners):
    """
    Accepts a list of Institution primary keys in the 'owners'
    parameter, and ensures that the given element is "owned" by
    exactly the corresponding set of Institutions.
    """
    element.owners.clear()
    for owner_primary_key in owners:
        owner = Institution.objects.get(pk=owner_primary_key)
        element.owners.add(owner)


class NodeSerializer(s.ModelSerializer):
    pk = s.ReadOnlyField()
    topologies = TopologyStubSerializer(many=True, read_only=True)
    properties = PropertySerializer(many=True, read_only=True)
    owners = InstitutionStubSerializer(many=True, read_only=True)

    class Meta:
        model = Node
        exclude = ['id']


class NodeDeserializer(s.ModelSerializer):
    """
    Nodes contain Properties and belong to Topologies and have owner
    Institutions.  These foreign keys and many-to-many relationships
    are nested models.  Writable nested serializers are not
    well-supported by Django REST Framework.  A common workaround is
    to provide two serializers, one simple one optimized for
    serialization (GET), one for deserialization (POST, PUT, PATCH).
    The principle difference between this deserializer and the normal
    serializer above is that nested models are deserialized using
    *ListingFields.  This should validate incoming data,
    but supplying data and writing is still not straightforward in DRF.
    We want to allow description of properties by name-value pairs only.
    We want to allow specification of Topologies by primary keys only.
    We want to allow specification of owner Institutions by PKs only.
    The create and update methods pop our related models off the
    validated incoming data, inserts them separately, then DRF can take
    over for the remaining fields.
    Note that this only supports adding properties!  They cannot be
    deleted by this particular set of API endpoints.
    """
    properties = PropertyListingField(many=True)
    topologies = TopologyListingField(many=True)
    owners = InstitutionListingField(many=True)

    class Meta:
        model = Node
        fields = '__all__'

    def create(self, validated_data):
        properties = validated_data.pop('properties', [])
        topologies = validated_data.pop('topologies', [])
        owners = validated_data.pop('owners', [])
        node = Node.objects.create(**validated_data)
        _add_properties(node, properties)
        _set_topologies(node, topologies)
        _set_owners(node, owners)
        return node

    def update(self, instance, validated_data):
        properties = validated_data.pop('properties', [])
        topologies = validated_data.pop('topologies', None)
        owners = validated_data.pop('owners', None)
        _add_properties(instance, properties)
        if topologies is not None:
            _set_topologies(instance, topologies)
        if owners is not None:
            _set_owners(instance, owners)
        return super().update(instance, validated_data)


class NodeStubSerializer(s.ModelSerializer):
    pk = s.ReadOnlyField()

    class Meta:
        model = Node
        fields = ['pk', 'grenml_id', 'name', 'short_name']


class NodeListingField(s.RelatedField):
    """
    Use this in place of a regular NodeSerializer for
    deserialization of Links, to allow specification of
    endpoint Nodes simply by primary key.

    Output format:
        {"id": <string>, "grenmld_id": <string>, "name": <string>}
    Input format:
        <primary key integer>
    """

    def get_queryset(self):
        return Institution.objects.all()

    def to_representation(self, value):
        """
        [Likely never used.]
        """
        return f'{{"id": {value.id}", "grenml_id": "{value.grenml_id}", "name": "{value.name}"}}'

    def to_internal_value(self, data):
        pk = data
        return pk


class LinkSerializer(s.ModelSerializer):
    pk = s.ReadOnlyField()
    topologies = TopologyStubSerializer(many=True, read_only=True)
    properties = PropertySerializer(many=True, read_only=True)
    owners = InstitutionStubSerializer(many=True, read_only=True)
    node_a = NodeStubSerializer()
    node_b = NodeStubSerializer()

    class Meta:
        model = Link
        exclude = ['id']


class LinkDeserializer(s.ModelSerializer):
    """
    Links contain Properties and belong to Topologies and have owner
    Institutions.  These foreign keys and many-to-many relationships
    are nested models.  Writable nested serializers are not
    well-supported by Django REST Framework.  A common workaround is
    to provide two serializers, one simple one optimized for
    serialization (GET), one for deserialization (POST, PUT, PATCH).
    The principle difference between this deserializer and the normal
    serializer above is that nested models are deserialized using
    *ListingFields.  This should validate incoming data,
    but supplying data and writing is still not straightforward in DRF.
    We want to allow description of properties by name-value pairs only.
    We want to allow specification of Topologies by primary keys only.
    We want to allow specification of owner Institutions by PKs only.
    The create and update methods pop our related models off the
    validated incoming data, inserts them separately, then DRF can take
    over for the remaining fields.
    Note that this only supports adding properties!  They cannot be
    deleted by this particular set of API endpoints.
    """
    properties = PropertyListingField(many=True)
    topologies = TopologyListingField(many=True)
    owners = InstitutionListingField(many=True)
    node_a = NodeListingField(many=False)
    node_b = NodeListingField(many=False)

    class Meta:
        model = Link
        fields = '__all__'

    def create(self, validated_data):
        properties = validated_data.pop('properties', [])
        topologies = validated_data.pop('topologies', [])
        owners = validated_data.pop('owners', [])
        # Convert PKs to actual object references
        validated_data['node_a'] = Node.objects.get(pk=validated_data.pop('node_a'))
        validated_data['node_b'] = Node.objects.get(pk=validated_data.pop('node_b'))
        link = Link.objects.create(**validated_data)
        _add_properties(link, properties)
        _set_topologies(link, topologies)
        _set_owners(link, owners)
        return link

    def update(self, instance, validated_data):
        properties = validated_data.pop('properties', [])
        topologies = validated_data.pop('topologies', None)
        owners = validated_data.pop('owners', None)
        # Convert PKs to actual object references
        try:
            validated_data['node_a'] = Node.objects.get(pk=validated_data.pop('node_a'))
        except KeyError:
            # It's okay if the request does not change node_a
            pass
        try:
            validated_data['node_b'] = Node.objects.get(pk=validated_data.pop('node_b'))
        except KeyError:
            # It's okay if the request does not change node_b
            pass
        _add_properties(instance, properties)
        if topologies is not None:
            _set_topologies(instance, topologies)
        if owners is not None:
            _set_owners(instance, owners)
        return super().update(instance, validated_data)
