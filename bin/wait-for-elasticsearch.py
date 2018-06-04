#!/usr/bin/env python

import backoff
import requests
from requests.exceptions import ConnectionError


def _backoff_hdlr(details):
    print(
        "Backing off {wait:.1f}s, {tries} tries, {elapsed:.1f}s elapsed"
        "".format(**details)
    )


@backoff.on_exception(
    backoff.constant,
    ConnectionError,
    max_tries=12,
    on_backoff=_backoff_hdlr,
    interval=2,
    jitter=None,
)
def fetch(url):
    response = requests.get(url)
    response.raise_for_status()


def run(hostname, port):
    url = f"http://{hostname}:{port}"

    try:
        fetch(url)
        return 0
    except ConnectionError:
        print(f"Unable to connect to {url}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(run(*sys.argv[1:]))
