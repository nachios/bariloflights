from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from scripts.distinct_flights import distinct_flight_data

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 3),
    'retries': 0,
}

with DAG(
        'distinct_bariloflights_dag',
        default_args=default_args,
        schedule_interval=None
        ) as dag:

    distinct_flights = PythonOperator(
        task_id='distinct_task',
        python_callable=distinct_flight_data
    )

    distinct_flights
