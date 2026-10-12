# Imports Bel Fuse 0ZCJ-series PPTC (polymeric PTC / resettable fuse)
# data into a KiCad database-library SQLite file.
#
# NEW CATEGORY: kicadlib's first `fuse_` database library. NAMING.md has
# no fuse section; the name follows the usual
# <component>_<type>_<vendor>_<series> shape - `fuse_pptc_bel_0zcj` -
# leaving room for e.g. `fuse_smd_...` one-time fuses later.
#
# SOURCE DATA: data/fuse_pptc_bel_0zcj.csv is a hand transcription of
# the "Part Numbers" table on Bel's product page (18 parts, 2026-10-02):
#   https://www.belfuse.com/products/circuit-protection/ptc-resettable-fuses/0zcj-series
# Column names are kept exactly as that table's headers. The numbers are
# the web table's, NOT cross-checked against the PDF datasheet. One row
# looks suspect at the source: 0ZCJ0200FF2C lists 0.08 ohm for BOTH
# initial and post-trip resistance (initial is probably lower) -
# imported as published.
#
# FIELDS (per Jonas): Hold Current, Trip Current, Max Current, Max
# Voltage, Resistance Initial, Resistance Post Trip. VALUE IS THE TRIP
# CURRENT (not the hold current) - shown on the schematic without its
# label, together with Max Voltage. Everything else is chooser-only.
#
# SYMBOL: Device:Polyfuse (KiCad stock), per Jonas.
#
# FOOTPRINT: Jonas:FUSC3216X85N for every part - the SnapEDA land
# pattern + STEP model Jonas downloaded for 0ZCJ0005FF2E
# (bel_0ZCJ0005FF2E.zip), installed as
# footprints/Jonas.pretty/FUSC3216X85N.kicad_mod and
# footprints/Jonas.3dshapes/0ZCJ0005FF2E.step. The whole series is 1206,
# so the land pattern is shared; body HEIGHT differs between parts, so
# the 0.85mm-tall 3D model is only exact for the lower-current parts.
# The only edits to the downloaded footprint: descr/tags filled in and a
# (model ...) reference added (STEP is Y-up, centred on the body, hence
# rotate -90 about X and +0.425mm Z offset).
#
# ID: F1206_<hold>_<voltage>V, hold current in unit-as-decimal-point
# notation (50m, 1A1, 2A) as in NAMING.md section 4. Hold current alone
# is not unique (the "AF" and "FF" variants share a hold current and
# differ in max voltage / max current), hold + voltage is - verified
# unique across all 18 rows; the seen_ids check is a safety net.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "Bel Fuse"
SYMBOL = "Device:Polyfuse"
FOOTPRINT = "Jonas:FUSC3216X85N"
CASE = "1206"

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def fmt_current(amps):
    """0.05 -> '50mA', 1.0 -> '1A', 2.2 -> '2.2A'."""
    if amps < 1:
        return f"{amps * 1000:g}mA"
    return f"{amps:g}A"


def id_current(amps):
    """0.05 -> '50m', 1.1 -> '1A1', 2.0 -> '2A'."""
    if amps < 1:
        return f"{amps * 1000:g}m".replace(".", "m")
    s = f"{amps:g}"
    return s.replace(".", "A") if "." in s else s + "A"


def fmt_resistance(ohms):
    """0.055 -> '55mR', 3.6 -> '3.6R', 50 -> '50R'."""
    if ohms < 1:
        return f"{ohms * 1000:g}mR"
    return f"{ohms:g}R"


def load_parts(csv_paths):
    parts = []
    seen_ids = {}

    for csv_path in csv_paths:
        with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
            for row in csv.DictReader(csvfile):
                part_number = row["Product"].strip()
                i_hold = float(row["Current - Hold (A)"])
                i_trip = float(row["Current - Trip (A)"])
                i_max = float(row["Current - Max (A)"])
                v_max = float(row["Voltage (VDC)"])
                r_init = float(row["Resistance - Initial (Ohm)"])
                r_post = float(row["Resistance - Post Trip (Ohm)"])

                id_str = f"F{CASE}_{id_current(i_hold)}_{v_max:g}V"
                if id_str in seen_ids:
                    print(f"WARNING: duplicate id '{id_str}' - {part_number} "
                          f"collides with {seen_ids[id_str]}, skipping")
                    continue
                seen_ids[id_str] = part_number

                hold_s = fmt_current(i_hold)
                trip_s = fmt_current(i_trip)
                imax_s = fmt_current(i_max)
                v_s = f"{v_max:g}V"
                ri_s = fmt_resistance(r_init)
                rp_s = fmt_resistance(r_post)
                value = trip_s

                description = (f"PPTC resettable fuse, {hold_s} hold, "
                               f"{trip_s} trip, {v_s}, {imax_s} max, "
                               f"{ri_s} initial / {rp_s} post-trip, "
                               f"{CASE}, Bel 0ZCJ")

                print(f"{len(parts) + 1} {id_str}, {part_number}, "
                      f"{hold_s} hold / {trip_s} trip, {v_s}")

                parts.append((id_str, value, FOOTPRINT, SYMBOL, hold_s,
                              trip_s, imax_s, v_s, ri_s, rp_s, description,
                              part_number, MANUFACTURER))

    return parts


def write_database(db_path, table, parts):
    if not TABLE_NAME_RE.match(table):
        raise ValueError(f"'{table}' is not a valid SQLite table name")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"DROP TABLE IF EXISTS {table}")
    cursor.execute(f"""
    CREATE TABLE {table} (
        id TEXT PRIMARY KEY,
        Value TEXT,
        Footprints TEXT,
        Symbol TEXT,
        "Hold Current" TEXT,
        "Trip Current" TEXT,
        "Max Current" TEXT,
        "Max Voltage" TEXT,
        "Resistance Initial" TEXT,
        "Resistance Post Trip" TEXT,
        Description TEXT,
        "Part Number" TEXT,
        Manufacturer TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, "Hold Current", "Trip Current",
         "Max Current", "Max Voltage", "Resistance Initial",
         "Resistance Post Trip", Description, "Part Number", Manufacturer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, parts)

    conn.commit()
    conn.close()


def build_field_defs():
    return [
        {"column": "Hold Current", "name": "Hold Current",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Trip Current", "name": "Trip Current",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Max Current", "name": "Max Current",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Max Voltage", "name": "Max Voltage",
         "visible_on_add": True, "visible_in_chooser": True, "show_name": False},
        {"column": "Resistance Initial", "name": "Resistance Initial",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Resistance Post Trip", "name": "Resistance Post Trip",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Manufacturer", "name": "Manufacturer",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Part Number", "name": "Part Number",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Value", "name": "Value",
         "visible_on_add": True, "visible_in_chooser": True, "show_name": False},
    ]


def write_kicad_dbl(dbl_path, db_path, table):
    content = {
        "meta": {"version": 0},
        "name": "Bel Fuse 0ZCJ PPTC Resettable Fuses",
        "description": ("Bel Fuse 0ZCJ-series 1206 PPTC resettable fuse "
                        "library (value = trip current)"),
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
                "name": "0ZCJ",
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import the Bel 0ZCJ PPTC part table into a KiCad "
                    "database-library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                        help="Path(s) to the input CSV(s).")
    parser.add_argument("--db", required=True,
                        help="Path to the output .db SQLite file.")
    parser.add_argument("--table", required=True,
                        help="Table name, e.g. fuse_pptc_bel_0zcj.")
    parser.add_argument("--kicad-dbl", required=True,
                        help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def main():
    args = parse_args()
    parts = load_parts(args.csv)
    write_database(args.db, args.table, parts)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(parts)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
