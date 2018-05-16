# buildhub2

Doing Buildhub the new awesome way.

Note: This is not intended as a web server. Just an awesome ORM with
great testing and management command integration.

## Get going

Create a PostgreSQL database. E.g. `createdb buildhub2`.
Make sure it's in UTC, with:
```sh
psql buildhub2
buildhub2=# ALTER DATABASE dbname SET TIMEZONE TO UTC;
```

Run the migrations:
```sh
./manage.py migrate
```
