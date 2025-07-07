import datetime as dt
import unittest
from unittest import mock

import pandas as pd
from freezegun import freeze_time

from pv_prediction.data.meteomatics.schemata import WeatherResponse
from pv_prediction.model.inferencing_runner import InferencingRunner
from pv_prediction.model.inferencing_runner import Prediction
from pv_prediction.model.inferencing_runner import PredictionResponse

# pylint: disable=protected-access


class TestInferencingRunner(unittest.TestCase):
    @mock.patch("pv_prediction.model.inferencing_runner.PVPipeline.load_from_mlflow")
    def test_model(self, mock_load_from_mlflow: mock.MagicMock) -> None:
        runner = InferencingRunner()
        self.assertEqual(runner.model, mock_load_from_mlflow.return_value)
        mock_load_from_mlflow.assert_called_once_with("pv_model", "production")

    @mock.patch("pv_prediction.model.inferencing_runner.InferencingRunner._lock")
    @mock.patch("pv_prediction.model.inferencing_runner.PVPipeline.load_from_mlflow")
    def test_load_model(
        self, mock_load_from_mlflow: mock.MagicMock, mock_lock: mock.MagicMock
    ) -> None:
        mock_lock.__enter__.side_effect = lambda: mock_load_from_mlflow(1)
        mock_lock.__exit__.side_effect = lambda x, y, z: mock_load_from_mlflow(2)

        InferencingRunner().load_model()
        mock_load_from_mlflow.assert_has_calls(
            [mock.call(1), mock.call("pv_model", "production"), mock.call(2)]
        )

    @freeze_time("2012-01-14 03:21:34", tz_offset=0)
    def test_apply_model(self) -> None:
        mock_model = mock.MagicMock()
        runner = InferencingRunner()
        runner._model = mock_model
        mock_model.model_info.model_uuid = "id"
        mock_model.predict.side_effect = lambda x: x.shape[0] * [1]
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
            ],
        }
        response = WeatherResponse(**response)  # pyre-ignore[6]
        self.assertEqual(
            runner.apply_model(response),
            PredictionResponse(
                pv_id="1",
                prediction_time=dt.datetime.now(dt.timezone.utc),
                model_id="id",
                predictions=[
                    # pyre-ignore[6]
                    Prediction(date="2025-06-28T22:00:00Z", energy_produced=1),
                    # pyre-ignore[6]
                    Prediction(date="2025-06-29T00:00:00Z", energy_produced=1),
                ],
            ),
        )
        mock_model.predict.assert_called_once()
        pd.testing.assert_frame_equal(
            mock_model.predict.call_args[0][0],
            pd.DataFrame([res.model_dump() for res in response.flatten_response()]),
        )
