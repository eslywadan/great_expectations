from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, List

import sqlalchemy as sa

import great_expectations as gx
from great_expectations.core import IDDict
from great_expectations.core.batch import BatchDefinition, BatchRequest
from great_expectations.core.batch_spec import SqlAlchemyDatasourceBatchSpec
from great_expectations.datasource import BaseDatasource
from great_expectations.datasource.data_connector import ConfiguredAssetSqlDataConnector
from great_expectations.execution_engine.sqlalchemy_batch_data import (
    SqlAlchemyBatchData,
)
from tests.integration.fixtures.partition_and_sample_data.partitioner_test_cases_and_fixtures import (
    TaxiPartitioningTestCase,
    TaxiPartitioningTestCasesBase,
)
from tests.test_utils import (
    LoadedTable,
    clean_up_tables_with_prefix,
    load_and_concatenate_csvs,
    load_data_into_test_database,
)

if TYPE_CHECKING:
    import pandas as pd

TAXI_DATA_TABLE_NAME: str = "taxi_data_all_samples"


def _load_data(
    connection_string: str,
    dialect: str,
    table_name: str = TAXI_DATA_TABLE_NAME,
    random_table_suffix: bool = True,
) -> LoadedTable:
    dialects_supporting_multiple_values_in_single_insert_clause: List[str] = [
        "redshift"
    ]
    to_sql_method: str = (
        "multi"
        if dialect in dialects_supporting_multiple_values_in_single_insert_clause
        else None
    )

    # Load the first 10 rows of each month of taxi data
    return load_data_into_test_database(
        table_name=table_name,
        csv_paths=[
            "./data/ten_trips_from_each_month/yellow_tripdata_sample_10_trips_from_each_month.csv"
        ],
        connection_string=connection_string,
        convert_colnames_to_datetime=["pickup_datetime", "dropoff_datetime"],
        load_full_dataset=True,
        random_table_suffix=random_table_suffix,
        to_sql_method=to_sql_method,
    )


def _is_dialect_athena(dialect: str) -> bool:
    """Is the dialect awsathena?"""
    return dialect == "awsathena"


@contextmanager
def loaded_table(dialect: str, connection_string: str) -> LoadedTable:
    test_df: pd.DataFrame
    table_name: str
    loaded_table: LoadedTable
    if _is_dialect_athena(dialect):
        table_name = "ten_trips_from_each_month"
        test_df = load_and_concatenate_csvs(
            csv_paths=[
                "./data/ten_trips_from_each_month/yellow_tripdata_sample_10_trips_from_each_month.csv"
            ],
            convert_column_names_to_datetime=["pickup_datetime", "dropoff_datetime"],
            load_full_dataset=True,
        )
        loaded_table = LoadedTable(
            table_name=table_name,
            inserted_dataframe=test_df,
        )
    else:
        loaded_table = _load_data(connection_string=connection_string, dialect=dialect)

    try:
        yield loaded_table
    finally:
        if not _is_dialect_athena(dialect):
            print("Cleaning up created loaded table")
            clean_up_tables_with_prefix(
                connection_string=connection_string,
                table_prefix=loaded_table.table_name,
            )


def _execute_taxi_partitioning_test_cases(
    taxi_partitioning_test_cases: TaxiPartitioningTestCasesBase,
    connection_string: str,
    table_name: str,
) -> None:
    test_cases: List[
        TaxiPartitioningTestCase
    ] = taxi_partitioning_test_cases.test_cases()

    test_case: TaxiPartitioningTestCase
    for test_case in test_cases:
        print("Testing partitioner method:", test_case.partitioner_method_name)

        # 1. Setup

        context = gx.get_context()

        datasource_name: str = "test_datasource"
        data_connector_name: str = "test_data_connector"
        data_asset_name: str = table_name  # Read from generated table name

        column_name: str = taxi_partitioning_test_cases.test_column_name
        column_names: List[str] = taxi_partitioning_test_cases.test_column_names

        # 2. Set partitioner in DataConnector config
        data_connector_config: dict = {
            "class_name": "ConfiguredAssetSqlDataConnector",
            "assets": {
                data_asset_name: {
                    "partitioner_method": test_case.partitioner_method_name,
                    "partitioner_kwargs": test_case.partitioner_kwargs,
                }
            },
        }

        # noinspection PyTypeChecker
        context.add_datasource(
            name=datasource_name,
            class_name="Datasource",
            execution_engine={
                "class_name": "SqlAlchemyExecutionEngine",
                "connection_string": connection_string,
            },
            data_connectors={data_connector_name: data_connector_config},
        )

        datasource: BaseDatasource = context.get_datasource(
            datasource_name=datasource_name
        )

        data_connector: ConfiguredAssetSqlDataConnector = datasource.data_connectors[
            data_connector_name
        ]

        # 3. Check if resulting batches are as expected
        # using data_connector.get_batch_definition_list_from_batch_request()
        batch_request: BatchRequest = BatchRequest(
            datasource_name=datasource_name,
            data_connector_name=data_connector_name,
            data_asset_name=data_asset_name,
        )
        batch_definition_list: List[
            BatchDefinition
        ] = data_connector.get_batch_definition_list_from_batch_request(
            batch_request=batch_request
        )
        print(len(batch_definition_list), "batch definitions found")
        print(test_case.num_expected_batch_definitions, "expected batch definitions")
        assert len(batch_definition_list) == test_case.num_expected_batch_definitions

        expected_batch_definition_list: List[BatchDefinition]
        if test_case.table_domain_test_case:
            expected_batch_definition_list = [
                BatchDefinition(
                    datasource_name=datasource_name,
                    data_connector_name=data_connector_name,
                    data_asset_name=data_asset_name,
                    batch_identifiers=IDDict({}),
                )
            ]
        else:
            column_value: Any
            if column_name:
                expected_batch_definition_list = [
                    BatchDefinition(
                        datasource_name=datasource_name,
                        data_connector_name=data_connector_name,
                        data_asset_name=data_asset_name,
                        batch_identifiers=IDDict({column_name: column_value}),
                    )
                    for column_value in test_case.expected_column_values
                ]
            elif column_names:
                dictionary_element: dict
                expected_batch_definition_list = [
                    BatchDefinition(
                        datasource_name=datasource_name,
                        data_connector_name=data_connector_name,
                        data_asset_name=data_asset_name,
                        batch_identifiers=IDDict(dictionary_element),
                    )
                    for dictionary_element in test_case.expected_column_values
                ]
            else:
                raise ValueError(
                    "Missing test_column_names or test_column_names attribute."
                )

        assert set(batch_definition_list) == set(
            expected_batch_definition_list
        ), f"BatchDefinition lists don't match\n\nbatch_definition_list:\n{batch_definition_list}\n\nexpected_batch_definition_list:\n{expected_batch_definition_list}"

        # 4. Check that loaded data is as expected

        # Use expected_batch_definition_list since it is sorted, and we already
        # asserted that it contains the same items as batch_definition_list
        batch_spec: SqlAlchemyDatasourceBatchSpec = data_connector.build_batch_spec(
            expected_batch_definition_list[0]
        )

        batch_data: SqlAlchemyBatchData = context.datasources[
            datasource_name
        ].execution_engine.get_batch_data(batch_spec=batch_spec)

        num_rows: int = batch_data.execution_engine.execute_query(
            sa.select(sa.func.count()).select_from(batch_data.selectable)
        ).scalar()
        assert num_rows == test_case.num_expected_rows_in_first_batch_definition
