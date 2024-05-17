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

Synopsis: Exceptions used throughout this app.
"""
import logging

from django.utils.translation import gettext as _

from base_app.exceptions import HealthException


log = logging.getLogger()


class MoreThanOneMainTopologyError(HealthException):
    def __init__(self):
        msg = _('More than one main Topology has been set.  Cannot export.  Select only one.')
        log.error(msg)
        self.message = msg


class MissingRootTopologyException(HealthException):
    """
    Root topology wasn't found in the database when it was required
    """
    pass


class MissingRootTopologyOwnerException(HealthException):
    """
    An owner wasn't found on the topology when it was required
    """
    pass
