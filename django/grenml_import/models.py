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

Synopsis: ORM model for GRENML imports, including files (XML or
    spreadsheet) and string data.  Logic to initiate import processes.
"""

import logging
import os
from io import BytesIO
from datetime import datetime

from redis import Redis

from django.db import models
from django.dispatch import Signal, receiver
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task

from grenml.excel_converter import XLSParser, ExcelParseError

from network_topology.models.topology import Topology
from .importer import GRENMLImporter
from .utils.import_exceptions import StreamParseError
from .utils.import_log import ImportLog
from .utils.import_exceptions import ImportError


START_IMPORTING_FILE = Signal()


logger = logging.getLogger(__name__)


UPLOAD_FILE_PATH = 'uploads/'
UPLOAD_FILE_TIMESTAMP_STRFTIME_FORMAT = '%Y-%m-%dT%H%M%S'
UPLOAD_FILE_NAME_TEMPLATE = '{path}{timestamp}.{filename}'


def file_name(instance, filename):
    """
    Calculates a file path and name, including timestamp.
    """
    return os.path.join(UPLOAD_FILE_NAME_TEMPLATE.format(
        path=UPLOAD_FILE_PATH,
        timestamp=datetime.utcnow().strftime(UPLOAD_FILE_TIMESTAMP_STRFTIME_FORMAT),
        filename=filename.split('.')[-1].strip().lower(),
    ))


def write_file_contents_to_redis(file_path):
    """
    Creates a key-value pair on redis associating the file path
    to its contents.
    """
    logger.info('write_file_contents_to_redis: %s - starting', file_path)
    r = Redis.from_url(os.environ.get('REDIS_HOST'))
    file_contents = None
    with open(file_path, 'rb') as f:
        file_contents = f.read()
    r.set(file_path, file_contents)
    logger.info('write_file_contents_to_redis: %s - done', file_path)


def read_stream_from_redis(key):
    """
    Gets then deletes a value from redis.
    Returns it as a byte stream.
    """
    r = Redis.from_url(os.environ.get('REDIS_HOST'))
    file_contents = r.get(key)
    r.delete(key)
    stream = BytesIO(file_contents)
    logger.info('read_stream_from_redis: %s', key)
    return stream


def create_file_from_value_in_redis(file_path):
    """
    Uses the file_path:
    - as a key in redis, to obtain a value, then
    - to create a new file whose contents will be the value received
      from redis.
    """
    # read contents from redis
    r = Redis.from_url(os.environ.get('REDIS_HOST'))
    file_contents = r.get(file_path)
    r.delete(file_path)

    # ensure directory exists
    os.makedirs(
        os.path.dirname(file_path),
        mode=0o755,
        exist_ok=True,
    )

    # write file
    with open(file_path, 'wb') as f:
        f.write(file_contents)

    logger.info('create_file_from_value_in_redis: %s', file_path)


class GRENMLImport(models.Model):
    """
    Abstract parent class for the various ways that GRENML can be
    imported, such as by file submission, or by distributed DB polling.
    """
    imported_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Imported at'),
    )
    # Import status should reflect the options in ImportLog
    default_status = ImportLog.IMPORT_STATUS_IN_PROGRESS
    import_status = models.CharField(
        max_length=100,
        default=f'{default_status}: {ImportLog.IMPORT_STATUS_PHRASES[default_status]}',
        verbose_name=_('import status'),
    )
    import_message = models.TextField(default='', verbose_name=_('import message'))

    parent_topology = models.ForeignKey(
        Topology,
        null=True, blank=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text=_(
            'The imported file\'s root Topology will be added as a child of the selected Topology.'
            ' To add a file\'s contents as a top-level Topology, select the blank entry here.'
        ),
        verbose_name=_('Parent topology'),
    )

    @property
    def import_state(self):
        return _(self.import_status)
    import_state.fget.short_description = _('Import state')

    class Meta:
        abstract = True


class ImportData(GRENMLImport):
    """
    Represents an import of a GRENML string such as from a polling
    source or an API submission.  Provides a location to cache/store
    the GRENML, and a method to initiate the import using a
    GRENMLImporter.  Raises ImportAborted if the import fails.
    """
    source = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_('Source'),
    )
    grenml_data = models.TextField(default='', verbose_name=_('GRENML data'))

    def execute_import(self, parent_topology=None):
        """
        Initiates the import of GRENML data stored in the grenml_data
        field using a GRENMLImporter.  Raises ImportAborted on failure.
        """
        if not self.grenml_data:
            raise ImportAborted(_('No GRENML data to import.'))
        try:
            stream = BytesIO(self.grenml_data.encode())
            importer = GRENMLImporter()
            import_log = importer.from_stream(stream, parent_topology=parent_topology)
            if import_log.status[0] == import_log.IMPORT_STATUS_ABORTED:
                logger.error('GRENML import aborted.')
                status_code, status_phrase = import_log.status
                self.import_status = '{}: {}'.format(status_code, status_phrase)
                self.import_message = str(import_log)
                self.save()
                raise ImportAborted(str(import_log))
            status_code, status_phrase = import_log.status
            self.import_status = '{}: {}'.format(status_code, status_phrase)
            self.import_message = str(import_log)
            self.save()
        except Exception as e:
            logger.exception('Unexpected GRENML import error.')
            self.import_status = '{}: {}'.format(
                ImportLog.IMPORT_STATUS_ABORTED,
                _(ImportLog.IMPORT_STATUS_PHRASES[ImportLog.IMPORT_STATUS_ABORTED]),
            )
            self.import_message = str(import_log)
            self.save()
            raise ImportAborted(str(e))

    def __str__(self):
        return _(
            # Translators: do not translate between the curly brackets.
            '{import_data_verbose_name} from {source} at {timestamp}'
        ).format(
            import_data_verbose_name=self._meta.verbose_name,
            source=self.source,
            timestamp=str(self.imported_at),
        )

    class Meta:
        verbose_name = _('GRENML Data Import')
        verbose_name_plural = _('GRENML Data Imports')


class ImportFile(GRENMLImport):
    """
    Represents a GRENML or XLS file submitted to the node for import
    into the database, usually via the Django Admin or the HTTP API.
    Saving this model triggers a Signal to perform the import
    asynchronously.
    """
    file = models.FileField(
        blank=False, null=False,
        upload_to=file_name,
        verbose_name=_('File'),
    )
    name = models.CharField(max_length=64, verbose_name=_('Name'))
    token_client_name = models.CharField(
        max_length=255,
        null=True,
        blank=False,
        help_text=_(
            'Equal to the client name associated to the access token '
            'in the import request. '
            'Imports done through the admin interface will use the null value.'
        ),
        verbose_name=_('Token client name'),
    )

    ADMIN_SOURCE = 'adm'
    API_SOURCE = 'api'
    source = models.CharField(
        max_length=3,
        null=False,
        blank=False,
        choices=[(ADMIN_SOURCE, 'admin import'), (API_SOURCE, 'API import')],
        default=ADMIN_SOURCE,
        help_text=_(
            'We can import files using the admin interface '
            'or the API endpoint.'
        ),
        verbose_name=_('Source'),
    )

    topology_name = models.CharField(
        max_length=128,
        null=True, blank=True,
        help_text=_(
            'New name for the imported topology. '
            'Required for Excel .xlsx files. '
            'Not applicable for .grenml or .xml files. '
        ),
        verbose_name=_('Topology name'),
    )

    def save(self, *args, **kwargs):
        self.name = self.file.name
        super(ImportFile, self).save(*args, **kwargs)
        write_file_contents_to_redis(self.file.path)

        # This method must call super.save before writing the file
        # contents on redis because super.save provides the file path
        # the writing function needs.
        #
        # We previously used the post_save signal, emitted by
        # super.save, to start the importing process on the task runner.
        #
        # We now use a custom signal because the task runner must not
        # start until the file is written in redis.
        START_IMPORTING_FILE.send(ImportFile, instance=self)

    def __str__(self):
        return self.file.name

    class Meta:
        verbose_name = _('GRENML File Import')
        verbose_name_plural = _('GRENML File Imports')


@receiver(START_IMPORTING_FILE, sender=ImportFile)
def post_save(instance, **kwargs):
    """
    Saving the model does not actually import the file.
    However, it will trigger this Signal, which spawns a Django-Q
    task to read the file and import it.
    """
    # The function grenml_import.views.api.import_file_contents
    # triggers this receiver twice: when it creates the file
    # (model.file.save()) and when it saves the model.
    #
    # Between creating the file and saving the model, the function
    # assigns values to the model's source and token_client_name
    # attributes.
    #
    # This check avoids spawning two tasks to import the file into
    # the database.
    if instance.source == ImportFile.ADMIN_SOURCE:
        async_task(save_file, instance)
    elif instance.source == ImportFile.API_SOURCE and instance.token_client_name:
        async_task(save_file, instance)


def save_file(instance):
    """
    Imports the uploaded file.  Intended to be run in a separate thread.
    Accepts an instance of ImportFile.
    Delegates the heavy lifting to GRENMLImporter.
    """
    try:
        logger.info('Importing file %s', instance.file.path)

        extension = instance.file.path.split('.')[-1].strip().lower()
        if extension in ['xml', 'grenml'] and instance.topology_name is not None:
            raise ImportError(_('Topology name is not applicable to GRENML/XML files.'))
        if extension == 'xlsx' and instance.topology_name is None:
            raise ImportError(_('Topology name is required for Excel files.'))

        importer = GRENMLImporter()
        if extension == 'xml' or extension == 'grenml':
            stream = read_stream_from_redis(instance.file.path)
            try:
                import_log = importer.from_stream(
                    stream,
                    instance.parent_topology,
                )
            except StreamParseError as e:
                raise ImportError(_('Error importing XML file.') + '  ' + str(e))
        elif extension == 'xlsx':
            create_file_from_value_in_redis(instance.file.path)
            try:
                parser = XLSParser(instance.topology_name, '')
                manager, errors = parser.parse_file(instance.file.path)
                if len(errors) > 0:
                    raise ExcelParseError(errors)
                logger.debug('Excel file parsed successfully.')
                import_log = importer.from_grenml_manager(
                    manager,
                    instance.parent_topology,
                )
            except ExcelParseError:
                logger.exception('Excel parsing error for file %s.', instance.file.path)
                raise ImportError(_('Error importing Excel file.\n') + '\n'.join(errors))
        else:
            raise ImportError(_('Unsupported file. Supported types: .grenml, .xml, .xlsx'))

    except ImportError as e:
        status = '{}: {}'.format(
            ImportLog.IMPORT_STATUS_ABORTED,
            _(ImportLog.IMPORT_STATUS_PHRASES[ImportLog.IMPORT_STATUS_ABORTED]),
        )
        # See below for why we do a "bulk" update here
        ImportFile.objects.filter(pk=instance.pk).update(
            import_status=status,
            import_message=str(e),
        )
        return

    except Exception as e:
        logger.exception('Unknown error importing %s', instance.file.path)
        status = '{}: {}'.format(
            ImportLog.IMPORT_STATUS_ABORTED,
            _(ImportLog.IMPORT_STATUS_PHRASES[ImportLog.IMPORT_STATUS_ABORTED]),
        )
        # See below for why we do a "bulk" update here
        ImportFile.objects.filter(pk=instance.pk).update(
            import_status=status,
            import_message='Unknown error! ' + str(e),
        )
        return

    status_code, status_phrase = import_log.status
    if status_code == ImportLog.IMPORT_STATUS_COMPLETED:
        logger.info('File imported successfully: %s', instance.file.path)
    else:
        logger.warning('File import problem: ' + status_phrase)

    # We have to do a "bulk" update (of just one item) because save()
    # on an individual object triggers a Signal hook and risks a loop
    ImportFile.objects.filter(pk=instance.pk).update(
        import_status='{}: {}'.format(status_code, status_phrase),
        import_message=str(import_log),
    )


class ImportAborted(ImportError):
    pass
