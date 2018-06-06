# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
import os

from django import http
from django.conf import settings
from django.conf.urls import url, include
from django.views.static import serve as django_serve

import buildhub.api.urls


def serve(request, **kwargs):
    _, ext = os.path.splitext(request.path_info)
    if ext:
        return http.HttpResponseNotFound(request.path_info)
    document_root = kwargs["document_root"]
    assert os.path.isdir(document_root), document_root
    return django_serve(request, "/index.html", **kwargs)


urlpatterns = [
    url(r"^api/", include(buildhub.api.urls, namespace="api")),
    url(r"", serve, {"document_root": settings.STATIC_ROOT}),
]
