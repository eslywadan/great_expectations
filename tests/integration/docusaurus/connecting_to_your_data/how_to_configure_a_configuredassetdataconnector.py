# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py imports">
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py imports no yaml">
import great_expectations as gx
from great_expectations.core.batch import BatchRequest

# </snippet>
from great_expectations.core.yaml_handler import YAMLHandler

yaml = YAMLHandler()
# </snippet>

context = gx.get_context()

# YAML
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py yaml datasource">
datasource_yaml = r"""
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
  default_configured_data_connector_name:
    class_name: ConfiguredAssetFilesystemDataConnector
    base_directory: <MY DIRECTORY>/
    assets:
      yellow_tripdata:
        pattern: yellow_tripdata_(.*)\.csv
        group_names:
          - month
"""
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the yaml above.
datasource_yaml = datasource_yaml.replace(
    "<MY DIRECTORY>/", "../data/single_directory_one_data_asset/"
)

test_yaml = context.test_yaml_config(
    datasource_yaml,
)

# Python
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py python datasource">
datasource_config = {
    "name": "taxi_datasource",
    "class_name": "Datasource",
    "module_name": "great_expectations.datasource",
    "execution_engine": {
        "module_name": "great_expectations.execution_engine",
        "class_name": "PandasExecutionEngine",
    },
    "data_connectors": {
        "default_configured_data_connector_name": {
            "class_name": "ConfiguredAssetFilesystemDataConnector",
            "base_directory": "<MY DIRECTORY>/",
            "assets": {
                "yellow_tripdata": {
                    "pattern": r"yellow_tripdata_(.*)\.csv",
                    "group_names": ["month"],
                }
            },
        },
    },
}
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the code above.
datasource_config["data_connectors"]["default_configured_data_connector_name"][
    "base_directory"
] = "../data/single_directory_one_data_asset/"

test_python = context.test_yaml_config(
    yaml.dump(datasource_config),
)

context.add_datasource(**datasource_config)

# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py basic datasource workthrough">
batch_request = BatchRequest(
    datasource_name="taxi_datasource",
    data_connector_name="default_configured_data_connector_name",
    data_asset_name="yellow_tripdata",
)

context.add_or_update_expectation_suite(
    expectation_suite_name="<MY EXPECTATION SUITE NAME>"
)

validator = context.get_validator(
    batch_request=batch_request,
    expectation_suite_name="<MY EXPECTATION SUITE NAME>",
    batch_identifiers={"month": "2019-02"},
)
print(validator.head())
# </snippet>

# NOTE: The following code is only for testing and can be ignored by users.
assert isinstance(validator, gx.validator.validator.Validator)
assert [ds["name"] for ds in context.list_datasources()] == ["taxi_datasource"]
assert "yellow_tripdata" in set(
    context.get_available_data_asset_names()["taxi_datasource"][
        "default_configured_data_connector_name"
    ]
)

# YAML
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py yaml datasource s3">
datasource_yaml = r"""
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
  default_inferred_data_connector_name:
    class_name: ConfiguredAssetS3DataConnector
    bucket: <MY S3 BUCKET>/
    prefix: <MY S3 BUCKET PREFIX>/
    assets:
      yellow_tripdata:
        pattern: yellow_tripdata_(.*)\.csv
        group_names:
          - month
"""
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the yaml above.
datasource_yaml = datasource_yaml.replace(
    "<MY S3 BUCKET>/", "superconductive-docs-test"
)
datasource_yaml = datasource_yaml.replace(
    "<MY S3 BUCKET PREFIX>/", "data/taxi_yellow_tripdata_samples/"
)

test_yaml = context.test_yaml_config(
    datasource_yaml,
)

# Python
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py python datasource s3">
datasource_config = {
    "name": "taxi_datasource",
    "class_name": "Datasource",
    "module_name": "great_expectations.datasource",
    "execution_engine": {
        "module_name": "great_expectations.execution_engine",
        "class_name": "PandasExecutionEngine",
    },
    "data_connectors": {
        "default_inferred_data_connector_name": {
            "class_name": "ConfiguredAssetS3DataConnector",
            "bucket": "<MY S3 BUCKET>/",
            "prefix": "<MY S3 BUCKET PREFIX>/",
            "assets": {
                "yellow_tripdata": {
                    "group_names": ["month"],
                    "pattern": r"yellow_tripdata_(.*)\.csv",
                },
            },
        },
    },
}
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the code above.
datasource_config["data_connectors"]["default_inferred_data_connector_name"][
    "bucket"
] = "superconductive-docs-test"
datasource_config["data_connectors"]["default_inferred_data_connector_name"][
    "prefix"
] = "data/taxi_yellow_tripdata_samples/"

test_python = context.test_yaml_config(
    yaml.dump(datasource_config),
)

context.add_datasource(**datasource_config)

assert [ds["name"] for ds in context.list_datasources()] == ["taxi_datasource"]
assert "yellow_tripdata" in set(
    context.get_available_data_asset_names()["taxi_datasource"][
        "default_inferred_data_connector_name"
    ]
)

# YAML
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py basic single asset yaml">
datasource_yaml = r"""
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
  default_configured_data_connector_name:
    class_name: ConfiguredAssetFilesystemDataConnector
    base_directory: <MY DIRECTORY>/
    assets:
      yellow_tripdata:
        pattern: (.*)\.csv
        group_names:
          - month
"""
# </snippet>
# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the yaml above.
datasource_yaml = datasource_yaml.replace(
    "<MY DIRECTORY>/", "../data/single_directory_one_data_asset/"
)

test_yaml = context.test_yaml_config(
    datasource_yaml,
)

# Python
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py basic single asset python">
datasource_config = {
    "name": "taxi_datasource",
    "class_name": "Datasource",
    "module_name": "great_expectations.datasource",
    "execution_engine": {
        "module_name": "great_expectations.execution_engine",
        "class_name": "PandasExecutionEngine",
    },
    "data_connectors": {
        "default_configured_data_connector_name": {
            "class_name": "ConfiguredAssetFilesystemDataConnector",
            "base_directory": "<MY DIRECTORY>/",
            "assets": {
                "yellow_tripdata": {
                    "pattern": r"yellow_tripdata_(.*)\.csv",
                    "group_names": ["month"],
                }
            },
        },
    },
}
# </snippet>
# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the code above.
datasource_config["data_connectors"]["default_configured_data_connector_name"][
    "base_directory"
] = "../data/single_directory_one_data_asset/"

test_python = context.test_yaml_config(
    yaml.dump(datasource_config),
)

# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py basic single asset output">
context.add_datasource(**datasource_config)

batch_request = BatchRequest(
    datasource_name="taxi_datasource",
    data_connector_name="default_configured_data_connector_name",
    data_asset_name="yellow_tripdata",
)

validator = context.get_validator(
    batch_request=batch_request,
    expectation_suite_name="<MY EXPECTATION SUITE NAME>",
    batch_identifiers={"month": "2019-02"},
)
# </snippet>

# NOTE: The following code is only for testing and can be ignored by users.
assert isinstance(validator, gx.validator.validator.Validator)
assert [ds["name"] for ds in context.list_datasources()] == ["taxi_datasource"]
assert "yellow_tripdata" in set(
    context.get_available_data_asset_names()["taxi_datasource"][
        "default_configured_data_connector_name"
    ]
)

# YAML
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py basic single asset yaml no regex">
datasource_yaml = r"""
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
  default_configured_data_connector_name:
    class_name: ConfiguredAssetFilesystemDataConnector
    base_directory: <MY DIRECTORY>/
    assets:
      yellow_tripdata:
        pattern: green_tripdata_(.*)\.csv
        group_names:
          - month
"""
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the yaml above.
datasource_yaml = datasource_yaml.replace(
    "<MY DIRECTORY>/", "../data/single_directory_one_data_asset/"
)

test_yaml = context.test_yaml_config(
    datasource_yaml,
)

# Python
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py basic single asset python no regex">
datasource_config = {
    "name": "taxi_datasource",
    "class_name": "Datasource",
    "module_name": "great_expectations.datasource",
    "execution_engine": {
        "module_name": "great_expectations.execution_engine",
        "class_name": "PandasExecutionEngine",
    },
    "data_connectors": {
        "default_configured_data_connector_name": {
            "class_name": "ConfiguredAssetFilesystemDataConnector",
            "base_directory": "<MY DIRECTORY>/",
            "assets": {
                "yellow_tripdata": {
                    "pattern": r"green_tripdata_(.*)\.csv",
                    "group_names": ["month"],
                }
            },
        },
    },
}
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the code above.
datasource_config["data_connectors"]["default_configured_data_connector_name"][
    "base_directory"
] = "../data/single_directory_one_data_asset/"

test_python = context.test_yaml_config(
    yaml.dump(datasource_config),
)

# NOTE: The following code is only for testing and can be ignored by users.
assert [ds["name"] for ds in context.list_datasources()] == ["taxi_datasource"]
assert "yellow_tripdata" in set(
    context.get_available_data_asset_names()["taxi_datasource"][
        "default_configured_data_connector_name"
    ]
)

# YAML
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py example 2 yaml">
datasource_yaml = r"""
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
  default_configured_data_connector_name:
    class_name: ConfiguredAssetFilesystemDataConnector
    base_directory: <MY DIRECTORY>/
    assets:
      yellow_tripdata:
        pattern: yellow_tripdata_(\d{4})-(\d{2})\.csv
        group_names:
          - year
          - month
      green_tripdata:
        pattern: green_tripdata_(\d{4})-(\d{2})\.csv
        group_names:
          - year
          - month
"""
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the yaml above.
datasource_yaml = datasource_yaml.replace(
    "<MY DIRECTORY>/", "../data/single_directory_two_data_assets/"
)

test_yaml = context.test_yaml_config(
    datasource_yaml,
)

# Python
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py example 2 python">
datasource_config = {
    "name": "taxi_datasource",
    "class_name": "Datasource",
    "module_name": "great_expectations.datasource",
    "execution_engine": {
        "module_name": "great_expectations.execution_engine",
        "class_name": "PandasExecutionEngine",
    },
    "data_connectors": {
        "default_configured_data_connector_name": {
            "class_name": "ConfiguredAssetFilesystemDataConnector",
            "base_directory": "<MY DIRECTORY>/",
            "assets": {
                "yellow_tripdata": {
                    "pattern": r"yellow_tripdata_(\d{4})-(\d{2})\.csv",
                    "group_names": ["year", "month"],
                },
                "green_tripdata": {
                    "pattern": r"green_tripdata_(\d{4})-(\d{2})\.csv",
                    "group_names": ["year", "month"],
                },
            },
        },
    },
}
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the code above.
datasource_config["data_connectors"]["default_configured_data_connector_name"][
    "base_directory"
] = "../data/single_directory_two_data_assets/"

test_python = context.test_yaml_config(
    yaml.dump(datasource_config),
)

# NOTE: The following code is only for testing and can be ignored by users.
assert [ds["name"] for ds in context.list_datasources()] == ["taxi_datasource"]
assert "yellow_tripdata" in set(
    context.get_available_data_asset_names()["taxi_datasource"][
        "default_configured_data_connector_name"
    ]
)
assert "green_tripdata" in set(
    context.get_available_data_asset_names()["taxi_datasource"][
        "default_configured_data_connector_name"
    ]
)

# YAML
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py example 3 yaml">
datasource_yaml = r"""
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
  default_configured_data_connector_name:
    class_name: ConfiguredAssetFilesystemDataConnector
    base_directory: <MY DIRECTORY>/
    assets:
      yellow_tripdata:
        base_directory: yellow_tripdata/
        pattern: yellow_tripdata_(\d{4})-(\d{2})\.csv
        group_names:
          - year
          - month
      green_tripdata:
        base_directory: green_tripdata/
        pattern: (\d{4})-(\d{2})\.csv
        group_names:
          - year
          - month
"""
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the yaml above.
datasource_yaml = datasource_yaml.replace(
    "<MY DIRECTORY>/", "../data/nested_directories_data_asset/"
)

test_yaml = context.test_yaml_config(
    datasource_yaml,
)

# Python
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py example 3 python">
datasource_config = {
    "name": "taxi_datasource",
    "class_name": "Datasource",
    "module_name": "great_expectations.datasource",
    "execution_engine": {
        "module_name": "great_expectations.execution_engine",
        "class_name": "PandasExecutionEngine",
    },
    "data_connectors": {
        "default_configured_data_connector_name": {
            "class_name": "ConfiguredAssetFilesystemDataConnector",
            "base_directory": "<MY DIRECTORY>/",
            "assets": {
                "yellow_tripdata": {
                    "base_directory": "yellow_tripdata/",
                    "pattern": r"yellow_tripdata_(\d{4})-(\d{2})\.csv",
                    "group_names": ["year", "month"],
                },
                "green_tripdata": {
                    "base_directory": "green_tripdata/",
                    "pattern": r"(\d{4})-(\d{2})\.csv",
                    "group_names": ["year", "month"],
                },
            },
        },
    },
}
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the code above.
datasource_config["data_connectors"]["default_configured_data_connector_name"][
    "base_directory"
] = "../data/nested_directories_data_asset/"

test_python = context.test_yaml_config(
    yaml.dump(datasource_config),
)

# NOTE: The following code is only for testing and can be ignored by users.
assert [ds["name"] for ds in context.list_datasources()] == ["taxi_datasource"]
assert "yellow_tripdata" in set(
    context.get_available_data_asset_names()["taxi_datasource"][
        "default_configured_data_connector_name"
    ]
)
assert "green_tripdata" in set(
    context.get_available_data_asset_names()["taxi_datasource"][
        "default_configured_data_connector_name"
    ]
)

# YAML
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py example 4 yaml">
datasource_yaml = r"""
name: taxi_datasource
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
  default_configured_data_connector_name:
    class_name: ConfiguredAssetFilesystemDataConnector
    base_directory: <MY DIRECTORY>/
    default_regex:
      pattern: (.*)_(\d{4})-(\d{2})\.(csv|txt)$
      group_names:
        - data_asset_name
        - year
        - month
    assets:
      yellow_tripdata:
        base_directory: yellow/tripdata/
        glob_directive: "*.txt"
      green_tripdata:
        base_directory: green_tripdata/
        glob_directive: "*.csv"
"""
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the yaml above.
datasource_yaml = datasource_yaml.replace(
    "<MY DIRECTORY>/", "../data/nested_directories_complex/"
)

test_yaml = context.test_yaml_config(
    datasource_yaml,
)

# Python
# <snippet name ="tests/integration/docusaurus/connecting_to_your_data/how_to_configure_a_configuredassetdataconnector.py example 4 python">
datasource_config = {
    "name": "taxi_datasource",
    "class_name": "Datasource",
    "module_name": "great_expectations.datasource",
    "execution_engine": {
        "module_name": "great_expectations.execution_engine",
        "class_name": "PandasExecutionEngine",
    },
    "data_connectors": {
        "default_configured_data_connector_name": {
            "class_name": "ConfiguredAssetFilesystemDataConnector",
            "base_directory": "<MY DIRECTORY>/",
            "default_regex": {
                "pattern": r"(.*)_(\d{4})-(\d{2})\.(csv|txt)$",
                "group_names": ["data_asset_name", "year", "month"],
            },
            "assets": {
                "yellow_tripdata": {
                    "base_directory": "yellow/tripdata/",
                    "glob_directive": "*.txt",
                },
                "green_tripdata": {
                    "base_directory": "green_tripdata/",
                    "glob_directive": "*.csv",
                },
            },
        },
    },
}
# </snippet>

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the code above.
datasource_config["data_connectors"]["default_configured_data_connector_name"][
    "base_directory"
] = "../data/nested_directories_complex/"

test_python = context.test_yaml_config(
    yaml.dump(datasource_config),
)

# NOTE: The following code is only for testing and can be ignored by users.
assert [ds["name"] for ds in context.list_datasources()] == ["taxi_datasource"]
assert "yellow_tripdata" in set(
    context.get_available_data_asset_names()["taxi_datasource"][
        "default_configured_data_connector_name"
    ]
)
assert "green_tripdata" in set(
    context.get_available_data_asset_names()["taxi_datasource"][
        "default_configured_data_connector_name"
    ]
)
