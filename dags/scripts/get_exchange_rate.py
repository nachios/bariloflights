import currencyapicom
import pandas as pd
from sqlalchemy import create_engine
import os

def get_exchange_rate():
    # Initialize the currency API client
    client = currencyapicom.Client(os.getenv('CURRENCYAPI_TOKEN'))
    
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

    # Define Redshift connection parameters using environment variables
    DATABASE_URL = (
        f"redshift+psycopg2://{os.getenv('REDSHIFT_USER')}:{os.getenv('REDSHIFT_PASSWORD')}"
        f"@{os.getenv('REDSHIFT_HOST')}:{os.getenv('REDSHIFT_PORT')}/{os.getenv('REDSHIFT_DB')}"
    )

    # Create SQLAlchemy engine
    engine = create_engine(DATABASE_URL)

    # Insert data into Redshift database
    try:
        df.to_sql('usd_daily_exchange_rate', con=engine, if_exists='append', index=False)
        print("Data successfully inserted into Redshift database.")
    except Exception as e:
        print(f"Error inserting data into Redshift: {e}")

# Call the function
get_exchange_rate()
