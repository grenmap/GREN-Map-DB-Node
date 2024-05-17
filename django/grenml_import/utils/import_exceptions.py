"""
Copyright 2022 GRENMap Authors

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

import logging
logger = logging.getLogger(__name__)


class ImportError(Exception):
    """
    Terminal errors that abort an import.
    Automatically sends messages to the Python logger at ERROR level.
    """
    def __init__(self, msg):
        logger.error(msg)
        super().__init__(msg)


class StreamParseError(ImportError):
    pass


class ImportWarning(Exception):
    """
    Non-terminal errors that occur during import.
    Any time one of these is raised, the data administrator likely
    ought to be warned of the situation.
    Automatically sends messages to the Python logger at WARN level.
    """
    def __init__(self, msg):
        self.msg = msg
        logger.warning(msg)
        super().__init__(msg)
