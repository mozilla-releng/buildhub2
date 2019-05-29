# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import socket
import sys
import re

logging.basicConfig(
    format="%(asctime)s %(message)s", stream=sys.stdout, level=logging.DEBUG
)
logger = logging.getLogger(__name__)

msg_format = re.compile(
    r"(?P<name>.*?):(?P<value>.*?)\|(?P<type>[a-z])(\|#(?P<tags>.*))?"
)

"""
These types will only be shown once, as they're noisy...

This should really be moved into the code, so events can easily be turned off
via the configuration instead of hacking within this helper script.
"""
single_events = []

# Stores the seen events (that are within single_events)
processed_events = {}


def bind_udp(ip=None, port=None):
    ip = ip or "0.0.0.0"
    port = port or 8125

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))

    return sock


def process(msg):
    m = msg_format.match(msg)
    if not m:
        logger.info("dogstatsd message: `Regex Error` {}".format(msg))
    else:
        event_name = m.group("name")
        if event_name in single_events:
            if event_name not in processed_events:
                processed_events[event_name] = dict(
                    value=m.group("value"), type=m.group("type"), tags=m.group("tags")
                )
        logger.info("dogstatsd message: {}".format(msg))


if __name__ == "__main__":
    sock = bind_udp()
    while True:
        data, addr = sock.recvfrom(1024)
        process(data.decode("utf-8"))
