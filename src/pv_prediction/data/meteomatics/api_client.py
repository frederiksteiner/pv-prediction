import dataclasses
import datetime as dt
import os

import pytz
import requests

from pv_prediction.data.meteomatics.schemata import WeatherResponse


@dataclasses.dataclass
class MeteomaticsConfig:
    """Meteomatics related configs."""

    username: str = dataclasses.field(
        default_factory=lambda: os.getenv("METEO_USERNAME", "")
    )
    password: str = dataclasses.field(
        default_factory=lambda: os.getenv("METEO_PASSWORD", "")
    )
    base_url: str = dataclasses.field(
        default_factory=lambda: os.getenv("BASE_URL", "https://api.meteomatics.com")
    )
    timezone: str = dataclasses.field(
        default_factory=lambda: os.getenv("TIMEZONE", "Europe/Zurich")
    )


class APIClient:
    """Meteomatics API Client to fetch weather data."""

    def __init__(self, config: MeteomaticsConfig | None = None) -> None:
        """Initialize the Meteomatics API client."""
        self.config: MeteomaticsConfig = (
            config if config is not None else MeteomaticsConfig()
        )
        self.base_url: str = self.config.base_url

    def _build_url(
        self, valid_datetime: str, parameters: str, locations: str, response_format: str
    ) -> str:
        """Build the full URL for the API query."""
        return f"{self.base_url}/{valid_datetime}/{parameters}/{locations}/{response_format}"

    def get_weather_data_for_date(
        self,
        date: dt.date,
        parameters: list[str],
        locations: list[tuple[float, float]],
    ) -> WeatherResponse:
        """Fetch weather data from the Meteomatics API for specific date.

        Args:
            date_range (datetime.date): Two isoformat datetime strings connected with "--" .
            parameters (list[str]): List of weather parameters to fetch.
            locations (list of tuple): List of location tuples (latitude, longitude).
            response_format (str, optional): Desired format for the response (default: "json").

        Returns:
            Parsed weather data as pandas DataFrame.
        """
        timezone = pytz.timezone(self.config.timezone)
        datetime = dt.datetime.combine(date, dt.datetime.min.time()).astimezone(
            timezone
        )
        following_day = datetime + dt.timedelta(days=1)
        iso_date_string = (
            datetime.isoformat() + "--" + following_day.isoformat() + ":PT1H"
        )
        return self._get_weather_data(
            iso_date_string,
            parameters,
            locations,
        )

    def _get_weather_data(
        self,
        date_range: str,
        parameters: list[str],
        locations: list[tuple[float, float]],
        response_format: str = "json",
    ) -> WeatherResponse:
        formatted_parameters = ",".join(parameters)
        formatted_locations = ",".join([f"{lat},{lon}" for lat, lon in locations])

        url = self._build_url(
            date_range, formatted_parameters, formatted_locations, response_format
        )
        response = requests.get(
            url, auth=(self.config.username, self.config.password), timeout=10
        )
        response.raise_for_status()
        if response_format != "json":
            raise NotImplementedError(
                f"The response format {response_format} has not been implemented yet"
            )
        return WeatherResponse(**response.json())
