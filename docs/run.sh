#!/usr/bin/env bash
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
