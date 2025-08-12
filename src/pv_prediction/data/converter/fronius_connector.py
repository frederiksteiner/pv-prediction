import dataclasses
import datetime as dt
import logging
import os
import pathlib
from typing import Any
from typing import Iterator

import click
import pandas as pd
import requests

LOGGER: logging.Logger = logging.getLogger(__name__)

MAX_QUERY_DAYS: int = 16


@dataclasses.dataclass()
class FroniusConfig:
    """Fronius related configs."""

    ip_adress: str = dataclasses.field(
        default_factory=lambda: os.getenv("FRONIUS_IP", "")
    )


class FroniusConnector:
    """Connector used to extract data from Fronius converter."""

    def __init__(self, config: FroniusConfig | None = None) -> None:
        """Initializes a Fronius connector to extract data of the corresponding API."""
        session = requests.Session()
        session.trust_env = False
        self.session: requests.Session = session
        self.config: FroniusConfig = config if config is not None else FroniusConfig()

    def _query_data(
        self, start_date: dt.date, end_date: dt.date, parameters: list[str]
    ) -> pd.DataFrame:
        date_format = "%-d.%-m.%Y"
        LOGGER.info(
            "Starting extraction from %s to %s",
            start_date.strftime(date_format),
            end_date.strftime(date_format),
        )
        channels = "&".join([f"Channel={p}" for p in parameters])
        url = (
            f"http://{self.config.ip_adress}/solar_api/v1/"
            + "GetArchiveData.cgi?Scope=System&"
            + f"StartDate={start_date.strftime(date_format)}&"
            + f"EndDate={end_date.strftime(date_format)}&"
            + f"{channels}"
        )
        LOGGER.debug("Calling the following url: %s", url)
        response = self.session.get(url)
        return self._transform_response(response, parameters)

    @classmethod
    def _iterate_over_body(
        cls, json_data: dict[str, Any], parameters: list[str]
    ) -> pd.DataFrame:
        series_list = []
        for k, v in json_data.items():
            if isinstance(v, dict):
                for series in cls._series_of_parameters(v, parameters.copy()):
                    series.index = pd.to_datetime(
                        json_data[k]["Start"]
                    ) + pd.to_timedelta(series.index.astype("int"), unit="sec")
                    series_list += [series]
        return pd.concat(series_list, axis=1)[parameters]

    @classmethod
    def _series_of_parameters(
        cls, json_data: dict[str, Any], parameters: list[str]
    ) -> Iterator[pd.Series]:
        if isinstance(json_data, dict):
            for k, v in json_data.items():
                if k in parameters:
                    parameters.remove(k)
                    series = pd.Series(v["Values"])
                    series.name = k
                    yield series
                if len(parameters) == 0:
                    break
                yield from (s for s in cls._series_of_parameters(v, parameters))

    @classmethod
    def _transform_response(
        cls, response: requests.Response, parameters: list[str]
    ) -> pd.DataFrame:
        response.raise_for_status()
        json_data = response.json()
        return cls._iterate_over_body(json_data["Body"]["Data"], parameters)

    def _get_data(
        self, start_date: dt.date, end_date: dt.date, parameters: list[str]
    ) -> pd.DataFrame:
        delta = dt.timedelta(days=MAX_QUERY_DAYS)
        if not (end_date - start_date).days > MAX_QUERY_DAYS:
            queried = self._query_data(start_date, end_date, parameters)
            return pd.concat([queried])
        LOGGER.info(
            "Date difference exceeded the maximum amout of querieble data of %i days. Continuing with batchwise extraction.",
            MAX_QUERY_DAYS,
        )
        query_starts = [
            date.date()
            for date in pd.date_range(start_date, end_date - delta, freq=delta)
        ]
        query_list = []
        for start in query_starts:
            queried = self._query_data(
                start, start + dt.timedelta(MAX_QUERY_DAYS - 1), parameters
            )
            if queried is not None:
                query_list += [queried]

        return pd.concat(query_list)

    def extract_data(
        self,
        start_date: dt.date,
        end_date: dt.date,
        file_path: pathlib.Path,
        parameters: list[str],
    ) -> None:
        """Extracts energy production data from a fronius converter.

        Args:
            start_date (dt.date): The data from when to start querying the data.
            end_data (dt.date): The data until when to query the data.
            file_path (pathlib.Path): Path to save pandas Dataframe to.
            parameters (list[str]): List of parameters to query for. For more information
                check out the documentation of the api here:
                https://www.fronius.com/~/downloads/Solar%20Energy/Operating%20Instructions/42,0410,2012.pdf

        Returns:
            None
        """
        api_df = self._get_data(start_date, end_date, parameters)
        api_df.to_parquet(file_path)


@click.command()
@click.option(
    "--start-date",
    required=True,
    type=click.DateTime(),
    help="Extract date from this date until --end-date",
)
@click.option(
    "--end-date",
    required=True,
    type=click.DateTime(),
    help="Extract data from --start-date until this date",
)
@click.option(
    "--output-file",
    default=pathlib.Path("data/data.parquet"),
    type=click.Path(
        exists=False, dir_okay=False, writable=True, path_type=pathlib.Path
    ),
    help="Output parquet data file",
)
@click.option(
    "--parameters",
    "-p",
    multiple=True,
    default=[
        "EnergyReal_WAC_Sum_Produced",
        "EnergyReal_WAC_Minus_Absolute",
        "EnergyReal_WAC_Plus_Absolute",
    ],
    type=click.STRING,
    help="Parameters to query for",
)
def cli(
    start_date: dt.datetime,
    end_date: dt.datetime,
    output_file: pathlib.Path,
    parameters: tuple[str, ...],
) -> None:
    """Extracts data from a Fronius converter."""
    FroniusConnector().extract_data(start_date, end_date, output_file, list(parameters))
