import pandas as pd
from unittest.mock import patch, MagicMock
from dags.scripts.distinct_flights import distinct_flight_data

# Sample data to mock the SQL table output
sample_data = pd.DataFrame({
    'flight_code': ['FO123', 'FO242', 'AA213'],
    'departure_date': ['2024-09-28 00:00:00', '2024-09-28 00:00:00', '2024-09-28 00:00:00'],
    'origin': ['BRC', 'BRC', 'BRC'],
    'destination': ['AEP', 'AEP', 'AEP'],
    'airline_code': ['FO', 'FO', 'AA'],
    'snapshot_date': ['2024-09-28 00:00:00', '2024-09-25 00:00:00', '2024-09-28 00:00:00']
})

# Expected output after processing
expected_data = pd.DataFrame({
    'flight_code': ['FO123', 'FO242', 'AA213'],
    'departure_date': pd.to_datetime(['2024-09-28', '2024-09-28', '2024-09-28']),
    'origin': ['BRC', 'BRC', 'BRC'],
    'destination': ['AEP', 'AEP', 'AEP'],
    'airline_code': ['FO', 'FO', 'AA'],
    'is_active': [1, 0, 1]
})


@patch('dags.scripts.distinct_flights.create_engine')
@patch('pandas.read_sql_table', return_value=sample_data)
@patch('airflow.hooks.base.BaseHook.get_connection')
def test_distinct_flight_data(mock_get_connection, mock_read_sql_table, mock_create_engine):
    # Mocking the connection object returned by BaseHook.get_connection
    mock_connection = MagicMock()
    mock_connection.login = 'user'
    mock_connection.password = 'password'
    mock_connection.host = 'localhost'
    mock_connection.port = '5439'
    mock_connection.schema = 'schema'
    mock_get_connection.return_value = mock_connection

    # Mocking the engine's connect method to avoid actual database connection
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_engine.connect.return_value = MagicMock()  # Mocking the connection object

    # Call the function
    actual_result = distinct_flight_data()

    # Assertions
    assert actual_result.equals(expected_data), "The output data does not match the expected data."
