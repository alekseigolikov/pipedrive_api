from datetime import datetime,timedelta
from airflow import DAG 
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.operators.empty import EmptyOperator
from airflow.models.baseoperator import chain

from modules.pipedriveapi import PipedriveDeals

def publish_data_to_pipedrive(self):
    with open('/tmp/dbt_dataset/pipedrive_orders.csv') as file_in:
        deal_api_obj = PipedriveDeals()
        for line in file_in:
            title, status, value = line.split(",")
            deal_api_obj.add_deal({ "title":title, "status":status, "value":value })

#Default arguments
default_args = {
    'retries':5,
    'retry_Delay':timedelta(minutes=10)
}

with DAG('pipedrive_pipelinee',
        default_args = default_args,
        start_date=datetime(2024,8,29),
        schedule_interval="@daily"
) as dag:
    extract_dataset  = BashOperator(
    bash_command = "git clone https://github.com/dbt-labs/jaffle-shop-classic.git /tmp/dbt_dataset",
    dag = pipedrive_pipeline,
    task_id = 'extract_dataset')

    update_models = BashOperator(
    bash_command = "cp dbt_models/schema.yml dbt_dataset/models/;cp dbt_models/pipedrive_orders.sql /tmp/dbt_dataset/models/",
    dag = pipedrive_pipeline,
    task_id = 'update_models')

    run_tranformations = BashOperator(
    bash_command = "cd /tmp/dbt_dataset/; dbt debug&&dbt build",
    dag = pipedrive_pipeline,
    task_id = run_transformations)

    extract_data = PostgresOperator(
    task_id = 'extract_data',
    sql = """COPY ( COPY ( SELECT
                    pipedrive_title as title,
                    pipedrive_status as status,
                    pipedrive_value::int as value
                    FROM dbt.pipedrive_orders
                    ORDER by order_id ASC
            ) TO '/tmp/dbt_dataset/pipedrive_orders.csv' WITH CSV DELIMITER ',';""",
    postgres_conn_id = 'postgress_localhost',
    autocommit = True,
    dag = pipedrive_pipeline)

    publish_data = PythonOperator(
    python_callable = publish_data_to_pipedrive,
    dag = pipedrive_pipeline,
    task_id = publish_data)

    cleanup_env = BashOperator(
    bash_command = "rm -rf /tmp/dbt_dataset",
    dag = pipedrive_pipeline,
    task_id = cleanup_env)

    extract_dataset >> update_models >> run_tranformations >> extract_data >> publish_data >> cleanup_env