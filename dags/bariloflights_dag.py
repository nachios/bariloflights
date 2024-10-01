from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from scripts.get_booking_flights import get_booking_flights
from scripts.transform_booking_flights import transform_flight_responses
from scripts.distinct_flights import distinct_flight_data

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 10, 1),
    'retries': 1,
}

with DAG(
        'bariloflights_dag', 
        default_args=default_args, 
        schedule_interval='@daily'
        ) as dag:
    
    get_flights = PythonOperator(
        task_id='get_booking_flights_task',
        python_callable=get_booking_flights
    )

    transform_responses = PythonOperator(
        task_id='transform_booking_responses_task',
        python_callable=transform_flight_responses
    )

    distinct_flights = PythonOperator(
        task_id='distinct_flight_data_task',
        python_callable=distinct_flight_data
    )

    get_flights >> transform_responses >> distinct_flights  # Setting task dependencies
