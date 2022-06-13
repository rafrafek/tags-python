"""
Depreciation calculator - tests

Rafal Glinski, 2022

Usage:
    python -m unittest depreciation_calculator_test.py
"""

import unittest
from csv import DictWriter
from datetime import date
from io import StringIO

from depreciation_calculator import (
    AssetItem,
    calculate_depreciation,
    calculate_end_date,
    calculate_year_month,
)


class TestDepreciationCalculator(unittest.TestCase):
    def test_calculate_year_month(self):
        # from_date, months_passed -> tuple[int, int]
        parameters = (
            ("2022-01-01", 1, (2022, 2)),
            ("2022-01-02", 1, (2022, 2)),
            ("2022-01-02", 11, (2022, 12)),
            ("2022-01-02", 12, (2023, 1)),
            ("2022-01-02", 0, (2022, 1)),
            ("2022-12-02", 0, (2022, 12)),
            ("2022-06-02", 1, (2022, 7)),
            ("2022-06-02", 2, (2022, 8)),
            ("2022-06-02", 3, (2022, 9)),
            ("2022-06-02", 4, (2022, 10)),
            ("2022-06-02", 5, (2022, 11)),
            ("2022-06-02", 6, (2022, 12)),
            ("2022-06-02", 7, (2023, 1)),
            ("2022-12-06", 1, (2023, 1)),
            ("2022-12-31", 120, (2032, 12)),
            ("2022-12-31", 1200, (2122, 12)),
            ("3022-12-31", 1200, (3122, 12)),
        )
        for given, months_passed, expected_result in parameters:
            given_date = date.fromisoformat(given)
            with self.subTest():
                self.assertEqual(
                    calculate_year_month(given_date, months_passed),
                    expected_result,
                    msg=(given_date, months_passed, expected_result),
                )

    def test_calculate_end_date(self):
        # purchase_date, expected_life -> end_date
        parameters = (
            ("2022-01-01", 1, "2022-01-31"),
            ("2022-01-02", 1, "2022-02-01"),
            ("2022-01-01", 12, "2022-12-31"),
            ("2020-03-06", 8, "2020-11-05"),  # FA001
            ("2021-06-07", 9, "2022-03-06"),  # FA002
            ("2020-05-12", 2, "2020-07-11"),  # FA004
        )
        for given, expected_life, expected in parameters:
            given_date = date.fromisoformat(given)
            expected_date = date.fromisoformat(expected)
            with self.subTest():
                self.assertEqual(
                    calculate_end_date(given_date, expected_life),
                    expected_date,
                )
        # Test against expected_life with zero value
        given_date = date.fromisoformat("2022-01-01")
        with self.assertRaises(ValueError):
            calculate_end_date(given_date, 0)

    def test_calculate_depreciation(self):
        assets = (
            (
                AssetItem("FA001", "2020-03-06", "8", "42651.76", "3959.76"),
                (
                    "asset_id,month,amount",
                    "FA001,2020-03,4056.41",
                    "FA001,2020-04,4836.50",
                    "FA001,2020-05,4836.50",
                    "FA001,2020-06,4836.50",
                    "FA001,2020-07,4836.50",
                    "FA001,2020-08,4836.50",
                    "FA001,2020-09,4836.50",
                    "FA001,2020-10,4836.50",
                    "FA001,2020-11,780.09",
                    "",
                ),
            ),
            (
                AssetItem("FA002", "2021-06-07", "9", "29927.35", "2269.92"),
                (
                    "asset_id,month,amount",
                    "FA002,2021-06,2458.43",
                    "FA002,2021-07,3073.04",
                    "FA002,2021-08,3073.04",
                    "FA002,2021-09,3073.04",
                    "FA002,2021-10,3073.04",
                    "FA002,2021-11,3073.04",
                    "FA002,2021-12,3073.04",
                    "FA002,2022-01,3073.04",
                    "FA002,2022-02,3073.04",
                    "FA002,2022-03,614.68",
                    "",
                ),
            ),
            (
                # end date: 2020-07-11
                # value lost: 22892.05 - 2624.48 = 20267.57
                # average monthly lost: 20267.57 / 2 = 10133.785 -> 10133.78
                # first month: 1 + 31 - 12 = 20
                #              (20 / 31) * 10133.78 = 6537.92
                # last month = 20267.57 - 6537.92 - 10133.78 = 3595.87
                AssetItem("FA004", "2020-05-12", "2", "22892.05", "2624.48"),
                (
                    "asset_id,month,amount",
                    "FA004,2020-05,6537.92",
                    "FA004,2020-06,10133.78",
                    "FA004,2020-07,3595.87",
                    "",
                ),
            ),
            (
                # end date: 2020-06-11
                # value lost: 22892.05 - 2624.48 = 20267.57
                # average monthly lost: 20267.57 / 1 = 20267.57
                # first month: 1 + 31 - 12 = 20
                #              (20 / 31) * 20267.57 = 13075.85
                # last month = 20267.57 - 13075.85 = 7191.72
                # last month days based calculation would be wrong:
                #   (11 / 30) * 20267.57 = 7431.44 (too much)
                #   that's because June has only 30 days
                #   (11 / 30) > (11 / 31)
                AssetItem("FA00X", "2020-05-12", "1", "22892.05", "2624.48"),
                (
                    "asset_id,month,amount",
                    "FA00X,2020-05,13075.85",
                    "FA00X,2020-06,7191.72",
                    "",
                ),
            ),
        )
        fieldnames = ("asset_id", "month", "amount")
        for asset, expected_output in assets:
            with StringIO() as output:
                assets_writer = DictWriter(output, fieldnames=fieldnames)
                assets_writer.writeheader()
                calculate_depreciation(asset, assets_writer.writerow)
                output_value = output.getvalue()
            with self.subTest():
                self.assertEqual(
                    output_value,
                    "\r\n".join(expected_output),
                )


if __name__ == "__main__":
    unittest.main()
