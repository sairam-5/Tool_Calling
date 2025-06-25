from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date 
from .Tools import flight_data

app = FastAPI(
    title="Indian Flight Mock API",
    description="Provides simulated flight availability between major Indian cities."
    
)

class FlightCheckRequest(BaseModel):
    """
    Request schema for checking flight availability.
    """
    origin: str
    destination: str
    travel_date: date

@app.post("/flights/check_availability")
async def check_flight_availability(request: FlightCheckRequest):
    """
    Handles POST requests to check mock flight availability.
    Returns the availability status based on internal simulated data.
    """
    origin_upper = request.origin.upper()
    destination_upper = request.destination.upper()
    travel_date = request.travel_date

    route_key = (origin_upper, destination_upper)

    availability_status = False
    details_message = "Flight route not recognized or no availability in mock data."

    if route_key in flight_data.MOCK_FLIGHT_DATA:
        if travel_date in flight_data.MOCK_FLIGHT_DATA[route_key]:
            availability_status = flight_data.MOCK_FLIGHT_DATA[route_key][travel_date]
            details_message = f"Flight status for {origin_upper} to {destination_upper} on {travel_date.isoformat()} based on mock data."
            if not availability_status:
                details_message = f"Flight from {origin_upper} to {destination_upper} on {travel_date.isoformat()} is marked as UNAVAILABLE in mock data."
        else:
            details_message = f"Availability for {travel_date.isoformat()} not specifically defined for this route. Assuming unavailable."
    else:
        details_message = f"Route '{request.origin}' to '{request.destination}' not found in mock Indian routes."

    return {
        "origin": request.origin,
        "destination": request.destination,
        "travel_date": travel_date.isoformat(),
        "is_available": availability_status,
        "details": details_message
    }
