# buildhub2

Doing Buildhub the new awesome way. I.e. consuming an AWS SQS (Simple
Queue Service) looking for `buildhub.json` files in S3.

Note: This is not intended as a web server. Just an ORM with
great testing and management command integration.

## Get going

Create a PostgreSQL database. E.g. `createdb buildhub2`.
Make sure it's in UTC, with:

```sh
psql buildhub2
buildhub2=# ALTER DATABASE dbname SET TIMEZONE TO UTC;
```

Note, when Django starts it will always set the timezone to UTC but setting
it permanently helps when using `psql` manually to poke around.

Run the migrations:

```sh
./manage.py migrate
```

Set the default Mozilla AWS DEV SQS queue URL in a `.env` file. E.g.

```sh
echo 'SQS_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/927034868273/buildhub-s3-events' >> .env
```

To start consuming the SQS queue you need to run:

```sh
./manage.py daemon
```

**This will run forever until any Python exception happens.** The code
deliberately does not do any recovery. If _any_ exception happens, the daemon
will exit and _you_ have to start it again.

By default we use the `dockerflow` logging format which means we use
`dockerflow.logging.JsonLogFormatter` to format each logging line. For
local development it's probably easier to use the plain `verbose` formatter.
To change that, set:

```sh
LOGGING_USE_JSON=False
```

## How to run `s3-file-maker`

[`s3-file-maker`](https://github.com/mostlygeek/s3-file-maker) is a
tool for putting files into an S3 bucket, some of which are valid (but
each time randomish) `buildhub.json` files.

To run it:

```sh
cd "$GOPATH/src"
git clone https://github.com/mostlygeek/s3-file-maker.git
cd s3-file-maker
dep ensure
go build main.go
./main [--help]
```

It relies on the credentials in `~/.aws/credentials`. Make sure the
`[default]` in there point to the Mozilla AWS DEV IAM.

Running this script, it will populate an S3 bucket called
[`buildhub-sqs-test`](https://s3.console.aws.amazon.com/s3/buckets/buildhub-sqs-test/?region=us-west-2&tab=overview).
All writes to that DB will trigger an SQS event to a queue called
[`buildhub-s3-events`](https://sqs.us-west-2.amazonaws.com/927034868273/buildhub-s3-events).

## Run the tests

Run all the things:

```sh
pytest
```

With code coverage:

```sh
pytest --cov=buildhub --cov-report html
```
