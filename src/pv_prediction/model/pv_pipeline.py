from __future__ import annotations

import mlflow.models.model
import mlflow.sklearn
from joblib import Memory
from lightgbm.sklearn import LGBMRegressor
from sklearn.pipeline import Pipeline

from pv_prediction.model.custom_blocks.select_subset import SelectSubset


class PVPipeline(Pipeline):
    """Sklearn based pipeline to train and predict pv power production."""

    def __init__(
        self,
        steps: list[tuple],  # pyre-ignore[24]
        weather_params: list[str],
        memory: Memory | str | None = None,
        verbose: bool = False,
    ) -> None:
        """Inits the pipeline with the sklearn steps and weather params to be used in the model."""
        super().__init__(steps, memory=memory, verbose=verbose)
        self.weather_params: list[str] = weather_params
        self._model_info: mlflow.models.model.ModelInfo | None = None

    @property
    def model_info(self) -> mlflow.models.model.ModelInfo:
        """Returns the model info of the pipeline if it is logged to mlflow."""
        if not self._model_info:
            raise ValueError("Model has not been logged yet.")
        return self._model_info

    @classmethod
    def get_pipeline(cls, weather_params: list[str]) -> PVPipeline:
        """Returns an example pipeline."""
        return cls(
            [
                ("selector", SelectSubset(weather_params)),
                ("estimator", LGBMRegressor()),
            ],
            weather_params,
        )

    def log_model(self) -> None:
        """Log model to mlflow as pv_model."""
        self._model_info = mlflow.sklearn.log_model(
            self, registered_model_name="pv_model"
        )

    def set_model_info(self, model_info: mlflow.models.model.ModelInfo) -> None:
        """Set model info."""
        self._model_info = model_info

    @staticmethod
    def load_from_mlflow(model_name: str, model_version_alias: str) -> PVPipeline:
        """Load model from mlflow by specifying model_name and model_version."""
        model_uri = f"models:/{model_name}@{model_version_alias}"
        model: PVPipeline = mlflow.sklearn.load_model(model_uri)
        model.set_model_info(mlflow.models.get_model_info(model_uri))
        return model
