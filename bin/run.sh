#!/usr/bin/env bash
set -eo pipefail

# default variables
: "${PORT:=8000}"
: "${SLEEP:=1}"
: "${TRIES:=60}"
: "${GUNICORN_WORKERS:=4}"
: "${GUNICORN_TIMEOUT:=300}"

usage() {
  echo "usage: ./bin/run.sh daemon|web|migrate|web-dev|test|bash"
  exit 1
}

[ $# -lt 1 ] && usage

# Only wait for backend services in development
# http://stackoverflow.com/a/13864829
# For example, bin/test.sh sets 'DEVELOPMENT' to something
if [ ! -z ${DEVELOPMENT+x} ]; then
  echo "Waiting for elasticsearch:9200"
  ./bin/wait-for-elasticsearch.py elasticsearch 9200
else
  echo "Not waiting for any services"
fi


case $1 in
  daemon)
    ${CMD_PREFIX_PYTHON:-python} manage.py daemon
    ;;
  migrate)
    ${CMD_PREFIX_PYTHON:-python} manage.py migrate --noinput
    ;;
  web)
    ${CMD_PREFIX_PYTHON:-python} gunicorn buildhub.wsgi:application -b 0.0.0.0:${PORT} --timeout ${GUNICORN_TIMEOUT} --workers ${GUNICORN_WORKERS} --access-logfile -
    ;;
  web-dev)
    ${CMD_PREFIX_PYTHON:-python} manage.py migrate --noinput
    ${CMD_PREFIX_PYTHON:-python} manage.py runserver 0.0.0.0:${PORT}
    ;;
  test)
    pytest
    ;;
  bash)
    # The likelyhood of needing pytest-watch when in shell is
    # big enough that it's worth always installing it before going
    # into the shell. This is up for debate as time and main developers
    # make.
    echo "For high-speed test development, run: pip install pytest-watch"
    exec "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
