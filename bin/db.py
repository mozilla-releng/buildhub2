# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import os
import sys
from urllib.parse import urlparse

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


DESCRIPTION = "Create and delete the database set by DATABASE_URL."

EPILOG = "Required DATABASE_URL to be set in the environment."


def parse_dsn(dsn):
    parsed = urlparse(dsn)
    db_name = parsed.path[1:]
    adjusted_dsn = dsn[: -(len(db_name) + 1)] + "/postgres"
    return db_name, adjusted_dsn


def create_database(dsn):
    db_name, adjusted_dsn = parse_dsn(dsn)

    conn = psycopg2.connect(adjusted_dsn)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE DATABASE %s" % db_name)
        print('Created database "%s".' % db_name)
    except psycopg2.ProgrammingError:
        print('Database "%s" already exists.' % db_name)
        return 1


def drop_database(dsn):
    db_name, adjusted_dsn = parse_dsn(dsn)

    conn = psycopg2.connect(adjusted_dsn)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        cursor.execute("DROP DATABASE %s" % db_name)
        print('Database "%s" dropped.' % db_name)
    except psycopg2.ProgrammingError:
        print('Database "%s" does not exist.' % db_name)
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=DESCRIPTION.strip(), epilog=EPILOG.strip()
    )
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True
    subparsers.add_parser("drop", help="drop existing database")
    subparsers.add_parser("create", help="create database")

    args = parser.parse_args()

    try:
        dsn = os.environ["DATABASE_URL"]
    except KeyError:
        dsn = ""

    if not dsn:
        parser.error("DATABASE_URL is not set in environment")

    if args.cmd == "drop":
        return drop_database(dsn)
    elif args.cmd == "create":
        return create_database(dsn)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
