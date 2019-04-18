FROM python:3.7-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    make

# add a non-privileged user for installing and running the application
# don't use --create-home option to prevent populating with skeleton files
RUN mkdir /app && \
    chown 10001:10001 /app && \
    groupadd --gid 10001 app && \
    useradd --no-create-home --uid 10001 --gid 10001 --home-dir /app app

# Install Python dependencies
COPY docs/requirements.txt /tmp/
WORKDIR /tmp
RUN pip install --no-cache-dir -r requirements.txt

# Switch back to home directory
WORKDIR /app
ADD docs /app

RUN chown -R 10001:10001 /app

USER 10001

ENTRYPOINT ["/bin/bash", "/app/run.sh"]
CMD ["build"]
