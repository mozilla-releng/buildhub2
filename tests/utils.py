import os
import uuid
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

# this is slow, so we evaluate this once and return the result
try:
    bigquery.Client()
    BIGQUERY_AUTHENTICATED = True
except DefaultCredentialsError:
    BIGQUERY_AUTHENTICATED = False


def salted_table_id(table_id):
    salt = str(uuid.uuid4())[:8]
    return f"{table_id}_{salt}"


def runif_bigquery_testing_enabled(func):
    """A decorator that will skip the test if the current environment is not
    set up for running tests.

        @runif_bigquery_testing_enabled
        def test_my_function_that_uses_bigquery(table_fixture):
            ...
    """
    # importing this at module scope will break test discoverability
    import pytest

    bigquery_testing_enabled = (
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and BIGQUERY_AUTHENTICATED
    )
    return pytest.mark.skipif(
        not bigquery_testing_enabled, reason="requires valid GCP credentials"
    )(func)
