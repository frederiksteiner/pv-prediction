import datetime as dt
from threading import Lock
from typing import Annotated

import pandas as pd
from pydantic import BaseModel
from pydantic import PlainSerializer

from pv_prediction.data.meteomatics.schemata import WeatherResponse
from pv_prediction.model.pv_pipeline import PVPipeline

DateTime = Annotated[dt.datetime, PlainSerializer(lambda dt: dt.isoformat())]


class Prediction(BaseModel):
    """PV prediction at some time."""

    date: DateTime
    enegry_produced: float


class PredictionResponse(BaseModel):
    """Predictionresponse."""

    pv_id: str
    prediction_time: DateTime
    model_id: str
    predictions: list[Prediction]


class InferencingRunner:
    """Class to apply the model online to some data."""

    _lock: Lock = Lock()
    model_name: str = "pv_model"
    model_alias = "production"

    def __init__(self) -> None:
        """Initialize the InferencingRunner."""
        self._model: PVPipeline | None = None

    @property
    def model(self) -> PVPipeline:
        """Returns the current model to predict."""
        if not self._model:
            self.load_model()
        return self._model  # pyre-ignore[7]

    def load_model(self) -> None:
        """Reload the model."""
        with self._lock:
            self._model = PVPipeline.load_from_mlflow(self.model_name, self.model_alias)

    def apply_model(
        self,
        response: WeatherResponse,
    ) -> PredictionResponse:
        """Applies model to weather data."""
        flattened = response.flatten_response()
        df_input = pd.DataFrame([res.model_dump() for res in flattened])
        preds = self.model.predict(df_input)
        return PredictionResponse(
            pv_id=str(1),
            prediction_time=dt.datetime.now(dt.timezone.utc),
            model_id=self.model.model_info.model_id,
            predictions=[
                Prediction(
                    date=ele.date,
                    enegry_produced=preds[i],
                )
                for i, ele in enumerate(flattened)
            ],
        )

    def run(self, pv_to_predict: WeatherResponse) -> PredictionResponse:
        """Run the prediction on the provided weather data."""
        with self._lock:
            return self.apply_model(pv_to_predict)
