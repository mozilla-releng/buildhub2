# buildhub2

[![CircleCI](https://circleci.com/gh/mozilla/buildhub2.svg?style=svg)](https://circleci.com/gh/mozilla/buildhub2)
[![Code style](https://img.shields.io/badge/Code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Documentation Status](https://readthedocs.org/projects/buildhub2/badge/?version=latest)](https://buildhub2.readthedocs.io/en/latest/?badge=latest)


Please use the documentation on: [buildhub2.readthedocs.io](https://buildhub2.readthedocs.io/)

## Overview

Every time [Taskcluster](https://tools.taskcluster.net/) builds a version of
Firefox, Fennec, etc. the built files are put into an S3 bucket. One of the files
that is always accompanied is a file called `buildhub.json` that we download,
validate an index into a PostgreSQL database as well as Elasticsearch.

The way we consume these is that every S3 write triggers its key into an SQS queue
which we consume with a daemon script.

The UI is a static single-page-app that helps you make Elasticsearch queries.

## Get going

See the [Developer documentation](https://buildhub2.readthedocs.io/en/latest/dev.html).

## Dockerhub

We deploy what we ship to [Docker Hub](https://hub.docker.com/r/mozilla/buildhub2/).

## Licence

[MPL 2.0](http://www.mozilla.org/MPL/2.0/)
