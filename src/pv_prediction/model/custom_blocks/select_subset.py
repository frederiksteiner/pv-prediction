import logging

import pandas as pd
from sklearn.preprocessing import FunctionTransformer

LOGGER: logging.Logger = logging.getLogger(__name__)


class SelectSubset(FunctionTransformer):
    """Custom transformation class that allows to select a subset of features."""

    def __init__(self, subset_features: list[str]) -> None:
        """Selects subset features specified in subset_features."""
        self.subset_features = subset_features

        def _subset_feature_names_callable(
            self: SelectSubset,
            input_names: list[str],  # pylint: disable=unused-argument
        ) -> list[str]:
            return self.subset_features

        super().__init__(
            func=self._select_subset,
            feature_names_out=_subset_feature_names_callable,
        )

    def _select_subset(self, x: pd.DataFrame) -> pd.DataFrame:
        LOGGER.info("Columns before transform: %s", x.columns)
        y = x[self.subset_features]
        LOGGER.info("Columns after transform: %s", y.columns)
        return y
