from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from great_expectations.compatibility import pydantic
from great_expectations.core.evaluation_parameters import (
    EvaluationParameterDict,  # noqa: TCH001
)
from great_expectations.expectations.expectation import (
    ColumnMapExpectation,
    InvalidExpectationConfigurationError,
)
from great_expectations.render.components import (
    LegacyRendererType,
    RenderedStringTemplateContent,
)
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.util import num_to_str, substitute_none_for_missing

if TYPE_CHECKING:
    from great_expectations.core import (
        ExpectationConfiguration,
    )
    from great_expectations.core.expectation_validation_result import (
        ExpectationValidationResult,
    )


class ExpectColumnValuesToNotMatchLikePatternList(ColumnMapExpectation):
    """Expect the column entries to be strings that do NOT match any of a provided list of like pattern expressions.

    expect_column_values_to_not_match_like_pattern_list is a \
    [Column Map Expectation](https://docs.greatexpectations.io/docs/guides/expectations/creating_custom_expectations/how_to_create_custom_column_map_expectations).

    Args:
        column (str): \
            The column name.
        like_pattern_list (List[str]): \
            The list of like pattern expressions the column entries should NOT match.

    Keyword Args:
        mostly (None or a float between 0 and 1): \
            Successful if at least mostly fraction of values match the expectation. \
            For more detail, see [mostly](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#mostly).

    Other Parameters:
        result_format (str or None): \
            Which output mode to use: BOOLEAN_ONLY, BASIC, COMPLETE, or SUMMARY. \
            For more detail, see [result_format](https://docs.greatexpectations.io/docs/reference/expectations/result_format).
        catch_exceptions (boolean or None): \
            If True, then catch exceptions and include them as part of the result object. \
            For more detail, see [catch_exceptions](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#catch_exceptions).
        meta (dict or None): \
            A JSON-serializable dictionary (nesting allowed) that will be included in the output without \
            modification. For more detail, see [meta](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#meta).

    Returns:
        An [ExpectationSuiteValidationResult](https://docs.greatexpectations.io/docs/terms/validation_result)

        Exact fields vary depending on the values passed to result_format, catch_exceptions, and meta.

    See Also:
        [expect_column_values_to_match_regex](https://greatexpectations.io/expectations/expect_column_values_to_match_regex)
        [expect_column_values_to_match_regex_list](https://greatexpectations.io/expectations/expect_column_values_to_match_regex_list)
        [expect_column_values_to_not_match_regex](https://greatexpectations.io/expectations/expect_column_values_to_not_match_regex)
        [expect_column_values_to_not_match_regex_list](https://greatexpectations.io/expectations/expect_column_values_to_not_match_regex_list)
        [expect_column_values_to_match_like_pattern](https://greatexpectations.io/expectations/expect_column_values_to_match_like_pattern)
        [expect_column_values_to_match_like_pattern_list](https://greatexpectations.io/expectations/expect_column_values_to_match_like_pattern_list)
        [expect_column_values_to_not_match_like_pattern](https://greatexpectations.io/expectations/expect_column_values_to_not_match_like_pattern)
    """

    like_pattern_list: Union[List[str], EvaluationParameterDict]

    @pydantic.validator("like_pattern_list")
    def validate_like_pattern_list(
        cls, like_pattern_list: list[str] | EvaluationParameterDict
    ) -> list[str] | EvaluationParameterDict:
        if len(like_pattern_list) < 1:
            raise ValueError(
                "At least one like_pattern must be supplied in the like_pattern_list."
            )

        return like_pattern_list

    library_metadata = {
        "maturity": "production",
        "tags": ["core expectation", "column map expectation"],
        "contributors": [
            "@great_expectations",
        ],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }

    map_metric = "column_values.not_match_like_pattern_list"
    success_keys = (
        "like_pattern_list",
        "mostly",
    )
    args_keys = (
        "column",
        "like_pattern_list",
    )

    def validate_configuration(
        self, configuration: Optional[ExpectationConfiguration] = None
    ) -> None:
        """
        Validates the configuration of an Expectation.

        For `expect_column_values_to_not_match_like_pattern_list` it is required that:
            - 'like_pattern_list' is present in configuration's kwarg
            - assert 'like_pattern_list' is of type list or dict
            - if 'like_pattern_list' is list, assert non-empty
            - if 'like_pattern_list' is dict, assert a key "$PARAMETER" is present

        Args:
            configuration: An `ExpectationConfiguration` to validate. If no configuration is provided, it will be pulled
                                  from the configuration attribute of the Expectation instance.

        Raises:
            `InvalidExpectationConfigurationError`: The configuration does not contain the values required by the
                                  Expectation."
        """
        super().validate_configuration(configuration)
        configuration = configuration or self.configuration
        try:
            assert (
                "like_pattern_list" in configuration.kwargs
            ), "Must provide like_pattern_list"
            assert isinstance(
                configuration.kwargs.get("like_pattern_list"), (list, dict)
            ), "like_pattern_list must be a list or dict"
            assert isinstance(configuration.kwargs.get("like_pattern_list"), dict) or (
                len(configuration.kwargs.get("like_pattern_list")) > 0
            ), "At least one like_pattern must be supplied in the like_pattern_list."
            if isinstance(configuration.kwargs.get("like_pattern_list"), dict):
                assert "$PARAMETER" in configuration.kwargs.get(
                    "like_pattern_list"
                ), 'Evaluation Parameter dict for like_pattern_list kwarg must have "$PARAMETER" key.'

        except AssertionError as e:
            raise InvalidExpectationConfigurationError(str(e))

    @classmethod
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    def _prescriptive_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
        **kwargs,
    ) -> List[RenderedStringTemplateContent]:
        runtime_configuration = runtime_configuration or {}
        _ = False if runtime_configuration.get("include_column_name") is False else True
        styling = runtime_configuration.get("styling")

        params = substitute_none_for_missing(
            configuration.kwargs,
            ["column", "like_pattern_list", "mostly"],
        )
        if params["mostly"] is not None:
            params["mostly_pct"] = num_to_str(
                params["mostly"] * 100, no_scientific=True
            )

        if (
            not params.get("like_pattern_list")
            or len(params.get("like_pattern_list")) == 0
        ):
            values_string = "[ ]"
        else:
            for i, v in enumerate(params["like_pattern_list"]):
                params[f"v__{i!s}"] = v
            values_string = " ".join(
                [f"$v__{i!s}" for i, v in enumerate(params["like_pattern_list"])]
            )

        template_str = (
            "Values must not match the following like patterns: " + values_string
        )

        if params["mostly"] is not None and params["mostly"] < 1.0:
            params["mostly_pct"] = num_to_str(
                params["mostly"] * 100, no_scientific=True
            )
            template_str += ", at least $mostly_pct % of the time."
        else:
            template_str += "."

        return [
            RenderedStringTemplateContent(
                **{
                    "content_block_type": "string_template",
                    "string_template": {
                        "template": template_str,
                        "params": params,
                        "styling": styling,
                    },
                }
            )
        ]
