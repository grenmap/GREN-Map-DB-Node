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

Many of the endpoints in the GRENMap server are internal or used only
by tests. They are not part of the API the server presents for external
programs.

In this module we constrain the schema generator to let it visit only
the endpoints we think are part of the public API.
"""

from drf_spectacular.generators import SchemaGenerator

PUBLIC_API_ENDPOINTS = [
    'status/',
    'grenml_export/',
    'grenml_import/upload/',
    'published_network_data/current/grenml_export/',
]


class GRENMapSchemaGenerator(SchemaGenerator):
    """
    Subclass of the Django REST Framework's schema generator
    that only includes selected endpoints in its output.

    Management command to write the OpenAPI schema:

    python manage.py spectacular \
    --generator-class base_app.schema.GRENMapSchemaGenerator
    """
    def __init__(self, *args, **kwargs):
        from base_app.urls import urlpatterns

        def is_selected_urlpattern(urlpattern):
            for endpoint in PUBLIC_API_ENDPOINTS:
                if urlpattern.pattern.regex.match(endpoint):
                    return True
            return False

        filtered_url_patterns = list(filter(
            is_selected_urlpattern,
            urlpatterns,
        ))
        kwargs['patterns'] = filtered_url_patterns
        super().__init__(*args, **kwargs)
