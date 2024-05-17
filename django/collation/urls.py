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

Leverages the fact that this file is run on the equivalent to
application startup, to ensure some required fixtures are loaded.
This is a common Django pattern.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.db.models.signals import post_migrate
from . import views as v
from .utils.synchronize_models import synchronize_match_and_action_type_tables


router = DefaultRouter()
# The views produced by these ViewSets are intended strictly for
# testing purposes and should not be used for any other purpose.
router.register(r'match_types', v.MatchTypeViewSet)
router.register(r'match_infos', v.MatchInfoViewSet)
router.register(r'match_criteria', v.MatchCriterionViewSet)
router.register(r'action_types', v.ActionTypeViewSet)
router.register(r'actions', v.ActionViewSet)
router.register(r'action_infos', v.ActionInfoViewSet)
router.register(r'rules', v.RuleViewSet)
router.register(r'rulesets', v.RulesetViewSet)

urlpatterns = [
    path('collation/test/', include(router.urls)),
    path('collation/test/import_rulesets', v.test_import_rulesets),
    path('collation/test/export_rulesets', v.test_export_rulesets),
    path('collation/rulesets/import', v.import_rulesets),
]


# Perform the model synchronization functions on application startup,
# but wait until migrations have occurred so the ORM is synched.
post_migrate.connect(synchronize_match_and_action_type_tables)
