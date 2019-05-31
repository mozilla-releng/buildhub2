# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

.PHONY: help
help: default

.PHONY: default
default:
	@echo "Welcome to the buildhub\n"
	@echo "The list of commands for local development:\n"
	@echo "  build            Builds the docker images for the docker-compose setup"
	@echo "  setup            Initializes and sets up Postgres and Elasticsearch services"
	@echo "  run              Runs the whole stack, served on http://localhost:8000/"
	@echo "  gunicorn         Runs the whole stack using gunicorn on http://localhost:8000/"
	@echo "  daemon           Start the SQS daemon"
	@echo "  stop             Stops the docker containers"
	@echo ""
	@echo "  shell            Opens a Bash shell"
	@echo "  currentshell     Opens a Bash shell into existing running 'web' container"
	@echo "  migrate          Runs the Django database migrations"
	@echo "  clean            Stops and removes all docker containers"
	@echo "  test             Runs the Python test suite"
	@echo "  lintcheck        Check that the code is well formatted"
	@echo "  lintfix          Just try to fix all the possible linting errors"
	@echo "  django-shell     Django integrative shell"
	@echo "  psql             Open the psql cli"
	@echo "\n"

# Dev configuration steps
.docker-build:
	make build

.env:
	./bin/cp-env-file.sh

.PHONY: build
build: .env
	docker-compose build
	touch .docker-build

.PHONY: setup
setup: .env
	docker-compose run web /app/bin/setup-services.sh

.PHONY: clean
clean: .env stop
	docker-compose rm -f
	rm -rf coverage/ .coverage
	rm -fr .docker-build

.PHONY: migrate
migrate: .env
	docker-compose run web python manage.py migrate

.PHONY: shell
shell: .env .docker-build
	# Use `-u 0` to automatically become root in the shell
	docker-compose run --user 0 --service-ports web bash

.PHONY: currentshell
currentshell: .env .docker-build
	# Use `-u 0` to automatically become root in the shell
	docker-compose exec --user 0 web bash

.PHONY: psql
psql: .env .docker-build
	docker-compose run db psql --host db --username postgres

.PHONY: stop
stop: .env
	docker-compose stop

.PHONY: test
test: .env .docker-build
	docker-compose run web test

.PHONY: run
run: .env .docker-build
	docker-compose up web ui

.PHONY: gunicorn
gunicorn: .env .docker-build
	docker-compose run --service-ports web web

.PHONY: django-shell
django-shell: .env .docker-build
	docker-compose run web python manage.py shell

.PHONY: lintcheck
lintcheck: .env .docker-build
	docker-compose run web lintcheck
	docker-compose run ui lintcheck

.PHONY: lintfix
lintfix: .env .docker-build
	docker-compose run web blackfix
	docker-compose run ui lintfix

.PHONY: docs
docs: .env .docker-build
	docker-compose run docs

.PHONY: tag
tag:
	@bin/make-tag.py

.PHONY: daemon
daemon: .env
	docker-compose run web python manage.py daemon
