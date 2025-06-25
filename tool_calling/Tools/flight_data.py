from datetime import date, timedelta
import random

# List of major Indian cities used for mock flight routes.
INDIAN_CITIES = [
    "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata",
    "Hyderabad", "Ahmedabad", "Pune", "Jaipur", "Lucknow"
]

# Dictionary to store mock flight availability.
# Keys are (ORIGIN_CITY_UPPER, DESTINATION_CITY_UPPER) tuples.
# Values are dictionaries: {date_object: is_available (boolean)}.
MOCK_FLIGHT_DATA = {}

def generate_mock_flight_availability(num_days_forecast=10):
    """
    Generates simulated flight availability data for routes between Indian cities.
    Availability is randomized, with a higher probability for 'available'.
    """
    today = date.today()
    for i in range(num_days_forecast):
        current_date = today + timedelta(days=i)
        for origin in INDIAN_CITIES:
            for destination in INDIAN_CITIES:
                if origin == destination:
                    continue

                route_key = (origin.upper(), destination.upper())
                if route_key not in MOCK_FLIGHT_DATA:
                    MOCK_FLIGHT_DATA[route_key] = {}

                # Simulate availability (e.g., 80% chance of being available).
                is_available = random.random() < 0.8
                MOCK_FLIGHT_DATA[route_key][current_date] = is_available

# populating MOCK_FLIGHT_DATA for immediate use by the router.
generate_mock_flight_availability()