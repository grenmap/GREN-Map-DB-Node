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

Synopsis: Migration to auto-run a function that populates a set of
    default ID collision Rules to run after database changes.
"""

from django.db import migrations
from ..defaults import populate_default_id_collision_rulesets_from_migrations
from ..defaults import unpopulate_default_id_collision_rulesets_from_migrations


class Migration(migrations.Migration):

    dependencies = [
        ('collation', '0003_auto_20221115_2042'),
    ]

    operations = [
        migrations.RunPython(
            populate_default_id_collision_rulesets_from_migrations,
            unpopulate_default_id_collision_rulesets_from_migrations,
        ),
    ]
