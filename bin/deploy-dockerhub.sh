#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# THIS IS MEANT TO BE RUN BY CI

set -e

# Usage: retry MAX CMD...
# Retry CMD up to MAX times. If it fails MAX times, returns failure.
# Example: retry 3 docker push "mozilla/buildhub2:$TAG"
function retry() {
    max=$1
    shift
    count=1
    until "$@"; do
        count=$((count + 1))
        if [[ $count -gt $max ]]; then
            return 1
        fi
        echo "$count / $max"
    done
    return 0
}

# configure docker creds
retry 3  echo "$DOCKER_PASSWORD" | docker login -u="$DOCKER_USERNAME" --password-stdin

# docker tag and push git branch to dockerhub
if [ -n "$1" ]; then
    [ "$1" == master ] && TAG=latest || TAG="$1"
    docker tag buildhub2 "mozilla/buildhub2:$TAG" ||
        (echo "Couldn't tag buildhub2 as mozilla/buildhub2:$TAG" && false)
    retry 3 docker push "mozilla/buildhub2:$TAG" ||
        (echo "Couldn't push mozilla/buildhub2:$TAG" && false)
    echo "Pushed mozilla/buildhub2:$TAG"
fi
