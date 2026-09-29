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

This file contains the GraphQL Schema, allowing graphql to know how
to query the network topology
"""

import graphene
import graphene_django_optimizer as gql_optimizer
from graphene_django.types import DjangoObjectType

from grenml_export.constants import RESERVED_PROPERTY_PREFIX

from network_topology import models

from .models import UIString
from .translation import (
    ensure_institution_popup_translations,
    ensure_ui_string_translations,
)


class PropertyType(DjangoObjectType):
    class Meta:
        model = models.Property
        fields = '__all__'


class InstitutionPopupTranslationType(graphene.ObjectType):
    language_code = graphene.String()
    summary = graphene.String()
    full_content = graphene.String()


class InstitutionType(DjangoObjectType):
    class Meta:
        model = models.Institution
        fields = '__all__'

    def resolve_id(self, info):
        return self.grenml_id

    properties = graphene.List(of_type=PropertyType)
    popup_translations = graphene.List(of_type=InstitutionPopupTranslationType)

    def resolve_properties(self, context_value, id=None, name=None):
        return self.properties.exclude(name__startswith=RESERVED_PROPERTY_PREFIX)

    def resolve_popup_translations(self, context_value, id=None, name=None):
        return ensure_institution_popup_translations(self)


class NodeType(DjangoObjectType):
    class Meta:
        model = models.Node
        fields = '__all__'

    def resolve_id(self, info):
        return self.grenml_id

    owners = graphene.List(of_type=InstitutionType)
    properties = graphene.List(of_type=PropertyType)
    # All owners that are connected to nodes that
    # are directly connected to the requested node
    connected_owners = graphene.List(InstitutionType)
    # All owning Institutions that have popup content registered
    # (a node may be owned by more than one; each gets its own tab
    # in the map popup rather than only the first one winning)
    popup_institutions = graphene.List(of_type=InstitutionType)

    def resolve_owners(self, context_value, id=None, name=None):
        return self.owners.all()

    def resolve_properties(self, context_value, id=None, name=None):
        return self.properties.exclude(name__startswith=RESERVED_PROPERTY_PREFIX)

    def resolve_connected_owners(self, context_value, id=None, name=None):
        return self.connected_owners

    def resolve_popup_institutions(self, context_value, id=None, name=None):
        return [
            institution for institution in self.owners.all()
            if institution.popup_summary or institution.popup_content
        ]


class LinkType(DjangoObjectType):
    class Meta:
        model = models.Link
        fields = '__all__'

    def resolve_id(self, info):
        return self.grenml_id

    owners = graphene.List(of_type=InstitutionType)
    properties = graphene.List(of_type=PropertyType)

    def resolve_owners(self, context_value, id=None, name=None):
        return self.owners.all()

    def resolve_properties(self, context_value, id=None, name=None):
        return self.properties.exclude(name__startswith=RESERVED_PROPERTY_PREFIX)


class UIStringTranslationType(graphene.ObjectType):
    language_code = graphene.String()
    text = graphene.String()


class UIStringType(graphene.ObjectType):
    key = graphene.String()
    text = graphene.String()
    translations = graphene.List(of_type=UIStringTranslationType)

    def resolve_translations(self, context_value, id=None, name=None):
        return ensure_ui_string_translations(self)


class Query(graphene.ObjectType):

    institution = graphene.Field(
        InstitutionType, id=graphene.String(), name=graphene.String()
    )
    institutions = graphene.List(InstitutionType, name=graphene.String())

    node = graphene.Field(NodeType, id=graphene.String(), name=graphene.String())
    nodes = graphene.List(NodeType, name=graphene.String())

    link = graphene.Field(LinkType, id=graphene.String(), name=graphene.String())
    links = graphene.List(LinkType, name=graphene.String())

    ui_strings = graphene.List(UIStringType)

    def resolve_id(self, info, **args):
        return args.get(id)

    @classmethod
    def resolve_ui_strings(cls, context_value, info, **kwargs):
        return UIString.objects.all()

    @classmethod
    def resolve_institution(cls, context_value, info, **kwargs):
        return Query.resolve_institutions(context_value, info, grenml_id=kwargs.get('id')).first()

    @classmethod
    def resolve_institutions(cls, context_value, info, **kwargs):
        if len(kwargs) > 0:
            return gql_optimizer.query(models.Institution.objects.filter(**kwargs), info)
        else:
            return gql_optimizer.query(models.Institution.objects.all(), info)

    @classmethod
    def resolve_node(cls, context_value, info, **kwargs):
        return Query.resolve_nodes(context_value, info, grenml_id=kwargs.get('id')).first()

    @classmethod
    def resolve_nodes(cls, context_value, info, **kwargs):
        if len(kwargs) > 0:
            return gql_optimizer.query(models.Node.objects.filter(**kwargs), info)
        else:
            return gql_optimizer.query(models.Node.objects.all(), info)

    @classmethod
    def resolve_link(cls, context_value, info, **kwargs):
        return Query.resolve_links(context_value, info, grenml_id=kwargs.get('id')).first()

    @classmethod
    def resolve_links(cls, context_value, info, **kwargs):
        if len(kwargs) > 0:
            return gql_optimizer.query(models.Link.objects.filter(**kwargs), info)
        else:
            return gql_optimizer.query(models.Link.objects.all(), info)


schema = graphene.Schema(query=Query)
