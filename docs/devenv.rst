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
it's set to ``''``. Meaning, unless set it won't be included as a header.
See the `MDN documentation on report-uri <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/report-uri>`_ for
more info.

.. _report-uri: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/report-uri


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
