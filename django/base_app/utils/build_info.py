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

Code shared by the management command that writes a file
with build attributes and the context processor that uses them.
"""

from collections import namedtuple

FILE_PATH = '/home/grenmapadmin/build_info'

BuildInfo = namedtuple(
    'BuildInfo',
    'date, git_hash, git_tag, grenml, vis',
)
