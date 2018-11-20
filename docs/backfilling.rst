===========
Backfilling
===========

.. _backfilling:

.. contents::


What it is
===========

The command ``./manage.py backfill`` is a tool to iterate over every single key in an
S3 bucket, filter out those called ``*buildhub.json`` and then for all those found,
we check if we have that record already.

The script takes a looong time to run. Hours. The Mozilla production S3 bucket used
for all builds is over 60 million records and when listing over them you can only
read 1,000 keys at a time.

How it knows what is new
========================

When iterating over all S3 keys we first filter out the ``*buildhub.json`` ones.
We then compare their S3 key name with what we have in our database. We also compare
the ETag which is also a known thing in our database. The code works like this:

.. code-block:: python

    all_previous_s3_keys = get_all_previous_s3_keys_from_database()
    for obj in objects_in_s3_bucket:
        if obj.key.endswith('buildhub.json'):
            if obj.key not in all_previous_s3_keys:
                download_and_insert(obj)
            else:
                this_etag = obj.etag
                previous_etag = all_previous_s3_keys[obj.key]
                if this_etag != previous_etag:
                    download_and_insert(obj)

In our database we don't just store the actual build (and its string hash) but we also
store the name and the ETag of the object from S3. That means we can do this
backfill very quickly without having to download all potential records to compare
them.

How to do run it
================

.. code-block:: shell

   $ ./manage.py backfill

The only configuration that matters is ``settings.S3_BUCKET_URL``. It's called
``DJANGO_S3_BUCKET_URL`` as an environment variable. This bucket needs to be
public read access.

The way it works is that it loads 1,000 records at a time from S3 in whatever
natural order they store things. This order is not necessarily useful or relevant
but it helps S3 know how to predictably return the same order of keys.

When you run it, for every "page" the script will dump information about this into a
``.json`` file on disk (see ``settings.RESUME_DISK_LOG_FILE`` aka.
``DJANGO_RESUME_DISK_LOG_FILE`` which is ``/tmp/backfill-last-successful-key.json``
by default). With this file, it's possible to **resume** the backfill from where it
last finished. This is useful if the backfill breaks due to an operational error
or even if you ``Ctrl-C`` the command the first time. To make it resume, you
have to set the flag ``--resume``:

.. code-block:: shell

   $ ./manage.py backfill --resume

You can set this from the very beginning too. If there's no disk to get information
about resuming from, it will just start from scratch.
