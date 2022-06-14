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
from sqlite3 import connect
from typing import Any, Callable, Mapping


class SQLiteWriter:
    def __init__(self, file_path: Path):
        self.connection = connect(file_path)
        cursor = self.connection.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS assets(
              id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              UNIQUE (name)
            )"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS rows(
              id INTEGER PRIMARY KEY,
              asset_id INTEGER NOT NULL,
              month TEXT NOT NULL,
              amount TEXT NOT NULL,
              FOREIGN KEY (asset_id)
                REFERENCES assets (id)
                  ON UPDATE NO ACTION
                  ON DELETE CASCADE,
              UNIQUE (asset_id, month)
            )"""
        )

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.connection.close()

    def create_asset_if_not_exists(self, asset_id: str):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, name FROM assets WHERE name=?", (asset_id,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO assets(name) VALUES(?)", (asset_id,))
            self.connection.commit()

    def update_or_create_row(self, row: Mapping[str, Any]):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, name FROM assets WHERE name=?", (row["asset_id"],))
        asset = cursor.fetchone()
        if asset is None:
            raise Exception(f"Asset {row['asset_id']} does not exist")
        asset_id, _ = asset
        cursor.execute(
            "SELECT asset_id, month, amount FROM rows WHERE asset_id=? AND month=?",
            (asset_id, row["month"]),
        )
        fetched = cursor.fetchone()
        if fetched is None:
            cursor.execute(
                "INSERT INTO rows(asset_id, month, amount) VALUES(?, ?, ?)",
                (asset_id, row["month"], str(row["amount"])),
            )
            self.connection.commit()
            return
        _, _, amount = fetched
        if amount == str(row["amount"]):
            return
        cursor.execute(
            "UPDATE rows SET amount=? WHERE asset_id=? AND month=?",
            (str(row["amount"]), asset_id, row["month"]),
        )
        self.connection.commit()


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
    if is_sqlite(args.output_file):
        use_sqlite(args.input_file, args.output_file)
    else:
        use_csv(args.input_file, args.output_file)


def is_sqlite(file_name: Path):
    return file_name.suffix in (".sqlite", ".sqlite3")


def use_sqlite(input_file: Path, output_file: Path):
    input_ = {
        "file": input_file,
        "newline": "",
    }
    with (
        open(**input_) as input_file_,
        SQLiteWriter(output_file) as sql_writer,
    ):
        assets_reader = DictReader(input_file_)
        for row_dict in assets_reader:
            asset = AssetItem(**row_dict)
            sql_writer.create_asset_if_not_exists(asset.asset_id)
            write_row = sql_writer.update_or_create_row
            calculate_depreciation(asset, write_row)


def use_csv(input_file: Path, output_file: Path):
    input_ = {
        "file": input_file,
        "newline": "",
    }
    output_ = {
        "file": output_file,
        "mode": "w",
        "newline": "",
    }
    with (
        open(**input_) as input_file_,
        open(**output_) as output_file_,
    ):
        assets_reader = DictReader(input_file_)
        assets_writer = DictWriter(
            output_file_, fieldnames=("asset_id", "month", "amount")
        )
        assets_writer.writeheader()
        for row_dict in assets_reader:
            asset = AssetItem(**row_dict)
            write_row = assets_writer.writerow
            calculate_depreciation(asset, write_row)


def calculate_depreciation(
    asset: AssetItem, write_row: Callable[[Mapping[str, Any]], Any]
):
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
    write_row(fm_row)

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
        write_row(row)
        i += 1
        sum_middle += monthly_loss

    # Calculate last month
    lm_loss = total_loss - fm_loss - sum_middle
    lm_row = {
        "asset_id": asset.asset_id,
        "month": f"{end_date.year}-{end_date.month:02d}",
        "amount": lm_loss,
    }
    write_row(lm_row)


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
