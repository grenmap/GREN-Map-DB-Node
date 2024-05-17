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

Synopsis: Constants used in this app that may be useful to be exported
    (no pun intended) to other apps.
"""


# _P for short; full name used where clarity is helpful
RESERVED_PROPERTY_PREFIX = _P = '!-'
EXTERNAL_TOPOLOGY_PROPERTY_KEY = _P + 'from_topology'
EXTERNAL_TOPOLOGY_PROPERTY_DELIMITER = ','


def is_reserved(property):
    return property.name.startswith(RESERVED_PROPERTY_PREFIX)
