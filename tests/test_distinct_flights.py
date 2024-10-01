import pandas as pd
import pytest
from unittest import mock
from dags.scripts.distinct_flights import distinct_flight_data

# Sample DataFrame to simulate the database response
sample_data = pd.DataFrame({
    'FlightCode': ['FO123', 'FO242', 'AA213'],
    'DepartureDate': ['2024-09-28', '2024-09-28', '2024-09-28'],
    'Origin': ['BRC', 'BRC', 'BRC'],
    'Destination': ['AEP', 'AEP', 'AEP'],
    'AirlineCode': ['FO', 'FO', 'AA'],
    'SnapshotDate': ['2024-09-28', '2024-09-25', '2024-09-28']  # This should be converted to datetime in the main function
})

# Mock function to return the sample data
def mock_read_sql_table(*args, **kwargs):
    return sample_data

# Test function to verify the is_active logic
@mock.patch('pandas.read_sql_table', side_effect=mock_read_sql_table)
def test_is_active(mock_read):
    # Call the distinct_flight_data function
    result_df = distinct_flight_data()

    # The latest snapshot date among the sample data is '2024-09-28'
    expected_is_active = [1, 0, 1]
    
    # Check the is_active column
    assert result_df['is_active'].tolist() == expected_is_active, "is_active values do not match expected output."

# Run the tests
if __name__ == "__main__":
    pytest.main()
