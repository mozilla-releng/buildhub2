=========================
Architecture and Overview
=========================

.. contents::

High-level
==========

Mozilla builds versions of Firefox, Fennec etc. and the built files are
uploaded to an S3 bucket. With each build a ``buildhub.json`` file is created
that has all the possible information we intend to store and make searchable.

When a new file is added (or edited) in S3 it triggers an event notification
that goes to an AWS SQS queue.

The daemon consumes the SQS queue. The daemon script looks for the exact file
match. Since the SQS message only contains the *name* of the S3 object, it
triggers a function that downloads that file, validates its content and stores
it in PostgreSQL and also in Elasticsearch.

The four parts of Buildhub are:

1. The Django web server
2. The SQS consumer daemon script
3. The PostgreSQL and Elasticsearch that makes it possible to search
4. A ``create-react-app`` based React app for the UI which essentially runs
   `SearchKit <https://github.com/searchkit/searchkit>`_

Flow
====

1. TaskCluster builds a, for example, ``Firefox-79-installer.exe`` and a ``buildhub.json``
2. TaskCluster uploads these files into S3.
3. An S3 configuration triggers an SQS event that puts this S3-write into the queue.
4. Buildhub2 processor daemon polls the SQS queue and gets the file creation event.
5. Buildhub2 processor daemon downloads the ``buildhub.json`` file from S3 using Python ``boto3``.
6. Buildhub2 processor daemon reads its payload and checks the JSON Schema validation.
7. Buildhub2 processor daemon inserts the JSON into PostgreSQL using the Django ORM.
8. The JSON is then inserted into Elasticsearch.

Validation
==========

The validation step before storing anything is to check that the data in the
``buildhub.json`` file matches the ``schema.yaml`` file. Since TaskCluster
builds the ``buildhub.json`` file and this service picks it up asynchronous and
delayed, there is at the moment no easy way to know an invalid
``buildhub.json`` file was built.

If you want to change the ``schema.yaml`` make sure it matches the schema used
inside ``mozilla-central`` when the ``buildhub.json`` files are created.


Metrics
=======

Keys
====

The following keys are tracked in the code. Each one with a different purpose.
Generally the pattern is that every key starts with a "context" keyword followed
by an underscore. For example ``sqs_``. That prefix is primarily to be able to
trace it back to the source code, but also as a form of namespace.

``sqs_process_buildhub_json_key``
---------------------------------

**Timer.**

How long it takes to consider a ``buildhub.json`` S3 key. This involves *both*
downloading it from S3 and to attempt to insert it into our database. That
"attempt to insert" means the hash is calculated, looked up and depending on if
it was found makes an insert or does nothing.


``sqs_inserted``
----------------

**Incr.**

Count of inserts that were new and actually inserted into the database coming
from the SQS queue.

``sqs_not_inserted``
--------------------

**Incr.**

Count of inserts, from a ``buildhub.json`` that were *attempted* to be inserted
but were rejected because it was already in the database.


``sqs_messages``
----------------

**Incr.**

This is a count of messages received by consuming the SQS queue. Assume this to
be equal to the number of messages deleted from the SQS queue. It can be less
messages deleted and than received in the unexpected cases where messages
trigger an unexpected Python exception (caught in Sentry).

Note! The total number of ``sqs_inserted`` + ``sqs_not_inserted`` is not equal
to the ``sqs_messages`` because of files that are not matching what we're looking
to process.

``sqs_key_matched``
-------------------

**Incr.**

Every time an S3 record is received whose S3 key we match. Expect this number
to match ``sqs_inserted`` + ``sqs_not_inserted``.

``sqs_not_key_matched``
-----------------------

**Incr.**

Every message received (see ``sqs_messages``) can contain multiple types of
messages. We only look into the S3 records. Of those, some S3 keys we can
quickly ignore as not matched. That is what this increment is counting.

So roughly, this number is ``sqs_messages`` minus ``sqs_insert`` minus
``sqs_not_inserted``.


``api_search``
--------------

**Timer.**

Timer of how long it takes to fullfil every ``/api/search`` request. This time
involves the Django request/response overheads as well as the time it takes to
send and receive the actual query to Elasticsearch.

``api_search_records``
----------------------

**Gauge.**

A count of the number of builds found by Elasticsarch in each API/search request.

``api_search_requests``
-----------------------

**Incr.**

Measurement of the number of requests received to be proxied to Elasticsearch.
Note that every incr is accompanied with a tag. That is ``method:$METHOD``.
For example, ``method:POST``.

``backfill_inserted``
---------------------

**Incr.**

When a build is inserted from the backfill job that we did not already have.
If this number goes up it means the SQS consumption is failing.

``backfill_not_inserted``
-------------------------

**Incr.**

When running the backfill, we iterate through all keys in the S3 bucket and
to avoid having to download every single matched key, we maintain a the keys'
full path and ETag in the database to make the lookups faster. If a key and ETag
is not recognized and we attempt to download and insert it but end up not needing
to, then this increment goes up. Expect this number to stay very near zero in a
healthy environment.

``backfill_listed``
-------------------

**Incr.**

When running the backfill, this is a count of the number of S3 objects we
download per page. To get an insight into the number of S3 objects considered,
**in total**, use this number but over a window of time.

``backfill_matched``
--------------------

**Incr.**

When running the backfill, we quickly filter all keys, per batch, down to the
ones that we consider. This is a count of that. It's an increment per batch.
Similar to ``backfill_listed``, to get an insight into the total, look at this
count over a window of time.

``backfill``
------------

**Timer.**

How long it takes to run the whole backfill job. This includes iterating over
every single S3 key.

``kinto_migrated``
------------------

**Incr.**

When we run the migration from Kinto, a count of the number of messages (per
batch) that we received from batch fetching from the legacy Kinto database.

``kinto_inserted``
------------------

**Incr.**

A count of the number of builds that are inserted from the Kinto migration.
One useful use of this is to that you can run the Kinto migration repeatedly
until this number does not increment.
