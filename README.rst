Buildhub2
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

When files are saved to the S3 bucket, the filename gets added to the SQS queue
which is consumed by the daemon. The daemon looks at the filenames and indexes
the ``buildhub.json`` ones into Buidlhub2.

Buildhub2 has a webapp which is a single-page-app that helps you make Elasticsearch
queries and displays the results.

Buildhub2 has an API which you can use to query the data.

For more on these, see the `user docs <https://buildhub2.readthedocs.io/en/latest/user.html>`_.


First Principles
----------------

**Buildhub2 reflects data on archive.mozilla.org.**

Buildhub2 will never modify, create, or remove build data from the
``buildhub.json`` files that are discovered and indexed. If the data is wrong,
it needs to be fixed on archive.mozilla.org.

**Buildhub2 records are immutable.**

If a certain ``buildhub.json`` file is created, its primary key becomes a hash
of its content. If, under the same URL, the ``buildhub.json`` is modified, it
will lead to **a new record in Buildhub**.
