from __future__ import annotations

import copy
import dataclasses
import functools
import logging
import uuid
import warnings
from pprint import pformat as pf
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    ClassVar,
    Dict,
    Final,
    Generic,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    Optional,
    Sequence,
    Set,
    Type,
    TypeVar,
    Union,
    overload,
)

from great_expectations._docs_decorators import public_api
from great_expectations.compatibility import pydantic
from great_expectations.compatibility.pydantic import (
    Field,
    StrictBool,
    StrictInt,
    validate_arguments,
)
from great_expectations.compatibility.pydantic import dataclasses as pydantic_dc
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.batch_config import BatchConfig
from great_expectations.core.config_substitutor import _ConfigurationSubstitutor
from great_expectations.datasource.fluent.constants import (
    _ASSETS_KEY,
)
from great_expectations.datasource.fluent.fluent_base_model import (
    FluentBaseModel,
)
from great_expectations.datasource.fluent.metadatasource import MetaDatasource
from great_expectations.exceptions.exceptions import DataContextError
from great_expectations.validator.metrics_calculator import MetricsCalculator
from great_expectations.validator.v1_validator import ResultFormat

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import pandas as pd
    from typing_extensions import Self, TypeAlias, TypeGuard

    from great_expectations.core.partitioners import Partitioner

    MappingIntStrAny = Mapping[Union[int, str], Any]
    AbstractSetIntStr = AbstractSet[Union[int, str]]
    from great_expectations.core import (
        ExpectationSuite,
        ExpectationSuiteValidationResult,
        ExpectationValidationResult,
    )
    from great_expectations.core.batch import (
        BatchData,
        BatchDefinition,
        BatchMarkers,
    )
    from great_expectations.core.config_provider import _ConfigurationProvider
    from great_expectations.core.id_dict import BatchSpec
    from great_expectations.data_context import (
        AbstractDataContext as GXDataContext,
    )
    from great_expectations.datasource.data_connector.batch_filter import BatchSlice
    from great_expectations.datasource.fluent import (
        BatchRequest,
        BatchRequestOptions,
    )
    from great_expectations.datasource.fluent.data_asset.data_connector import (
        DataConnector,
    )
    from great_expectations.datasource.fluent.type_lookup import (
        TypeLookup,
    )
    from great_expectations.expectations.expectation import Expectation
    from great_expectations.validator.v1_validator import (
        Validator as V1Validator,
    )


class TestConnectionError(Exception):
    pass


class GxDatasourceWarning(UserWarning):
    """
    Warning related to usage or configuration of a Datasource that could lead to
    unexpected behavior.
    """


class GxSerializationWarning(GxDatasourceWarning):
    pass


BatchMetadata: TypeAlias = Dict[str, Any]


@pydantic_dc.dataclass(frozen=True)
class Sorter:
    key: str
    reverse: bool = False


SortersDefinition: TypeAlias = List[Union[Sorter, str, dict]]


def _is_sorter_list(
    sorters: SortersDefinition,
) -> TypeGuard[list[Sorter]]:
    if len(sorters) == 0 or isinstance(sorters[0], Sorter):
        return True
    return False


def _is_str_sorter_list(sorters: SortersDefinition) -> TypeGuard[list[str]]:
    if len(sorters) > 0 and isinstance(sorters[0], str):
        return True
    return False


def _sorter_from_list(sorters: SortersDefinition) -> list[Sorter]:
    if _is_sorter_list(sorters):
        return sorters

    # mypy doesn't successfully type-narrow sorters to a list[str] here, so we use
    # another TypeGuard. We could cast instead which may be slightly faster.
    sring_valued_sorter: str
    if _is_str_sorter_list(sorters):
        return [
            _sorter_from_str(sring_valued_sorter) for sring_valued_sorter in sorters
        ]

    # This should never be reached because of static typing but is necessary because
    # mypy doesn't know of the if conditions must evaluate to True.
    raise ValueError(f"sorters is a not a SortersDefinition but is a {type(sorters)}")


def _sorter_from_str(sort_key: str) -> Sorter:
    """Convert a list of strings to Sorter objects

    Args:
        sort_key: A batch metadata key which will be used to sort batches on a data asset.
                  This can be prefixed with a + or - to indicate increasing or decreasing
                  sorting.  If not specified, defaults to increasing order.
    """
    if sort_key[0] == "-":
        return Sorter(key=sort_key[1:], reverse=True)

    if sort_key[0] == "+":
        return Sorter(key=sort_key[1:], reverse=False)

    return Sorter(key=sort_key, reverse=False)


# It would be best to bind this to Datasource, but we can't now due to circular dependencies
_DatasourceT = TypeVar("_DatasourceT", bound=MetaDatasource)


class DataAsset(FluentBaseModel, Generic[_DatasourceT]):
    # To subclass a DataAsset one must define `type` as a Class literal explicitly on the sublass
    # as well as implementing the methods in the `Abstract Methods` section below.
    # Some examples:
    # * type: Literal["MyAssetTypeID"] = "MyAssetTypeID",
    # * type: Literal["table"] = "table"
    # * type: Literal["csv"] = "csv"
    name: str
    type: str
    id: Optional[uuid.UUID] = Field(default=None, description="DataAsset id")

    order_by: List[Sorter] = Field(default_factory=list)
    batch_metadata: BatchMetadata = pydantic.Field(default_factory=dict)
    batch_configs: List[BatchConfig] = Field(default_factory=list)

    # non-field private attributes
    _save_batch_config: Callable[[BatchConfig], None] = pydantic.PrivateAttr()
    _datasource: _DatasourceT = pydantic.PrivateAttr()
    _data_connector: Optional[DataConnector] = pydantic.PrivateAttr(default=None)
    _test_connection_error_message: Optional[str] = pydantic.PrivateAttr(default=None)

    @property
    def datasource(self) -> _DatasourceT:
        return self._datasource

    def test_connection(self) -> None:
        """Test the connection for the DataAsset.

        Raises:
            TestConnectionError: If the connection test fails.
        """
        raise NotImplementedError(
            """One needs to implement "test_connection" on a DataAsset subclass."""
        )

    # Abstract Methods
    @property
    def batch_request_options(self) -> tuple[str, ...]:
        """The potential keys for BatchRequestOptions.

        Example:
        ```python
        >>> print(asset.batch_request_options)
        ("day", "month", "year")
        >>> options = {"year": "2023"}
        >>> batch_request = asset.build_batch_request(options=options)
        ```

        Returns:
            A tuple of keys that can be used in a BatchRequestOptions dictionary.
        """
        raise NotImplementedError(
            """One needs to implement "batch_request_options" on a DataAsset subclass."""
        )

    def get_batch_request_options_keys(
        self, partitioner: Optional[Partitioner]
    ) -> tuple[str, ...]:
        raise NotImplementedError(
            """One needs to implement "get_batch_request_options_keys" on a DataAsset subclass."""
        )

    def build_batch_request(
        self,
        options: Optional[BatchRequestOptions] = None,
        batch_slice: Optional[BatchSlice] = None,
        partitioner: Optional[Partitioner] = None,
    ) -> BatchRequest:
        """A batch request that can be used to obtain batches for this DataAsset.

        Args:
            options: A dict that can be used to filter the batch groups returned from the asset.
                The dict structure depends on the asset type. The available keys for dict can be obtained by
                calling batch_request_options.
            batch_slice: A python slice that can be used to limit the sorted batches by index.
                e.g. `batch_slice = "[-5:]"` will request only the last 5 batches after the options filter is applied.
            partitioner: A Partitioner used to narrow the data returned from the asset.

        Returns:
            A BatchRequest object that can be used to obtain a batch list from a Datasource by calling the
            get_batch_list_from_batch_request method.
        """
        raise NotImplementedError(
            """One must implement "build_batch_request" on a DataAsset subclass."""
        )

    def get_batch_list_from_batch_request(
        self, batch_request: BatchRequest
    ) -> List[Batch]:
        raise NotImplementedError

    def _validate_batch_request(self, batch_request: BatchRequest) -> None:
        """Validates the batch_request has the correct form.

        Args:
            batch_request: A batch request object to be validated.
        """
        raise NotImplementedError(
            """One must implement "_validate_batch_request" on a DataAsset subclass."""
        )

    # End Abstract Methods

    @public_api
    def add_batch_config(
        self, name: str, partitioner: Optional[Partitioner] = None
    ) -> BatchConfig:
        """Add a BatchConfig to this DataAsset.
        BatchConfig names must be unique within a DataAsset.

        If the DataAsset is tied to a DataContext, the BatchConfig will be persisted.

        Args:
            name (str): Name of the new batch config.
            partitioner: Optional Partitioner to partition this BatchConfig

        Returns:
            BatchConfig: The new batch config.
        """
        batch_config_names = {bc.name for bc in self.batch_configs}
        if name in batch_config_names:
            raise ValueError(
                f'"{name}" already exists (all existing batch_config names are {", ".join(batch_config_names)})'
            )

        # Let mypy know that self.datasource is a Datasource (it is currently bound to MetaDatasource)
        assert isinstance(self.datasource, Datasource)

        batch_config = BatchConfig(name=name, partitioner=partitioner)
        batch_config.set_data_asset(self)
        self.batch_configs.append(batch_config)
        if self.datasource.data_context:
            try:
                batch_config = self.datasource.add_batch_config(batch_config)
            except Exception:
                self.batch_configs.remove(batch_config)
                raise
        self.update_batch_config_field_set()
        return batch_config

    @public_api
    def delete_batch_config(self, batch_config: BatchConfig) -> None:
        """Delete a batch config.

        Args:
            batch_config (BatchConfig): BatchConfig to delete.
        """
        batch_config_names = {bc.name for bc in self.batch_configs}
        if batch_config not in self.batch_configs:
            raise ValueError(
                f'"{batch_config.name}" does not exist (all existing batch_config names are {batch_config_names})'
            )

        # Let mypy know that self.datasource is a Datasource (it is currently bound to MetaDatasource)
        assert isinstance(self.datasource, Datasource)

        self.batch_configs.remove(batch_config)
        if self.datasource.data_context:
            try:
                self.datasource.delete_batch_config(batch_config)
            except Exception:
                self.batch_configs.append(batch_config)
                raise

        self.update_batch_config_field_set()

    def update_batch_config_field_set(self) -> None:
        """Ensure that we have __fields_set__ set correctly for batch_configs to ensure we serialize IFF needed."""

        has_batch_configs = len(self.batch_configs) > 0
        if "batch_configs" in self.__fields_set__ and not has_batch_configs:
            self.__fields_set__.remove("batch_configs")
        elif "batch_configs" not in self.__fields_set__ and has_batch_configs:
            self.__fields_set__.add("batch_configs")

    def get_batch_config(self, batch_config_name: str) -> BatchConfig:
        batch_configs = [
            batch_config
            for batch_config in self.batch_configs
            if batch_config.name == batch_config_name
        ]
        if len(batch_configs) == 0:
            raise KeyError(f"BatchConfig {batch_config_name} not found")
        elif len(batch_configs) > 1:
            raise KeyError(f"Multiple keys for {batch_config_name} found")
        return batch_configs[0]

    def _batch_request_options_are_valid(
        self, options: BatchRequestOptions, partitioner: Optional[Partitioner]
    ) -> bool:
        valid_options = self.get_batch_request_options_keys(partitioner=partitioner)
        return set(options.keys()).issubset(set(valid_options))

    def _get_batch_metadata_from_batch_request(
        self, batch_request: BatchRequest
    ) -> BatchMetadata:
        """Performs config variable substitution and populates batch request options for
        Batch.metadata at runtime.
        """
        batch_metadata = copy.deepcopy(self.batch_metadata)
        config_variables = self._datasource.data_context.config_variables  # type: ignore[attr-defined]
        batch_metadata = _ConfigurationSubstitutor().substitute_all_config_variables(
            data=batch_metadata, replace_variables_dict=config_variables
        )
        batch_metadata.update(copy.deepcopy(batch_request.options))
        return batch_metadata

    # Sorter methods
    @pydantic.validator("order_by", pre=True)
    def _parse_order_by_sorters(
        cls, order_by: Optional[List[Union[Sorter, str, dict]]] = None
    ) -> List[Sorter]:
        return Datasource.parse_order_by_sorters(order_by=order_by)

    def add_sorters(self: Self, sorters: SortersDefinition) -> Self:
        """Associates a sorter to this DataAsset

        The passed in sorters will replace any previously associated sorters.
        Batches returned from this DataAsset will be sorted on the batch's
        metadata in the order specified by `sorters`. Sorters work left to right.
        That is, batches will be sorted first by sorters[0].key, then
        sorters[1].key, and so on. If sorter[i].reverse is True, that key will
        sort the batches in descending, as opposed to ascending, order.

        Args:
            sorters: A list of either Sorter objects or strings. The strings
              are a shorthand for Sorter objects and are parsed as follows:
              r'[+-]?.*'
              An optional prefix of '+' or '-' sets Sorter.reverse to
              'False' or 'True' respectively. It is 'False' if no prefix is present.
              The rest of the string gets assigned to the Sorter.key.
              For example:
              ["key1", "-key2", "key3"]
              is equivalent to:
              [
                  Sorter(key="key1", reverse=False),
                  Sorter(key="key2", reverse=True),
                  Sorter(key="key3", reverse=False),
              ]

        Returns:
            This DataAsset with the passed in sorters accessible via self.order_by
        """
        # NOTE: (kilo59) we could use pydantic `validate_assignment` for this
        # https://docs.pydantic.dev/usage/model_config/#options
        self.order_by = _sorter_from_list(sorters)
        return self

    def sort_batches(self, batch_list: List[Batch]) -> None:
        """Sorts batch_list in place in the order configured in this DataAsset.

        Args:
            batch_list: The list of batches to sort in place.
        """
        for sorter in reversed(self.order_by):
            try:
                batch_list.sort(
                    key=functools.cmp_to_key(
                        _sort_batches_with_none_metadata_values(sorter.key)
                    ),
                    reverse=sorter.reverse,
                )
            except KeyError as e:
                raise KeyError(
                    f"Trying to sort {self.name} table asset batches on key {sorter.key} "
                    "which isn't available on all batches."
                ) from e


def _sort_batches_with_none_metadata_values(
    key: str,
) -> Callable[[Batch, Batch], int]:
    def _compare_function(a: Batch, b: Batch) -> int:
        if a.metadata[key] is not None and b.metadata[key] is not None:
            if a.metadata[key] < b.metadata[key]:
                return -1

            if a.metadata[key] > b.metadata[key]:
                return 1

            return 0

        if a.metadata[key] is None and b.metadata[key] is None:
            return 0

        if a.metadata[key] is None:  # b.metadata[key] is not None
            return -1

        if a.metadata[key] is not None:  # b.metadata[key] is None
            return 1

        # This line should never be reached; hence, "ValueError" with corresponding error message is raised.
        raise ValueError(
            f'Unexpected Batch metadata key combination, "{a.metadata[key]}" and "{b.metadata[key]}", was encountered.'
        )

    return _compare_function


# If a Datasource can have more than 1 _DataAssetT, this will need to change.
_DataAssetT = TypeVar("_DataAssetT", bound=DataAsset)


# It would be best to bind this to ExecutionEngine, but we can't now due to circular imports
_ExecutionEngineT = TypeVar("_ExecutionEngineT")


class Datasource(
    FluentBaseModel,
    Generic[_DataAssetT, _ExecutionEngineT],
    metaclass=MetaDatasource,
):
    # To subclass Datasource one needs to define:
    # asset_types
    # type
    # assets
    #
    # The important part of defining `assets` is setting the Dict type correctly.
    # In addition, one must define the methods in the `Abstract Methods` section below.
    # If one writes a class level docstring, this will become the documenation for the
    # data context method `data_context.sources.add_my_datasource` method.

    # class attrs
    asset_types: ClassVar[Sequence[Type[DataAsset]]] = []
    # Not all Datasources require a DataConnector
    data_connector_type: ClassVar[Optional[Type[DataConnector]]] = None
    # Datasource sublcasses should update this set if the field should not be passed to the execution engine
    _EXTRA_EXCLUDED_EXEC_ENG_ARGS: ClassVar[Set[str]] = set()
    _type_lookup: ClassVar[  # This attribute is set in `MetaDatasource.__new__`
        TypeLookup
    ]
    # Setting this in a Datasource subclass will override the execution engine type.
    # The primary use case is to inject an execution engine for testing.
    execution_engine_override: ClassVar[Optional[Type[_ExecutionEngineT]]] = None  # type: ignore[misc]  # ClassVar cannot contain type variables

    # instance attrs
    type: str
    name: str
    id: Optional[uuid.UUID] = Field(default=None, description="Datasource id")
    assets: MutableSequence[_DataAssetT] = []

    # private attrs
    _data_context: Union[GXDataContext, None] = pydantic.PrivateAttr(None)
    _cached_execution_engine_kwargs: Dict[str, Any] = pydantic.PrivateAttr({})
    _execution_engine: Union[_ExecutionEngineT, None] = pydantic.PrivateAttr(None)

    @property
    def _config_provider(self) -> Union[_ConfigurationProvider, None]:
        return getattr(self._data_context, "config_provider", None)

    @property
    def data_context(self) -> GXDataContext | None:
        """The data context that this datasource belongs to.

        This method should only be used by library implementers.
        """
        return self._data_context

    @pydantic.validator("assets", each_item=True)
    @classmethod
    def _load_asset_subtype(
        cls: Type[Datasource[_DataAssetT, _ExecutionEngineT]], data_asset: DataAsset
    ) -> _DataAssetT:
        """
        Some `data_asset` may be loaded as a less specific asset subtype different than
        what was intended.
        If a more specific subtype is needed the `data_asset` will be converted to a
        more specific `DataAsset`.
        """
        logger.debug(f"Loading '{data_asset.name}' asset ->\n{pf(data_asset, depth=4)}")
        asset_type_name: str = data_asset.type
        asset_type: Type[_DataAssetT] = cls._type_lookup[asset_type_name]

        if asset_type is type(data_asset):
            # asset is already the intended type
            return data_asset

        # strip out asset default kwargs
        kwargs = data_asset.dict(exclude_unset=True)
        logger.debug(f"{asset_type_name} - kwargs\n{pf(kwargs)}")

        cls._update_asset_forward_refs(asset_type)

        asset_of_intended_type = asset_type(**kwargs)
        logger.debug(f"{asset_type_name} - {asset_of_intended_type!r}")
        return asset_of_intended_type

    @pydantic.validator(_ASSETS_KEY, each_item=True)
    def _update_batch_configs(cls, data_asset: DataAsset) -> DataAsset:
        for batch_config in data_asset.batch_configs:
            batch_config.set_data_asset(data_asset)
        return data_asset

    def _execution_engine_type(self) -> Type[_ExecutionEngineT]:
        """Returns the execution engine to be used"""
        return self.execution_engine_override or self.execution_engine_type

    def add_batch_config(self, batch_config: BatchConfig) -> BatchConfig:
        asset_name = batch_config.data_asset.name
        if not self.data_context:
            raise DataContextError("Cannot save datasource without a data context.")

        loaded_datasource = self.data_context.get_datasource(self.name)
        if loaded_datasource is not self:
            # CachedDatasourceDict will return self; only add batch config if this is a remote copy
            assert isinstance(loaded_datasource, Datasource)
            loaded_asset = loaded_datasource.get_asset(asset_name)
            loaded_asset.batch_configs.append(batch_config)
            loaded_asset.update_batch_config_field_set()
        updated_datasource = self.data_context.update_datasource(loaded_datasource)
        assert isinstance(updated_datasource, Datasource)

        output = updated_datasource.get_asset(asset_name).get_batch_config(
            batch_config.name
        )
        output.set_data_asset(batch_config.data_asset)
        return output

    def delete_batch_config(self, batch_config: BatchConfig) -> None:
        asset_name = batch_config.data_asset.name
        if not self.data_context:
            raise DataContextError("Cannot save datasource without a data context.")

        loaded_datasource = self.data_context.get_datasource(self.name)
        if loaded_datasource is not self:
            # CachedDatasourceDict will return self; only add batch config if this is a remote copy
            assert isinstance(loaded_datasource, Datasource)
            loaded_asset = loaded_datasource.get_asset(asset_name)
            loaded_asset.batch_configs.remove(batch_config)
            loaded_asset.update_batch_config_field_set()
        updated_datasource = self.data_context.update_datasource(loaded_datasource)
        assert isinstance(updated_datasource, Datasource)

    def get_execution_engine(self) -> _ExecutionEngineT:
        current_execution_engine_kwargs = self.dict(
            exclude=self._get_exec_engine_excludes(),
            config_provider=self._config_provider,
        )
        if (
            current_execution_engine_kwargs != self._cached_execution_engine_kwargs
            or not self._execution_engine
        ):
            self._execution_engine = self._execution_engine_type()(
                **current_execution_engine_kwargs
            )
            self._cached_execution_engine_kwargs = current_execution_engine_kwargs
        return self._execution_engine

    def get_batch_list_from_batch_request(
        self, batch_request: BatchRequest
    ) -> List[Batch]:
        """A list of batches that correspond to the BatchRequest.

        Args:
            batch_request: A batch request for this asset. Usually obtained by calling
                build_batch_request on the asset.

        Returns:
            A list of batches that match the options specified in the batch request.
        """
        data_asset = self.get_asset(batch_request.data_asset_name)
        return data_asset.get_batch_list_from_batch_request(batch_request)

    def get_assets_as_dict(self) -> MutableMapping[str, _DataAssetT]:
        """Returns available DataAsset objects as dictionary, with corresponding name as key.

        Returns:
            Dictionary of "_DataAssetT" objects with "name" attribute serving as key.
        """
        asset: _DataAssetT
        assets_as_dict: MutableMapping[str, _DataAssetT] = {
            asset.name: asset for asset in self.assets
        }

        return assets_as_dict

    def get_asset_names(self) -> Set[str]:
        """Returns the set of available DataAsset names

        Returns:
            Set of available DataAsset names.
        """
        asset: _DataAssetT
        return {asset.name for asset in self.assets}

    def get_asset(self, asset_name: str) -> _DataAssetT:
        """Returns the DataAsset referred to by asset_name

        Args:
            asset_name: name of DataAsset sought.

        Returns:
            _DataAssetT -- if named "DataAsset" object exists; otherwise, exception is raised.
        """
        # This default implementation will be used if protocol is inherited
        try:
            asset: _DataAssetT
            found_asset: _DataAssetT = list(
                filter(lambda asset: asset.name == asset_name, self.assets)
            )[0]
            found_asset._datasource = self
            return found_asset
        except IndexError as exc:
            raise LookupError(
                f'"{asset_name}" not found. Available assets are ({", ".join(self.get_asset_names())})'
            ) from exc

    def delete_asset(self, asset_name: str) -> None:
        """Removes the DataAsset referred to by asset_name from internal list of available DataAsset objects.

        Args:
            asset_name: name of DataAsset to be deleted.
        """
        from great_expectations.data_context import CloudDataContext

        asset: _DataAssetT
        asset = self.get_asset(asset_name=asset_name)

        if self._data_context and isinstance(self._data_context, CloudDataContext):
            self._data_context._delete_asset(id=str(asset.id))

        self.assets = list(filter(lambda asset: asset.name != asset_name, self.assets))
        self._save_context_project_config()

    def _add_asset(
        self, asset: _DataAssetT, connect_options: dict | None = None
    ) -> _DataAssetT:
        """Adds an asset to a datasource

        Args:
            asset: The DataAsset to be added to this datasource.
        """
        # The setter for datasource is non-functional, so we access _datasource directly.
        # See the comment in DataAsset for more information.
        asset._datasource = self

        if not connect_options:
            connect_options = {}
        self._build_data_connector(asset, **connect_options)

        asset.test_connection()

        asset_names: Set[str] = self.get_asset_names()
        if asset.name in asset_names:
            raise ValueError(
                f'"{asset.name}" already exists (all existing assets are {", ".join(asset_names)})'
            )

        self.assets.append(asset)

        # if asset was added to a cloud FDS, _update_fluent_datasource will return FDS fetched from cloud,
        # which will contain the new asset populated with an id
        if self._data_context:
            updated_datasource = self._data_context._update_fluent_datasource(
                datasource=self
            )
            assert isinstance(updated_datasource, Datasource)
            if asset_id := updated_datasource.get_asset(asset_name=asset.name).id:
                asset.id = asset_id

        return asset

    def _save_context_project_config(self) -> None:
        """Check if a DataContext is available and save the project config."""
        if self._data_context:
            try:
                self._data_context._save_project_config()
            except TypeError as type_err:
                warnings.warn(str(type_err), GxSerializationWarning)

    def _rebuild_asset_data_connectors(self) -> None:
        """
        If Datasource required a data_connector we need to build the data_connector for each asset.

        A warning is raised if a data_connector cannot be built for an asset.
        Not all users will have access to the needed dependencies (packages or credentials) for every asset.
        Missing dependencies will stop them from using the asset but should not stop them from loading it from config.
        """
        asset_build_failure_direct_cause: dict[str, Exception | BaseException] = {}

        if self.data_connector_type:
            for data_asset in self.assets:
                try:
                    # check if data_connector exist before rebuilding?
                    connect_options = getattr(data_asset, "connect_options", {})
                    self._build_data_connector(data_asset, **connect_options)
                except Exception as dc_build_err:
                    logger.info(
                        f"Unable to build data_connector for {self.type} {data_asset.type} {data_asset.name}",
                        exc_info=True,
                    )
                    # reveal direct cause instead of generic, unhelpful MyDatasourceError
                    asset_build_failure_direct_cause[data_asset.name] = (
                        dc_build_err.__cause__ or dc_build_err
                    )
        if asset_build_failure_direct_cause:
            # TODO: allow users to opt out of these warnings
            names_and_error: List[str] = [
                f"{name}:{type(exc).__name__}"
                for (name, exc) in asset_build_failure_direct_cause.items()
            ]
            warnings.warn(
                f"data_connector build failure for {self.name} assets - {', '.join(names_and_error)}",
                category=RuntimeWarning,
            )

    @staticmethod
    def parse_order_by_sorters(
        order_by: Optional[List[Union[Sorter, str, dict]]] = None
    ) -> List[Sorter]:
        order_by_sorters: list[Sorter] = []
        if order_by:
            for idx, sorter in enumerate(order_by):
                if isinstance(sorter, str):
                    if not sorter:
                        raise ValueError(
                            '"order_by" list cannot contain an empty string'
                        )
                    order_by_sorters.append(_sorter_from_str(sorter))
                elif isinstance(sorter, dict):
                    key: Optional[Any] = sorter.get("key")
                    reverse: Optional[Any] = sorter.get("reverse")
                    if key and reverse:
                        order_by_sorters.append(Sorter(key=key, reverse=reverse))
                    elif key:
                        order_by_sorters.append(Sorter(key=key))
                    else:
                        raise ValueError(
                            '"order_by" list dict must have a key named "key"'
                        )
                else:
                    order_by_sorters.append(sorter)
        return order_by_sorters

    @staticmethod
    def _update_asset_forward_refs(asset_type: Type[_DataAssetT]) -> None:
        """Update forward refs of an asset_type if necessary.

        Note, this should be overridden in child datasource classes if forward
        refs need to be updated. For example, in Spark datasources we need to
        update forward refs only if the optional spark dependencies are installed
        so this method is overridden. Here it is a no op.

        Args:
            asset_type: Asset type to update forward refs.

        Returns:
            None, asset refs is updated in place.
        """
        pass

    # Abstract Methods
    @property
    def execution_engine_type(self) -> Type[_ExecutionEngineT]:
        """Return the ExecutionEngine type use for this Datasource"""
        raise NotImplementedError(
            """One needs to implement "execution_engine_type" on a Datasource subclass."""
        )

    def test_connection(self, test_assets: bool = True) -> None:
        """Test the connection for the Datasource.

        Args:
            test_assets: If assets have been passed to the Datasource, an attempt can be made to test them as well.

        Raises:
            TestConnectionError: If the connection test fails.
        """
        raise NotImplementedError(
            """One needs to implement "test_connection" on a Datasource subclass."""
        )

    def _build_data_connector(self, data_asset: _DataAssetT, **kwargs) -> None:
        """Any Datasource subclass that utilizes DataConnector should overwrite this method.

        Specific implementations instantiate appropriate DataConnector class and set "self._data_connector" to it.

        Args:
            data_asset: DataAsset using this DataConnector instance
            kwargs: Extra keyword arguments allow specification of arguments used by particular DataConnector subclasses
        """
        pass

    @classmethod
    def _get_exec_engine_excludes(cls) -> Set[str]:
        """
        Return a set of field names to exclude from the execution engine.

        All datasource fields are passed to the execution engine by default unless they are in this set.

        Default implementation is to return the combined set of field names from `_EXTRA_EXCLUDED_EXEC_ENG_ARGS`
        and `_BASE_DATASOURCE_FIELD_NAMES`.
        """
        return cls._EXTRA_EXCLUDED_EXEC_ENG_ARGS.union(_BASE_DATASOURCE_FIELD_NAMES)

    # End Abstract Methods


# This is used to prevent passing things like `type`, `assets` etc. to the execution engine
_BASE_DATASOURCE_FIELD_NAMES: Final[Set[str]] = {
    name for name in Datasource.__fields__.keys()
}


@dataclasses.dataclass(frozen=True)
class HeadData:
    """
    An immutable wrapper around pd.DataFrame for .head() methods which
        are intended to be used for visual inspection of BatchData.
    """

    data: pd.DataFrame

    @override
    def __repr__(self) -> str:
        return self.data.__repr__()


@public_api
class Batch:
    """This represents a batch of data.

    This is usually not the data itself but a hook to the data on an external datastore such as
    a spark or a sql database. An exception exists for pandas or any in-memory datastore.
    """

    def __init__(  # noqa: PLR0913
        self,
        datasource: Datasource,
        data_asset: DataAsset,
        batch_request: BatchRequest,
        data: BatchData,
        batch_markers: BatchMarkers,
        batch_spec: BatchSpec,
        batch_definition: BatchDefinition,
        metadata: Dict[str, Any] | None = None,
    ):
        # Immutable attributes
        self._datasource = datasource
        self._data_asset = data_asset
        self._batch_request = batch_request
        self._data = data

        # Immutable legacy attributes
        # TODO: These legacy fields are required but we should figure out how to delete them
        self._batch_markers = batch_markers
        self._batch_spec = batch_spec
        self._batch_definition = batch_definition

        # Mutable Attribute
        # metadata is any arbitrary data one wants to associate with a batch. GX will add arbitrary metadata
        # to a batch so developers may want to namespace any custom metadata they add.
        self.metadata = metadata or {}

        # Immutable generated attribute
        self._id = self._create_id()

    def _create_id(self) -> str:
        options_list = []
        for key, value in self.batch_request.options.items():
            if key != "path":
                options_list.append(f"{key}_{value}")
        return "-".join([self.datasource.name, self.data_asset.name, *options_list])

    @property
    def datasource(self) -> Datasource:
        return self._datasource

    @property
    def data_asset(self) -> DataAsset:
        return self._data_asset

    @property
    def batch_request(self) -> BatchRequest:
        return self._batch_request

    @property
    def data(self) -> BatchData:
        return self._data

    @property
    def batch_markers(self) -> BatchMarkers:
        return self._batch_markers

    @property
    def batch_spec(self) -> BatchSpec:
        return self._batch_spec

    @property
    def batch_definition(self) -> BatchDefinition:
        return self._batch_definition

    @property
    def id(self) -> str:
        return self._id

    @public_api
    @validate_arguments
    def columns(self) -> List[str]:
        """Return column names of this Batch.

        Returns
            List[str]
        """
        self.data.execution_engine.batch_manager.load_batch_list(batch_list=[self])
        metrics_calculator = MetricsCalculator(
            execution_engine=self.data.execution_engine,
            show_progress_bars=True,
        )
        return metrics_calculator.columns()

    @public_api
    @validate_arguments
    def head(
        self,
        n_rows: StrictInt = 5,
        fetch_all: StrictBool = False,
    ) -> HeadData:
        """Return the first n rows of this Batch.

        This method returns the first n rows for the Batch based on position.

        For negative values of n_rows, this method returns all rows except the last n rows.

        If n_rows is larger than the number of rows, this method returns all rows.

        Parameters
            n_rows: The number of rows to return from the Batch.
            fetch_all: If True, ignore n_rows and return the entire Batch.

        Returns
            HeadData
        """
        self.data.execution_engine.batch_manager.load_batch_list(batch_list=[self])
        metrics_calculator = MetricsCalculator(
            execution_engine=self.data.execution_engine,
            show_progress_bars=True,
        )
        table_head_df: pd.DataFrame = metrics_calculator.head(
            n_rows=n_rows,
            domain_kwargs={"batch_id": self.id},
            fetch_all=fetch_all,
        )
        return HeadData(data=table_head_df.reset_index(drop=True, inplace=False))

    @property
    def result_format(self) -> str | ResultFormat:
        # We always `return a ResultFormat`. However to prevent having to do #ignore[assignment] we return
        # `str | ResultFormat`. When the getter/setter have different types mypy gets confused on lines like:
        # batch.result_format = "SUMMARY"
        # See:
        # https://github.com/python/mypy/issues/3004
        return self._validator.result_format

    @result_format.setter
    def result_format(self, result_format: str | ResultFormat):
        # We allow a str result_format because this is an interactive workflow
        self._validator.result_format = ResultFormat(result_format)

    @overload
    def validate(self, expect: Expectation) -> ExpectationValidationResult:
        ...

    @overload
    def validate(self, expect: ExpectationSuite) -> ExpectationSuiteValidationResult:
        ...

    @public_api
    def validate(
        self, expect: Expectation | ExpectationSuite
    ) -> ExpectationValidationResult | ExpectationSuiteValidationResult:
        from great_expectations.core import ExpectationSuite
        from great_expectations.expectations.expectation import Expectation

        if isinstance(expect, Expectation):
            return self._validate_expectation(expect)
        elif isinstance(expect, ExpectationSuite):
            return self._validate_expectation_suite(expect)
        else:
            # If we are type checking, we should never fall through to this case. However, exploratory
            # workflows are not being type checked.
            raise ValueError(
                f"Trying to validate something that isn't an Expectation or an ExpectationSuite: {expect}"
            )

    def _validate_expectation(self, expect: Expectation) -> ExpectationValidationResult:
        return self._validator.validate_expectation(expect)

    def _validate_expectation_suite(
        self, expect: ExpectationSuite
    ) -> ExpectationSuiteValidationResult:
        return self._validator.validate_expectation_suite(expect)

    @functools.cached_property
    def _validator(self) -> V1Validator:
        from great_expectations.validator.v1_validator import Validator as V1Validator

        context = self.datasource.data_context
        if context is None:
            raise ValueError(
                "We can't validate batches that are attached to datasources without a data context"
            )
        batch_config = self.data_asset.add_batch_config(
            name="-".join(
                [self.datasource.name, self.data_asset.name, str(uuid.uuid4())]
            )
        )
        return V1Validator(
            context=context,
            batch_config=batch_config,
            batch_request_options=self.batch_request.options,
        )
