================
UI Documentation
================

Overview
========

The ui code tries to be as separate from the web server code as possible.
The ui is a static app (written in React with ``react-router``) that
communicates with the web server by making AJAX calls for JSON/REST and
rendering in run-time.

The goal is for the web server (i.e. Django) to only return pure
responses in JSON (or plain text or specific to some files) and never
generate HTML templates.

The Code
========

All source code is in the ``./ui`` directory. More specifically
the ``./ui/src`` which are the files you're most likely going to
edit to change the front-end.

All ``CSS`` is loaded with ``yarn`` by either drawing from ``.css`` files
installed in the ``node_modules`` directory or from imported ``.css`` files
inside the ``./ui/src`` directory.

The project is based on `create-react-app`_ so the main rendering engine
is React. There is no server-side rendering. The idea is that all (unless
explicitly routed in Nginx) requests that don't immediately find a static file
should fall back on ``./ui/build/index.html``. For example, loading
:base_url:`/uploads/browse` will actually load ``./ui/build/index.html``
which renders the ``.js`` bundle which loads ``react-router`` which, in turn,
figures out which component to render and display based on the path
("/uploads/browse" for example).

.. _`create-react-app`: https://github.com/facebookincubator/create-react-app


Upgrading/Adding Dependencies
=============================

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


Production Build
================

(At the moment...)

Ultimately, the command ``cd ui && yarn run build`` will output
all the files you need in the ``build`` directory. These files are purely
static and do *not* depend on NodeJS to run in production.

The contents of the directory changes names every time and ``.css`` and
``.js`` files are not only minified and bundled, they also have a hash
in the filename so the files can be very aggressively cached.

The command to generate the build artifact is done by CircleCI.
See the ``.circleci/config.yml`` file which kicks off a build.

You never need the production build when doing local development, on your
laptop, with Docker.

To make the Django server use these (with Django Whitenoise), locally on
``localhost:8000``, after you've run ``yarn run build`` cp the build directory
into the root with: ``mv build ..``. Now, running something like
``http://localhost:8000`` will serve the ``./build/index.html`` file.

Proxying
========

The dev server is able to proxy any requests that would otherwise be a
``404 Not Found`` over to the the same URL but with a different host.
See the ``ui/package.json`` (the "proxy" section). Instead, it
rewrites the request to ``http://web:8000/$uri`` which is the Django server.
So, if in ``http://localhost:3000`` you try to load something like
``http://localhost:3000/api/users/search`` it knows to actually forward
that to ``http://localhost:8000/api/users/search``.

When you run in production, this is entirely disabled. To route requests
between the Django server and the static files (with its ``react-router``
implementation) that has to be configured in Nginx.
