#!/usr/bin/env bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -eo pipefail

usage() {
  echo "usage: ./run.sh start|build|outdated|lintcheck|lintfix"
  echo ""
  echo "    start                         Start React dev server"
  echo "    build                         Build all static assets"
  echo "    outdated                      List npm packages that are outdated"
  echo "    lintcheck                     Prettier check all the source files"
  echo "    lintfix                       Let Prettier fix all source files"
  echo ""
  exit 1
}

[ $# -lt 1 ] && usage


case $1 in
  start)
    yarn run start | cat
    ;;
  build)
    yarn run build
    ;;
  outdated)
    yarn outdated
    ;;
  lintcheck)
    yarn run lint:prettier
    ;;
  lintfix)
    yarn run lint:prettierfix
    ;;
  *)
    exec "$@"
    ;;
esac
