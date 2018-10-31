=============
Bootstrapping
=============

.. _bootstrapping:

.. contents::


Starting From Scratch
=====================

At this point, let's assume you have created a PostgreSQL database and an Elasticsearch
connection. First create the PostgreSQL database:

.. code-block:: shell

   $ ./manage.py migrate

That will create all the necessary tables.

Next, you need to create the Elasticsearch index:

.. code-block:: shell

   $ ./manage.py reindex-elasticsearch

Check that this created the index by visiting ``http://localhost:9200/buildhub2``
where the base URL needs to match what you set ``DJANGO_ES_URLS`` to.


Migrating from Kinto (over HTTP)
================================

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

A much faster way to migrate from Kinto (legacy Buildhub) is to have a dedicated
PostgreSQL connection. See the :ref:`PostgreSQLforKinto` section for setting up an
explicit connection just for the Kinto database.

Once that's configured you simply run:

.. code-block:: shell

   $ ./manage.py kinto-database-migration --skip-validation

It will migrate **every single** record in one sweep (but broken up into batches
of 10,000 rows at a time). If it fails, you can most likely just try again.

Also, see the note about about the need to run ``./manage.py reindex-elasticsearch``
afterwards.
