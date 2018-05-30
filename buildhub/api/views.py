# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging

from django import http

from buildhub.main.search import BuildDoc


logger = logging.getLogger('buildhub')


def search(request):
    """Proxy requests to Elasticsearch"""
    search = BuildDoc.search()
    if request.method in ('POST',):
        arguments = json.loads(request.body.decode('utf-8'))
        if arguments:
            search.update_from_dict(arguments)
    response = search.execute()
    logger.info(
        f"Finding {format(response.hits.total, ',')} total records."
    )
    response_dict = response.to_dict()
    http_response = http.JsonResponse(response_dict)
    return http_response
