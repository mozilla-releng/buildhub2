==========
Deployment
==========

.. contents::

Environments and deploys
========================

Buildhub2 has two server environments: stage and prod.


Stage
-----

Stage is at: https://stage.buildhub2.nonprod.cloudops.mozgcp.net/

To deploy to stage, tag the master branch and push the tag::

   $ make tag


.. Note::

   This assumes the remote is named "origin".


Prod
----

Prod is at: https://buildhub.moz.tools/

To deploy to prod, ask ops to promote the tag on stage.


About tags
==========

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

.. _CircleCI: https://circleci.com/gh/mozilla-services/buildhub2
.. _`Docker Hub`: https://hub.docker.com/r/mozilla/buildhub2/


Bootstrapping
=============

See the :ref:`Bootstrapping <bootstrapping>` documentation for how to prepare the
databases for the very first time.
