"""
Depreciation calculator

Rafal Glinski, 2022

Usage:
    python depreciation_calculator.py input_file [-o OUTPUT_FILE]

    E.g.:
    python depreciation_calculator.py assets.csv

Output file default name:
    line_items.csv

Input CSV fields:
    asset_id, purchase_date, expected_life, original_value, salvage_value

Output CSV fields:
    asset_id, month, amount
"""

from __future__ import annotations

from argparse import ArgumentParser
from calendar import monthrange
from csv import DictReader, DictWriter
from datetime import date, timedelta
from decimal import ROUND_FLOOR, Decimal
from pathlib import Path


class AssetItem:
    def __init__(
        self,
        asset_id: str,
        purchase_date: str,
        expected_life: str,
        original_value: str,
        salvage_value: str,
    ) -> None:
        self.asset_id = asset_id
        self.purchase_date = date.fromisoformat(purchase_date)
        self.expected_life = int(expected_life)
        self.original_value = Decimal(original_value)
        self.salvage_value = Decimal(salvage_value)


def parse_args():
    parser = ArgumentParser(
        description="Calculate fixed asset depreciation.",
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to assets CSV file.",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        type=Path,
        help="Path to output file.",
        default="line_items.csv",
    )
    args = parser.parse_args()
    return args


def main() -> None:
    args = parse_args()
    input_ = {
        "file": args.input_file,
        "newline": "",
    }
    output_ = {
        "file": args.output_file,
        "mode": "w",
        "newline": "",
    }
    with open(**input_) as input_file, open(**output_) as output_file:
        assets_reader = DictReader(input_file)
        assets_writer = DictWriter(
            output_file, fieldnames=("asset_id", "month", "amount")
        )
        assets_writer.writeheader()
        for row_dict in assets_reader:
            asset = AssetItem(**row_dict)
            calculate_depreciation(asset, assets_writer)


def calculate_depreciation(asset: AssetItem, assets_writer: DictWriter[str]):
    cents = Decimal("0.01")
    total_loss = asset.original_value - asset.salvage_value
    monthly_loss = total_loss / Decimal(asset.expected_life)
    monthly_loss = monthly_loss.quantize(cents, rounding=ROUND_FLOOR)
    purchase_date = asset.purchase_date

    # Calculate first month
    _, fm_days = monthrange(purchase_date.year, purchase_date.month)
    fm_days_included = 1 + fm_days - purchase_date.day
    fm_ratio = fm_days_included / fm_days
    fm_loss = Decimal(fm_ratio) * monthly_loss
    fm_loss = fm_loss.quantize(cents, rounding=ROUND_FLOOR)
    fm_row = {
        "asset_id": asset.asset_id,
        "month": f"{purchase_date.year}-{purchase_date.month:02d}",
        "amount": fm_loss,
    }
    assets_writer.writerow(fm_row)

    # Calculate middle months
    end_date = calculate_end_date(purchase_date, asset.expected_life)
    sum_middle = Decimal(0)
    i = 1
    while True:
        year, month = calculate_year_month(purchase_date, i)
        # Break if last month
        if year == end_date.year and month == end_date.month:
            break
        row = {
            "asset_id": asset.asset_id,
            "month": f"{year}-{month:02d}",
            "amount": monthly_loss,
        }
        assets_writer.writerow(row)
        i += 1
        sum_middle += monthly_loss

    # Calculate last month
    lm_loss = total_loss - fm_loss - sum_middle
    lm_row = {
        "asset_id": asset.asset_id,
        "month": f"{end_date.year}-{end_date.month:02d}",
        "amount": lm_loss,
    }
    assets_writer.writerow(lm_row)


def calculate_end_date(purchase_date: date, expected_life: int) -> date:
    if expected_life < 1:
        raise ValueError(f"Given expected_life is not valid: {expected_life}")

    year, month = calculate_year_month(purchase_date, expected_life)
    _, days = monthrange(year, month)
    day = days if days < purchase_date.day else purchase_date.day
    end_date = date(year, month, day) - timedelta(days=1)
    return end_date


def calculate_year_month(from_date: date, months_passed: int) -> tuple[int, int]:
    # Operate on 0-11 range:
    months_sum = from_date.month + months_passed - 1
    year = from_date.year + int(months_sum / 12)
    month = months_sum % 12
    # Back to 1-12 range:
    month += 1
    return year, month


if __name__ == "__main__":
    main()
