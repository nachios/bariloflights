import requests
import pandas as pd
from datetime import datetime
from airflow.models import Variable
import pytz

# API Request
base_url = Variable.get('RAPIDAPI_BASE_URL')
headers = {
    "x-rapidapi-key": Variable.get('RAPIDAPI_KEY'),
    "x-rapidapi-host": Variable.get('RAPIDAPI_HOST')
}

# Initialize flight_data list to store all flights
flight_data = []

utc_min_3 = pytz.timezone('America/Buenos_Aires')
current_date = datetime.now(utc_min_3)


def get_booking_flights(departureDate, route):
    """
    Args:
        departureDate (str): Departure date in 'yyyy-MM-dd' format.
        route (str): The route for the flight search (BRC to AEP or AEP to BRC).
    Fetch one-way flights based on the specified route and departure date.
    """

    # Validate the departureDate format and range
    departure_min = datetime.strptime("2025-02-01", "%Y-%m-%d")
    departure_max = datetime.strptime("2025-02-05", "%Y-%m-%d")
    return_min = datetime.strptime("2025-02-12", "%Y-%m-%d")
    return_max = datetime.strptime("2025-02-16", "%Y-%m-%d")

    # Convert input to datetime object
    departure_date_dt = datetime.strptime(departureDate, "%Y-%m-%d")

    # Add assertions for date range
    assert (
        (route == "BRC to AEP" and departure_min <= departure_date_dt <= departure_max) or
        (route == "AEP to BRC" and return_min <= departure_date_dt <= return_max)
    ), f"Departure date {departureDate} is out of range for route {route}!"

    # Initialize pagination variables
    current_page = 1
    total_pages = 1

    # Set query parameters based on the route
    while current_page <= total_pages:
        if route == "BRC to AEP":
            querystring = {
                "fromId": "BRC",
                "toId": "AEP",
                "departureDate": departureDate,
                "cabinClass": "ECONOMY",
                "numberOfStops": "nonstop_flights",
                "adults": "1",
                "airlines": "FO,AR,WJ",
                "page": current_page
            }
        else:  # AEP to BRC
            querystring = {
                "fromId": "AEP",
                "toId": "BRC",
                "departureDate": departureDate,
                "cabinClass": "ECONOMY",
                "numberOfStops": "nonstop_flights",
                "adults": "1",
                "airlines": "FO,AR,WJ",
                "page": current_page
            }

        # Fetch response
        response = requests.get(base_url, headers=headers, params=querystring)
        data = response.json()

        # Extract flights info from response
        flights = data.get("data", {}).get("flights", [])
        meta = data.get("meta", {})
        # total_records = meta.get("totalRecords", 0)
        total_pages = meta.get("totalPage", 1)

        if not flights:
            print(f"No flight results found for departure on {departureDate} for route {route}. "
                  "Please check the API request limits.")
            break

        # Process flights data to get fields for each item
        for flight in flights:
            for bound in flight.get("bounds", []):
                for segment in bound.get("segments", []):
                    flight_info = {
                        "Origin": segment.get("origin", {}).get("code", ""),
                        "Destination": segment.get("destination", {}).get("code", ""),
                        "AirlineCode": segment.get("marketingCarrier", {}).get("code", ""),
                        "FlightCode": segment.get("flightNumber", ""),
                        "DepartureDate": segment.get("departuredAt", ""),
                        "ReturnDate": segment.get("arrivedAt", ""),
                        "Price": None,
                        "VAT": None,
                        "CurrencyCode": None,
                        "SnapshotDate": datetime.now(),
                    }
                    for traveler_price in flight.get("travelerPrices", []):
                        price_info = traveler_price.get("price", {})
                        flight_info["Price"] = price_info.get("price", {}).get("value", "")
                        flight_info["VAT"] = price_info.get("vat", {}).get("value", "")
                        flight_info["CurrencyCode"] = (
                            price_info.get("price", {}).get("currency", {}).get("code", "")
                        )
                        break

            flight_data.append(flight_info)

        current_page += 1  # Move to the next page

    # Create DataFrame
    df = pd.DataFrame(flight_data)

    # Get filename with current date in UTC-3
    filename = current_date.strftime("%Y-%m-%d")

    # Save to Parquet
    df.to_parquet(f"/opt/airflow/data/{filename}.data.parquet", index=False)

    print(f"Data successfully saved to {filename}.data.parquet.")


def batch_get_booking_flights():
    # Define the pairs of departure dates for both routes
    date_pairs = [
        ("2025-02-01", "BRC to AEP"),
        ("2025-02-02", "BRC to AEP"),
        ("2025-02-03", "BRC to AEP"),
        ("2025-02-04", "BRC to AEP"),
        ("2025-02-05", "BRC to AEP"),
        ("2025-02-12", "AEP to BRC"),
        ("2025-02-13", "AEP to BRC"),
        ("2025-02-14", "AEP to BRC"),
        ("2025-02-15", "AEP to BRC"),
        ("2025-02-16", "AEP to BRC"),
    ]

    for departureDate, route in date_pairs:
        print(f"Fetching flights for departure on {departureDate} for route {route}...")
        get_booking_flights(departureDate, route)
