import pandas as pd
from sqlalchemy import create_engine
from airflow.hooks.base import BaseHook


def distinct_flight_data():
    # Retrieve the Redshift connection details using Airflow connection ID
    redshift_conn = BaseHook.get_connection('PDA')

    # Create the Redshift connection string
    DATABASE_URL = (
        f"redshift+psycopg2://{redshift_conn.login}:{redshift_conn.password}"
        f"@{redshift_conn.host}:{redshift_conn.port}/{redshift_conn.schema}"
    )

    connection = None  # Initialize connection variable
    try:
        # Create SQLAlchemy engine and connect to the database
        engine = create_engine(DATABASE_URL)
        connection = engine.connect()  # Explicit connection
        print("Database connection established.")

        # Read the 'flights_daily_snapshots' table into a DataFrame
        print("Reading 'flights_daily_snapshots' table.")
        df = pd.read_sql_table('flights_daily_snapshots', con=connection, schema='2024_ignacio_santangelo_schema')
        print("Data read successfully from Redshift.")

    except Exception as e:
        print(f"Error connecting to the database or reading data: {e}")
        if connection:
            connection.close()  # Close connection if it was opened
            engine.dispose()
        return  # Stop further execution if there's an error

    # Proceed with data transformation since connection and data reading succeeded
    df['departure_date'] = pd.to_datetime(df['departure_date'])
    df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])

    # Drop duplicates based on 'flight_code' and 'departure_date'
    df_unique = df.drop_duplicates(subset=['flight_code', 'departure_date'])

    # Get the latest snapshot date for each flight
    df_last_snapshot = df.groupby('flight_code')['snapshot_date'].max().reset_index()

    # Get the latest snapshot date for comparison
    latest_snapshot_date = df_last_snapshot['snapshot_date'].max().date()

    # Determine 'is_active' based on the latest snapshot date
    df_final = pd.merge(df_unique, df_last_snapshot, on='flight_code', how='left', suffixes=('', '_last'))
    df_final['is_active'] = df_final['snapshot_date_last'].apply(
        lambda x: 1 if pd.notna(x) and x.date() >= latest_snapshot_date else 0
    )

    # Select the relevant columns: 'flight_code', 'departure_date', 'origin', 'destination', 'airline_code', 'is_active'
    df_result = df_final[['flight_code', 'departure_date', 'origin', 'destination', 'airline_code', 'is_active']]

    try:
        # Insert the processed data into the 'flights' table
        df_result.to_sql(
            'flights',
            schema='2024_ignacio_santangelo_schema',
            con=connection,
            if_exists='replace',
            index=False)
        print("Data inserted into 'flights' table successfully.")

    except Exception as e:
        print(f"Error inserting data: {e}")

    finally:
        # Close connection after insertion
        if connection:
            connection.close()
            engine.dispose()
            print("Database connection closed.")

    return df_result
