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

Base app constants.
"""

from django.utils.translation import gettext_lazy as _

# Message fragments shown on the Swagger UI page:

# For endpoints to which the server grants access
# when the request contains a collect token:
COLLECT_TOKEN_MESSAGE = _(
    # Translators: <br> is an HTML tag that inserts a new line. Please keep it between the two sentences.  # noqa
    'Requires a "polling" token. <br>'
    'Navigate to Home > Base App > Tokens in the admin site to obtain one.'
)

# For endpoints that require an import token:
IMPORT_TOKEN_MESSAGE = _(
    # Translators: <br> is an HTML tag that inserts a new line. Please keep it between the two sentences.  # noqa
    'Requires an "import" token. <br>'
    'Navigate to Home > Base App > Tokens in the admin site to obtain one.'
)

# Message fragment describing how to create a snapshot of the database.
SNAPSHOT_FILE_MESSAGE = _(
    # Translators: <br> is an HTML tag that inserts a new line. Please keep both tags at the end of the message.  # noqa
    'To create a snapshot, open the admin site and navigate to '
    'Home > Published Network Data. <br> <br>'
)
