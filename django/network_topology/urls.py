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

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import api


router = DefaultRouter()
# The views produced by these ViewSets are intended strictly for
# testing purposes and should not be used for any other purpose.
router.register(r'topologies', api.TopologyViewSet)
router.register(r'institutions', api.InstitutionViewSet)
router.register(r'nodes', api.NodeViewSet)
router.register(r'links', api.LinkViewSet)
router.register(r'properties', api.PropertyViewSet)

"""
Example URLs for the above:
    topologies/                    name: 'topology-list'
    topologies/<pk>/               name: 'topology-detail'
    topologies/delete/
    institutions/                  name: 'institution-list'
    institutions/<pk>/             name: 'institution-detail'
    nodes/                         name: 'node-list'
    nodes/<pk>/                    name: 'node-detail'
    links/                         name: 'link-list'
    links/<pk>/                    name: 'link-detail'
    properties/                    name: 'property-list'
    properties/<pk>/               name: 'property-detail'
"""


urlpatterns = [
    path('network_topology/test/', include(router.urls)),
]
