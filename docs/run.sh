#!/usr/bin/env bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -eo pipefail

usage() {
  echo "usage: ./run.sh build"
  echo ""
  echo "    build                         Build all documents"
  echo ""
  exit 1
}

[ $# -lt 1 ] && usage


case $1 in
  build)
    make html
    ;;
  *)
    exec "$@"
    ;;
esac
