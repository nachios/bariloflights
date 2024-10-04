from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from scripts.get_exchange_rate import get_exchange_rate

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 1),
    'retries': 0,
}

with DAG(
        'get_exchange_rate_dag',
        default_args=default_args,
        schedule_interval='5 0 * * *',
        catchup=False
) as dag:

    get_exchange_rates = PythonOperator(
        task_id='get_exchange_rate_task',
        python_callable=get_exchange_rate
    )

    get_exchange_rates
