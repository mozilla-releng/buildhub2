=======================
Development environment
=======================

You can set up a Buildhub2 development environment that runs on your local
machine for development and testing.


Setting up
==========

To set up a dev environment, install the following:

* Docker
* make
* git
* bash

Clone the repo from GitHub at `<https://github.com/mozilla-services/buildhub2>`_.

Then do the following:

.. code-block:: shell

   # Build the Docker images
   $ make build

   # Wipe and initialize services
   $ make setup

If ``make setup`` fails, run the following command to see detailed logs:

.. code-block:: shell

   $ docker-compose up

Once you've done that, you can run Buildhub2.

Configuration
=============

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
it's set to ``''``. Meaning, unless set it won't be included as a header. See
the `MDN documentation on report-uri`__ for more info.

.. _report-uri: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/report-uri
__ report-uri_

To configure writing to BigQuery, the following variables will need to be set:

.. code-block:: shell

    DJANGO_BQ_ENABLED=True
    DJANGO_BQ_PROJECT_ID=...
    DJANGO_BQ_DATASET_ID=...
    DJANGO_BQ_TABLE_ID=...

The project and dataset will need to be provisioned before running the server
with this functionality enabled. Additionally, credentials will need to be
passed to the server. If it is running in Google Compute Engine, this is
configured through the default service account. To run this via
``docker-compose``, the following lines in ``docker-compose.yml`` will need to
be un-commented:

.. code-block:: yaml

    volumes:
      ...
      # - ${GOOGLE_APPLICATION_CREDENTIALS}:/tmp/credentials

In addition, set the following variable after downloading the service account
credentials from ``IAM & admin > Service accounts`` in the Google Cloud Platform
console for the project.

.. code-block:: shell

    GOOGLE_APPLICATION_CREDENTIALS=/path/to/keyfile.json

Run ``make test`` and check that none of the tests are skipped.

Adding data
===========

FIXME: How to add data to your local instance?


Running the webapp
==================

The webapp consists of a part that runs on the server powered by Django and
a part that runs in the browser powered by React.

To run all the services required and the server and a service that builds
static assets needed by the browser ui, do:

.. code-block:: shell

   $ make run

This will start the server on port ``8000`` and the web ui on port ``3000``.

You can use ``http://localhost:3000`` with your browser to use the web interface
and curl/requests/whatever to use the API.


Running the daemon
==================

Buildhub2 has a daemon that polls SQS for events and processes new files on
archive.mozilla.org.

You can run the daemon with:

.. code-block:: shell

   $ make daemon

You can quit it with ``Ctrl-C``.


Troubleshooting
===============

Below are some known issues you might run into and their workarounds.

* ElasticSearch fails with following error during ``make setup``:

.. code-block:: shell

   elasticsearch    | ERROR: [1] bootstrap checks failed
   elasticsearch    | [1]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]

This can be worked around by running:

.. code-block:: shell

   $ sysctl -w vm.max_map_count=262144

If you want this to be permanent across restarts, you also need to add this
value to ``/etc/sysctl.conf``.


