# ruff: noqa: PTH118
import os

# <snippet name="tests/integration/docusaurus/connecting_to_your_data/how_to_introspect_and_partition_your_data/files/yaml_example_gradual.py imports">
import great_expectations as gx
from great_expectations.core.yaml_handler import YAMLHandler

yaml = YAMLHandler()
# </snippet>

# <snippet name="tests/integration/docusaurus/connecting_to_your_data/how_to_introspect_and_partition_your_data/files/yaml_example_gradual.py get_context">
context = gx.get_context()
# </snippet>

# <snippet name="tests/integration/docusaurus/connecting_to_your_data/how_to_introspect_and_partition_your_data/files/yaml_example_gradual.py datasource_yaml">
datasource_yaml = """
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
    default_inferred_data_connector_name:
        class_name: InferredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name
"""
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the yaml above.
data_dir_path = os.path.join("..", "data")

datasource_yaml = datasource_yaml.replace("<PATH_TO_YOUR_DATA_HERE>", data_dir_path)

# <snippet name="tests/integration/docusaurus/connecting_to_your_data/how_to_introspect_and_partition_your_data/files/yaml_example_gradual.py test_yaml_config">
context.test_yaml_config(datasource_yaml)
# </snippet>

# <snippet name="tests/integration/docusaurus/connecting_to_your_data/how_to_introspect_and_partition_your_data/files/yaml_example_gradual.py buggy_data_connector_yaml">
buggy_data_connector_yaml = """
    buggy_inferred_data_connector_name:
        class_name: InferredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:  # required "data_asset_name" reserved group name for "InferredAssetFilePathDataConnector" is absent
            - nonexistent_group_name
"""
# </snippet>

# noinspection PyRedeclaration
buggy_datasource_yaml = """
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
    default_inferred_data_connector_name:
        class_name: InferredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name
    buggy_inferred_data_connector_name:
        class_name: InferredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:  # required "data_asset_name" reserved group name for "InferredAssetFilePathDataConnector" is absent
            - nonexistent_group_name
"""

buggy_datasource_yaml = buggy_datasource_yaml.replace(
    "<PATH_TO_YOUR_DATA_HERE>", data_dir_path
)

context.test_yaml_config(buggy_datasource_yaml)

# <snippet name="tests/integration/docusaurus/connecting_to_your_data/how_to_introspect_and_partition_your_data/files/yaml_example_gradual.py another_buggy_data_connector_yaml">
another_buggy_data_connector_yaml = """
    buggy_inferred_data_connector_name:
        class_name: InferredAssetFilesystemDataConnector
        base_directory: <PATH_TO_BAD_DATA_DIRECTORY_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name
"""
# </snippet>

# noinspection PyRedeclaration
buggy_datasource_yaml = """
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
    default_inferred_data_connector_name:
        class_name: InferredAssetFilesystemDataConnector
        base_directory: <PATH_TO_BAD_DATA_DIRECTORY_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name
    buggy_inferred_data_connector_name:
        class_name: InferredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name
"""

buggy_datasource_yaml = buggy_datasource_yaml.replace(
    "<PATH_TO_BAD_DATA_DIRECTORY_HERE>", data_dir_path
)

report = context.test_yaml_config(buggy_datasource_yaml, shorten_tracebacks=True)

# <snippet name="tests/integration/docusaurus/connecting_to_your_data/how_to_introspect_and_partition_your_data/files/yaml_example_gradual.py add_datasource">
context.add_datasource(**yaml.load(datasource_yaml))
# </snippet>
# <snippet name="tests/integration/docusaurus/connecting_to_your_data/how_to_introspect_and_partition_your_data/files/yaml_example_gradual.py get_available_data_asset_names">
available_data_asset_names = context.datasources[
    "taxi_datasource"
].get_available_data_asset_names(
    data_connector_names="default_inferred_data_connector_name"
)[
    "default_inferred_data_connector_name"
]
assert len(available_data_asset_names) == 36
# </snippet>

bare_bones_configured_data_connector_yaml = """
   configured_data_connector_name:
        class_name: ConfiguredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name
        assets: {}
"""

# <snippet name="tests/integration/docusaurus/connecting_to_your_data/how_to_introspect_and_partition_your_data/files/yaml_example_gradual.py add configureed asset data connector to datasource">
datasource_yaml = """
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
    configured_data_connector_name:
        class_name: ConfiguredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name
        assets: {}
"""
# </snippet>

datasource_yaml = datasource_yaml.replace("<PATH_TO_YOUR_DATA_HERE>", data_dir_path)

context.test_yaml_config(datasource_yaml)

# <snippet name="tests/integration/docusaurus/connecting_to_your_data/how_to_introspect_and_partition_your_data/files/yaml_example_gradual.py configured_data_connector_yaml only by filename and type">
configured_data_connector_yaml = """
    configured_data_connector_name:
        class_name: ConfiguredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name
        assets:
          taxi_data_flat:
            base_directory: samples_2020
            pattern: (yellow_tripdata_sample_.+)\\.csv
            group_names:
              - filename
"""
# </snippet>

datasource_yaml = """
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
    configured_data_connector_name:
        class_name: ConfiguredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name
        assets:
          taxi_data_flat:
            base_directory: samples_2020
            pattern: (yellow_tripdata_sample_.+)\\.csv
            group_names:
              - filename
"""

datasource_yaml = datasource_yaml.replace("<PATH_TO_YOUR_DATA_HERE>", data_dir_path)

context.test_yaml_config(datasource_yaml)

context.add_datasource(**yaml.load(datasource_yaml))
available_data_asset_names = context.datasources[
    "taxi_datasource"
].get_available_data_asset_names(data_connector_names="configured_data_connector_name")[
    "configured_data_connector_name"
]
assert len(available_data_asset_names) == 1

# noinspection PyRedeclaration
# <snippet name="tests/integration/docusaurus/connecting_to_your_data/how_to_introspect_and_partition_your_data/files/yaml_example_gradual.py configured_data_connector_yaml add granular group_names">
configured_data_connector_yaml = """
    configured_data_connector_name:
        class_name: ConfiguredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name
        assets:
          taxi_data_flat:
            base_directory: samples_2020
            pattern: (yellow_tripdata_sample_.+)\\.csv
            group_names:
              - filename
          taxi_data_year_month:
            base_directory: samples_2020
            pattern: ([\\w]+)_tripdata_sample_(\\d{4})-(\\d{2})\\.csv
            group_names:
              - name
              - year
              - month
"""
# </snippet>

datasource_yaml = """
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
    default_inferred_data_connector_name:
        class_name: InferredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name

    configured_data_connector_name:
        class_name: ConfiguredAssetFilesystemDataConnector
        base_directory: <PATH_TO_YOUR_DATA_HERE>
        glob_directive: "*.csv"
        default_regex:
          pattern: (.*)
          group_names:
            - data_asset_name
        assets:
          taxi_data_flat:
            base_directory: samples_2020
            pattern: (yellow_tripdata_sample_.+)\\.csv
            group_names:
              - filename
          taxi_data_year_month:
            base_directory: samples_2020
            pattern: ([\\w]+)_tripdata_sample_(\\d{4})-(\\d{2})\\.csv
            group_names:
              - name
              - year
              - month
"""

datasource_yaml = datasource_yaml.replace("<PATH_TO_YOUR_DATA_HERE>", data_dir_path)

context.test_yaml_config(datasource_yaml)

context.add_datasource(**yaml.load(datasource_yaml))
available_data_asset_names = context.datasources[
    "taxi_datasource"
].get_available_data_asset_names(data_connector_names="configured_data_connector_name")[
    "configured_data_connector_name"
]
assert len(available_data_asset_names) == 2

# NOTE: The following code is only for testing and can be ignored by users.
assert "taxi_datasource" in [ds["name"] for ds in context.list_datasources()]
assert "yellow_tripdata_sample_2019-01.csv" in set(
    context.get_available_data_asset_names()["taxi_datasource"][
        "default_inferred_data_connector_name"
    ]
)
