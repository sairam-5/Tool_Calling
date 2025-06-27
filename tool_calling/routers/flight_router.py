from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List

from Tools.flight_data import FLIGHT_ROUTES

app = FastAPI(
    title="Flight Tool API",
    version="1.0.0",
)

class FlightOption(BaseModel):
    flight_name: str
    price: int

# Pydantic model for the response when searching for flights.
# Includes only essential search parameters and available flights.
class FlightSearchResponse(BaseModel):
    origin_region: str
    destination_region: str
    date: str
    available_flights: List[FlightOption]

@app.get(
    "/flights/search",
    response_model=FlightSearchResponse,
)
async def search_flights(
    origin_region: str = Query(...),
    destination_region: str = Query(...),
    date: str = Query(...)
) -> FlightSearchResponse:
    """
    Retrieves static flight name and price information between specified regions and date.
    """
    # Convert region names to title case for consistent lookup in FLIGHT_ROUTES.
    origin_region_title = origin_region.title()
    destination_region_title = destination_region.title()

    # Look up static flight options based on the provided broad regions.
    flight_options_raw = FLIGHT_ROUTES.get((origin_region_title, destination_region_title))

    if not flight_options_raw:
        # If no specific route is found, returns an empty list of flights.
        return FlightSearchResponse(
            origin_region=origin_region_title,
            destination_region=destination_region_title,
            date=date,
            available_flights=[]
        )
    
    # If flights are found, converts the raw dictionaries into Pydantic FlightOption models.
    available_flights = [FlightOption(**f) for f in flight_options_raw]
    
    return FlightSearchResponse(
        origin_region=origin_region_title,
        destination_region=destination_region_title,
        date=date,
        available_flights=available_flights
    )
