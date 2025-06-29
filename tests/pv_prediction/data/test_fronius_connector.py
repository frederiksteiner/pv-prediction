import unittest

import pandas as pd

from pv_prediction.data.fronius_connector import FroniusConnector


class TestFroniusConnector(unittest.TestCase):
    def test_iterate_over_body(self) -> None:
        json_data = {
            "inverter": {
                "Data": {
                    "Param3": {
                        "Unit": "Wh",
                        "Values": {
                            "1": 0.1,
                            "2": 0.2,
                            "3": 0.3,
                        },
                        "_comment": "channelId=67830024",
                    }
                },
                "DeviceType": 232,
                "End": "2024-07-24T23:59:59+02:00",
                "NodeType": 97,
                "Start": "2024-07-09T00:00:00+02:00",
            },
            "meter": {
                "Data": {
                    "Param1": {
                        "Unit": "Wh",
                        "Values": {"1": 4, "2": 5, "3": 6},
                        "_comment": "channelId=167837960",
                    },
                    "Param2": {
                        "Unit": "Wh",
                        "Values": {"1": 1, "2": 3, "3": 2},
                        "_comment": "channelId=167772424",
                    },
                },
                "End": "2024-07-24T00:00:00+02:00",
                "Start": "2024-07-09T00:00:00+02:00",
            },
        }
        result = FroniusConnector._iterate_over_body(
            json_data, ["Param1", "Param2", "Param3"]
        )
        pd.testing.assert_frame_equal(
            result,
            pd.DataFrame(
                {
                    "Param1": [4, 5, 6],
                    "Param2": [1, 3, 2],
                    "Param3": [0.1, 0.2, 0.3],
                },
                index=pd.Series(
                    [
                        pd.to_datetime("2024-07-09T00:00:01+02:00"),
                        pd.to_datetime("2024-07-09T00:00:02+02:00"),
                        pd.to_datetime("2024-07-09T00:00:03+02:00"),
                    ]
                ),
            ),
        )
