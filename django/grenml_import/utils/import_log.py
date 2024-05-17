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
from itertools import chain

from django.utils.translation import gettext as _, gettext_noop as __


logger = logging.getLogger(__name__)


class ImportElementLog:
    """
    One of these per element per element encountered in the parsed
    GRENML should comprise an ImportElementTypeLog.
    If an encountered parsed item is not imported (skipped), its
    primary key (pk) will be None.
    Automatically sends info_messages included upon initialization
    to Python logger at DEBUG level.  Does not do so for warnings,
    because those Exceptions should do so as they see fit when raised.
    """
    def __init__(self, id=None, pk=None, info_messages=[], warnings=[]):
        self.id = id
        self.pk = pk
        self.info_messages = info_messages if info_messages else list()
        self.warnings = warnings if warnings else list()

        for msg in self.info_messages:
            logger.debug(msg)


class ImportElementTypeLog:
    """
    One of these objects per element type (below) should comprise an
    ImportLog instance.
    """
    def __init__(self, element_type):
        """
        element_type should be a string representing one of:
            Topology
            Institution
            Node
            Link
        """
        self.element_type = element_type
        self.element_logs = []

    def log_skipped(self, id, info_messages=[], warnings=[]):
        """
        Log an element that was encountered but not imported, noting
        its GRENML ID.
        The 'info_messages' parameter may be a list of strings,
        identifying notable situations encountered during the
        attempted import of this element.
        The 'warnings' parameter, if supplied, should be a list of
        Exceptions like ImportWarning.
        """
        self.element_logs.append(ImportElementLog(
            id=id,
            pk=None,
            info_messages=info_messages,
            warnings=warnings,
        ))

    def log_imported(self, id, pk, info_messages=[], warnings=[]):
        """
        Log an element that was imported, noting its GRENML ID.
        The 'info_messages' parameter may be a list of strings,
        identifying notable situations encountered during the
        import of this element.
        The 'warnings' parameter, if supplied, should be a list of
        Exceptions like ImportWarning.
        """
        self.element_logs.append(ImportElementLog(
            id=id,
            pk=pk,
            info_messages=info_messages,
            warnings=warnings,
        ))

    def update_log(self, id, pk=None, info_messages=[], warnings=[]):
        """
        Update an existing stored ImportElementLog, identified by ID,
        updating the stored primary key (which notes whether it was
        successful).
        Appends any new info_message strings or warning Exceptions
        to the appropriate lists; cannot remove any existing ones.
        """
        for log in self.element_logs:
            if log.id == id:
                log.pk = pk
                log.info_messages.extend(info_messages)
                log.warnings.extend(warnings)

    @property
    def encountered(self):
        """
        Returns the number of parsed elements encountered, whether they
        were imported or not.
        """
        return len(self.element_logs)

    @property
    def imported(self):
        """
        Returns the number of parsed elements encountered and imported.
        Elements that were encountered & not imported are not counted.
        """
        return len([elem for elem in self.element_logs if elem.pk is not None])

    @property
    def info_messages(self):
        """
        Flattens the list of info_messages in the list of element logs
        into a single list of all info message strings.
        """
        return list(chain.from_iterable([elem.info_messages for elem in self.element_logs]))

    @property
    def warning_messages(self):
        """
        Flattens the list of warnings in the list of element logs
        into a single list of all warning strings.
        """
        all_warnings = chain.from_iterable([elem.warnings for elem in self.element_logs])
        return [warning.msg for warning in all_warnings]


class ImportLog:
    """
    Collects statistics and messages related to an import process.
    Its contents may be shown in the Django Admin, stored in the DB
    record of the import, or returned to an API endpoint, etc.
    """
    IMPORT_STATUS_IN_PROGRESS = 0
    IMPORT_STATUS_COMPLETED = 1
    IMPORT_STATUS_WARNING = 2
    IMPORT_STATUS_ABORTED = 3
    IMPORT_STATUS_PHRASES = {
        IMPORT_STATUS_IN_PROGRESS: __('Import in progress'),
        IMPORT_STATUS_COMPLETED: __('Import complete'),
        IMPORT_STATUS_WARNING: __('Import completed, with warnings'),
        IMPORT_STATUS_ABORTED: __('Import aborted'),
    }

    def __init__(self):
        self.topologies = ImportElementTypeLog('Topology')
        self.institutions = ImportElementTypeLog('Institution')
        self.nodes = ImportElementTypeLog('Node')
        self.links = ImportElementTypeLog('Link')
        self._exceptions = []
        self._complete = False
        self._error_state = False

    def abort(self, exception=None):
        """
        Sets an internal variable that causes a status check to return
        IMPORT_STATUS_ABORTED.
        """
        self._error_state = True
        if exception:
            self._exceptions.append(exception)

    def complete(self):
        """
        Sets an internal variable that causes a status check to return
        IMPORT_STATUS_COMPLETED.
        """
        self._complete = True

    def _status_string_tuple(self, status):
        return (status, _(self.IMPORT_STATUS_PHRASES[status]))

    @property
    def status(self):
        """
        With help from _status_string_tuple, returns a tuple:
            - one of the IMPORT_STATUS_* states above, as applicable
            - a phrase associated with the current status flag
        Strings are runs through the translation matrix.

        Decision tree:
            if error state: return ABORTED
            else if complete:
                if warning messages encountered: return WARNING
                else return COMPLETED
            else return IN_PROGRESS
        """
        if self._error_state:
            return self._status_string_tuple(self.IMPORT_STATUS_ABORTED)

        if self._complete:
            if (
                self.topologies.warning_messages
                or self.institutions.warning_messages
                or self.nodes.warning_messages
                or self.links.warning_messages
            ):
                return self._status_string_tuple(self.IMPORT_STATUS_WARNING)
            else:
                return self._status_string_tuple(self.IMPORT_STATUS_COMPLETED)

        return self._status_string_tuple(self.IMPORT_STATUS_IN_PROGRESS)

    def __str__(self):
        """
        Returns a string representation summarizing the activity of a
        GRENML import event, in the following format:

            Status: Import complete

            Topologies: _ parsed, _ imported
            ....helpful message
            ....another helpful message
            ....WARNING: warning about something
            ....WARNING: warning about another thing

            Institutions: _ parsed, _ imported
                ...

            Nodes: ...
                ...

            Links: ...
                ...
        """
        status, message = self.status
        # Translators: {} is one of the translated messages: "import in progress", "import complete", "import completed with warnings", "import aborted"  # noqa
        output = _('Status: {}\n').format(message)
        output += '\n'

        # Translators: {}'s are numbers of topologies  # noqa
        output += _('Topologies: {} parsed, {} imported\n').format(
            self.topologies.encountered,
            self.topologies.imported,
        )
        for msg in self.topologies.info_messages:
            output += '\t' + msg + '\n'
        for msg in self.topologies.warning_messages:
            output += '\t' + _('WARNING: ') + msg + '\n'
        output += '\n'

        # Translators: {}'s are numbers of institutions  # noqa
        output += _('Institutions: {} parsed, {} imported\n').format(
            self.institutions.encountered,
            self.institutions.imported,
        )
        for msg in self.institutions.info_messages:
            output += '\t' + msg + '\n'
        for msg in self.institutions.warning_messages:
            output += '\t' + _('WARNING: ') + msg + '\n'
        output += '\n'

        # Translators: {}'s are numbers of nodes  # noqa
        output += _('Nodes: {} parsed, {} imported\n').format(
            self.nodes.encountered,
            self.nodes.imported,
        )
        for msg in self.nodes.info_messages:
            output += '\t' + msg + '\n'
        for msg in self.nodes.warning_messages:
            output += '\t' + _('WARNING: ') + msg + '\n'
        output += '\n'

        # Translators: {}'s are numbers of links  # noqa
        output += _('Links: {} parsed, {} imported\n').format(
            self.links.encountered,
            self.links.imported,
        )
        for msg in self.links.info_messages:
            output += '\t' + msg + '\n'
        for msg in self.links.warning_messages:
            output += '\t' + _('WARNING: ') + msg + '\n'
        output += '\n'

        if self._exceptions:
            output += _('ERRORS:\n')
            output += '\n'.join([str(exc) for exc in self._exceptions])
            output += '\n'

        return output.replace('\t', '....')
