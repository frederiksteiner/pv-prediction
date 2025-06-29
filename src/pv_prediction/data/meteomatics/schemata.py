from datetime import datetime

from pydantic import BaseModel


class DateValue(BaseModel):
    """Measurement date and its value."""

    date: datetime
    value: float | int | datetime


class Coordinate(BaseModel):
    """Coordinates and its measurements."""

    lat: float
    lon: float
    dates: list[DateValue]


class DataParameter(BaseModel):
    """Parameters and its coordinates."""

    parameter: str
    coordinates: list[Coordinate]


class WeatherResponse(BaseModel):
    """Response of weather API."""

    version: str
    user: str
    dateGenerated: datetime
    status: str
    data: list[DataParameter]
