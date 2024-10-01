import pandas as pd
import datetime
from sqlalchemy import create_engine
import os

def transform_flight_responses():
    # Get the current date for the Parquet file name
    parquet_file = f"{datetime.date.today()}.data.parquet"
    
    # Check if the Parquet file exists
    if not os.path.exists(parquet_file):
        print(f"File {parquet_file} not found. Skipping processing.")
        return
    
    # Read the Parquet file
    print(f"Reading the Parquet file: {parquet_file}")
    df = pd.read_parquet(parquet_file)
    print("Parquet file read successfully.")

    # Convert 'DepartureDate' and 'ReturnDate' to datetime format
    df["DepartureDate"] = pd.to_datetime(df["DepartureDate"])
    df["ReturnDate"] = pd.to_datetime(df["ReturnDate"])  # Keep this line for conversion

    # Rename 'ReturnDate' to 'ArrivalDate'
    df.rename(columns={"ReturnDate": "ArrivalDate"}, inplace=True)

    # Calculate flight duration as the difference between 'ArrivalDate' and 'DepartureDate'
    df["FlightDuration"] = (
        (df["ArrivalDate"] - df["DepartureDate"]).dt.total_seconds() / 3600
    ).round(2)

    # Divide 'Price' and 'VAT' by 100
    df["Price"] = df["Price"] / 100
    df["VAT"] = df["VAT"] / 100
    df["TotalAmount"] = df["Price"] + df["VAT"]

    # Remove duplicates based on flight number, origin, and departure date
    df.drop_duplicates(subset=["FlightCode", "Origin", "DepartureDate"], keep='first', inplace=True)

    print("Data transformation completed.")

    # Define Redshift connection parameters
    DATABASE_URL = (
        f"redshift+psycopg2://{os.getenv('REDSHIFT_USER')}:{os.getenv('REDSHIFT_PASSWORD')}"
        f"@{os.getenv('REDSHIFT_HOST')}:{os.getenv('REDSHIFT_PORT')}/{os.getenv('REDSHIFT_DB')}"
    )

    # Create SQLAlchemy engine
    try:
        engine = create_engine(DATABASE_URL)
        print("Database connection established.")
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return

    # Read existing records from the database
    existing_records_query = """
    SELECT "FlightCode", "Origin", "DepartureDate"
    FROM public.flights_daily_snapshots
    """
    existing_records = pd.read_sql(existing_records_query, con=engine)

    # Merge the DataFrame with existing records to find new entries
    merged_df = df.merge(existing_records, on=["FlightCode", "Origin", "DepartureDate"], how="left", indicator=True)

    # Keep only new records (those that did not exist in the database)
    new_records = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])

    # Insert new data into Redshift database
    if not new_records.empty:
        try:
            new_records.to_sql('flights_daily_snapshots', con=engine, if_exists='append', index=False, method='multi')
            print(f"{len(new_records)} new records successfully inserted into Redshift database.")
        except Exception as e:
            print(f"Error inserting data into Redshift: {e}")
    else:
        print("No new records to insert into Redshift.")

transform_flight_responses()
