import os
from google.cloud import bigquery

# this is slow, so we evaluate this once and return the result
try:
    bigquery.Client()
    BIGQUERY_AUTHENTICATED = True
except Exception:
    # google.auth.exceptions.DefaultCredentialsError
    BIGQUERY_AUTHENTICATED = False


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
