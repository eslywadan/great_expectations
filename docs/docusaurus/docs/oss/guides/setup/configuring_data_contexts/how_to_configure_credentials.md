---
title: Configure credentials
---
import Prerequisites from '../../../../components/_prerequisites.jsx'
import Tabs from '@theme/Tabs'
import TabItem from '@theme/TabItem'
import TechnicalTag from '../../../../reference/learn/term_tags/_tag.mdx';

This guide will explain how to populate credentials either through an environment variable, or configure your Great Expectations project to load credentials from either a YAML file or a secret manager.

If your Great Expectations deployment is in an environment without a file system, refer to [Instantiate an Ephemeral Data Context](/oss/guides/setup/configuring_data_contexts/instantiating_data_contexts/instantiate_data_context.md).

## Prerequisites

<Prerequisites></Prerequisites>

## Using Environment Variables

The quickest way to get started is by setting up your credentials as environment variables. 

First set values by entering ``export ENV_VAR_NAME=env_var_value`` in the terminal or adding the commands to your ``~/.bashrc`` file:

```bash title="Terminal input" name="docs/docusaurus/docs/oss/guides/setup/configuring_data_contexts/how_to_configure_credentials.py export_env_vars"
```

These can then be loaded into the `connection_string` parameter when we are adding a `datasource` to the Data Context.

```python title="Python input" name="docs/docusaurus/docs/oss/guides/setup/configuring_data_contexts/how_to_configure_credentials.py add_credentials_as_connection_string"
```


## Using YAML or Secret Manager 

<Tabs
  groupId="yaml-or-secret-manager"
  defaultValue='yaml'
  values={[
    {label: 'YAML', value:'yaml'},
    {label: 'Secret Manager', value: 'secret-manager'},
    ]}>

<TabItem value="yaml">

## Using the `config_variables.yml` file 

A more advanced option is to use the config variables YAML file. YAML files make variables more visible, easily editable, and allow for modularization (e.g. one file for dev, another for prod). 

If using a YAML file, save desired credentials or config values to ``great_expectations/uncommitted/config_variables.yml``:

```yaml title="YAML"name="docs/docusaurus/docs/oss/guides/setup/configuring_data_contexts/how_to_configure_credentials.py config_variables_yaml"
```

:::note

  - If you wish to store values that include the dollar sign character ``$``, please escape them using a backslash ``\`` so substitution is not attempted. For example in the above example for Postgres credentials you could set ``password: pa\$sword`` if your password is ``pa$sword``. Say that 5 times fast, and also please choose a more secure password!
  - You can also have multiple substitutions for the same item, e.g. ``database_string: ${USER}:${PASSWORD}@${HOST}:${PORT}/${DATABASE}``

:::

Then the config variable can be loaded into the `connection_string` parameter when we are adding a `datasource` to the Data Context.

```python title="Python input" name="docs/docusaurus/docs/oss/guides/setup/configuring_data_contexts/how_to_configure_credentials.py add_credential_from_yml"
```

## Additional Notes

- The default ``config_variables.yml`` file located at ``great_expectations/uncommitted/config_variables.yml`` applies to deployments using  ``FileSystemDataContexts``.
- To view the full script used in this page, see it on GitHub: [how_to_configure_credentials.py](https://github.com/great-expectations/great_expectations/tree/develop/docs/docusaurus/docs/oss/guides/setup/configuring_data_contexts/how_to_configure_credentials.py)

</TabItem>
<TabItem value="secret-manager">

Select one of the following secret manager applications:
<Tabs
  groupId="secret-manager"
  defaultValue='aws'
  values={[
  {label: 'AWS Secrets Manager', value:'aws'},
  {label: 'GCP Secret Manager', value:'gcp'},
  {label: 'Azure Key Vault', value:'azure'},
  ]}>

<TabItem value="aws">

Configure your Great Expectations project to substitute variables from the AWS Secrets Manager.

## Prerequisites

<Prerequisites>

- An AWS Secrets Manager instance. See [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/tutorials_basic.html).

</Prerequisites>

:::warning

Secrets store substitution uses the configurations from your ``config_variables.yml`` file **after** all other types of substitution are applied from environment variables.

The secrets store substitution works based on keywords. It tries to retrieve secrets from the secrets store for the following values :

- AWS: values starting with ``secret|arn:aws:secretsmanager`` if the values you provide don't match with the keywords above, the values won't be substituted.

:::

## Setup

To use AWS Secrets Manager, you may need to install the ``great_expectations`` package with its ``aws_secrets`` extra requirement:

```bash title="Terminal input"
pip install 'great_expectations[aws_secrets]'
```

In order to substitute your value by a secret in AWS Secrets Manager, you need to provide an arn of the secret like this one:
``secret|arn:aws:secretsmanager:123456789012:secret:my_secret-1zAyu6``

:::note

The last 7 characters of the arn are automatically generated by AWS and are not mandatory to retrieve the secret, thus ``secret|arn:aws:secretsmanager:region-name-1:123456789012:secret:my_secret`` will retrieve the same secret.

:::

You will get the latest version of the secret by default.

You can get a specific version of the secret you want to retrieve by specifying its version UUID like this: ``secret|arn:aws:secretsmanager:region-name-1:123456789012:secret:my_secret:00000000-0000-0000-0000-000000000000``

If your secret value is a JSON string, you can retrieve a specific value like this:
``secret|arn:aws:secretsmanager:region-name-1:123456789012:secret:my_secret|key``

Or like this:
``secret|arn:aws:secretsmanager:region-name-1:123456789012:secret:my_secret:00000000-0000-0000-0000-000000000000|key``

**Example config_variables.yml:**

```yaml title="YAML"
# We can configure a single connection string
my_aws_creds:  secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|connection_string

# Or each component of the connection string separately
drivername: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|drivername
host: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|host
port: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|port
username: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|username
password: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|password
database: secret|arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:dev_db_credentials|database
```

Once configured, the credentials can be loaded into the `connection_string` parameter when we are adding a `datasource` to the Data Context.

```python title="Python" 
# We can use a single connection string
pg_datasource = context.sources.add_or_update_sql(
    name="my_postgres_db", connection_string="${my_aws_creds}"
)

# Or each component of the connection string separately
pg_datasource = context.sources.add_or_update_sql(
    name="my_postgres_db", connection_string="${drivername}://${username}:${password}@${host}:${port}/${database}"
)
```


</TabItem>
<TabItem value="gcp">

Configure your Great Expectations project to substitute variables from the GCP Secrets Manager.

## Prerequisites

<Prerequisites>

- Configured a secret manager and secrets in the cloud with [GCP Secret Manager](https://cloud.google.com/secret-manager/docs/quickstart)

</Prerequisites>

:::warning

Secrets store substitution uses the configurations from your ``config_variables.yml`` project config **after** substitutions are applied from environment variables.

The secrets store substitution works based on keywords. It tries to retrieve secrets from the secrets store for the following values :

- GCP: values matching the following regex ``^secret\|projects\/[a-z0-9\_\-]{6,30}\/secrets`` if the values you provide don't match with the keywords above, the values won't be substituted.

:::

## Setup

To use GCP Secret Manager, you may need to install the ``great_expectations`` package with its ``gcp`` extra requirement:

```bash title="Terminal input"
pip install 'great_expectations[gcp]'
```

In order to substitute your value by a secret in GCP Secret Manager, you need to provide a name of the secret like this one:
``secret|projects/project_id/secrets/my_secret``

You will get the latest version of the secret by default.

You can get a specific version of the secret you want to retrieve by specifying its version id like this: ``secret|projects/project_id/secrets/my_secret/versions/1``

If your secret value is a JSON string, you can retrieve a specific value like this:
``secret|projects/project_id/secrets/my_secret|key``

Or like this:
``secret|projects/project_id/secrets/my_secret/versions/1|key``

**Example config_variables.yml:**

```yaml title="YAML"
# We can configure a single connection string
my_gcp_creds: secret|projects/${PROJECT_ID}/secrets/dev_db_credentials|connection_string

# Or each component of the connection string separately
drivername: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_DRIVERNAME
host: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_HOST
port: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_PORT
username: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_USERNAME
password: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_PASSWORD
database: secret|projects/${PROJECT_ID}/secrets/PROD_DB_CREDENTIALS_DATABASE
```

Once configured, the credentials can be loaded into the `connection_string` parameter when we are adding a `datasource` to the Data Context.

```python title="Python" 
# We can use a single connection string 
pg_datasource = context.sources.add_or_update_sql(
    name="my_postgres_db", connection_string="${my_gcp_creds}"
)

# Or each component of the connection string separately
pg_datasource = context.sources.add_or_update_sql(
    name="my_postgres_db", connection_string="${drivername}://${username}:${password}@${host}:${port}/${database}"
)
```

</TabItem>
<TabItem value="azure">

Configure your Great Expectations project to substitute variables from the Azure Key Vault.

## Prerequisites

<Prerequisites>

- [Set up a working deployment of Great Expectations](/oss/guides/setup/setup_overview.md)
- Configured a secret manager and secrets in the cloud with [Azure Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/general/overview)

</Prerequisites>

:::warning

Secrets store substitution uses the configurations from your ``config_variables.yml`` file **after** all other types of substitution are applied from environment variables.

The secrets store substitution works based on keywords. It tries to retrieve secrets from the secrets store for the following values :

- Azure : values matching the following regex ``^secret\|https:\/\/[a-zA-Z0-9\-]{3,24}\.vault\.azure\.net`` if the values you provide don't match with the keywords above, the values won't be substituted.

:::

## Setup

To use Azure Key Vault, you may need to install the ``great_expectations`` package with its ``azure_secrets`` extra requirement:

```bash title="Terminal input"
pip install 'great_expectations[azure_secrets]'
```

In order to substitute your value by a secret in Azure Key Vault, you need to provide a name of the secret like this one:
``secret|https://my-vault-name.vault.azure.net/secrets/my-secret``

You will get the latest version of the secret by default.

You can get a specific version of the secret you want to retrieve by specifying its version id (32 lowercase alphanumeric characters) like this: ``secret|https://my-vault-name.vault.azure.net/secrets/my-secret/a0b00aba001aaab10b111001100a11ab``

If your secret value is a JSON string, you can retrieve a specific value like this:
``secret|https://my-vault-name.vault.azure.net/secrets/my-secret|key``

Or like this:
``secret|https://my-vault-name.vault.azure.net/secrets/my-secret/a0b00aba001aaab10b111001100a11ab|key``


**Example config_variables.yml:**

```yaml title="YAML"
# We can configure a single connection string
my_abs_creds: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|connection_string

# Or each component of the connection string separately
drivername: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|host
host: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|host
port: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|port
username: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|username
password: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|password
database: secret|https://${VAULT_NAME}.vault.azure.net/secrets/dev_db_credentials|database
```

Once configured, the credentials can be loaded into the `connection_string` parameter when we are adding a `datasource` to the Data Context.

```python title="Python" 
# We can use a single connection string
pg_datasource = context.sources.add_or_update_sql(
    name="my_postgres_db", connection_string="${my_gcp_creds}"
)

# Or each component of the connection string separately
pg_datasource = context.sources.add_or_update_sql(
    name="my_postgres_db", connection_string="${drivername}://${username}:${password}@${host}:${port}/${database}"
)
```
</TabItem>
</Tabs>

</TabItem>
</Tabs>