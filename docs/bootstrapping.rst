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
