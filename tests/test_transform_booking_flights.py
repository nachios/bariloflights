import pandas as pd
from unittest.mock import patch, MagicMock
from dags.scripts.transform_booking_flights import transform_flight_responses

# Sample data to mock the Parquet file output
sample_data = {
    "DepartureDate": ["2024-10-01 08:00:00"],
    "ReturnDate": ["2024-10-01 10:30:00"],
    "FlightCode": ["FO123"],
    "AirlineCode": ["FO"],
    "Origin": ["BRC"],
    "Destination": ["AEP"],
    "Price": [10000],
    "VAT": [2000],
    "CurrencyCode": ["USD"],
    "SnapshotDate": ["2024-10-01 08:00:00"]
}
df = pd.DataFrame(sample_data)

# Expected output after transformation
expected_data = pd.DataFrame({
    "departure_date": pd.to_datetime(["2024-10-01 08:00:00"]),
    "arrival_date": pd.to_datetime(["2024-10-01 10:30:00"]),
    "flight_code": ["FO123"],
    "airline_code": ["FO"],
    "origin": ["BRC"],
    "destination": ["AEP"],
    "price": 100.0,
    "vat": 20.0,
    "currency_code": ["USD"],
    "snapshot_date": pd.to_datetime(["2024-10-01 08:00:00"]),
    "flight_duration": 2.5,
    "total_amount": 120.0
})


@patch('dags.scripts.transform_booking_flights.create_engine')
@patch('pandas.read_parquet', return_value=df)
@patch('airflow.hooks.base.BaseHook.get_connection')
@patch('os.path.exists', return_value=True)
def test_transform_flight_responses(mock_exists, mock_get_connection, mock_read_parquet, mock_create_engine):
    # Mocking the connection object returned by BaseHook.get_connection
    mock_connection = MagicMock()
    mock_connection.login = 'user'
    mock_connection.password = 'password'
    mock_connection.host = 'localhost'
    mock_connection.port = '5439'
    mock_connection.schema = 'your_schema'
    mock_get_connection.return_value = mock_connection

    # Mocking the engine's connect method to avoid actual database connection
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_engine.connect.return_value = MagicMock()  # Mocking the connection object

    # Mock the to_sql method to track calls
    mock_connection = mock_engine.connect.return_value
    mock_connection.to_sql = MagicMock()

    # Call the function
    actual_result = transform_flight_responses()

    assert actual_result.equals(expected_data), "The output data does not match the expected data. Please check values and data types."
