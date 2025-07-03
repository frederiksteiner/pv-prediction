import re
from datetime import datetime

from pydantic import BaseModel


class FlattenedWeather(BaseModel):
    """Weather Response but flattened with lat, lon and date as must have keys."""

    lat: float
    lon: float
    date: datetime
    wind_speed_10m: float | None = None
    wind_dir_10m: float | None = None
    wind_gusts_10m_1h: float | None = None
    wind_gusts_10m_24h: float | None = None
    t_2m: float | None = None
    t_max_2m_24h: float | None = None
    t_min_2m_24h: float | None = None
    msl_pressure: float | None = None
    precip_1h: float | None = None
    precip_24h: float | None = None
    weather_symbol_1h: int | None = None
    weather_symbol_24h: int | None = None
    uv: int | None = None
    sunrise: datetime | None = None
    sunset: datetime | None = None


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

    def flatten_response(self) -> list[FlattenedWeather]:
        """Flattens weather response."""
        flattened_dict = {}
        for param in self.data:
            parameter = param.parameter
            for coord in param.coordinates:
                for date_value in coord.dates:
                    key = f"{coord.lat}-{coord.lon}-{date_value.date}"
                    if key not in flattened_dict:
                        flattened_dict[key] = {
                            "lat": coord.lat,
                            "lon": coord.lon,
                            "date": date_value.date,
                        }
                    changed_param, transformed_value = self._preprocess_params(
                        parameter, date_value.value
                    )
                    flattened_dict[key] = flattened_dict[key] | {
                        changed_param: transformed_value
                    }
        return [FlattenedWeather(**value) for value in flattened_dict.values()]

    @classmethod
    def _preprocess_params(
        cls, parameter: str, value: float | int | datetime
    ) -> tuple[str, float | int | datetime]:
        new_param, unit = cls._split_units(parameter)
        if isinstance(value, datetime):
            return new_param, value
        if parameter.startswith("t"):
            return new_param, cls._preprocess_temperature(value, unit)
        if parameter.startswith("wind_gusts"):
            return new_param, cls._preprocess_wind_speed(value, unit)
        if parameter.startswith("msl_pressure"):
            return new_param, cls._preprocess_pressure(value, unit)
        return new_param, value

    @staticmethod
    def _split_units(parameter: str) -> tuple[str, str]:
        splits = parameter.split(":")
        if len(splits) == 1:
            return splits[0], ""
        only_letters_unit = re.sub("[^a-zA-Z]", "", splits[1])
        return splits[0], only_letters_unit

    @staticmethod
    def _preprocess_wind_speed(value: int | float, unit: str) -> float | int:
        if unit == "kmh":
            return value / 3.6
        if unit == "kn":
            return value / 1.94384001
        if unit == "bft":
            return value * 0.836
        return value

    @staticmethod
    def _preprocess_temperature(value: int | float, unit: str) -> float | int:
        if unit == "F":
            return (value - 32) / 1.8
        if unit == "K":
            return value - 273.15
        return value

    @staticmethod
    def _preprocess_pressure(value: int | float, unit: str) -> float | int:
        if unit == "Pa":
            return value / 100
        return value
