.PHONY: build clean migrate redis-cache-cli redis-store-cli revision shell currentshell stop test run django-shell docs psql build-frontend

help:
	@echo "Welcome to the tecken\n"
	@echo "The list of commands for local development:\n"
	@echo "  build            Builds the docker images for the docker-compose setup"
	@echo "  clean            Stops and removes all docker containers"
	@echo "  migrate          Runs the Django database migrations"
	@echo "  shell            Opens a Bash shell"
	@echo "  currentshell     Opens a Bash shell into existing running 'web' container"
	@echo "  test             Runs the Python test suite"
	@echo "  run              Runs the whole stack, served on http://localhost:8000/"
	@echo "  gunicorn         Runs the whole stack using gunicorn on http://localhost:8000/"
	@echo "  lintcheck        Check that the code is well formatted"
	@echo "  lintfix          Just try to fix all the possible linting errors"
	@echo "  stop             Stops the docker containers"
	@echo "  django-shell     Django integrative shell"
	@echo "  psql             Open the psql cli"
	# @echo "  lint-frontend    Runs a linting check on the frontend"
	# @echo "  lint-frontend-ci Runs a linting check on the frontend in CI"
	# @echo "  build-frontend   Builds the frontend static files"
	@echo "\n"

# Dev configuration steps
.docker-build:
	make build

.env:
	./bin/cp-env-file.sh

build: .env
	docker-compose build
	touch .docker-build

clean: .env stop
	docker-compose rm -f
	rm -rf coverage/ .coverage
	rm -fr .docker-build

migrate: .env
	# docker-compose run web python manage.py migrate --run-syncdb
	docker-compose run web python manage.py migrate

shell: .env .docker-build
	# Use `-u 0` to automatically become root in the shell
	docker-compose run --user 0 web bash

currentshell: .env .docker-build
	# Use `-u 0` to automatically become root in the shell
	docker-compose exec --user 0 web bash

psql: .env .docker-build
	docker-compose run db psql -h db -U postgres

stop: .env
	docker-compose stop

test: .env .docker-build
	docker-compose run web test

run: .env .docker-build
	docker-compose up web ui

gunicorn: .env .docker-build
	docker-compose run --service-ports web web

django-shell: .env .docker-build
	docker-compose run web python manage.py shell

lintcheck: .env .docker-build
	docker-compose run web lintcheck
	docker-compose run ui lintcheck

lintfix: .env .docker-build
	docker-compose run web blackfix
	docker-compose run ui lintfix

docs: .env .docker-build
	docker-compose run -u 0 web ./bin/build_docs.sh

tag:
	@bin/make-tag.py

# lint-frontend:
# 	docker-compose run frontend lint

# lint-frontend-ci:
# 	docker-compose run frontend-ci lint

# build-frontend:
# 	docker-compose run -u 0 -e CI base ./bin/build_frontend.sh
