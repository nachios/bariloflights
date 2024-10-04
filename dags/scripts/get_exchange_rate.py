import currencyapicom
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from airflow.hooks.base import BaseHook
from airflow.models import Variable


def get_exchange_rate():
    # Initialize the currency API client
    client = currencyapicom.Client(Variable.get('CURRENCYAPI_TOKEN'))

    # Fetch exchange rate for today
    result = client.latest(currencies=['ARS'])

    # Extract necessary information
    last_updated_at = result['meta']['last_updated_at']
    currency_code = result['data']['ARS']['code']
    currency_value = result['data']['ARS']['value']

    # Create a DataFrame
    df = pd.DataFrame({
        'date': [last_updated_at],
        'currency': [currency_code],
        'value': [currency_value]
    })

    # Retrieve the Redshift connection details using Airflow connection ID
    redshift_conn = BaseHook.get_connection('PDA')

    # Create the Redshift connection string
    DATABASE_URL = (
        f"redshift+psycopg2://{redshift_conn.login}:{redshift_conn.password}"
        f"@{redshift_conn.host}:{redshift_conn.port}/{redshift_conn.schema}"
    )

    # Create SQLAlchemy engine and insert data into Redshift database
    try:
        engine = create_engine(DATABASE_URL)
        print("Database connection established.")

        # Attempt to insert the data into Redshift
        try:
            df.to_sql(
                'usd_daily_exchange_rate',
                schema='2024_ignacio_santangelo_schema',
                con=engine,
                if_exists='append',
                index=False)
            print("Data successfully inserted into Redshift database.")
        except SQLAlchemyError as e:
            print(f"Error inserting data into Redshift: {e}")

    except Exception as e:
        print(f"Error connecting to the database: {e}")

    finally:
        # Close the connection
        if 'engine' in locals():
            engine.dispose()
            print("Database connection closed.")
