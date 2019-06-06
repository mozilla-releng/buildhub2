===============
Using Buildhub2
===============

.. contents::

Products supported by Buildhub2
===============================

Buildhub2 indexes build information that exists on archive.mozilla.org.

If you want build information for your product in Buildhub2, you'll need to
change the release process to additionally add files to archive.mozilla.org
in the same way that Firefox does.


Fields in Buildhub2
===================

Buildhub2 records have the same structure as ``buildhub.json`` files on archive.mozilla.org.

Example: https://archive.mozilla.org/pub/firefox/candidates/68.0b7-candidates/build1/linux-x86_64/en-US/buildhub.json 

.. code-block::

   {
     "build": {
       "as": "/builds/worker/workspace/build/src/clang/bin/clang -std=gnu99",
       "cc": "/builds/worker/workspace/build/src/clang/bin/clang -std=gnu99",
       "cxx": "/builds/worker/workspace/build/src/clang/bin/clang++",
       "date": "2019-06-03T18:14:08Z",
       "host": "x86_64-pc-linux-gnu",
       "id": "20190603181408",
       "target": "x86_64-pc-linux-gnu"
     },
     "download": {
       "date": "2019-06-03T20:49:46.559307+00:00",
       "mimetype": "application/octet-stream",
       "size": 63655677,
       "url": "https://archive.mozilla.org/pub/firefox/candidates/68.0b7-candidates/build1/linux-x86_64/en-US/firefox-68.0b7.tar.bz2"
     },
     "source": {
       "product": "firefox",
       "repository": "https://hg.mozilla.org/releases/mozilla-beta",
       "revision": "ed47966f79228df65b6326979609fbee94731ef0",
       "tree": "mozilla-beta"
     },
     "target": {
       "channel": "beta",
       "locale": "en-US",
       "os": "linux",
       "platform": "linux-x86_64",
       "version": "68.0b7"
     }
   }

If you want different fields, the Taskcluster task will need to be changed to include
the new information. Additionally, Buildhub2 will need to adjust the schema. Please
open up an issue with your request.


Website
=======

You can query build information using the website at `<https://buildhub.moz.tools/>`_.

The search box uses Elasticsearch querystring syntax.

.. seealso::

   Elasticsearch querystring syntax: https://www.elastic.co/guide/en/elasticsearch/reference/6.7/query-dsl-query-string-query.html#query-string-syntax


Example: All records for a given build id
-----------------------------------------

Search for::

    build.id:20170713200529
 

API
===

The API endpoint is at: https://buildhub.moz.tools/api/search

You can query it by passing in Elasticsearch search queries as HTTP POST payloads.

.. seealso::

   Links to Elasticsearch 6.7 search documentation:

   * Request body search: https://www.elastic.co/guide/en/elasticsearch/reference/6.7/search-request-body.html
   * Query: https://www.elastic.co/guide/en/elasticsearch/reference/6.7/search-request-query.html
   * Query DSL: https://www.elastic.co/guide/en/elasticsearch/reference/6.7/query-dsl.html
   * Aggregations: https://www.elastic.co/guide/en/elasticsearch/reference/6.7/search-aggregations.html


Example: Is this an official build id?
--------------------------------------

Is ``20170713200529`` an official build id?

We can query for records where ``build.id`` has that value, limit the size to 0
so we're not getting records, back, and then check the total.

.. code-block:: shell

   $ curl -s -X POST https://buildhub.moz.tools/api/search \
       -d '{"size": 0, "query": {"term": {"build.id": "20170713200529"}}}' | \
       jq .hits.total


Example: What is the Mercurial commit ID for a given build id?
--------------------------------------------------------------

What is the Mercurial commit ID for a given build id?

Query for the build id and only return 1 record. Extract the specific value
using ``jq``.

.. code-block:: shell

   $ curl -s -X POST https://buildhub.moz.tools/api/search \
       -d '{"size": 1, "query": {"term": {"build.id": "20170713200529"}}}' | \
       jq '.hits.hits[] | ._source.source.revision'


Example: What platforms are available for a given build id?
-----------------------------------------------------------

What platforms are available for a given build id?

To get this, we want to do an aggregation on ``target.platform``. We set the
``size`` to 0 so it doesn't return aggregations and results for the query.

.. code-block:: shell

   $ curl -s -X POST https://buildhub.moz.tools/api/search \
       -d '{"size": 0, "query": {"term": {"build.id": "20170713200529"}}, "aggs": {"platforms": {"terms": {"field": "target.platform"}}}}' | \
       jq '.aggregations.platforms.buckets'
