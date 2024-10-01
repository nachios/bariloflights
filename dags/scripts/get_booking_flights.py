import requests
import pandas as pd
from datetime import datetime, date
import os

# API Request
base_url = os.getenv('RAPIDAPI_BASE_URL')
headers = {"x-rapidapi-key": os.getenv('RAPIDAPI_KEY'), "x-rapidapi-host": os.getenv('RAPIDAPI_HOST')}

# Initialize flight_data list to store all flights
flight_data = []

def get_booking_flights(departureDate, returnDate):
    """
    Args:
        departureDate (str): Departure date in 'yyyy-MM-dd' format.
        returnDate (str): Return date in 'yyyy-MM-dd' format.
    We are using return journeys to get more information of different flights in a single request,
    because we are able to get for each flight the price of it and not the combination of the two.
    """

    # Validate the departureDate and returnDate format and range
    departure_min = datetime.strptime("2025-02-01", "%Y-%m-%d")
    departure_max = datetime.strptime("2025-02-05", "%Y-%m-%d")
    return_min = datetime.strptime("2025-02-12", "%Y-%m-%d")
    return_max = datetime.strptime("2025-02-16", "%Y-%m-%d")

    # Convert input to datetime objects
    departure_date_dt = datetime.strptime(departureDate, "%Y-%m-%d")
    return_date_dt = datetime.strptime(returnDate, "%Y-%m-%d")

    # Add assertions for date ranges
    assert (
        departure_min <= departure_date_dt <= departure_max
    ), f"Departure date {departureDate} is out of range! It must be between 2025-02-01 and 2025-02-05."

    assert (
        return_min <= return_date_dt <= return_max
    ), f"Return date {returnDate} is out of range! It must be between 2025-02-12 and 2025-02-16."

    # Pagination variables
    current_page = 1
    total_pages = 1

    # Querystring with dynamic departureDate and returnDate
    querystring = {
        "fromId": "BRC",
        "toId": "AEP",
        "departureDate": departureDate,
        "returnDate": returnDate,
        "cabinClass": "ECONOMY",
        "adults": "2",
        "nonstopFlightsOnly": "true",
        "numberOfStops": "nonstop_flights",
        "airlines": "FO,AR,WJ",
    }

    while current_page <= total_pages:
        # Update querystring with the current page
        querystring["page"] = current_page

        # Fetch response
        response = requests.get(base_url, headers=headers, params=querystring)
        data = response.json()

        # Extract flights info from response
        flights = data.get("data", {}).get("flights", [])

        if not flights:
            print(f"No flight results found on page {current_page}.")
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

        # Check for pagination
        meta = data.get("meta", {})
        total_pages = meta.get("totalPage", 1)
        current_page += 1

    # Create DataFrame
    df = pd.DataFrame(flight_data)

    # Save to Parquet
    df.to_parquet(f"{date.today()}.data.parquet", index=False)

    print(f"Data successfully saved to {date.today()}.data.parquet.")

def batch_get_booking_flights():
    # Define the pairs of departure and return dates
    date_pairs = [
        ("2025-02-01", "2025-02-12"),
        ("2025-02-02", "2025-02-13"),
        ("2025-02-03", "2025-02-14"),
        ("2025-02-04", "2025-02-15"),
        ("2025-02-05", "2025-02-16"),
    ]

    for departureDate, returnDate in date_pairs:
        print(f"Fetching flights for departure on {departureDate} and return on {returnDate}...")
        get_booking_flights(departureDate, returnDate)

# Run the batch function
if __name__ == "__main__":
    batch_get_booking_flights()
