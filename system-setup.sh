#!/usr/bin/env bash

set -v -e

apt-get update
apt-get install -y --force-yes --no-install-recommends \
    gcc \
    libpq-dev \
    libc-dev

pip install --upgrade pip~=21.3
pip install --no-cache-dir -r requirements/base.txt
# TODO: Stop installing these into the main container
pip install --no-cache-dir -r requirements/test.txt
