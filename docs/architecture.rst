=========================
Architecture and Overview
=========================

.. contents::

High-level
==========

Mozilla builds versions of Firefox, Fennec etc. and the built files are uploaded to
an S3 bucket. With each build a ``buildhub.json`` file is created that has all the
possible information we intend to store and make searchable.

When a new file is added (or edited) in S3 it triggers an event notification that
goes to an AWS SQS queue. That's the queue that we consume constantly, with a
daemon script.

The daemon script looks for the exact file match. Since the SQS message only contains
the *name* of the S3 object, it triggers a function that downloads that file,
validates its content and stores it in PostgreSQL and also in Elasticsearch.

The four pillars of Buildhub are:

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
4. This service notices the new file.
5. Downloads the ``buildhub.json`` file from S3 using Python ``boto3``.
6. Reads its payload and checks the JSON Schema validation.
7. Inserts the JSON into PostgreSQL using the Django ORM.
8. That JSON inserted into PosgreSQL is also inserted into Elasticsearch.

Validation
==========

The validation step before storing anything is to check that the data in the
``buildhub.json`` file matches the ``schema.yaml`` file. Since TaskCluster builds
the ``buildhub.json`` file and this service picks it up asynchronous
and delayed, there is at the moment no easy way to know an invalid
``buildhub.json`` file was built.

If you want to change the ``schema.yaml`` make sure it matches the schema used
inside ``mozilla-central`` when the ``buildhub.json`` files are created.
