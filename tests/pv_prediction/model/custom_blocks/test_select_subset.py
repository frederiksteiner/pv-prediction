import unittest

import pandas as pd

from pv_prediction.data.fronius_connector import FroniusConnector
from pv_prediction.model.custom_blocks.select_subset import SelectSubset


class TestSelectSubset(unittest.TestCase):
    def test_transform(self) -> None:

        test_df = pd.DataFrame({"COL1": [1, 2], "COL2": [3, 5], "COL5": [4, 5]})
        result_df = SelectSubset(["COL1", "COL2"]).transform(test_df)
        pd.testing.assert_frame_equal(result_df, test_df[["COL1", "COL2"]])

    def test_get_features_name_out(self) -> None:
        selector = SelectSubset(["COL1", "COL2"])
        out_features = selector.get_feature_names_out()
        self.assertEqual(list(out_features), ["COL1", "COL2"])
