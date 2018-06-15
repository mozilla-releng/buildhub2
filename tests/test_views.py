# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.

import os

from django.urls import reverse


def test_always_index_html(client, temp_static_root, settings):
    with open(os.path.join(temp_static_root, "index.html"), "w") as f:
        f.write(
            """
            <!doctype html><html>
            <h1>Hi!</h1>
            </html>
            """.strip()
        )
    with open(os.path.join(temp_static_root, "foo.js"), "w") as f:
        f.write(
            """
            $(function() {
                alert('Hi!);
            })
            """.strip()
        )

    response = client.get("/")
    assert response.status_code == 200
    assert response["content-type"] == "text/html"
    content = response.getvalue().decode(response.charset)
    assert "<h1>Hi!</h1>" in content

    # Actually, it doesn't matter much what the URL is. You get this same content.
    response = client.get("/some/path/react/router/maybe")
    assert response.status_code == 200
    second_content = response.getvalue().decode(response.charset)
    assert content == second_content

    # However, if the file exists it gets served thanks to Whitenoise
    response = client.get("/foo.js")
    assert response.status_code == 200
    assert response["content-type"] == 'application/javascript; charset="utf-8"'
    content = response.getvalue().decode(response.charset)
    assert "alert('Hi!)" in content

    # However, since we default all URLs back to $STATIC_ROOT/index.html and
    # if you have a thing like <img src="/typo.pmg"> that would respond with
    # 200 OK and would serve up a HTML page. That makes it rather hard to debug
    # missing static assets.
    response = client.get("/image.png")
    assert response.status_code == 404


def test_custom_cache_control_whitenoise(client, temp_static_root, settings):
    with open(os.path.join(temp_static_root, "main.8741ee2b.js"), "w") as f:
        f.write("alert('Hi!)")

    response = client.get("/main.8741ee2b.js")
    assert response.status_code == 200
    assert response["content-type"] == 'application/javascript; charset="utf-8"'
    assert response["cache-control"] == "max-age=315360000, public, immutable"


def test_custom_cache_control_serve(client, temp_static_root, settings):
    with open(os.path.join(temp_static_root, "index.html"), "w") as f:
        f.write(
            """
            <!doctype html><html>
            <h1>Hi!</h1>
            </html>
            """.strip()
        )

    response = client.get("/")
    assert response.status_code == 200
    assert response["cache-control"] == "max-age=86400, public"
    assert response["last-modified"]

    response = client.get("/", HTTP_IF_MODIFIED_SINCE=response["last-modified"])
    assert response.status_code == 304


def test_contribute_json(client):
    response = client.get("/contribute.json")
    assert response.status_code == 200
    # No point testing that the content can be deserialized because
    # the view would Internal Server Error if the ./contribute.json
    # file on disk is invalid.
    assert response["Content-type"] == "application/json"


def test_legacy_search_redirect(client):
    response = client.get("/v1/buckets/build-hub/collections/releases/search")
    assert response.status_code == 301
    assert response["location"] == reverse("api:search")
