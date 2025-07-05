import unittest
from unittest import mock

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OrdinalEncoder

from pv_prediction.model.pv_pipeline import PVPipeline


class TestPVPipeline(unittest.TestCase):
    def test_get_pipeline(self) -> None:
        params = ["param1", "param2"]
        pipe = PVPipeline.get_pipeline(params)
        self.assertEqual(pipe.weather_params, params)

    @mock.patch("pv_prediction.model.pv_pipeline.mlflow.sklearn.log_model")
    def test_log_model(self, mock_log_model: mock.MagicMock) -> None:
        pipeline = PVPipeline(
            [("ordinal", OrdinalEncoder()), ("estimator", LinearRegression())],
            ["param1"],
        )
        with self.assertRaises(ValueError):
            _ = pipeline.model_info
        pipeline.log_model()
        mock_log_model.assert_called_once_with(
            pipeline, registered_model_name="pv_model"
        )
        self.assertEqual(pipeline.model_info, mock_log_model.return_value)

    @mock.patch("pv_prediction.model.pv_pipeline.mlflow.sklearn.load_model")
    def test_load_from_mlflow(self, mock_load_model: mock.MagicMock) -> None:
        model = PVPipeline.load_from_mlflow("name", "alias")
        mock_load_model.assert_called_once_with("models:/name@alias")
        self.assertEqual(model, mock_load_model.return_value)
