#!/usr/bin/env python

import backoff
import requests
from requests.exceptions import ConnectionError, HTTPError


def _backoff_hdlr(details):
    # We can do this because this handler function is very specific.
    details["url"] = details["args"][0]
    print(
        "Backing off {url} for {wait:.1f}s, {tries} tries, {elapsed:.1f}s elapsed"
        "".format(**details)
    )


def _fatal_code(exception):
    """Return True if this should halt the backoff attempts.
    Return true and the backoff will try again unless the max_tries or max_time
    conditions are true."""
    if isinstance(exception, HTTPError):
        # Sometimes, if we try to send requests to Elasticsearch whilst it's
        # starting up you can get a 401 Unauthorized error.
        if exception.response.status_code == 401:
            return False
        return True
    return False


@backoff.on_exception(
    backoff.constant,
    (ConnectionError, HTTPError),
    max_tries=12,
    on_backoff=_backoff_hdlr,
    interval=2,
    jitter=None,
    giveup=_fatal_code,
)
def fetch(url):
    response = requests.get(url)
    response.raise_for_status()


def run(hostname, port=None):
    if "http://" in hostname:
        hostname = hostname.replace("http://", "")
    if port is None:
        hostname, port = hostname.split(":")
    url = f"http://{hostname}:{port}"

    try:
        fetch(url)
        return 0
    except ConnectionError:
        print(f"Unable to connect to {url}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(run(*sys.argv[1:]))
