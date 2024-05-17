"""
Copyright 2020 GRENMap Authors

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

Adds the Graphql endpoint for querying nodes.
"""

from django.urls import path
from visualization.views.api import visualization_graphql_api
from visualization.views.api import fullscreen_map
from visualization.views.api import visualization_enabled_setting
from visualization.views.api import visualization_enabled_setting_toggle
from visualization.views.api import visualization_allow_origins
from visualization.views.api import visualization_allow_origin
from visualization.views.api import initial_coordinates_setting
from visualization.views.api import initial_map_zoom_setting

urlpatterns = [
    path('visualization/graphql/', visualization_graphql_api),
    path('', fullscreen_map),
    path('visualization/initial_coordinates/', initial_coordinates_setting),
    path('visualization/initial_zoom/', initial_map_zoom_setting),

    path('visualization/test/enabled_setting/', visualization_enabled_setting),
    path('visualization/test/enabled_setting/<int:enable>/', visualization_enabled_setting_toggle),
    path('visualization/test/allow_origin/', visualization_allow_origins),
    path('visualization/test/allow_origin/<str:name>/', visualization_allow_origin),
]
