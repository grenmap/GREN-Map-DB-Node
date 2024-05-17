#!/usr/bin/env python
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
"""

from base_app.settings import LANGUAGES

# B404 exclusion: subprocess.run replaces os.system (less safe)
# Reference:
# https://security.openstack.org/guidelines/dg_use-subprocess-securely.html
import subprocess  # nosec B404

command = ['/usr/local/bin/python', 'manage.py', 'makemessages']
for language in LANGUAGES:
    command.append('-l')
    command.append(language[0])
# B603 exclusion: locales is derived from a constant, its value is known
subprocess.run(command)  # nosec B603
