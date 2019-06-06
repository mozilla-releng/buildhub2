#!/bin/bash

curl -s -X POST https://buildhub.moz.tools/api/search \
    -d '{"size": 0, "query": {"term": {"build.id": "20170713200529"}}, "aggs": {"platforms": {"terms": {"field": "target.platform"}}}}' | \
    jq '.aggregations.platforms.buckets'
