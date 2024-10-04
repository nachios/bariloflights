from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime
from scripts.get_booking_flights import batch_get_booking_flights
from scripts.transform_booking_flights import transform_flight_responses

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 1),
    'retries': 0,
}

with DAG(
        'bariloflights_dag',
        default_args=default_args,
        schedule_interval='0 22 * * *',
        catchup=False
        ) as dag:

    get_flights = PythonOperator(
        task_id='get_booking_flights_task',
        python_callable=batch_get_booking_flights
    )

    transform_responses = PythonOperator(
        task_id='transform_booking_responses_task',
        python_callable=transform_flight_responses
    )

    trigger_distinct_flights = TriggerDagRunOperator(
        task_id='trigger_distinct_bariloflights_dag',
        trigger_dag_id='distinct_bariloflights_dag',
        wait_for_completion=False
    )

    get_flights >> transform_responses >> trigger_distinct_flights
