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

First Principles
================

**Buildhub will never modify, create, or remove build data** from the ``buildhub.json``
files that are discovered and indexed.

Meaning, the sole purpoose of Buildhub is to download, check, and store all and
any ``buildhub.json`` file created by the Mozilla build architecture. Yes, internally
it will download and *open* the ``.json`` files but it only does this for the
purpose of doing a JSON Schema validation check.

This means, as an example, if a certain Firefox build comes into existance
but doesn't have a record in Buildhub the solution is not to change this code to
make up that record. Instead the solution is to look to ``mozilla-central``
(where most build step code run in TaskCluster exists) and make a change there.

Another example is tricks of copying from, one channel to another, and releasing
the same version but under a different channel. If that means the ``version`` field
is not correct any more, the solution is to change the ``buildhub.json`` files
instead.

**Buildhub is immutable**. If a certain ``buildhub.json`` file is created, its
primary key becomes a hash of its content. If, under the same URL, the
``buildhub.json`` is modified, it will lead to **a new record in Buildhub**.

.. note:: Some of this is different from "the old Buildhub" (aka. buildhub1) where
          it attempted to create the build data by looking at the released files.
          Especially the found executables and using various regular expressions
          to guess the version name.

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
``buildhub.json`` file matches the ``schema.yaml`` file. Since TaskCluster builds
the ``buildhub.json`` file and this service picks it up asynchronous
and delayed, there is at the moment no easy way to know an invalid
``buildhub.json`` file was built.

If you want to change the ``schema.yaml`` make sure it matches the schema used
inside ``mozilla-central`` when the ``buildhub.json`` files are created.
