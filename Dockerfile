# First all the things for building the UI

FROM node:9 AS ui

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

FROM python:3.7-slim@sha256:ceab3384b540d7812a29ae5678da98d5eab553000f0a161476382306baaa4c9a

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/

# add a non-privileged user for installing and running the application
# don't use --create-home option to prevent populating with skeleton files
RUN mkdir /app && \
    chown 10001:10001 /app && \
    groupadd --gid 10001 app && \
    useradd --no-create-home --uid 10001 --gid 10001 --home-dir /app app

COPY . /app

# Install Python dependencies
COPY requirements.txt /tmp/
WORKDIR /tmp
RUN pip install --no-cache-dir -r requirements.txt

# COPY . /app

# Switch back to home directory
WORKDIR /app

# Copy built static assets from the ui container
COPY --from=ui /app/ui/build /app/ui/build

RUN chown -R 10001:10001 /app

USER 10001

# CMD ["/bin/bash", "/app/bin/run.sh", "web"]

ENTRYPOINT ["/bin/bash", "/app/bin/run.sh"]
CMD ["web"]
