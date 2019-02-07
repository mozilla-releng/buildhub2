# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging

import markus
from django import http
from django.conf import settings
from elasticsearch.exceptions import RequestError

from buildhub.main.models import Build
from buildhub.main.search import BuildDoc


logger = logging.getLogger("buildhub")
metrics = markus.get_metrics("buildhub2")


@metrics.timer_decorator("api_search")
def search(request):
    """Proxy requests to Elasticsearch"""
    search = BuildDoc.search()
    arguments = None
    if request.method in ("POST",):
        try:
            arguments = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError as exception:
            return http.JsonResponse({"error": str(exception)}, status=400)
        if arguments:
            if arguments.get("size") and arguments["size"] > settings.MAX_SEARCH_SIZE:
                return http.JsonResponse(
                    {"error": f"Search size too large ({arguments['size']})"},
                    status=400,
                )
            try:
                search.update_from_dict(arguments)
            except ValueError as exception:
                return http.JsonResponse({"error": exception.args[0]}, status=400)
    metrics.incr("api_search_requests", tags=[f"method:{request.method}"])
    try:
        response = search.execute()
    except RequestError as exception:
        return http.JsonResponse(exception.info, status=400)
    logger.info(f"Finding {format(response.hits.total, ',')} total records.")
    metrics.gauge("api_search_records", response.hits.total)
    response_dict = response.to_dict()
    http_response = http.JsonResponse(response_dict)
    return http_response


def records(request):
    context = {"builds": {"total": Build.objects.all().count()}}
    return http.JsonResponse(context)
