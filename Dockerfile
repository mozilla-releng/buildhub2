# First all the things for building the UI
FROM node:10.16.0-slim as ui

ARG CI=false
ENV CI=${CI}

ADD ui/package.json /package.json
ADD ui/yarn.lock /yarn.lock
RUN yarn

ENV NODE_PATH=/node_modules
ENV PATH=$PATH:/node_modules/.bin

COPY . /app
WORKDIR /app

RUN bin/build-ui.sh


# Next, all the things for building the Python web service
FROM python:3.7-slim@sha256:3e4be41076ebb6fe8c3112b220ce133ef0dc49c814024e4874ca76eae3c8dec0

WORKDIR /app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/

# add a non-privileged user for installing and running the application
# don't use --create-home option to prevent populating with skeleton files
RUN groupadd --gid 10001 app && \
    useradd --no-create-home --uid 10001 --gid 10001 --home-dir /app app

# Install Python dependencies
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r requirements/base.txt
# TODO: Stop installing these into the main container
RUN pip install --no-cache-dir -r requirements/test.txt

# Copy the app
COPY . /app

# Copy built static assets from the ui container
COPY --from=ui /app/ui/build /app/ui/build

# app should own everything under /app in the container
RUN chown -R app.app /app

USER app

ENTRYPOINT ["/bin/bash", "/app/bin/run.sh"]
CMD ["web"]
