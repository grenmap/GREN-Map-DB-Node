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
------------------------------------------------------------------------

This file contains the model for visualization CORS enabled origins

"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class VisualizationAllowedOrigin(models.Model):
    """
    List of allowable origins for requests to the traffic map
    """

    # The displayed name of the origin
    name = models.CharField(
        max_length=140,
        unique=True,
        verbose_name=_('name'),
        help_text=_('An easy to remember name for this hostname.'
                    ' i.e. The organization this is for.')
    )

    origin = models.CharField(
        max_length=255, null=False, unique=True,
        verbose_name=_('origin'),
    )

    active = models.BooleanField(
        default=True, null=False,
        verbose_name=_('active'),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Visualization Allowed Origin')
        verbose_name_plural = _('Visualization Map Allowed Origins')
