=======================
Developer Documentation
=======================

Code
====

License preamble
----------------

All code files need to start with the MPLv2 header::

    # This Source Code Form is subject to the terms of the Mozilla Public
    # License, v. 2.0. If a copy of the MPL was not distributed with this
    # file, You can obtain one at http://mozilla.org/MPL/2.0/.

Black
-----

All Pythoncode is expected to be formatted exactly as
`black <https://github.com/ambv/black>`_ wants it formatted. The version of ``black``
is dictated by the ``requirements.txt``. Make sure your IDE matches that.

The CI job will check that all code needs *no* formatted or else the CI build fails.

To make sure the code you write is ``black`` compatible run:

.. code-block:: shell

    $ docker-compose run web blackfix

Flake8
------

``black`` will take care of nit-style formatting such as quotation marks and
indentation but the code also needs to be ``flake8`` perfect. This is also tested
in CI. It relies on the ``.flake8`` file whose ``max-line-length`` matches
the configuration for ``black`` and it's **88 characters**.

There is no automated tool to fix ``flake8`` errors but since ``black`` takes care
of most formatting, ``flake8`` is usually checking for unused imports and such.

To check that your code is ``flake8`` perfect, run:

.. code-block:: shell

    $ docker-compose run web lintcheck

Local development
=================

You run everything in Docker with:

.. code-block:: shell

    $ make build  # only needed once
    $ make run

This will start a server that is exposed on port ``8000`` so now you can
reach ``http://localhost:8000`` with your browser or curl.

It will also start the ``create-react-app`` dev server on port ``3000``. That's
the main URL to use.

Lastly, you need to start the SQS daemon. This is started with:

.. code-block:: shell

    $ make daemon

This will run until an unexpected error happens or until you kill it with ``Ctrl-C``.

SQS Functional testing
======================

By default, for local development you can consume the SQS queue set up for Dev.
For this you need AWS credentials. You need to set up your AWS IAM Dev credentials
in ``~/.aws/credentials`` (under default) or in ``.env``.

The best tool for putting objects into S3 **and** populate the Dev SQS queue is to
run `s3-file-maker`_. To do that run, on your host:

.. code-block:: shell

    cd "$GOPATH/src"
    git clone https://github.com/mostlygeek/s3-file-maker.git
    cd s3-file-maker
    dep ensure
    go build main.go
    ./main [--help]

.. note:: This SQS queue can only be consumed by one person at a time.

.. _`s3-file-maker`: https://github.com/mostlygeek/s3-file-maker

Documentation
=============

Documentation is compiled with Sphinx_ and is available on ReadTheDocs.
API is automatically extracted from docstrings in the code.

To build the docs, run this:

.. code-block:: shell

    $ make docs

This is the same as running:

.. code-block:: shell

    $ docker-compose run docs

To iterate on writing docs and testing that what you type compiles correctly,
run the above mentioned command on every save and then open the file
``docs/_build/html/index.html``. E.g.

.. code-block:: shell

    # the 'open' command is for OSX
    $ open docs/_build/html/index.html


.. _Sphinx: http://www.sphinx-doc.org/en/stable/

Hyperactive Document Writing
============================

If you write a lot and want to see the changes much sooner after having
written them, you can temporarily enter a shell and run exactly the
minimum needed.

.. code-block:: shell

   $ docker-compose run docs bash

Now, you can run the command manually with just...:

.. code-block:: shell

   > make html

And keep an browser open to the file ``docs/_build/html/index.html`` in
the host environment.


Testing
=======

To run the tests, run this:

.. code-block:: shell

   $ make test

This is the same as running:

.. code-block:: shell

   $ docker-compose run web test

If you need to run specific tests or pass in different arguments, you can run
bash in the base container and then run ``py.test`` with whatever args you
want. For example:

.. code-block:: shell

   $ make shell
   > pytest

   <pytest output>


Hyperactive Test Running
========================

If you want to make tests run as soon as you save a file you have to
enter a shell and run ``ptw`` which is a Python package that is
automatically installed when you enter the shell. For example:

.. code-block:: shell

   $ make shell
   > pip install pytest-watch

That will re-run ``pytest`` as soon as any of the files change.
If you want to pass any other regular options to ``pytest`` you can
after ``--`` like this:

.. code-block:: shell

  $ make shell
  > pip install pytest-watch
  > ptw -- -x --other-option


Python Requirements
===================

All Python requirements needed for development and production needs to be
listed in ``requirements.txt`` with sha256 hashes.

The most convenient way to modify this is to run ``hashin`` in a shell.
For example:

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
   > pip install piprot
   > piprot -o

The ``-o`` flag means it only lists requirements that are *out of date*.

.. note:: A good idea is to install ``hashin`` and ``piprot`` globally
   on your computer instead. It doesn't require a virtual environment if
   you use `pipsi`_.

.. _piprot: https://github.com/sesh/piprot
.. _pipsi: https://github.com/mitsuhiko/pipsi


How to Memory Profile Python
============================

The trick is to install https://pypi.python.org/pypi/memory_profiler
(and ``psutil``) and then start Gunicorn with it. First start a
shell and install it there:

.. code-block:: shell

    $ docker-compose run --service-ports --user 0  web bash
    # pip install memory_profiler psutil

Now, to see memory reports of running functions, add some code to the
relevant functions you want to memory profile:

.. code-block:: python


    from memory_profiler import profile

    @profile
    def some_view(request):
        ...

Now run Gunicorn:

.. code-block:: shell

    $ python -m memory_profiler  `which gunicorn` tecken.wsgi:application -b 0.0.0.0:8000 --timeout 60 --workers 1 --access-logfile -



Python warnings
===============

The best way to get **all** Python warnings out on ``stdout`` is to run
Django with the ``PYTHONWARNINGS`` environment variable.

.. code-block:: shell

    $ docker-compose run --service-ports --user 0  web bash

Then when you're in bash of the web container:

.. code-block:: shell

    # PYTHONWARNINGS=d ./manage.py runserver 0.0.0.0:8000


How to ``psql``
===============

The simplest way is to use the shortcut in the ``Makefile``

.. code-block:: shell

    $ make psql

If you have a ``.sql`` file you want to send into ``psql`` you can do that
too with:

.. code-block:: shell

    $ docker-compose run db psql -h db -U postgres < stats-queries.sql

...for example.


Running Elasticsearch locally
=============================

Elasticsearch is started automatically in Docker thanks to the ``docker-compose.yml``.
However, since it's very memory intensive it might not work very well inside
Docker. Especially when there's starting to be quite a lot of data inside it.

On macOS you can set, in your ``.env``:

.. code-block:: shell

    DJANGO_ES_URLS=http://docker.for.mac.host.internal:9200

Now, the Python inside Docker will connect to the Elasticsearch running on your host.
