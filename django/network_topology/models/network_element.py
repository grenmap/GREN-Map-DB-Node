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

from django.db import models
from django.utils.translation import gettext_lazy as _


from .grenml import ShortNamed
from .base_model import BaseModel
from .institution import Institution


class NetworkElement(BaseModel, ShortNamed):
    """
    Model for representing network elements in GRENML
    """
    # The owners of the element
    owners = models.ManyToManyField(
        Institution,
        related_name='elements',
        verbose_name=_('owners'),
    )

    def __init__(self, *args, **kwargs):
        kwargs = self._init_trimmed_fields(**kwargs)
        super().__init__(*args, **kwargs)

    class Meta:
        verbose_name = _('Network Element')
        verbose_name_plural = _('Network Elements')
