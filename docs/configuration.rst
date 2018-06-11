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

AWS
===

The service needs to talk to the publicly availble S3 bucket where releases
are uploaded. That bucket is ``net-mozaws-prod-delivery-inventory-us-east-1``
in ``us-east-1``.

To override the name of the bucket set (for example):

.. code-block:: shell

    DJANGO_S3_BUCKET_URL=https://s3-us-west-2.amazonaws.com/buildhub-sqs-test


Reading the S3 bucket is public and doesn't require ``AWS_ACCESS_KEY_ID``
and ``AWS_ACCESS_KEY_ID`` but to read the SQS queue these need to be set up.

.. code-block:: shell

    AWS_ACCESS_KEY_ID=AKI....H6A
    AWS_SECRET_ACCESS_KEY=....


.. note:: The access key ID and secret access keys are *not* prefixed with ``DJANGO_``.

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



StatsD
======

The three environment variables to control the statsd are as follows
(with their defaults):

1. ``DJANGO_STATSD_HOST`` (*localhost*)

2. ``DJANGO_STATSD_PORT`` (*8125*)

3. ``DJANGO_STATSD_NAMESPACE`` (*''* (empty string))
