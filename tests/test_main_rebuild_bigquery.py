import pytest
from django.core.management import call_command

from buildhub.main.models import Build
from utils import runif_bigquery_testing_enabled
from google.api_core.exceptions import NotFound


@runif_bigquery_testing_enabled
@pytest.mark.django_db
def test_rebuild_bigquery_command_no_table_and_dataset(settings):
    settings.BQ_ENABLED = True
    settings.BQ_DATASET_ID = "testing_not_exists_dataset"
    settings.BQ_TABLE_ID = "testing_not_exists_table"
    # Dataset not found
    with pytest.raises(NotFound, match=fr".*{settings.BQ_DATASET_ID}.*"):
        call_command("rebuild-bigquery", yes=True)


@runif_bigquery_testing_enabled
@pytest.mark.django_db
def test_rebuild_bigquery_command_no_table(
    bigquery_client, bigquery_testing_dataset, settings
):
    client = bigquery_client
    settings.BQ_ENABLED = True
    settings.BQ_DATASET_ID = bigquery_testing_dataset.dataset_id
    settings.BQ_TABLE_ID = "testing_not_exists_table"

    # Ensure table is created during startup if not found
    client.get_table(f"{settings.BQ_DATASET_ID}.{settings.BQ_TABLE_ID}")

    call_command("rebuild-bigquery", yes=True)
    bigquery_client.get_table(f"{settings.BQ_DATASET_ID}.{settings.BQ_TABLE_ID}")


@runif_bigquery_testing_enabled
@pytest.mark.django_db
def test_rebuild_bigquery_command(
    bigquery_client, bigquery_testing_table, valid_build, settings
):
    """Test that the fixture is created and insertion is successful.

    Note that streaming data into a recreated table does not work in testing due
    to caching (see salting in the bigquery fixture in conftest.py).
    """
    client = bigquery_client
    table = bigquery_testing_table

    # We insert data into the database that predates BigQuery functionality
    settings.BQ_ENABLED = False
    n_documents = 10
    build = valid_build()
    for i in range(n_documents):
        build["build"]["number"] = i
        inserted = Build.insert(build)
        assert inserted

    settings.BQ_ENABLED = True
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
