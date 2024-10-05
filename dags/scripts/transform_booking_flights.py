import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from airflow.hooks.base import BaseHook
import pytz
import os


def transform_flight_responses():
    # Get current date in UTC-3
    utc_min_3 = pytz.timezone('America/Buenos_Aires')
    current_date = datetime.now(utc_min_3)
    filename = current_date.strftime("%Y-%m-%d")
    parquet_file = f"/opt/airflow/data/{filename}.data.parquet"

    if not os.path.exists(parquet_file):
        print(f"File {parquet_file} not found. Skipping processing.")
        return

    # Load the data from Parquet file
    df = pd.read_parquet(parquet_file)

    # Ensure the column names match the new table structure
    df["DepartureDate"] = pd.to_datetime(df["DepartureDate"])
    df["ReturnDate"] = pd.to_datetime(df["ReturnDate"])
    df["SnapshotDate"] = pd.to_datetime(df["SnapshotDate"])

    # Rename columns to match the new table schema
    df.rename(columns={
        "DepartureDate": "departure_date",
        "ReturnDate": "arrival_date",
        "FlightCode": "flight_code",
        "AirlineCode": "airline_code",
        "Origin": "origin",
        "Destination": "destination",
        "Price": "price",
        "VAT": "vat",
        "CurrencyCode": "currency_code",
        "SnapshotDate": "snapshot_date"
    }, inplace=True)

    # Calculate flight duration and total amount
    df["flight_duration"] = (
        (df["arrival_date"] - df["departure_date"]).dt.total_seconds() / 3600
    ).round(2)
    df["price"] = df["price"] / 100
    df["vat"] = df["vat"] / 100
    df["total_amount"] = df["price"] + df["vat"]
    df.drop_duplicates(subset=["flight_code", "origin", "departure_date"], keep='first', inplace=True)

    print("Data transformation completed.")

    # Retrieve the Redshift connection details using Airflow connection ID
    redshift_conn = BaseHook.get_connection('PDA')

    # Create the Redshift connection string
    DATABASE_URL = (
        f"redshift+psycopg2://{redshift_conn.login}:{redshift_conn.password}"
        f"@{redshift_conn.host}:{redshift_conn.port}/{redshift_conn.schema}"
    )

    connection = None  # Initialize the connection variable
    try:
        # Create SQLAlchemy engine and connect to the database
        engine = create_engine(DATABASE_URL)
        connection = engine.connect()  # Explicit connection
        print("Database connection established.")

        # Insert new records into Redshift
        df.to_sql(
            'flights_daily_snapshots',
            con=connection,
            schema='2024_ignacio_santangelo_schema',
            if_exists='append',
            index=False,
            method='multi'
        )
        print(f"{len(df)} records successfully inserted into Redshift database.")

    except Exception as e:
        print(f"Error connecting to the database or inserting data: {e}")

    # Ensure the connection is closed after all operations
    if connection:
        connection.close()
        engine.dispose()
        print("Database connection closed.")

    return df
