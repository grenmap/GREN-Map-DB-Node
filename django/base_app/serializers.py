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

Serializers used in the extend_schema annotations to help the OpenAPI
schema generator.

Extend_schema is a decorator provided by the drf-spectacular library
that, when applied to a handler (function or method) associated to
a URL, lets us override or augment the information collected by the
schema generator when it visits that handler.

https://github.com/tfranzel/drf-spectacular
https://drf-spectacular.readthedocs.io/en/latest/readme.html
"""

from django.utils.translation import gettext as _, gettext_lazy
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from grenml_export.exceptions import NoTopologyOwnerError
from network_topology.exceptions import (
    MissingRootTopologyException,
    MissingRootTopologyOwnerException,
)


@extend_schema_field(OpenApiTypes.BINARY)
class BinaryFileField(serializers.FileField):
    """
    Django REST Framework FileField containing a byte stream.
    By default, the OpenAPI schema generator will create a field
    that expects a URI. """
    pass


class GRENMLExportSerializer(serializers.Serializer):
    """
    This represents the response body of export calls
    (those returning the server's network information stored in
    the database or in a snapshot file).
    """
    file = serializers.FileField()


class GRENMLImportSerializer(serializers.Serializer):
    """
    This informs the schema generator on which attributes should appear
    in the body of an import request.
    """
    file = BinaryFileField()
    parent_topology_id = serializers.CharField(
        help_text=_('ID of an existing topology.'),
        required=False,
    )
    topology_name = serializers.CharField(
        help_text=_(
            "Name to be given to the file's root topology "
            'once the server imports it.'
        ),
        required=False,
    )


# Dictionary associating an error type string
# (which is just the name of an exception class)
# to a UI message.
EXPORTING_ERRORS = {
    MissingRootTopologyException.__name__:
    gettext_lazy('Source server does not have a root topology.'),

    MissingRootTopologyOwnerException.__name__: (
        gettext_lazy(
            'Root topology in source server does not have an owner.\n'
            'On the source server, '
            'go to Home › Network Topology › Network Topologies, '
            'then click on the root topology to see an edit page.\n'
            'Click on the plus button in the "Owner" row to add an owner institution.'
        )
    ),

    NoTopologyOwnerError.__name__:
    gettext_lazy('Topology in source server does not have an owner.'),

    # This is the fall-back message.
    Exception.__name__:
    gettext_lazy('Internal server error.'),
}


class AccessDeniedSerializer(serializers.Serializer):
    """
    Serializer for responses blocked due to missing
    or invalid token.
    """
    detail = serializers.CharField(required=True)


class ErrorSerializer(serializers.Serializer):
    """
    This declares a response containing an error,
    currently used by the exporting endpoint.
    """
    error_type = serializers.ChoiceField(
        list(EXPORTING_ERRORS.keys()),
        required=True,
    )
