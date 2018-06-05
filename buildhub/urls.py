# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

from django import http
from django.conf.urls import url, include

import buildhub.api.urls


urlpatterns = [
    url(r"^api/", include(buildhub.api.urls, namespace="api")),
    url(r"", lambda r: http.HttpResponse("Works\n")),
]
