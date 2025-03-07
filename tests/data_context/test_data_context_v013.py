import datetime
import os
import re

import pytest

from great_expectations.core import ExpectationSuite
from great_expectations.core.batch import Batch, RuntimeBatchRequest
from great_expectations.core.config_peer import ConfigOutputModes
from great_expectations.core.yaml_handler import YAMLHandler
from great_expectations.data_context import get_context
from great_expectations.data_context.types.base import (
    DataContextConfig,
    dataContextConfigSchema,
)
from great_expectations.data_context.util import file_relative_path
from great_expectations.exceptions import ExecutionEngineError
from great_expectations.execution_engine.pandas_batch_data import PandasBatchData
from great_expectations.execution_engine.sqlalchemy_batch_data import (
    SqlAlchemyBatchData,
)
from great_expectations.validator.validator import Validator
from tests.data_context.conftest import (
    USAGE_STATISTICS_QA_URL,
)
from tests.test_utils import create_files_in_directory, get_sqlite_temp_table_names

yaml = YAMLHandler()


@pytest.fixture
def basic_data_context_v013_config():
    return DataContextConfig(
        **{
            "commented_map": {},
            "config_version": 3,
            "plugins_directory": "plugins/",
            "evaluation_parameter_store_name": "evaluation_parameter_store",
            "validations_store_name": "does_not_have_to_be_real",
            "expectations_store_name": "expectations_store",
            "checkpoint_store_name": "checkpoint_store",
            "config_variables_file_path": "uncommitted/config_variables.yml",
            "datasources": {},
            "stores": {
                "expectations_store": {
                    "class_name": "ExpectationsStore",
                    "store_backend": {
                        "class_name": "TupleFilesystemStoreBackend",
                        "base_directory": "expectations/",
                    },
                },
                "evaluation_parameter_store": {
                    "module_name": "great_expectations.data_context.store",
                    "class_name": "EvaluationParameterStore",
                },
                "checkpoint_store": {
                    "class_name": "CheckpointStore",
                    "store_backend": {
                        "class_name": "TupleFilesystemStoreBackend",
                        "base_directory": "checkpoints/",
                    },
                },
            },
            "data_docs_sites": {},
            "anonymous_usage_statistics": {
                "enabled": True,
                "data_context_id": "6a52bdfa-e182-455b-a825-e69f076e67d6",
                "usage_statistics_url": USAGE_STATISTICS_QA_URL,
            },
        }
    )


@pytest.fixture
def data_context_with_runtime_sql_datasource_for_testing_get_batch(
    sa,
    empty_data_context,
):
    context = empty_data_context
    db_file_path: str = file_relative_path(
        __file__,
        os.path.join(  # noqa: PTH118
            "..", "test_sets", "test_cases_for_sql_data_connector.db"
        ),
    )

    datasource_config: str = f"""
        class_name: Datasource

        execution_engine:
            class_name: SqlAlchemyExecutionEngine
            connection_string: sqlite:///{db_file_path}

        data_connectors:
            my_runtime_data_connector:
                module_name: great_expectations.datasource.data_connector
                class_name: RuntimeDataConnector
                batch_identifiers:
                    - pipeline_stage_name
                    - airflow_run_id
    """

    context.add_datasource(
        name="my_runtime_sql_datasource", **yaml.load(datasource_config)
    )

    # noinspection PyProtectedMember
    context._save_project_config()
    return context


@pytest.mark.filesystem
def test_ConfigOnlyDataContext_v013__initialization(
    tmp_path_factory, basic_data_context_v013_config
):
    config_path = str(
        tmp_path_factory.mktemp("test_ConfigOnlyDataContext__initialization__dir")
    )
    context = get_context(
        basic_data_context_v013_config,
        config_path,
    )

    assert len(context.plugins_directory.split("/")[-3:]) == 3
    assert "" in context.plugins_directory.split("/")[-3:]

    pattern = re.compile(r"test_ConfigOnlyDataContext__initialization__dir\d*")
    assert (
        len(
            list(
                filter(
                    lambda element: element,
                    sorted(
                        pattern.match(element) is not None
                        for element in context.plugins_directory.split("/")[-3:]
                    ),
                )
            )
        )
        == 1
    )


@pytest.mark.unit
def test__normalize_absolute_or_relative_path(
    tmp_path_factory, basic_data_context_v013_config
):
    full_test_path = tmp_path_factory.mktemp(
        "test__normalize_absolute_or_relative_path__dir"
    )
    test_dir = full_test_path.parts[-1]
    config_path = str(full_test_path)
    context = get_context(
        basic_data_context_v013_config,
        config_path,
    )

    assert context._normalize_absolute_or_relative_path("yikes").endswith(
        f"{test_dir}/yikes"
    )
    assert (
        "test__normalize_absolute_or_relative_path__dir"
        not in context._normalize_absolute_or_relative_path("/yikes")
    )
    assert "/yikes" == context._normalize_absolute_or_relative_path("/yikes")


@pytest.mark.filesystem
def test_load_config_variables_file(
    basic_data_context_v013_config, tmp_path_factory, monkeypatch
):
    # Setup:
    base_path = str(tmp_path_factory.mktemp("test_load_config_variables_file"))
    os.makedirs(  # noqa: PTH103
        os.path.join(base_path, "uncommitted"), exist_ok=True  # noqa: PTH118
    )
    with open(
        os.path.join(base_path, "uncommitted", "dev_variables.yml"), "w"  # noqa: PTH118
    ) as outfile:
        yaml.dump({"env": "dev"}, outfile)
    with open(
        os.path.join(base_path, "uncommitted", "prod_variables.yml"),  # noqa: PTH118
        "w",
    ) as outfile:
        yaml.dump({"env": "prod"}, outfile)
    basic_data_context_v013_config[
        "config_variables_file_path"
    ] = "uncommitted/${TEST_CONFIG_FILE_ENV}_variables.yml"

    try:
        # We should be able to load different files based on an environment variable
        monkeypatch.setenv("TEST_CONFIG_FILE_ENV", "dev")
        context = get_context(
            basic_data_context_v013_config, context_root_dir=base_path
        )
        config_vars = context.config_variables
        assert config_vars["env"] == "dev"
        monkeypatch.setenv("TEST_CONFIG_FILE_ENV", "prod")
        context = get_context(
            basic_data_context_v013_config, context_root_dir=base_path
        )
        config_vars = context.config_variables
        assert config_vars["env"] == "prod"
    except Exception:
        raise
    finally:
        # Make sure we unset the environment variable we're using
        monkeypatch.delenv("TEST_CONFIG_FILE_ENV")


@pytest.mark.filesystem
def test_get_config(empty_data_context):
    context = empty_data_context

    # We can call get_config in several different modes
    assert type(context.get_config()) is DataContextConfig
    assert type(context.get_config(mode=ConfigOutputModes.TYPED)) is DataContextConfig
    assert type(context.get_config(mode=ConfigOutputModes.DICT)) == dict  # noqa: E721
    assert type(context.get_config(mode=ConfigOutputModes.YAML)) == str  # noqa: E721
    assert type(context.get_config(mode="yaml")) == str  # noqa: E721
    with pytest.raises(ValueError):
        context.get_config(mode="foobar")

    print(context.get_config(mode=ConfigOutputModes.YAML))
    print(context.get_config(mode=ConfigOutputModes.DICT).keys())

    assert set(context.get_config(mode=ConfigOutputModes.DICT).keys()) == {
        "config_version",
        "datasources",
        "config_variables_file_path",
        "plugins_directory",
        "stores",
        "expectations_store_name",
        "fluent_datasources",
        "validations_store_name",
        "evaluation_parameter_store_name",
        "checkpoint_store_name",
        "data_docs_sites",
        "anonymous_usage_statistics",
        "include_rendered_content",
    }


@pytest.mark.filesystem
def test_config_variables(empty_data_context):
    context = empty_data_context
    assert type(context.config_variables) == dict  # noqa: E721
    assert set(context.config_variables.keys()) == {"instance_id"}


@pytest.mark.filesystem
@pytest.mark.filterwarnings(
    "ignore:get_batch is deprecated*:DeprecationWarning:great_expectations.data_context.data_context"
)
def test_conveying_partitioning_and_sampling_directives_from_data_context_to_pandas_execution_engine(
    empty_data_context, test_df, tmp_path_factory
):
    base_directory = str(
        tmp_path_factory.mktemp(
            "test_conveying_partitioning_and_sampling_directives_from_data_context_to_pandas_execution_engine"
        )
    )

    create_files_in_directory(
        directory=base_directory,
        file_name_list=[
            "somme_file.csv",
        ],
        file_content_fn=lambda: test_df.to_csv(header=True, index=False),
    )

    context = empty_data_context

    yaml_config = f"""
class_name: Datasource

execution_engine:
    class_name: PandasExecutionEngine

data_connectors:
    my_filesystem_data_connector:
        class_name: ConfiguredAssetFilesystemDataConnector
        base_directory: {base_directory}

        default_regex:
            pattern: (.+)\\.csv
            group_names:
                - alphanumeric

        assets:
            A:
"""
    # noinspection PyUnusedLocal
    context.test_yaml_config(
        name="my_directory_datasource",
        yaml_config=yaml_config,
    )
    # print(json.dumps(report_object, indent=2))
    # print(context.datasources)

    my_batch_list = context.get_batch_list(
        datasource_name="my_directory_datasource",
        data_connector_name="my_filesystem_data_connector",
        data_asset_name="A",
        batch_spec_passthrough={
            "sampling_method": "_sample_using_hash",
            "sampling_kwargs": {
                "column_name": "date",
                "hash_function_name": "md5",
                "hash_value": "f",
            },
        },
    )
    my_batch = my_batch_list[0]
    assert my_batch.batch_definition["data_asset_name"] == "A"

    df_data = my_batch.data.dataframe
    assert df_data.shape == (10, 10)
    df_data["date"] = df_data.apply(
        lambda row: datetime.datetime.strptime(row["date"], "%Y-%m-%d").date(), axis=1
    )
    assert (
        test_df[
            (test_df["date"] == datetime.date(2020, 1, 15))
            | (test_df["date"] == datetime.date(2020, 1, 29))
        ]
        .drop("timestamp", axis=1)
        .equals(df_data.drop("timestamp", axis=1))
    )

    my_batch_list = context.get_batch_list(
        datasource_name="my_directory_datasource",
        data_connector_name="my_filesystem_data_connector",
        data_asset_name="A",
        batch_spec_passthrough={
            "partitioner_method": "_partition_on_multi_column_values",
            "partitioner_kwargs": {
                "column_names": ["y", "m", "d"],
                "batch_identifiers": {"y": 2020, "m": 1, "d": 5},
            },
        },
    )
    my_batch = my_batch_list[0]

    df_data = my_batch.data.dataframe
    assert df_data.shape == (4, 10)
    df_data["date"] = df_data.apply(
        lambda row: datetime.datetime.strptime(row["date"], "%Y-%m-%d").date(), axis=1
    )
    df_data["belongs_in_partition"] = df_data.apply(
        lambda row: row["date"] == datetime.date(2020, 1, 5), axis=1
    )
    df_data = df_data[df_data["belongs_in_partition"]]
    assert df_data.drop("belongs_in_partition", axis=1).shape == (4, 10)


@pytest.mark.filesystem
@pytest.mark.filterwarnings(
    "ignore:get_batch is deprecated*:DeprecationWarning:great_expectations.data_context.data_context"
)
def test_relative_data_connector_default_and_relative_asset_base_directory_paths(
    empty_data_context, test_df, tmp_path_factory
):
    context = empty_data_context

    create_files_in_directory(
        directory=context.root_directory,
        file_name_list=[
            "test_dir_0/A/B/C/logfile_0.csv",
            "test_dir_0/A/B/C/bigfile_1.csv",
            "test_dir_0/A/filename2.csv",
            "test_dir_0/A/filename3.csv",
        ],
        file_content_fn=lambda: test_df.to_csv(header=True, index=False),
    )

    yaml_config = """
class_name: Datasource

execution_engine:
    class_name: PandasExecutionEngine

data_connectors:
    my_filesystem_data_connector:
        class_name: ConfiguredAssetFilesystemDataConnector
        base_directory: test_dir_0/A
        glob_directive: "*"
        default_regex:
            pattern: (.+)\\.csv
            group_names:
            - name

        assets:
            A:
                base_directory: B/C
                glob_directive: "log*.csv"
                pattern: (.+)_(\\d+)\\.csv
                group_names:
                - name
                - number
"""
    my_datasource = context.test_yaml_config(
        name="my_directory_datasource",
        yaml_config=yaml_config,
    )
    assert (
        my_datasource.data_connectors["my_filesystem_data_connector"].base_directory
        == f"{context.root_directory}/test_dir_0/A"
    )
    assert (
        my_datasource.data_connectors[
            "my_filesystem_data_connector"
        ]._get_full_file_path_for_asset(
            path="bigfile_1.csv",
            asset=my_datasource.data_connectors["my_filesystem_data_connector"].assets[
                "A"
            ],
        )
        == f"{context.root_directory}/test_dir_0/A/B/C/bigfile_1.csv"
    )

    my_batch_list = context.get_batch_list(
        datasource_name="my_directory_datasource",
        data_connector_name="my_filesystem_data_connector",
        data_asset_name="A",
    )
    my_batch = my_batch_list[0]

    df_data = my_batch.data.dataframe
    assert df_data.shape == (120, 10)


@pytest.mark.filesystem
@pytest.mark.slow  # 1.06s
def test_in_memory_data_context_configuration(
    titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled,
):
    project_config_dict: dict = titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled.get_config(
        mode=ConfigOutputModes.DICT
    )
    project_config_dict["plugins_directory"] = None
    project_config_dict["validation_operators"] = {
        "action_list_operator": {
            "class_name": "ActionListValidationOperator",
            "action_list": [
                {
                    "name": "store_validation_result",
                    "action": {"class_name": "StoreValidationResultAction"},
                },
                {
                    "name": "store_evaluation_params",
                    "action": {"class_name": "StoreEvaluationParametersAction"},
                },
                {
                    "name": "update_data_docs",
                    "action": {"class_name": "UpdateDataDocsAction"},
                },
            ],
        }
    }

    # Roundtrip through schema validation to remove any illegal fields add/or restore any missing fields.
    project_config_dict = dataContextConfigSchema.dump(project_config_dict)
    project_config_dict = dataContextConfigSchema.load(project_config_dict)

    project_config: DataContextConfig = DataContextConfig(**project_config_dict)
    data_context = get_context(
        project_config=project_config,
        context_root_dir=titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled.root_directory,
    )

    my_validator: Validator = data_context.get_validator(
        datasource_name="my_datasource",
        data_connector_name="my_basic_data_connector",
        data_asset_name="Titanic_1912",
        create_expectation_suite_with_name="my_test_titanic_expectation_suite",
    )

    assert my_validator.expect_table_row_count_to_equal(1313)["success"]
    assert my_validator.expect_table_column_count_to_equal(7)["success"]


@pytest.mark.sqlite
@pytest.mark.filterwarnings(
    "ignore:get_batch is deprecated*:DeprecationWarning:great_expectations.data_context.data_context"
)
def test_get_batch_with_query_in_runtime_parameters_using_runtime_data_connector(
    sa,
    data_context_with_runtime_sql_datasource_for_testing_get_batch,
    sqlite_view_engine,
):
    context = data_context_with_runtime_sql_datasource_for_testing_get_batch

    batch_list = context.get_batch_list(
        batch_request=RuntimeBatchRequest(
            datasource_name="my_runtime_sql_datasource",
            data_connector_name="my_runtime_data_connector",
            data_asset_name="IN_MEMORY_DATA_ASSET",
            runtime_parameters={
                "query": "SELECT * FROM table_partitioned_by_date_column__A"
            },
            batch_identifiers={
                "pipeline_stage_name": "core_processing",
                "airflow_run_id": 1234567890,
            },
        ),
    )
    batch = batch_list[0]

    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "IN_MEMORY_DATA_ASSET"
    assert isinstance(batch.data, SqlAlchemyBatchData)

    selectable_table_name = batch.data.selectable.name
    selectable_count_sql_str = f"select count(*) from {selectable_table_name}"
    execution_engine = batch.data.execution_engine

    assert (
        execution_engine.execute_query(sa.text(selectable_count_sql_str)).scalar()
        == 123
    )
    assert batch.batch_markers.get("ge_load_time") is not None
    # since create_temp_table defaults to True, there should be 1 temp table
    assert len(get_sqlite_temp_table_names(batch.data.execution_engine)) == 1

    # if create_temp_table in batch_spec_passthrough is set to False, no new temp tables should be created
    batch_list = context.get_batch_list(
        batch_request=RuntimeBatchRequest(
            datasource_name="my_runtime_sql_datasource",
            data_connector_name="my_runtime_data_connector",
            data_asset_name="IN_MEMORY_DATA_ASSET",
            runtime_parameters={
                "query": "SELECT * FROM table_partitioned_by_date_column__A"
            },
            batch_identifiers={
                "pipeline_stage_name": "core_processing",
                "airflow_run_id": 1234567890,
            },
            batch_spec_passthrough={"create_temp_table": False},
        ),
    )
    batch = batch_list[0]
    assert len(get_sqlite_temp_table_names(batch.data.execution_engine)) == 1


@pytest.mark.sqlite
def test_get_validator_with_query_in_runtime_parameters_using_runtime_data_connector(
    sa,
    data_context_with_runtime_sql_datasource_for_testing_get_batch,
):
    context = data_context_with_runtime_sql_datasource_for_testing_get_batch
    my_expectation_suite: ExpectationSuite = context.add_expectation_suite(
        "my_expectations"
    )

    validator: Validator

    validator = context.get_validator(
        batch_request=RuntimeBatchRequest(
            datasource_name="my_runtime_sql_datasource",
            data_connector_name="my_runtime_data_connector",
            data_asset_name="IN_MEMORY_DATA_ASSET",
            runtime_parameters={
                "query": "SELECT * FROM table_partitioned_by_date_column__A"
            },
            batch_identifiers={
                "pipeline_stage_name": "core_processing",
                "airflow_run_id": 1234567890,
            },
        ),
        expectation_suite=my_expectation_suite,
    )

    assert len(validator.batches) == 1


@pytest.mark.filesystem
@pytest.mark.filterwarnings(
    "ignore:get_batch is deprecated*:DeprecationWarning:great_expectations.data_context.data_context"
)
def test_get_batch_with_path_in_runtime_parameters_using_runtime_data_connector(
    sa,
    titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled,
):
    context = titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled
    data_asset_path = os.path.join(  # noqa: PTH118
        context.root_directory, "..", "data", "titanic", "Titanic_19120414_1313.csv"
    )

    batch: Batch

    batch_list = context.get_batch_list(
        batch_request=RuntimeBatchRequest(
            datasource_name="my_datasource",
            data_connector_name="my_runtime_data_connector",
            data_asset_name="IN_MEMORY_DATA_ASSET",
            runtime_parameters={"path": data_asset_path},
            batch_identifiers={
                "pipeline_stage_name": "core_processing",
                "airflow_run_id": 1234567890,
            },
        ),
    )
    batch = batch_list[0]

    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "IN_MEMORY_DATA_ASSET"
    assert isinstance(batch.data, PandasBatchData)
    assert len(batch.data.dataframe.index) == 1313
    assert batch.batch_markers.get("ge_load_time") is not None

    # using path with no extension
    data_asset_path_no_extension = os.path.join(  # noqa: PTH118
        context.root_directory, "..", "data", "titanic", "Titanic_19120414_1313"
    )

    # with no reader_method in batch_spec_passthrough
    with pytest.raises(ExecutionEngineError):
        context.get_batch_list(
            batch_request=RuntimeBatchRequest(
                datasource_name="my_datasource",
                data_connector_name="my_runtime_data_connector",
                data_asset_name="IN_MEMORY_DATA_ASSET",
                runtime_parameters={"path": data_asset_path_no_extension},
                batch_identifiers={
                    "pipeline_stage_name": "core_processing",
                    "airflow_run_id": 1234567890,
                },
            ),
        )

    # with reader_method in batch_spec_passthrough
    batch_list = context.get_batch_list(
        batch_request=RuntimeBatchRequest(
            datasource_name="my_datasource",
            data_connector_name="my_runtime_data_connector",
            data_asset_name="IN_MEMORY_DATA_ASSET",
            runtime_parameters={"path": data_asset_path_no_extension},
            batch_identifiers={
                "pipeline_stage_name": "core_processing",
                "airflow_run_id": 1234567890,
            },
            batch_spec_passthrough={"reader_method": "read_csv"},
        ),
    )
    batch = batch_list[0]

    assert batch.batch_spec is not None
    assert batch.batch_definition["data_asset_name"] == "IN_MEMORY_DATA_ASSET"
    assert isinstance(batch.data, PandasBatchData)
    assert len(batch.data.dataframe.index) == 1313
    assert batch.batch_markers.get("ge_load_time") is not None


@pytest.mark.filesystem
def test_get_validator_with_path_in_runtime_parameters_using_runtime_data_connector(
    sa,
    titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled,
):
    context = titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled
    data_asset_path = os.path.join(  # noqa: PTH118
        context.root_directory, "..", "data", "titanic", "Titanic_19120414_1313.csv"
    )
    my_expectation_suite: ExpectationSuite = context.add_expectation_suite(
        "my_expectations"
    )

    validator: Validator

    validator = context.get_validator(
        batch_request=RuntimeBatchRequest(
            datasource_name="my_datasource",
            data_connector_name="my_runtime_data_connector",
            data_asset_name="IN_MEMORY_DATA_ASSET",
            runtime_parameters={"path": data_asset_path},
            batch_identifiers={
                "pipeline_stage_name": "core_processing",
                "airflow_run_id": 1234567890,
            },
        ),
        expectation_suite=my_expectation_suite,
    )

    assert len(validator.batches) == 1

    # using path with no extension
    data_asset_path_no_extension = os.path.join(  # noqa: PTH118
        context.root_directory, "..", "data", "titanic", "Titanic_19120414_1313"
    )

    # with no reader_method in batch_spec_passthrough
    with pytest.raises(ExecutionEngineError):
        context.get_validator(
            batch_request=RuntimeBatchRequest(
                datasource_name="my_datasource",
                data_connector_name="my_runtime_data_connector",
                data_asset_name="IN_MEMORY_DATA_ASSET",
                runtime_parameters={"path": data_asset_path_no_extension},
                batch_identifiers={
                    "pipeline_stage_name": "core_processing",
                    "airflow_run_id": 1234567890,
                },
            ),
            expectation_suite=my_expectation_suite,
        )

    # with reader_method in batch_spec_passthrough
    validator = context.get_validator(
        batch_request=RuntimeBatchRequest(
            datasource_name="my_datasource",
            data_connector_name="my_runtime_data_connector",
            data_asset_name="IN_MEMORY_DATA_ASSET",
            runtime_parameters={"path": data_asset_path_no_extension},
            batch_identifiers={
                "pipeline_stage_name": "core_processing",
                "airflow_run_id": 1234567890,
            },
            batch_spec_passthrough={"reader_method": "read_csv"},
        ),
        expectation_suite=my_expectation_suite,
    )

    assert len(validator.batches) == 1
