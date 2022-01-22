from pandas.testing import assert_frame_equal
import pandas as pd

from omnipath._misc import dtypes


class TestMisc:
    def test_auto_dtype(self):

        inp = pd.DataFrame(
            {
                "a": ["1", "2", "3"],
                "b": ["1", "2", 3],
                "c": ["1", "2", "3.14"],
                "d": ["1", "0", "1"],
                "e": ["Y", "N", "Y"],
                "f": [2.3, 4.7, 3.1],
                "g": [False, True, True],
            }
        )

        exp = pd.DataFrame(
            {
                "a": [1, 2, 3],
                "b": [1, 2, 3],
                "c": [1.0, 2.0, 3.14],
                "d": [True, False, True],
                "e": [True, False, True],
                "f": [2.3, 4.7, 3.1],
                "g": [False, True, True],
            }
        )

        out = dtypes.auto_dtype(inp)

        assert_frame_equal(exp, out)
