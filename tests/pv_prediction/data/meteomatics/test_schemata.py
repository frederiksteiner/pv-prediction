import unittest
from datetime import datetime

from pv_prediction.data.meteomatics.schemata import FlattenedWeather
from pv_prediction.data.meteomatics.schemata import WeatherResponse

# pylint: disable=protected-access


class TestWeatherResponse(unittest.TestCase):
    def test_flatte_response(self) -> None:
        response = {
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
                    "parameter": "uv:idx",
                    "coordinates": [
                        {
                            "lat": 30.556,
                            "lon": 5.693083,
                            "dates": [
                                {
                                    "date": "2025-06-28T22:00:00Z",
                                    "value": 1,
                                },
                                {
                                    "date": "2025-06-29T00:00:00Z",
                                    "value": 2,
                                },
                            ],
                        }
                    ],
                },
            ],
        }

        response = WeatherResponse(**response)  # pyre-ignore[6]
        result = response.flatten_response()
        self.assertEqual(
            [
                FlattenedWeather(
                    lat=30.556,
                    lon=5.693083,
                    date="2025-06-28T22:00:00Z",  # pyre-ignore[6]
                    t_2m=20.1,
                    uv=1,
                ),
                FlattenedWeather(
                    lat=30.556,
                    lon=5.693083,
                    date="2025-06-29T00:00:00Z",  # pyre-ignore[6]
                    t_2m=18.2,
                    uv=2,
                ),
            ],
            result,
        )

    def test_preprocess_params_temperature(self) -> None:
        self.assertEqual(("t_2m", 1), WeatherResponse._preprocess_params("t_2m:C", 1))
        self.assertEqual(("t_2m", 1), WeatherResponse._preprocess_params("t_2m", 1))
        self.assertEqual(
            ("t_2m", -272.15), WeatherResponse._preprocess_params("t_2m:K", 1)
        )
        self.assertEqual(("t_2m", 0), WeatherResponse._preprocess_params("t_2m:F", 32))

    def test_preprocess_params_pressure(self) -> None:
        self.assertEqual(
            ("msl_pressure", 1),
            WeatherResponse._preprocess_params("msl_pressure:hPa", 1),
        )
        self.assertEqual(
            ("msl_pressure", 1), WeatherResponse._preprocess_params("msl_pressure", 1)
        )
        self.assertEqual(
            ("msl_pressure", 0.01),
            WeatherResponse._preprocess_params("msl_pressure:Pa", 1),
        )

    def test_preprocess_params_wind(self) -> None:
        self.assertEqual(
            ("wind_gusts", 1),
            WeatherResponse._preprocess_params("wind_gusts:km/h", 3.6),
        )
        self.assertEqual(
            ("wind_gusts", 1), WeatherResponse._preprocess_params("wind_gusts:ms", 1)
        )
        self.assertEqual(
            ("wind_gusts", 1), WeatherResponse._preprocess_params("wind_gusts:m/s", 1)
        )
        self.assertEqual(
            ("wind_gusts", 1), WeatherResponse._preprocess_params("wind_gusts", 1)
        )
        self.assertEqual(
            ("wind_gusts", 0.836),
            WeatherResponse._preprocess_params("wind_gusts:bft", 1),
        )
        self.assertEqual(
            ("wind_gusts", 0.5144456307389208),
            WeatherResponse._preprocess_params("wind_gusts:kn", 1),
        )

    def test_preprocess_params_other(self) -> None:
        self.assertEqual(("asdf", 1), WeatherResponse._preprocess_params("asdf:h", 1))
        dtm = datetime(2025, 12, 10, 10, 10, 10)
        self.assertEqual(
            ("asdf", dtm), WeatherResponse._preprocess_params("asdf:h", dtm)
        )
