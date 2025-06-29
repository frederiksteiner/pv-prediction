import datetime as dt
import unittest
from unittest import mock

import pandas as pd
from pydantic import ValidationError

from pv_prediction.data.meteomatics.api_client import APIClient
from pv_prediction.data.meteomatics.api_client import MeteomaticsConfig
from pv_prediction.data.meteomatics.schemata import WeatherResponse

# pylint: disable=protected-access


class TestAPIClient(unittest.TestCase):
    def setUp(self) -> None:
        self.client = APIClient(
            MeteomaticsConfig(
                username="user",
                password="password",
            )
        )
        self.response = {
            "version": "3.0",
            "user": "-_steiner_frederik",
            "dateGenerated": "2025-06-29T07:53:41Z",
            "status": "OK",
            "data": [
                {
                    "parameter": "t_2m:C",
                    "coordinates": [
                        {
                            "lat": 30.556,
                            "lon": 5.693083,
                            "dates": [
                                {"date": "2025-06-28T22:00:00Z", "value": 20.1},
                                {"date": "2025-06-29T00:00:00Z", "value": 18.2},
                            ],
                        }
                    ],
                },
                {
                    "parameter": "sunrise:sql",
                    "coordinates": [
                        {
                            "lat": 30.556,
                            "lon": 5.693083,
                            "dates": [
                                {
                                    "date": "2025-06-28T22:00:00Z",
                                    "value": "2025-06-28T03:40:00Z",
                                },
                                {
                                    "date": "2025-06-29T00:00:00Z",
                                    "value": "2025-06-28T03:40:00Z",
                                },
                            ],
                        }
                    ],
                },
            ],
        }

    @mock.patch("pv_prediction.data.meteomatics.api_client.APIClient._parse_response")
    @mock.patch("pv_prediction.data.meteomatics.api_client.APIClient._get_weather_data")
    def test_get_weather_data_for_date(
        self, mock_get_weather_data: mock.MagicMock, mock_parse_response: mock.MagicMock
    ) -> None:
        result = self.client.get_weather_data_for_date(
            dt.date(2025, 12, 12), ["param1", "param2"], [(1.0, 2.0)]
        )
        mock_get_weather_data.assert_called_once_with(
            "2025-12-12T00:00:00+01:00--2025-12-13T00:00:00+01:00:PT1H",
            ["param1", "param2"],
            [(1.0, 2.0)],
        )
        mock_parse_response.assert_called_once_with(mock_get_weather_data.return_value)
        self.assertEqual(result, mock_parse_response.return_value)

    @mock.patch("pv_prediction.data.meteomatics.api_client.requests.get")
    def test_get_weather_data(self, mock_get: mock.MagicMock) -> None:
        mock_response: mock.MagicMock = mock_get.return_value
        mock_response.json.return_value = self.response
        result = self.client._get_weather_data(
            "date_range", ["param1", "param2"], [(1.0, 1.0), (2.0, 2.0)]
        )
        # pyre-ignore[6]
        self.assertEqual(WeatherResponse(**self.response), result)
        mock_response.raise_for_status.assert_called_once()
        mock_get.assert_called_once_with(
            "https://api.meteomatics.com/date_range/param1,param2/1.0,1.0,2.0,2.0/json",
            auth=("user", "password"),
            timeout=10,
        )

    @mock.patch("pv_prediction.data.meteomatics.api_client.requests.get")
    def test_get_weather_data_wrong_response(self, mock_get: mock.MagicMock) -> None:
        mock_response: mock.MagicMock = mock_get.return_value
        with self.assertRaises(ValidationError):
            self.client._get_weather_data(
                "date_range", ["param1", "param2"], [(1.0, 1.0), (2.0, 2.0)]
            )
        mock_response.raise_for_status.assert_called_once()
        mock_get.assert_called_once_with(
            "https://api.meteomatics.com/date_range/param1,param2/1.0,1.0,2.0,2.0/json",
            auth=("user", "password"),
            timeout=10,
        )

    @mock.patch("pv_prediction.data.meteomatics.api_client.requests.get")
    def test_get_weather_data_response_format(self, mock_get: mock.MagicMock) -> None:
        mock_response: mock.MagicMock = mock_get.return_value
        with self.assertRaises(NotImplementedError):
            self.client._get_weather_data(
                "date_range",
                ["param1", "param2"],
                [(1.0, 1.0), (2.0, 2.0)],
                response_format="csv",
            )
        mock_response.raise_for_status.assert_called_once()
        mock_get.assert_called_once_with(
            "https://api.meteomatics.com/date_range/param1,param2/1.0,1.0,2.0,2.0/csv",
            auth=("user", "password"),
            timeout=10,
        )

    def test_parse_response(self) -> None:
        # pyre-ignore[6]
        result = APIClient._parse_response(WeatherResponse(**self.response))
        pd.testing.assert_frame_equal(
            pd.DataFrame(
                {
                    "lat": 2 * [30.556],
                    "lon": 2 * [5.693083],
                    "date": [
                        dt.datetime(2025, 6, 28, 22, 0, 0, 0, tzinfo=dt.timezone.utc),
                        dt.datetime(2025, 6, 29, 0, 0, 0, 0, tzinfo=dt.timezone.utc),
                    ],
                    "t_2m:C": [20.1, 18.2],
                    "sunrise:sql": [
                        dt.datetime(2025, 6, 28, 3, 40, 0, 0, tzinfo=dt.timezone.utc),
                        dt.datetime(2025, 6, 28, 3, 40, 0, 0, tzinfo=dt.timezone.utc),
                    ],
                }
            ),
            result,
            check_dtype=False,
        )
