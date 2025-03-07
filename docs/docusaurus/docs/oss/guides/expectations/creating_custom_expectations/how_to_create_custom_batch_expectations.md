---
title: Create a Custom Batch Expectation
---
import Prerequisites from '../creating_custom_expectations/components/prerequisites.jsx'
import TechnicalTag from '../../../../reference/learn/term_tags/_tag.mdx';

**`BatchExpectations`** are one of the most common types of <TechnicalTag tag="expectation" text="Expectation"/>. 
They are evaluated for an entire Batch, and answer a semantic question about the Batch itself. For example, `expect_table_column_count_to_equal` and `expect_table_row_count_to_equal` answer how many columns and rows are in your Batch.

This guide will walk you through the process of creating your own custom `BatchExpectation`.

## Prerequisites

<Prerequisites>

</Prerequisites>

## Choose a name for your Expectation

First, decide on a name for your own Expectation. By convention, `BatchExpectations` always start with `expect_table_`. 
For more on Expectation naming conventions, see the [Expectations section](../../../contributing/style_guides/code_style.md#expectations) of the Code Style Guide.

Your Expectation will have two versions of the same name: a `CamelCaseName` and a `snake_case_name`. For example, this tutorial will use:

- `ExpectBatchColumnsToBeUnique`
- `expect_batch_columns_to_be_unique`

## Copy and rename the template file

By convention, each Expectation is kept in its own python file, named with the snake_case version of the Expectation's name.

You can find the template file for a custom [BatchExpectation here](https://github.com/great-expectations/great_expectations/blob/develop/examples/expectations/batch_expectation_template.py).
Download the file, place it in the appropriate directory, and rename it to the appropriate name.

```bash title="Terminal input"
cp batch_expectation_template.py /SOME_DIRECTORY/expect_batch_columns_to_be_unique.py
```

### Storing Expectation files

During development, you don't need to store Expectation files in a specific location. Expectation files are self-contained and can be executed anywhere as long as GX is installed However, to use your new Expectation with other GX components, you'll need to make sure the file is stored one of the following locations:

- If you're building a <TechnicalTag tag="custom_expectation" text="Custom Expectation" /> for personal use, you'll need to put it in the <code>great_expectations/plugins/expectations</code> folder of your GX deployment, and import your Custom Expectation from that directory whenever it will be used. When you instantiate the corresponding <code>DataContext</code>, it will automatically make all <TechnicalTag tag="plugin" text="Plugins" /> in the directory available for use.

- If you're building a Custom Expectation to contribute to the open source project, you'll need to put it in the repo for the Great Expectations library itself. Most likely, this will be within a package within <code>contrib/</code>: <code>great_expectations/contrib/SOME_PACKAGE/SOME_PACKAGE/expectations/</code>. To use these Expectations, you'll need to install the package.

For more information about Custom Expectations, see [Use a Custom Expectation](./how_to_use_custom_expectations.md).

## Generate a diagnostic checklist for your Expectation

Once you've copied and renamed the template file, you can execute it as follows.

```bash title="Terminal input"
python expect_batch_columns_to_be_unique.py
```

The template file is set up so that this will run the Expectation's `print_diagnostic_checklist()` method. This will run a diagnostic script on your new Expectation, and return a checklist of steps to get it to full production readiness.
This guide will walk you through the first five steps, the minimum for a functioning Custom Expectation and all that is required for [contribution back to open source](/oss/contributing/contributing_maturity.md#expectation-contributions) at an Experimental level.

```
Completeness checklist for ExpectColumnAggregateToMatchSomeCriteria:
  ✔ Has a valid library_metadata object
    Has a docstring, including a one-line short description that begins with "Expect" and ends with a period
    Has at least one positive and negative example case, and all test cases pass
    Has core logic and passes tests on at least one Execution Engine
    Passes all linting checks
...
```

When in doubt, the next step to implement is the first one that doesn't have a ✔ next to it. This guide covers the first five steps on the checklist.

## Change the Expectation class name and add a docstring

By convention, your <TechnicalTag tag="metric" text="Metric"/> class is defined first in a Custom Expectation. For now, we're going to skip to the Expectation class and begin laying the groundwork for the functionality of your Custom Expectation.

Let's start by updating your Expectation's name and docstring.

Replace the Expectation class name
```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/batch_expectation_template.py ExpectBatchToMeetSomeCriteria class_def"
```

with your real Expectation class name, in upper camel case:
```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/expect_batch_columns_to_be_unique.py ExpectBatchColumnsToBeUnique class_def"
```

You can also go ahead and write a new one-line docstring, replacing
```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/batch_expectation_template.py docstring"
```

with something like:
```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/expect_batch_columns_to_be_unique.py docstring"
```

Make sure your one-line docstring begins with "Expect " and ends with a period. You'll also need to change the class name at the bottom of the file, by replacing this line:
```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/batch_expectation_template.py diagnostics"
```

with this one:
```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/expect_batch_columns_to_be_unique.py diagnostics"
```

Later, you can go back and write a more thorough docstring. See [Expectation Docstring Formatting](https://github.com/great-expectations/great_expectations/blob/develop/docs/expectation_gallery/3-expectation-docstring-formatting.md).

At this point you can re-run your diagnostic checklist. You should see something like this:
```
$ python expect_batch_columns_to_be_unique.py

Completeness checklist for ExpectBatchColumnsToBeUnique:
  ✔ Has a valid library_metadata object
  ✔ Has a docstring, including a one-line short description that begins with "Expect" and ends with a period
    Has at least one positive and negative example case, and all test cases pass
    Has core logic and passes tests on at least one Execution Engine
    Passes all linting checks
...
```

Congratulations! You're one step closer to implementing a Custom Expectation.

## Add example cases

You're going to search for `examples = []` in your file, and replace it with at least two test examples. These examples serve the following purposes:

- They provide test fixtures that Great Expectations can execute automatically with pytest.

- They help users understand the logic of your Expectation by providing tidy examples of paired input and output. If you contribute your Expectation to open source, these examples will appear in the Gallery.

Your examples will look similar to this example:

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/expect_batch_columns_to_be_unique.py examples"
```

Here's a quick overview of how to create test cases to populate `examples`. The overall structure is a list of dictionaries. Each dictionary has two keys:

* `data`: defines the input data of the example as a Batch. In these examples the Batch has three columns (`col1`, `col2` and `col3`). These columns have 5 rows. (Note: if you define multiple columns, make sure that they have the same number of rows.)
* `tests`: a list of test cases to validate against the data frame defined in the corresponding `data`.
	* `title` should be a descriptive name for the test case. Make sure to have no spaces.
	* `include_in_gallery`: This must be set to `True` if you want this test case to be visible in the Gallery as an example.
	* `in` contains exactly the parameters that you want to pass in to the Expectation. `"in": {"strict": True}` in the example above is equivalent to `expect_batch_columns_to_be_unique(strict=True)`
	* `out` is based on the Validation Result returned when executing the Expectation.
	* `exact_match_out`: if you set `exact_match_out=False`, then you don’t need to include all the elements of the Validation Result object - only the ones that are important to test.
* `only_for` (optional): the list of backends that the Expectation should use for testing
* `suppress_test_for` (optional): the list of backends that the Expectation should not use for testing
* `only_for` and `suppres_test_for` can be specified at the top-level (next to `data` and `tests`) or within specific tests (next to `title`, and so on)

If you run your Expectation file again, you won't see any new checkmarks, as the logic for your Custom Expectation hasn't been implemented yet. 
However, you should see that the tests you've written are now being caught and reported in your checklist:

```
$ python expect_batch_columns_to_be_unique.py

Completeness checklist for ExpectBatchColumnsToBeUnique:
  ✔ Has a valid library_metadata object
  ✔ Has a docstring, including a one-line short description that begins with "Expect" and ends with a period
...
	Has core logic that passes tests for all applicable Execution Engines and SQL dialects
		  Only 0 / 2 tests for pandas are passing
		  Failing: basic_positive_test, basic_negative_test
...
```

:::note
For more information on tests and example cases, <br/>
see our guide on [creating example cases for a Custom Expectation](../features_custom_expectations/how_to_add_example_cases_for_an_expectation.md).
:::

## Implement your Metric and connect it to your Expectation

This is the stage where you implement the actual business logic for your Expectation. 
To do so, you'll need to implement a function within a <TechnicalTag tag="metric" text="Metric"/> class, and link it to your Expectation.
By the time your Expectation is complete, your Metric will have functions for all three Execution Engines (Pandas, Spark, and SQLAlchemy) supported by Great Expectations. For now, we're only going to define one.

:::note
Metrics answer questions about your data posed by your Expectation, <br/> and allow your Expectation to judge whether your data meets ***your*** expectations.
:::

Your Metric function will have the `@metric_value` decorator, with the appropriate `engine`. Metric functions can be as complex as you like, but they're often very short. For example, here's the definition for a Metric function to find the unique columns of a Batch with the PandasExecutionEngine.

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/expect_batch_columns_to_be_unique.py pandas"
```

:::note
The `@metric_value` decorator allows us to explicitly structure queries and directly access our compute domain. 
While this can result in extra roundtrips to your database in some situations, it allows for advanced functionality and customization of your Custom Expectations.
:::

This is all that you need to define for now. In the next step, we will implement the method to validate the result of this Metric.

### Other parameters

Expectation Success Keys - A tuple consisting of values that must / could be provided by the user and defines how the Expectation evaluates success.

Expectation Default Kwarg Values (Optional) - Default values for success keys and the defined domain, among other values.

Metric Condition Value Keys (Optional) - Contains any additional arguments passed as parameters to compute the Metric.

Next, choose a Metric Identifier for your Metric. By convention, Metric Identifiers for Column Map Expectations start with `column.`. 
The remainder of the Metric Identifier simply describes what the Metric computes, in snake case. For this example, we'll use `column.custom_max`.

You'll need to substitute this metric into two places in the code. First, in the Metric class, replace

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/batch_expectation_template.py metric_name"
```

with

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/expect_batch_columns_to_be_unique.py metric_name"
```

Second, in the Expectation class, replace

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/batch_expectation_template.py metric_dependencies"
```

with

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/expect_batch_columns_to_be_unique.py metric_dependencies"
```

It's essential to make sure to use matching Metric Identifier strings across your Metric class and Expectation class. This is how the Expectation knows which Metric to use for its internal logic.

Finally, rename the Metric class name itself, using the camel case version of the Metric Identifier, minus any periods.

For example, replace:

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/batch_expectation_template.py BatchMeetsSomeCriteria class_def"
```

with 

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/expect_batch_columns_to_be_unique.py BatchColumnsUnique class_def"
```

## Validate

In this step, we simply need to validate that the results of our Metrics meet our Expectation.

The validate method is implemented as `_validate(...)`:

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/batch_expectation_template.py validate"
```

This method takes a dictionary named `metrics`, which contains all Metrics requested by your Metric dependencies, 
and performs a simple validation against your success keys (i.e. important thresholds) in order to return a dictionary indicating whether the Expectation has evaluated successfully or not.

To do so, we'll be accessing our success keys, as well as the result of our previously-calculated Metrics.
For example, here is the definition of a `_validate(...)` method to validate the results of our `table.columns.unique` Metric against our success keys:

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/expect_batch_columns_to_be_unique.py validate"
```

Running your diagnostic checklist at this point should return something like this:
```
$ python expect_batch_columns_to_be_unique.py

Completeness checklist for ExpectBatchColumnsToBeUnique:
  ✔ Has a valid library_metadata object
  ✔ Has a docstring, including a one-line short description that begins with "Expect" and ends with a period
  ✔ Has at least one positive and negative example case, and all test cases pass
  ✔ Has core logic and passes tests on at least one Execution Engine
    Passes all linting checks
...
```

## Linting

Finally, we need to lint our now-functioning Custom Expectation. Our CI system will test your code using `black`, and `ruff`.

If you've [set up your dev environment](https://github.com/great-expectations/great_expectations/blob/develop/CONTRIBUTING_CODE.md), these libraries will already be available to you, and can be invoked from your command line to automatically lint your code:

```console title="Terminal input"
black <PATH/TO/YOUR/EXPECTATION.py>
ruff <PATH/TO/YOUR/EXPECTATION.py> --fix
```

:::info
If desired, you can automate this to happen at commit time. See our [guidance on linting](../../../contributing/style_guides/code_style.md#linting) for more on this process.
:::

Once this is done, running your diagnostic checklist should now reflect your Custom Expectation as meeting our linting requirements:

```
$ python expect_batch_columns_to_be_unique.py

Completeness checklist for ExpectBatchColumnsToBeUnique:
  ✔ Has a valid library_metadata object
  ✔ Has a docstring, including a one-line short description that begins with "Expect" and ends with a period
  ✔ Has at least one positive and negative example case, and all test cases pass
  ✔ Has core logic and passes tests on at least one Execution Engine
  ✔ Passes all linting checks
...
```
## Contribute (Optional)

This guide will leave you with a Custom Expectation sufficient for [contribution](https://github.com/great-expectations/great_expectations/blob/develop/CONTRIBUTING_EXPECTATIONS.md) to Great Expectations at an Experimental level.

If you plan to contribute your Expectation to the public open source project, you should update the `library_metadata` object before submitting your [Pull Request](https://github.com/great-expectations/great_expectations/pulls). For example:

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/batch_expectation_template.py library_metadata"
```

would become

```python title="Python" name="docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/expect_batch_columns_to_be_unique.py library_metadata"
```

This is particularly important because ***we*** want to make sure that ***you*** get credit for all your hard work!

:::note
For more information on our code standards and contribution, see our guide on [Levels of Maturity](/oss/contributing/contributing_maturity.md#expectation-contributions) for Expectations.

To view the full script used in this page, see it on GitHub:
- [expect_batch_columns_to_be_unique.py](https://github.com/great-expectations/great_expectations/blob/develop/docs/docusaurus/docs/oss/guides/expectations/creating_custom_expectations/expect_batch_columns_to_be_unique.py)
:::
