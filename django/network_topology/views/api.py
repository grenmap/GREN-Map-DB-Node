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

------------------------------------------------------------------------

Synopsis: Network_topology API
"""

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from ..models import (
    Topology,
    Institution,
    Node,
    Link,
    Property,
)
from ..serializers import (
    TopologySerializer,
    TopologyDeserializer,
    InstitutionSerializer,
    InstitutionDeserializer,
    NodeSerializer,
    NodeDeserializer,
    LinkSerializer,
    LinkDeserializer,
    PropertySerializer,
)


class TopologyViewSet(ModelViewSet):
    """
    Standard REST CRUD API for Topologies.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = Topology.objects.all().order_by('pk')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TopologySerializer
        else:
            return TopologyDeserializer

    @action(detail=False, methods=['delete'])
    def delete(self, request):
        """
        A handy shortcut to delete all Topologies
        (and thus, in most cases, all GRENML data
        such as Institutions, Nodes, and Links).
        """
        Topology.objects.all().delete()
        return Response('', status=status.HTTP_204_NO_CONTENT)


class InstitutionViewSet(ModelViewSet):
    """
    Standard REST CRUD API for Institutions.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = Institution.objects.all().order_by('pk')
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return InstitutionSerializer
        else:
            return InstitutionDeserializer


class NodeViewSet(ModelViewSet):
    """
    Standard REST CRUD API for Nodes.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = Node.objects.all().order_by('pk')
    serializer_class = NodeSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NodeSerializer
        else:
            return NodeDeserializer


class LinkViewSet(ModelViewSet):
    """
    Standard REST CRUD API for Links.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = Link.objects.all().order_by('pk')
    serializer_class = LinkSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return LinkSerializer
        else:
            return LinkDeserializer


class PropertyViewSet(ModelViewSet):
    """
    Standard REST CRUD API for Properties.
    The views produced by this ViewSet are intended strictly for
    testing purposes and should not be used for any other purpose.
    """
    queryset = Property.objects.all().order_by('pk')
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]
