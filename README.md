# Pipedrive ETL flow

## Task
* Create ETL flow, load test data set from git repo, transforming with use of dbt and then loading result to pipedrive system

## Solution structure
* [Apache Airflow pipeline definition](./airflow_dag.py) - Airflow DAG definition which is triggered once a day and executing :
    * cloning of jaffle-shop-classic data set and copying own definition of schema and pipedrive_orders models definitions.
    * loading example data and trigering data transformation
    * extracting data from DB to temporary csv file
    * loading data pipedrive backend with use of its REST API
    * cleaning up all temp files
* [Keyvault class](./modules/keyvault.py) - Fake keyvault class that is used for purpose of storing and retreival of toknes for API authentication.
* [Pipedrive API class](./modules/pipedriveapi.py) - Small piece of Pipedrive implementation that is capable of:
    * PipedriveREST - Authentication and tokens management
    * PipedriveUser - Class for querying User information
    * PipedriveDeals - Class for querying and importing deals information
    * PipedriveCLI - Class for providing methods for CLI utility
* [CLI utility](./pipedrive.py) - CLI utility for managing tokens/accessing API methods from commandline, here are some examples:
    * `pipedrive.py fetch_token`
    * `pipedrive.py refresh_token`
    * `pipedrive.py whoami`
    * `pipedrive.py deals`
    * `pipedrive.py set_auth client_id some_clinet_id_value`
    * `pipedrive.py load_file path_to_csv_extracted_after_transformation`
* [DBT models for data transformation](./dbt_models/pipedrive_orders.sql)


## HowToStart
* Create App and get client_id, client_secret as described in [Pipedive documentation](https://pipedrive.readme.io/docs/marketplace-creating-a-proper-app)
* Authorize an app for some account and "code" token for further requesting authorization tokens for app as described in [Pipeline Oauth documentation](https://pipedrive.readme.io/docs/marketplace-oauth-authorization#step-1-requesting-authorization)
* store client_id, client_secret, code and app callback uri:
    * directly to config.json
    * or using pipedrive.py CLI<br />
    `pipedrive.py set_auth client-secret client_secret_value`
* Run pipedrive.py requesting new set of authorization and refresh tokens:<br />
`pipedrive.py fetch_token`
* Any time API will detect that token was expired, it will trigger token refresh procedure, alternativelly you can do it manually:<br />
`pipedrive.py refresh_token`
* Test that authorization tokens are correctly stored and pipedrive API working fine requesting info of account that authorized access for app <br />
`pipedrive.py whoami`
* Start Apache Airflow and trigger DAG execution

## What is missing in the solution:
* Data is not updated in Pipedrive if there are some data exists, every time data is loaded without checking.
