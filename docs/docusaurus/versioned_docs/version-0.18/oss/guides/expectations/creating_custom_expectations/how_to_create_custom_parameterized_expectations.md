---
title: Create Custom Parameterized Expectations
---
import Prerequisites from '../creating_custom_expectations/components/prerequisites.jsx'
import TechnicalTag from '../../../../reference/learn/term_tags/_tag.mdx';

This guide will walk you through the process of creating Parameterized <TechnicalTag tag="expectation" text="Expectations" /> - very quickly. This method is only available using the new Modular Expectations API in 0.13.

## Prerequisites

<Prerequisites>

</Prerequisites>

A Parameterized <TechnicalTag tag="expectation" text="Expectation"/> is a capability unlocked by Modular Expectations. Now that Expectations are structured in class form, it is easy to inherit from these classes and build similar Expectations that are adapted to your own needs.

## Select an Expectation to inherit from

For the purpose of this exercise, we will implement the Expectations `expect_column_mean_to_be_positive` and `expect_column_values_to_be_two_letter_country_code` - realistic Expectations
of the data that can easily inherit from `expect_column_mean_to_be_between` and `expect_column_values_to_be_in_set` respectively.

## Select default values for your class

Our first implementation will be `expect_column_mean_to_be_positive`.

As can be seen in the implementation below, we have chosen to keep our default minimum value at 0, given that we are validating that all our values are positive. Setting the upper bound to `None` means that no upper bound will be checked – effectively setting the threshold at ∞ and allowing any positive value.

Notice that we do not need to set `default_kwarg_values` for all kwargs: it is sufficient to set them only for ones for which we would like to set a default value. To keep our implementation simple, we do not override the `metric_dependencies` or `success_keys`.

````python name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/test_expect_column_mean_to_be_positive.py ExpectColumnMeanToBePositive_class_def"
````

:::info
We could also explicitly override our parent methods to modify the behavior of our new Expectation, for example by updating the configuration validation to require the values we set as defaults not be altered.

```python name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/test_expect_column_mean_to_be_positive.py validate_config"
```
:::

For another example, let's take a look at `expect_column_values_to_be_in_set`.

In this case, we will only be changing our `value_set`:

```python name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/test_expect_column_values_to_be_in_set.py ExpectColumnValuesToBeTwoLetterCountryCode_class_def"
```

## Contribute (Optional)

If you plan to contribute your Expectation to the public open source project, you should include a `library_metadata` object. For example:

```python name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/test_expect_column_mean_to_be_positive.py library_metadata"
```

This is particularly important because ***we*** want to make sure that ***you*** get credit for all your hard work!

Additionally, you will need to implement some basic examples and test cases before your contribution can be accepted. For guidance on examples and testing, see our [guide on implementing examples and test cases](../features_custom_expectations/how_to_add_example_cases_for_an_expectation.md).

:::note
For more information on our code standards and contribution, see our guide on [Levels of Maturity](/oss/contributing/contributing_maturity.md#expectation-contributions) for Expectations.
:::
