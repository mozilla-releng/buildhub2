=======
Testing
=======

Unit tests
==========

Buildhub2 has a suite of unit tests for Python. We use pytest to run them.

.. code-block:: shell

   $ make test

If you need to run specific tests or pass in different arguments, you can run
bash in the base container and then run ``pytest`` with whatever args you want.
For example:

.. code-block:: shell

   $ make shell
   root@...:/app# pytest


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
