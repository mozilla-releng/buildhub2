# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging

import markus
from django import http

from buildhub.main.search import BuildDoc


logger = logging.getLogger("buildhub")
metrics = markus.get_metrics("tecken")


@metrics.timer_decorator("api_search")
def search(request):
    """Proxy requests to Elasticsearch"""
    search = BuildDoc.search()
    arguments = None
    if request.method in ("POST",):
        arguments = json.loads(request.body.decode("utf-8"))
        if arguments:
            search.update_from_dict(arguments)
    metrics.incr("api_search_requests", tags=[f"method:{request.method}"])
    response = search.execute()
    logger.info(f"Finding {format(response.hits.total, ',')} total records.")
    metrics.gauge("api_search_records", response.hits.total)
    response_dict = response.to_dict()
    http_response = http.JsonResponse(response_dict)
    return http_response
