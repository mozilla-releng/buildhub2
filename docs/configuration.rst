=============
Configuration
=============

.. contents::

High-level things
=================

The following services are required:

1. PostgreSQL 9.6

2. Elasticsearch 6.x

3. Python and Django (run by Gunicorn)

4. Script to run ``python manage.py sqs`` (which is the never-ending daemon)

5. Datadog daemon

General Configuration
=====================

The Django settings depends on there being an environment variable
called ``DJANGO_CONFIGURATION``.

.. code-block:: shell

    # If production
    DJANGO_CONFIGURATION=Prod

    # If stage
    DJANGO_CONFIGURATION=Stage

You need to set a random ``DJANGO_SECRET_KEY``. It should be predictably
random and a decent length:

.. code-block:: shell

    DJANGO_SECRET_KEY=sSJ19WAj06QtvwunmZKh8yEzDdTxC2IPUXfea5FkrVGNoM4iOp

The ``ALLOWED_HOSTS`` needs to be a list of valid domains that will be
used to from the outside to reach the service. If there is only one
single domain, it doesn't need to list any others. For example:

.. code-block:: shell

    DJANGO_ALLOWED_HOSTS=buildhub.mozilla.org

For Sentry the key is ``SENTRY_DSN`` which is sensitive but for the
front-end (which hasn't been built yet at the time of writing) we also
need the public key called ``SENTRY_PUBLIC_DSN``. For example:

.. code-block:: shell

    SENTRY_DSN=https://bb4e266xxx:d1c1eyyy@sentry.prod.mozaws.net/001
    SENTRY_PUBLIC_DSN=https://bb4e266xxx@sentry.prod.mozaws.net/001

Content Security Policy (CSP) headers are on by default. To change the URL for
where violations are sent you can change ``DJANGO_CSP_REPORT_URI``. By default
it's set to ``''``. Meaning, unless set it won't be included as a header.
See the `MDN documentation on report-uri <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/report-uri>`_ for
more info.

.. _report-uri: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/report-uri

AWS
===

We talk to S3 in two different capacities. When we get a payload in SQS about a new
``buildhub.json`` key, we go and download that. When we download it, we use the
bucket name mentioned in the SQS message payload.

Also, we have a backfill script that you can use that will connect to S3 and download
a list of every single ``buildhub.json`` file. That bucket is called
``net-mozaws-prod-delivery-inventory-us-east-1`` in ``us-east-1``. It's left
as default in the configuration. *If* you need to override it set, for example:

.. code-block:: shell

    DJANGO_S3_BUCKET_URL=https://s3-us-west-2.amazonaws.com/buildhub-sqs-test

If you know, in advance, what the S3 bucket that is mentioned in the SQS payloads is,
you can set that up with:

.. code-block:: shell

    DJANGO_SQS_S3_BUCKET_URL=https://s3-us-west-2.amazonaws.com/mothership

If either of these are set, they are tested during startup to make sure you have
relevant read access.

Reading the S3 bucket is public and doesn't require ``AWS_ACCESS_KEY_ID``
and ``AWS_ACCESS_KEY_ID`` but to read the SQS queue these need to be set up.

.. code-block:: shell

    AWS_ACCESS_KEY_ID=AKI....H6A
    AWS_SECRET_ACCESS_KEY=....


.. note:: The access key ID and secret access keys are *not* prefixed with ``DJANGO_``.

SQS
===

The writes to S3 needs to be configured to send to an SQS. That name of that queue
needs to be set in two places:

1. In the S3 configuration
2. In this server under the name ``DJANGO_SQS_QUEUE_URL``.

The *name* of the queue is drawn from the URL. So is the region. The default
value for this is:

.. code-block:: shell

    DJANGO_SQS_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/927034868273/buildhub-s3-events

Note that when the SQS message contains a payload referring to a key and bucket
we try to download that as a file. If you know that bucket is public you can
use a client connection that does not require the connection to be signed. This is
on by default. If you want to disable it, you can set:

.. code-block:: shell

    DJANGO_UNSIGNED_SQS_S3_CLIENT=false

That means that when it does download from S3 the credentials, that ``boto3`` pick up
by default, need to match the access for that bucket.

Elasticsearch
=============

The only thing you need to configure Elasticsearch is to set an environment
variable called ``DJANGO_ES_URLS``. It can be a list with a comma separator.
For example:

.. code-block:: shell

    DJANGO_ES_URLS=http://elasticsearch.node1:9200,http://elasticsearch.node2:9200

The default value is ``http://localhost:9200``.

Gunicorn
========

At the moment, the only configuration for ``Gunicorn`` is that you can
set the number of workers. The default is 4 and it can be overwritten by
setting the environment variable ``GUNICORN_WORKERS``.

The number should ideally be a function of the web head's number of cores
according to this formula: ``(2 x $num_cores) + 1`` as `documented here`_.

.. _`documented here`: http://docs.gunicorn.org/en/stable/design.html#how-many-workers


PostgreSQL
==========

The environment variable that needs to be set is: ``DATABASE_URL``
and it can look like this:

.. code-block:: shell

    DATABASE_URL="postgres://username:password@hostname/databasename"

The connection needs to be able connect in SSL mode.
The database server is expected to have a very small footprint. So, as
long as it can scale up in the future it doesn't need to be big.

.. Note::

    Similar to the AWS access ID and AWS secret access key, this one is
    not prefixed with ``DJANGO_``.


.. _PostgreSQLforKinto:

PostgreSQL for Kinto
====================

When doing the migration from Kinto you can either rely on HTTP, or, you can
connect directly to a Kinto database. The way this works is it, **optionally**,
sets up a separate PostgreSQL connection. The ``kinto-migration`` script will
then be able to talk directly to this database. It's disabled by default.

To enable it, it's the same "rules" as for ``DATABASE_URL`` except it's called
``KINTO_DATABASE_URL``. E.g.:

.. code-block:: shell

    KINTO_DATABASE_URL="postgres://username:password@hostname/kinto"

Metrics
=======

The default configuration for all metrics is to send ``statsd`` calls to
``localhost:8125`` which is intended to be picked up by a local Datadog daemon
that buffers metrics to be sent to ``datadoghq.com``.

The three environment variables to control the statsd are as follows
(with their defaults):

1. ``DJANGO_STATSD_HOST`` (*localhost*)

2. ``DJANGO_STATSD_PORT`` (*8125*)

3. ``DJANGO_STATSD_NAMESPACE`` (*''* (empty string))

The configuration is, by default, to log all metrics measures when doing local
development.
