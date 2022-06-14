from argparse import ArgumentParser
from pathlib import Path
from sqlite3 import connect


class LookupError(Exception):
    pass


def parse_args():
    parser = ArgumentParser(
        description="Look up for given asset ID in database.",
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to SQLite file for lookup.",
    )
    parser.add_argument(
        "-a",
        "--asset_id",
        type=str,
        help="Asset ID for the lookup",
        default=None,
    )
    args = parser.parse_args()
    return args, parser


def lookup(input_file: Path, asset_name: str):
    if asset_name is None:
        raise LookupError("Please specify asset ID")
    with connect(input_file) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM assets WHERE name=?", (asset_name,))
        asset = cursor.fetchone()
        if asset is None:
            raise LookupError(f"Asset {asset_name} does not exist")
        asset_id, _ = asset
        cursor.execute(
            "SELECT asset_id, month, amount FROM rows WHERE asset_id=?",
            (asset_id,),
        )
        for row in cursor:
            _, month, amount = row
            print(asset_name, month, amount)


def main():
    args, parser = parse_args()
    try:
        lookup(args.input_file, args.asset_id)
    except LookupError as e:
        print("Error when performing lookup")
        print(e)
        parser.print_usage()
        raise SystemExit(4)


if __name__ == "__main__":
    main()
