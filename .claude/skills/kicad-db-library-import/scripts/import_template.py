# Template for a kicadlib database-library importer. Copy this file to
# scripting/import_<library_name>.py and fill in the marked TODOs. This
# skeleton carries the boilerplate that's identical across every importer
# in the repo (table-name validation, the seen_ids dedup pattern, the
# write_database/write_kicad_dbl pair, the argparse interface) so each new
# library only has to supply the CSV-specific parsing and the field style.
#
# See references/field_styles.md for the two build_field_defs() styles
# (ceramic-MLCC vs. polarized-electrolytic) and their matching
# CREATE TABLE column lists - swap in whichever one applies and delete
# the other's leftover columns.
#
# TODO: replace this header comment with one specific to this library:
# what the source CSV is (vendor, export type), which field style was
# chosen and why, the footprint mapping (and any near-miss substitutions
# or custom footprints), and anything non-obvious about the dedup id.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "TODO"  # or derive per-row if the CSV spans multiple manufacturers

# TODO: case-size key (however this CSV identifies it - an EIA code, a
# (length, width) tuple, whatever's natural) -> (footprint library
# nickname, footprint name). Use "Capacitor_SMD" / "Capacitor_Tantalum_SMD"
# for KiCad standard footprints; use a custom nickname only if a matching
# footprints/<Nickname>.pretty/ has already been built for this case.
footprint_mapping = {
    # "1808": ("Capacitor_SMD", "C_1808_4520Metric"),
}

# TODO: vendor tolerance-column string -> the short numeric string used in
# the id and description (e.g. "±10%" -> "10").
tolerance_mapping = {
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import a TODO CSV export into a KiCad database-"
                     "library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s). Multiple "
                              "values are merged into one library.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database. Must match the corresponding "
                              ".kicad_dbl 'table' field.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


# TODO: capacitance/resistance/etc. parsing helpers go here. Vendor CSVs
# are inconsistent about comma-thousands-separators ("1,000pF"), compound
# strings with tolerance baked in ("4.5mm ±0.3mm"), and which of several
# near-identical columns is actually populated for a given part family -
# print a handful of raw values from the real CSV before writing these,
# don't guess the format.
#
# def parse_capacitance(raw): ...
# def format_capacitance(farads): ...  # -> (short_str_for_id, full_display_str)


def load_parts(csv_paths):
    count = 0
    skipped_footprint = {}
    skipped_other = {}
    parts = []
    seen_ids = {}

    for csv_path in csv_paths:
        with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # TODO: pull raw fields out of `row` by column name, map
                # case size to a footprint via footprint_mapping (skip +
                # tally into skipped_footprint on no match), map tolerance
                # via tolerance_mapping, parse capacitance/voltage/etc.

                # TODO: build a semantic id from every field that could
                # distinguish two electrically-different parts - not just
                # the "obvious" ones. If more than ~5-10% of rows collide,
                # diff a few colliding pairs' FULL rows (not just the
                # fields already in the id) before trusting that they're
                # genuine packaging-suffix duplicates - a missing
                # distinguishing field (e.g. ESR grade) can masquerade as
                # a high duplicate rate.
                id_str = "TODO"
                part_number = row.get("TODO_PART_NUMBER_COLUMN")

                if id_str in seen_ids:
                    print(f"WARNING: duplicate id '{id_str}' - "
                          f"{part_number} collides with {seen_ids[id_str]}, skipping")
                    continue
                seen_ids[id_str] = part_number

                count += 1
                # TODO: build the row tuple matching write_database's
                # INSERT column order below.
                # part = (id_str, value, footprint, symbol, ...)
                # parts.append(part)

    if skipped_footprint:
        total_skipped = sum(skipped_footprint.values())
        print(f"\nSkipped {total_skipped} rows with no matching footprint:")
        for code, n in sorted(skipped_footprint.items(), key=lambda x: -x[1]):
            print(f"  {code}: {n} parts")

    if skipped_other:
        total_skipped = sum(skipped_other.values())
        print(f"\nSkipped {total_skipped} rows for other reasons:")
        for reason, n in sorted(skipped_other.items(), key=lambda x: -x[1]):
            print(f"  {reason}: {n} parts")

    return parts


def write_database(db_path, table, parts):
    if not TABLE_NAME_RE.match(table):
        raise ValueError(f"'{table}' is not a valid SQLite table name")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"DROP TABLE IF EXISTS {table}")
    # TODO: pick the column list matching the chosen field style - see
    # references/field_styles.md for the two CREATE TABLE variants.
    cursor.execute(f"""
    CREATE TABLE {table} (
        id TEXT PRIMARY KEY,
        Value TEXT,
        Footprints TEXT,
        Symbol TEXT
        -- TODO: remaining columns
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol)
    VALUES (?, ?, ?, ?)
    """, parts)

    conn.commit()
    conn.close()


def build_field_defs():
    # TODO: return one of the two styles from references/field_styles.md,
    # verbatim or lightly adapted (e.g. adding "Safety Rating").
    return []


def write_kicad_dbl(dbl_path, db_path, table):
    content = {
        "meta": {"version": 0},
        "name": "TODO Human-Readable Library Name",
        "description": "TODO Human-readable description",
        "source": {
            "type": "odbc",
            "dsn": "",
            "username": "",
            "password": "",
            "timeout_seconds": 2,
            "connection_string": (
                "Driver={SQLite3 ODBC Driver};"
                f"Database=${{CWD}}/{Path(db_path).name}"
            ),
        },
        "libraries": [
            {
                "name": "TODO",  # SHORT nickname shown in KiCad's chooser -
                                 # e.g. "VJ", "GA3", "OSCON", "ECHU(X)" - a
                                 # few characters pulled from the series
                                 # name, NOT the full table name
                "table": table,
                "key": "id",
                "symbols": "Symbol",
                "footprints": "Footprints",
                "fields": build_field_defs(),
                "properties": {"description": "Description"},
            }
        ],
    }

    with open(dbl_path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=4)
        f.write("\n")


def main():
    args = parse_args()
    parts = load_parts(args.csv)
    write_database(args.db, args.table, parts)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(parts)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
