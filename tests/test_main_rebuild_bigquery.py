import pytest
from django.core.management import call_command

from buildhub.main.models import Build
from utils import runif_bigquery_testing_enabled


@runif_bigquery_testing_enabled
@pytest.mark.django_db
def test_rebuild_bigquery_command(bigquery_testing_table, valid_build, settings):
    """Test that the fixture is created and insertion is successful.

    This test relies on implicit behavior to work correctly. First, streaming
    data into a recreated table does not work in testing due to caching (see
    salting in the bigquery fixture in conftest.py). Additionally, inserting
    data into the Build model will trigger a callback to send data to the
    BigQuery table. Once data has been inserted into the default (unconfigured)
    table, we mock the settings to point to our testing table. We then run the
    rebuild-table command and assert our conditions.
    """
    client, table = bigquery_testing_table

    n_documents = 10
    build = valid_build()
    for i in range(n_documents):
        build["build"]["number"] = i
        inserted = Build.insert(build)
        assert inserted

    # ordering matters
    settings.BQ_DATASET_ID = table.dataset_id
    settings.BQ_TABLE_ID = table.table_id
    settings.BQ_REBUILD_MAX_ERROR_COUNT = 0
    # done in 4 chunks
    settings.BQ_REBUILD_CHUNK_SIZE = 3

    call_command("rebuild-bigquery", yes=True)

    table_id = f"{table.dataset_id}.{table.table_id}"
    query = f"SELECT COUNT(*) as n_rows FROM {table_id}"
    print(query)
    job = client.query(query)
    result = list(job.result())[0]
    assert result.n_rows == n_documents
