from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from lib.extract_digital_iservices_data import extract_consumption_data
from lib.format_digital_iservices_data import format_consumption_data
from lib.format_ademe_data import format_carbon_data
from lib.combination import combine_data
from lib.index import index_data_to_elasticsearch

with DAG(
        dag_id='datalake_dag',
        schedule="@daily",
        start_date=datetime(2024, 6, 15)
) as dag:
    task_extract_consumption_data = PythonOperator(
        task_id="extract_consumption_data",
        python_callable=extract_consumption_data,
    )

    task_format_consumption_data = PythonOperator(
        task_id="format_consumption_data",
        python_callable=format_consumption_data,
    )

    task_format_carbon_data = PythonOperator(
        task_id="format_carbon_data",
        python_callable=format_carbon_data,
    )

    task_combine_data = PythonOperator(
        task_id="combine_data",
        python_callable=combine_data,
    )

    index_data_to_elasticsearch = PythonOperator(
        task_id="index_data_to_elasticsearch",
        python_callable=index_data_to_elasticsearch,
    )

    task_extract_consumption_data >> [task_format_consumption_data, task_format_carbon_data] >> task_combine_data >> index_data_to_elasticsearch