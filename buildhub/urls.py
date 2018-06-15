# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os

from django import http
from django.conf import settings
from django.conf.urls import url, include
from django.views.static import serve as django_serve
from django.views.generic import RedirectView

import buildhub.api.urls


def serve(request, **kwargs):
    if request.path_info == "/contribute.json":
        # Advantages of having our own custom view over using
        # django.view.static.serve is that we get the right content-type
        # and as a view we write a unit test that checks that the JSON is valid
        # and can be deserialized.
        with open(os.path.join(settings.BASE_DIR, "contribute.json")) as f:
            contribute_json_dict = json.load(f)
        return http.JsonResponse(contribute_json_dict, json_dumps_params={"indent": 3})
    _, ext = os.path.splitext(request.path_info)
    if ext:
        return http.HttpResponseNotFound(request.path_info)
    document_root = kwargs["document_root"]
    assert os.path.isdir(document_root), document_root

    response = django_serve(request, "/index.html", **kwargs)
    if isinstance(response, http.FileResponse):
        max_age = 60 * 60 * 24
        response["cache-control"] = f"max-age={max_age}, public"
    return response


urlpatterns = [
    # This is a legacy redirect. If someone is using the old mozilla-services/buildhub
    # elasticsearch-kinto URL, then that should continue to work.
    url(
        r"^v1/buckets/build-hub/collections/releases/search",
        RedirectView.as_view(url="/api/search", permanent=True),
    ),
    url(r"^api/", include(buildhub.api.urls, namespace="api")),
    url(r"", serve, {"document_root": settings.STATIC_ROOT}),
]
