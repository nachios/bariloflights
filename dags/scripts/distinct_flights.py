import pandas as pd
from sqlalchemy import create_engine
import os

def distinct_flight_data():
    # Define Redshift connection parameters
    DATABASE_URL = (
        f"redshift+psycopg2://{os.getenv('REDSHIFT_USER')}:{os.getenv('REDSHIFT_PASSWORD')}"
        f"@{os.getenv('REDSHIFT_HOST')}:{os.getenv('REDSHIFT_PORT')}/{os.getenv('REDSHIFT_DB')}"
    )

    # Create SQLAlchemy engine
    engine = create_engine(DATABASE_URL)

    # Read the 'flights_daily_snapshots' table into a DataFrame
    print("Reading 'flights_daily_snapshots' table...")
    df = pd.read_sql_table('flights_daily_snapshots', con=engine)
    print("Data read successfully from Redshift.")

    # Ensure 'DepartureDate' is in datetime format
    df['DepartureDate'] = pd.to_datetime(df['DepartureDate']).dt.date  # Keep only the date part
    
    # Convert 'SnapshotDate' to datetime
    df['SnapshotDate'] = pd.to_datetime(df['SnapshotDate'])

    # Drop duplicates based on 'FlightCode' and 'DepartureDate'
    df_unique = df.drop_duplicates(subset=['FlightCode', 'DepartureDate'])

    # Get the latest snapshot date for each flight
    df_last_snapshot = df.groupby('FlightCode')['SnapshotDate'].max().reset_index()

    # Get the latest snapshot date for comparison
    latest_snapshot_date = df_last_snapshot['SnapshotDate'].max().date()

    # Determine 'is_active' based on the latest snapshot date
    df_final = pd.merge(df_unique, df_last_snapshot, on='FlightCode', how='left', suffixes=('', '_last'))
    df_final['is_active'] = df_final['SnapshotDate_last'].apply(
        lambda x: 1 if pd.notna(x) and x.date() >= latest_snapshot_date else 0
    )

    # Select the relevant columns: 'FlightCode', 'DepartureDate', 'Origin', 'Destination', 'AirlineCode', 'is_active'
    df_result = df_final[['FlightCode', 'DepartureDate', 'Origin', 'Destination', 'AirlineCode', 'is_active']]

    # Insert the DataFrame into the 'flights' table in PostgreSQL
    df_result.to_sql('flights', con=engine, if_exists='replace', index=False)
    print("Data inserted into 'flights' table successfully.")

    return df_result  # Return the result DataFrame for testing

distinct_flight_data()