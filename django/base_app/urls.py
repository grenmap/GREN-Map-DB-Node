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

Synopsis: base_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information
please see: https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include,
    path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from .views.api import (
    create_superuser,
    create_token,
    flush_db,
    load_fixture,
    openapi_schema,
    status_api,
)
from visualization.urls import urlpatterns as visualization_urls
from grenml_import.urls import urlpatterns as grenml_import_urls
from django.utils.translation import gettext as _
from django.conf.urls.static import static
from django.conf import settings
from grenml_export.urls import urlpatterns as grenml_export_node_urls
from collation.urls import urlpatterns as collation_urls
from published_network_data.urls import urlpatterns as published_data_urls
from fim.urls import urlpatterns as fim_urls
from fim.views.auth import fim_login, fim_logout
from network_topology.urls import urlpatterns as network_urls
from drf_spectacular.views import SpectacularSwaggerView

polling_urls = []
if not settings.SANDBOX:
    from polling.urls import urlpatterns as polling_urls


admin.site.site_header = _('Administration')

# Redirect the admin login/logout to use FIM
admin.site.login = fim_login
admin.site.logout = fim_logout

urlpatterns = [
    path('admin/', admin.site.urls),
    path('status/', status_api),
    path('test/flushdb/', flush_db),
    path('test/loadfixture/', load_fixture),
    path('test/create_superuser/', create_superuser),
    path('test/token/', create_token),

    path('api-schema/', openapi_schema, name='api-schema'),
    path(
        'swagger-ui/',
        SpectacularSwaggerView.as_view(
            template_name='swagger-ui.html',
            url_name='api-schema',
        ),
        name='swagger-ui',
    ),
]

urlpatterns += polling_urls
urlpatterns += visualization_urls
urlpatterns += grenml_import_urls
urlpatterns += grenml_export_node_urls
urlpatterns += collation_urls
urlpatterns += published_data_urls
urlpatterns += fim_urls
urlpatterns += network_urls

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
