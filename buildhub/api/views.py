import requests

from django import http
from django.conf import settings


def search(request):
    """Proxy requests to Elasticsearch"""
    # XXX Need to figure out how kinto-elasticsearch does this
    if request.method in ('POST',):
        if list(request.POST.items()):
            raise NotImplementedError('work harder!')
        response = requests.get(
            settings.ES_URLS[0] + '/' + settings.ES_BUILD_INDEX + '/_search'
        )
        response.raise_for_status()
        http_response = http.JsonResponse(response.json())
    else:
        http_response = http.JsonResponse({'it': 'works'})
    return http_response
