"""
Copyright 2020 GRENMap Authors

SPDX-License-Identifier: Apache License 2.0

Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from django.urls import path
from grenml_import.views.api import post_xml_file, test_import_files, test_post_xml_data

urlpatterns = [
    path('grenml_import/upload/', post_xml_file),
    path('grenml_import/test/', test_import_files),
    path('grenml_import/test/upload/', test_post_xml_data),
]
