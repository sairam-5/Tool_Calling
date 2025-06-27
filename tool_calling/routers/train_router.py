from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List

from Tools.train_data import TRAIN_ROUTES

app = FastAPI(
    title="Train Tool API",
)

class TrainOption(BaseModel):
    train_name: str
    price: int

class TrainSearchResponse(BaseModel):
    origin_region: str
    destination_region: str
    date: str
    available_trains: List[TrainOption]

@app.get(
    "/trains/search",
    response_model=TrainSearchResponse,
)
async def search_trains(
    origin_region: str = Query(...),
    destination_region: str = Query(...),
    date: str = Query(...)
) -> TrainSearchResponse:
    """
    Retrieves static train name and price information between specified regions and date.
    """
    origin_region_title = origin_region.title()
    destination_region_title = destination_region.title()

    # Look up static train options based on the provided broad regions.
    train_options_raw = TRAIN_ROUTES.get((origin_region_title, destination_region_title))

    if not train_options_raw:
        # If no specific route is found, return an empty list of trains.
        return TrainSearchResponse(
            origin_region=origin_region_title,
            destination_region=destination_region_title,
            date=date,
            available_trains=[]
        )
    
    available_trains = [TrainOption(**t) for t in train_options_raw]
    
    return TrainSearchResponse(
        origin_region=origin_region_title,
        destination_region=destination_region_title,
        date=date,
        available_trains=available_trains
    )
