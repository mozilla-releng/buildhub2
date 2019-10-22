=================================
Development conventions and howto
=================================

.. contents::

Conventions
===========

License preamble
----------------

All code files need to start with the MPLv2 header::

    # This Source Code Form is subject to the terms of the Mozilla Public
    # License, v. 2.0. If a copy of the MPL was not distributed with this
    # file, You can obtain one at http://mozilla.org/MPL/2.0/.

Linting
-------

We use `flake8 <http://flake8.pycqa.org/>`_ for linting Python code. See
https://github.com/mozilla-services/buildhub2/blob/master/.flake8 for rules.

We use `black <https://github.com/ambv/black>`_ for fixing Python code
formatting. The specific version is in ``requirements.txt`` so use that one in
your IDE.

We use `eslint <https://eslint.org>`_ for linting and fixing JS code.

CI will fail if linting raises any errors.

To run linting tasks on Python and JS files:

.. code-block:: shell

   $ make lintcheck

To run lint-based fixing tasks on Python and JS files:

.. code-block:: shell

   $ make lintfix


Documentation
-------------

We use Sphinx_ to generate documentation. Documentation is written using
restructured text.

To build the docs, do:

.. code-block:: shell

   $ make docs

You can view the docs in ``docs/_build/html/index.html`` in your browser.

Documentation is published at `<https://buildhub2.readthedocs.io/>`_ every time
changes land in master branch.

.. _Sphinx: https://www.sphinx-doc.org/


Backend (webapp server and daemon)
==================================

The backend is written in Python using Django. This covers both the backend
webserver as well as the daemon.


Maintaining dependencies
------------------------

All Python requirements needed for development and production needs to be
listed in ``requirements.txt`` with sha256 hashes.

The most convenient way to modify this is to run ``hashin``. For example:

.. code-block:: shell

   $ pip install hashin
   $ hashin Django==1.10.99
   $ hashin other-new-package

This will automatically update your ``requirements.txt`` but it won't
install the new packages. To do that, you need to exit the shell and run:

.. code-block:: shell

   $ make build

To check which Python packages are outdated, use `piprot`_ in a shell:

.. code-block:: shell

   $ make shell
   root@...:/app# pip install piprot
   root@...:/app# piprot -o requirements.txt

The ``-o`` flag means it only lists requirements that are *out of date*.

.. note:: A good idea is to install ``hashin`` and ``piprot`` globally
   on your computer instead. It doesn't require a virtual environment if
   you use `pipx`_.

.. _piprot: https://github.com/sesh/piprot
.. _pipx: https://pypi.org/project/pipx/


Frontend (ui)
=============

The ui is a React single-page-app. It makes API calls to the backend
to retrieve data.

All source code is in the ``./ui`` directory. More specifically
the ``./ui/src`` which are the files you're most likely going to
edit to change the front-end.

All ``CSS`` is loaded with ``yarn`` by either drawing from ``.css`` files
installed in the ``node_modules`` directory or from imported ``.css`` files
inside the ``./ui/src`` directory.

The project is based on `create-react-app`_ so the main rendering engine is
React. There is no server-side rendering. The idea is that all (unless
explicitly routed in Nginx) requests that don't immediately find a static file
should fall back on ``./ui/build/index.html``. For example, loading
https://buildhub.moz.tools/uploads/browse` will actually load
``./ui/build/index.html`` which renders the ``.js`` bundle which loads
``react-router`` which, in turn, figures out which component to render and
display based on the path ("/uploads/browse" for example).

.. _`create-react-app`: https://github.com/facebookincubator/create-react-app


Handling dependencies
---------------------

A "primitive" way of changing dependencies is to edit the list
of dependencies in ``ui/package.json`` and running
``docker-compose build ui``. **This is not recommended**.

A much better way to change dependencies is to use ``yarn``. Use
the ``yarn`` installed in the Docker ui container. For example:

.. code-block:: shell

    $ docker-compose run ui bash
    > yarn outdated                   # will display which packages can be upgraded today
    > yarn upgrade date-fns --latest  # example of upgrading an existing package
    > yarn add new-hotness            # adds a new package

When you're done, you have to rebuild the ui Docker container:

.. code-block:: shell

    $ docker-compose build ui

Your change should result in changes to ``ui/package.json`` *and*
``ui/yarn.lock`` which needs to both be checked in and committed.


Tools
=====

Postgres/psql
-------------

To access the Postgres database, do:

.. code-block:: shell

   $ make psql


Elasticsearch
-------------

To access Elasticsearch, you can use the Elasticsearch API against
``http://localhost:9200``.


Deployment
==========

Buildhub2 has two server environments: stage and prod.

Buildhub2 images are located on `Docker Hub <https://hub.docker.com/r/mozilla/buildhub2/>`_.

Notifications for deployment status are in ``#buildhub`` on Slack.


Deploy to Stage
---------------

Stage is at: https://stage.buildhub2.nonprod.cloudops.mozgcp.net/

To deploy to stage, tag the master branch and push the tag::

   $ make tag


Deploy to Prod
--------------

Prod is at: https://buildhub.moz.tools/

To deploy to prod, ask ops to promote the tag on stage.


Backfilling
===========

There's a ``./manage.py backfill`` command that uses the S3 API to iterate over
every single key in an S3 bucket, filter out those called ``*buildhub.json``
and then check to see if we have those records.

The script takes FOREVER to run. The Mozilla production S3 bucket used for all
builds is over 60 million records and when listing over them you can only read
1,000 keys at a time.

When iterating over all S3 keys it first filter out the ``*buildhub.json`` ones,
compares the S3 keys and ETags with what is in the database, and inserts/updates
accordingly.


Configuration
-------------

The S3 bucket it uses is called ``net-mozaws-prod-delivery-inventory-us-east-1``
in ``us-east-1``. It's left as default in the configuration. *If* you need to
override it set, for example:

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

.. Note::

   The access key ID and secret access keys are *not* prefixed with ``DJANGO_``.


How to run it
-------------

Get ops to run:

.. code-block:: shell

   $ ./manage.py backfill

This uses ``settings.S3_BUCKET_URL`` which is the ``DJANGO_S3_BUCKET_URL``
environment variable.

The script will dump information about files it's seen into a ``.json`` file on
disk (see ``settings.RESUME_DISK_LOG_FILE`` aka.
``DJANGO_RESUME_DISK_LOG_FILE`` which is
``/tmp/backfill-last-successful-key.json`` by default). With this file, it's
possible to **resume** the backfill from where it last finished. This is useful
if the backfill breaks due to an operational error or even if you ``Ctrl-C``
the command the first time. To make it resume, you have to set the flag
``--resume``:

.. code-block:: shell

   $ ./manage.py backfill --resume

You can set this from the very beginning too. If there's no disk to get
information about resuming from, it will just start from scratch.


Migrating from Kinto (over HTTP)
================================

.. Note::

   This can be removed after Buildhub has been decomissioned.


If you intend to migrate from the old Buildhub's Kinto database you need to run:

.. code-block:: shell

   $ ./manage.py kinto-migration http://localhost:8888

That URL obviously depends on where the Kinto server is hosted. If the old Kinto
database contains old legacy records that don't conform you might get errors like::

    Traceback (most recent call last):
    ...
    jsonschema.exceptions.ValidationError: ['c:/builds/moz2_slave/m-rel-w64-00000000000000000000/build/', 'src/vs2015u3/VC/bin/amd64/link.exe'] is not of type 'string'

    Failed validating 'type' in schema['properties']['build']['properties']['ld']:
        {'description': 'Executable', 'title': 'Linker', 'type': 'string'}

    On instance['build']['ld']:
        ['c:/builds/moz2_slave/m-rel-w64-00000000000000000000/build/',
        'src/vs2015u3/VC/bin/amd64/link.exe']

Then simply run:

.. code-block:: shell

   $ ./manage.py kinto-migration http://localhost:8888 --skip-validation

Note, during an early period, where the old Kinto database is still getting populated
you can run this command repeatedly and it will continue where it left off.

.. note::

    If you have populated a previously empty PostgreSQL from records from the Kinto
    database, you have to run ``./manage.py reindex-elasticsearch`` **again**.

Migrating from Kinto (by PostgreSQL)
====================================

.. Note::

   This can be removed after Buildhub has been decomissioned.

A much faster way to migrate from Kinto (legacy Buildhub) is to have a dedicated
PostgreSQL connection.

Once that's configured you simply run:

.. code-block:: shell

   $ ./manage.py kinto-database-migration

This will validate every single record and crash if any single record is invalid.
If you're confident that all the records, about to be migrated, are valid, you can run:

.. code-block:: shell

   $ ./manage.py kinto-database-migration --skip-validation

Another option is to run the migration and run validation on each record, but
instead of crashing, simply skip the invalid ones. In fact, this is the recommended
way to migrate:

.. code-block:: shell

   $ ./manage.py kinto-database-migration --skip-invalid

Keep an eye on the log output about the number of invalid records skipped.

It will migrate **every single** record in one sweep (but broken up into batches
of 10,000 rows at a time). If it fails, you can most likely just try again.

Also, see the note about about the need to run ``./manage.py reindex-elasticsearch``
afterwards.

Configuration
-------------

When doing the migration from Kinto you can either rely on HTTP, or, you can
connect directly to a Kinto database. The way this works is it, **optionally**,
sets up a separate PostgreSQL connection. The ``kinto-migration`` script will
then be able to talk directly to this database. It's disabled by default.

To enable it, it's the same "rules" as for ``DATABASE_URL`` except it's called
``KINTO_DATABASE_URL``. E.g.:

.. code-block:: shell

    KINTO_DATABASE_URL="postgres://username:password@hostname/kinto"
