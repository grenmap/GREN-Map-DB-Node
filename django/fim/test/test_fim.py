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

Synopsis: Tests for rs_identity models.
"""

import pytest

from fim.models import RSIdentity


@pytest.mark.django_db(transaction=True)
class TestRSIdentity:

    def test_eppn_with_special_char_replace1(self):
        """
        Check the django user will be created
        by replacing special characters
        """
        eppn1 = "testuser2#user11#!33@example.org"
        expect_username = "testuser2_user11__33@example.org"
        rs = RSIdentity.objects.create(
            eppn=eppn1,
            email="test@test.com"
        )
        assert rs.user.username == expect_username

    def test_eppn_with_special_char_replace2(self):
        """
        Check the django user will be created
        by replacing special characters
        """
        eppn1 = "testuse^*r2@user11@example.org"
        expect_username = "testuse__r2@user11@example.org"
        rs = RSIdentity.objects.create(
            eppn=eppn1,
            email="test@test.com"
        )
        assert rs.user.username == expect_username

    def test_eppn_with_special_char_without_replace(self):
        """
        Check the django user will be created
        by the same eppn which include all the allowed
        special characters
        """
        eppn1 = "testuser2@.+-_user3@example.org"
        rs = RSIdentity.objects.create(
            eppn=eppn1,
            email="test@test.com"
        )
        assert rs.user.username == eppn1

    def test_eppn_with_existing_name(self):
        """
        Check the django user will be created
        by different name
        """
        eppn1 = "testuser_2@example.org"
        eppn2 = "testuser#2@example.org"
        eppn3 = "testuser*2@example.org"
        rs1 = RSIdentity.objects.create(
            eppn=eppn1,
            email="test@test.com"
        )
        assert rs1.user.username == eppn1

        rs2 = RSIdentity.objects.create(
            eppn=eppn2,
            email="test2@test.com"
        )
        assert rs2.user.username == eppn1 + '2'

        rs3 = RSIdentity.objects.create(
            eppn=eppn3,
            email="test3@test.com"
        )
        assert rs3.user.username == eppn1 + '3'
