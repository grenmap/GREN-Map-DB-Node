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

This file contains the definition for R&S Identity model

"""
import re
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
import logging
import os

logger = logging.getLogger(__name__)

# The Django's username only allows for: letters, numbers,
# and @/./+/-/_ characters
DJANGO_ALLOWED_CHARS = ['@', '.', '+', '-', '_']


class RSIdentity(models.Model):
    """
    Research and Scholarship (R&S) Identify
    """

    # Related Django User
    user = models.ForeignKey(
        User,
        default=None, null=True,
        on_delete=models.SET_NULL,
        verbose_name=_('User'),
    )

    # eduPerson Principle Name
    eppn = models.CharField(
        _('eduPerson Principal Name'),
        max_length=150,
        blank=False, unique=True,
        error_messages={
            'unique': _('A R&S Identity with that eppn already exists.'),
        },
    )

    email = models.EmailField(
        _('email'),
        default='', blank=True,
    )

    display_name = models.CharField(
        _('Display Name'),
        max_length=150,
        default='', blank=True,
    )

    first_name = models.CharField(
        _('First Name'),
        max_length=150,
        default='', blank=True,
    )

    last_name = models.CharField(
        _('Last Name'),
        max_length=150,
        default='', blank=True,
    )

    def save(self, *args, **kwargs):
        if not self.eppn:
            raise ValidationError(
                'eppn is empty'
            )
        try:
            self.create_update_user()
        except Exception as err:
            raise ValidationError(
                'Save RS Identify failed with exception: %s' % err
            )

        super().save(*args, **kwargs)

    def translated_eppn(self, eppn):
        """
        Replace the chararters with '_' if it's not in the
        allowed charater list for Django username
        """
        eppn_modified = re.sub(r'[^@.+-//_a-zA-Z0-9]', "_", eppn)
        return eppn_modified

    def create_django_user(self, django_username):
        # Create a new Django user
        staff_u = False
        super_u = False
        admin_eppns = os.getenv('ADMIN_EPPNS')
        logger.info('ADMIN_EPPNS list: %s' % admin_eppns)
        # The user in the ADMIN_EPPNS list gets admin permission
        if admin_eppns:
            if self.eppn.lower() in admin_eppns.lower().split(' '):
                staff_u = True
                super_u = True
        django_user = User.objects.create(
            username=django_username,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            is_staff=staff_u,
            is_superuser=super_u,
        )
        self.user = django_user
        if super_u:
            logger.info(f'Created SUPER user: {django_user.username} \
                with eppn: {self.eppn}')
        else:
            logger.info(f'Created general user: {django_user.username} \
                with eppn: {self.eppn}')

    def update_django_user(self, django_user):
        # Update Django user
        updated = False
        for field in ['first_name', 'last_name', 'email']:
            if (not getattr(django_user, field)) and getattr(self, field):
                setattr(django_user, field, getattr(self, field))
                updated = True
        if updated:
            django_user.save()
            logger.info('Updated user: %s' % django_user.username)

    def create_update_user(self):
        """
        Create or update django user. When create a new user,
        if the username is existed already, the new name will be
        added by a number until it's unique.
        """
        try:
            rs = RSIdentity.objects.get(eppn__iexact=self.eppn)
            self.update_django_user(rs.user)
        except ObjectDoesNotExist:
            modified_eppn = self.translated_eppn(self.eppn)
            try:
                num = 2
                django_username = modified_eppn
                while True:
                    User.objects.get(username=django_username)
                    logger.info('Found duplicated name so append number')
                    django_username = modified_eppn + str(num)
                    num += 1
            except ObjectDoesNotExist:
                self.create_django_user(django_username)

    class Meta:
        verbose_name = _('RS Identity')
        verbose_name_plural = _('RS Identities')
