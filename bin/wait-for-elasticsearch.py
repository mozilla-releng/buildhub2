#!/usr/bin/env python

import backoff
import requests
from requests.exceptions import ConnectionError


def _backoff_hdlr(details):
    print(
        "Backing off {wait:0.1f} seconds afters {tries} tries "
        "calling function {target} with args {args} and kwargs "
        "{kwargs}".format(**details)
    )


@backoff.on_exception(
    backoff.expo,
    ConnectionError,
    max_time=10,
    on_backoff=_backoff_hdlr,
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
