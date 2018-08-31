==========
Deployment
==========

.. contents::

Environments
============

Mozilla Symbol Server is deployed in 3 different environments:

1. Production (To Be Decided)

2. Stage (To Be Decided)

The stage environments is updated on every new tag created.

The prod environment requires a tag and a manual task by CloudOps.

Tagging
=======

Code is pushed to GitHub. On every push, CircleCI_ builds a
"latest" build to `Docker Hub`_ as well as one based on the CircleCI
build number and one based on any git tags.

Git tagging is done manually by the team. The expected format is something
like this::

    git tag -s -a 2017.04.17 -m "Message about this release"

The tag format isn't particularly important but it's useful to make it
chronological in nature so it's easy to compare tags without having
to dig deeper. The format is a date, but if there are more tags
made on the same date, append a hyphen and a number. For example::

    git tag -s -a 2017.04.17-2 -m "Fix for sudden problem"

.. _CircleCI: https://circleci.com/gh/mozilla/buildhub2
.. _`Docker Hub`: https://hub.docker.com/r/mozilla/buildhub2/

Automation
==========

To make a tag run:

.. code-block:: shell

   $ make tag

and it will guide you through create a git tag and having that pushed.

Stage and production deployment requires that the development team
communicates the desired git tag name to the Cloud OPs team.

Bootstrapping
=============

See the :ref:`Bootstrapping <bootstrapping>` documentation for how to prepare the
databases for the very first time.
