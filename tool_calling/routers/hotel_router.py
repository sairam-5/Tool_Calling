from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List

from Tools.hotel_data import HOTEL_DATA

app = FastAPI(
    title="Hotel Tool API",
)

class HotelOption(BaseModel):
    hotel_name: str
    price: int

# Includes only essential search parameters and available hotels.
class HotelSearchResponse(BaseModel):
    region: str
    check_in_date: str
    check_out_date: str
    available_hotels: List[HotelOption]

@app.get(
    "/hotels/search",
    response_model=HotelSearchResponse,
)
async def search_hotels(
    region: str = Query(...),
    check_in_date: str = Query(...),
    check_out_date: str = Query(...)
) -> HotelSearchResponse:
    """
    Retrieves static hotel name and price information for a specified region and dates.
    """
    region_title = region.title()

    # Look up static hotel options based on the provided region.
    hotel_options_raw = HOTEL_DATA.get(region_title)

    if not hotel_options_raw:
        # If no hotels are found for the given region, return an empty list.
        return HotelSearchResponse(
            region=region_title,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            available_hotels=[]
        )
    
    # If hotels are found, convert the raw dictionaries into Pydantic HotelOption models.
    available_hotels = [HotelOption(**h) for h in hotel_options_raw]
    
    return HotelSearchResponse(
        region=region_title,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        available_hotels=available_hotels
    )

