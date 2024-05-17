"""
Copyright 2023 GRENMap Authors

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

------------------------------------------------------------------------

Synopsis: Contains a class to mock a File object, generally used for
    uploading "files" to an API from string contents.
"""


class MockFile:
    """
    Mock a File object to send along with file import requests.
    This presents a sufficiently-file-like object to Python requests
    library that it can read the data (for encoding) and include
    a filename alongside it.  (It looks for a 'name' attribute.)
    """
    def __init__(self, filename, content):
        self.name = filename
        self.content = content

    def read(self):
        return self.content
