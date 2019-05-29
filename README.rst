buildhub2
=========

Buildhub2 is an index of build information for Firefox, Firefox Dev Edition,
Thunderbird, and Fennec.

|circleci| |docsstatus| |whatsdeployed|

* License: MPLv2
* Documentation: `<https://buildhub2.readthedocs.io/>`_
* Community Participation Guidelines: `<https://github.com/mozilla-services/tecken/blob/master/CODE_OF_CONDUCT.md>`_
* CI: `CircleCI <https://circleci.com/gh/mozilla-services/buildhub2>`_
* Dependencies: `pyup <https://pyup.io/repos/github/mozilla-services/buildhub2/>`_ |
  `Renovate <https://renovateapp.com/>`_
* Code style: `Black <https://github.com/ambv/black>`_
* Deploy status: `What's Deployed <https://whatsdeployed.io/s-3QC>`_

Production server: https://buildhub.moz.tools/

.. |circleci| image:: https://circleci.com/gh/mozilla-services/buildhub2.svg?style=svg
.. |docsstatus| image:: https://readthedocs.org/projects/buildhub2/badge/?version=latest
.. |whatsdeployed| image:: https://img.shields.io/badge/whatsdeployed-stage,prod-green.svg


Overview
--------

Every time `Taskcluster <https://tools.taskcluster.net/>`_ builds a version of
Firefox, Fennec, etc. the built files are put into an S3 bucket. One of the
files that is always accompanied is a file called ``buildhub.json`` that we
download, validate an index into a PostgreSQL database as well as
Elasticsearch.

The way we consume these is that every S3 write triggers its key into an SQS
queue which we consume with a daemon script.

The UI is a static single-page-app that helps you make Elasticsearch queries.

First Principles
----------------

Please read the
`First Principles <https://buildhub2.readthedocs.io/en/latest/architecture.html#first-principles>`_
section in the main documentation about some important basic rules about Buildhub2.

Get going
---------

`Developer documentation <https://buildhub2.readthedocs.io/en/latest/dev.html>`_.

Dockerhub
---------

We deploy what we ship to `Docker Hub <https://hub.docker.com/r/mozilla/buildhub2/>`_.

Environments and deployments
----------------------------

`Deploy documentation <https://buildhub2.readthedocs.io/en/latest/deployments.html>`_
