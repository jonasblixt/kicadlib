# Imports Murata BLM-series ferrite EMI suppression bead data (Murata's
# own product-table CSV export, split across four files) into a KiCad
# database-library SQLite file.
#
# This is a plain 2-terminal signal/power-line EMI bead - NAMING.md's
# `bead_emi` subtype (as opposed to `bead_power`) - not a coupled/
# common-mode part, so it uses KiCad's stock Device:FerriteBead symbol
# rather than anything from this repo's cmc/coupled-inductor territory.
# It supersedes the legacy hand-maintained library/beads_BLM.kicad_sym
# (per-part symbols, e.g. "BL0402_BLM15AG100SH1D") per NAMING.md's
# migration map (`beads_BLM.lib` -> `bead_emi_murata_blm`).
#
# Four source CSVs (ind_cmc_murata_dlw5b-style per-pull exports), one EIA
# case size predominating per file but not exclusively - case size is
# read per-row from the "Size code in mm(inch)" column, not inferred
# from the source filename:
#   - bead_emi_murata_blm_1.csv (30 rows): mostly 0603 (BLM18* series)
#   - bead_emi_murata_blm_2.csv (31 rows): mostly 0805 (BLM21* series)
#   - bead_emi_murata_blm_3.csv (4 rows):  1206 (BLM31SN series)
#   - bead_emi_murata_blm_4.csv (30 rows): 0805 (BLM21PG series)
#
# FOOTPRINT: per Jonas's explicit direction, this uses KiCad's own
# standard EIA chip-inductor footprints from Inductor_SMD.pretty (same
# "point at the official footprint, don't duplicate it" approach as
# NAMING.md section 5 and import_cap_mlcc_murata.py) rather than a
# custom bead-shaped footprint - a 2-pad chip bead and a 2-pad chip
# inductor share the identical EIA land pattern, so this is a direct,
# exact-match substitution, not an approximation:
#   0603 (1608 metric) -> Inductor_SMD:L_0603_1608Metric
#   0805 (2012 metric) -> Inductor_SMD:L_0805_2012Metric
#   1206 (3216 metric) -> Inductor_SMD:L_1206_3216Metric
#
# ID: FB<case>_<impedance>_<current>, per NAMING.md section 4's ferrite-
# bead pattern (impedance conventionally at 100MHz, which is exactly
# what "Impedance (at 100MHz)" already is here, so no reference-frequency
# caveat is needed in Description). Tolerance is NOT part of the id
# (matches NAMING.md's own worked example, "FB0603_600R_3A", which has
# no tolerance component) - verified safe: across all 36 distinct
# (case, impedance-ohms, current) combinations in this dataset, no group
# has more than one DC-Resistance or tolerance value, so nothing
# electrically distinct is being folded together by leaving tolerance
# out of the id. "Impedance (at Target Frequency)" is blank for every
# row in all four files and is dropped rather than added as an
# always-empty column.
#
# ID COLLISION NOTE: of 95 total rows, only 36 distinct (case, impedance,
# current) combinations exist - the other 59 rows are packaging/taping
# variants (part-number suffix differs only in the reel/tape code, e.g.
# BLM18SG121TN1# vs BLM18SG121TZ1#: same size, same impedance, same
# current, same DCR - verified by diffing full rows across a sample of
# collision groups). This is exactly the "packaging suffix only" case
# the skill calls out as normal and safe to skip silently - every
# colliding group was spot-checked (and the DCR/tolerance-consistency
# check above ran across all 36 groups, not just a sample) before
# accepting the collision rate.
#
# CURRENT FORMATTING: a few Rated Current values aren't whole tenths of
# an amp (e.g. 1,150mA, 1,250mA, 1,550mA), so the usual single-decimal
# "1A5"-style formatter (used by the sibling ind_* scripts) would lose
# precision and risk silently colliding two different currents (e.g.
# rounding both 1,150mA and 1,200mA to "1A2"). format_current_id() below
# works from the exact milliamp integer (no float division) and keeps
# only as many fractional digits as the value actually needs: 500mA ->
# "0A5", 3,700mA -> "3A7", 1,150mA -> "1A15", 8,500mA -> "8A5".
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "Murata"

FOOTPRINT_MAP = {
    "0603": "Inductor_SMD:L_0603_1608Metric",
    "0805": "Inductor_SMD:L_0805_2012Metric",
    "1206": "Inductor_SMD:L_1206_3216Metric",
}
SYMBOL = "Device:FerriteBead"

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
IMPEDANCE_RE = re.compile(r"^([\d,]+)Ω\s*(.*)$")
CURRENT_RE = re.compile(r"^([\d,]+)mA$")
SERIES_RE = re.compile(r"^(BLM\d+[A-Z]+)\d")


def parse_case(raw):
    # "1608/0603" -> "0603"
    return raw.split("/")[1]


def parse_impedance(raw):
    # "120Ω ±25%" -> (120, "±25%"), "22Ω ±7Ω" -> (22, "±7Ω"),
    # "30Ω Typ." -> (30, "Typ.")
    m = IMPEDANCE_RE.match(raw.strip())
    if not m:
        raise ValueError(f"could not parse impedance from {raw!r}")
    return int(m.group(1).replace(",", "")), m.group(2).strip()


def format_impedance_disp(ohms):
    # 1000 -> "1kΩ", 120 -> "120Ω" - same k-scaling as the DLW5B CMC
    # import, for the same reason (a handful of these run into the kΩ
    # range: 1000Ω).
    if ohms >= 1000:
        val = ohms / 1000
        s = f"{val:.1f}".rstrip("0").rstrip(".")
        return f"{s}kΩ"
    return f"{ohms}Ω"


def parse_current_ma(raw):
    # "3,000mA" -> 3000 (int, milliamps - kept as an int rather than
    # converted to float amps, so id formatting never has to worry about
    # binary-float rounding of values like 1,150mA).
    m = CURRENT_RE.match(raw.strip().replace(",", ""))
    if not m:
        raise ValueError(f"could not parse current from {raw!r}")
    return int(m.group(1))


def format_current_id(ma):
    # See header comment: exact-milliamp string formatting, variable
    # fractional-digit count, no float division.
    whole, frac = divmod(ma, 1000)
    if frac == 0:
        return f"{whole}A0"
    frac_str = f"{frac:03d}".rstrip("0")
    return f"{whole}A{frac_str}"


def format_current_disp(ma):
    s = f"{ma / 1000:.2f}".rstrip("0").rstrip(".")
    return f"{s}A"


def load_beads(csv_path):
    beads = []
    seen_ids = {}

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            part_number = row["Part Number"].rstrip("#")
            case = parse_case(row["Size code in mm(inch)"])

            if case not in FOOTPRINT_MAP:
                print(f"WARNING: no footprint mapped for case {case!r} - "
                      f"{part_number}, skipping")
                continue
            footprint = FOOTPRINT_MAP[case]

            ohms, tolerance = parse_impedance(row["Impedance (at 100MHz)"])
            ma = parse_current_ma(row["Rated Current"])
            current_id = format_current_id(ma)
            current_disp = format_current_disp(ma)
            dcr = row["DC Resistance(max.)"].strip()

            m = SERIES_RE.match(part_number)
            series = m.group(1) if m else "BLM"

            id_str = f"FB{case}_{ohms}R_{current_id}"
            if id_str in seen_ids:
                print(f"NOTE: duplicate id '{id_str}' - {part_number} is a "
                      f"packaging/taping variant of {seen_ids[id_str]}, "
                      f"skipping")
                continue
            seen_ids[id_str] = part_number

            value_disp = format_impedance_disp(ohms)
            description = (f"{value_disp} {tolerance} @100MHz, "
                            f"{current_disp}, DCR {dcr} Max., EIA {case}, "
                            f"{series}, ferrite EMI suppression bead")

            print(f"{len(beads) + 1} {id_str} {part_number}, "
                  f"{value_disp} {tolerance}, {current_disp}")

            bead = (id_str, value_disp, footprint, SYMBOL, value_disp,
                    tolerance, current_disp, dcr, series, description,
                    part_number, MANUFACTURER)
            beads.append(bead)

    return beads


def write_database(db_path, table, beads):
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
        Impedance TEXT,
        Tolerance TEXT,
        "Rated Current" TEXT,
        DCR TEXT,
        Series TEXT,
        Description TEXT,
        "Part Number" TEXT,
        Manufacturer TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, Impedance, Tolerance,
         "Rated Current", DCR, Series, Description, "Part Number",
         Manufacturer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, beads)

    conn.commit()
    conn.close()


def build_field_defs():
    return [
        {"column": "Impedance", "name": "Impedance @100MHz",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Tolerance", "name": "Tolerance",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": False},
        {"column": "Rated Current", "name": "Rated Current",
         "visible_on_add": True, "visible_in_chooser": True, "show_name": False},
        {"column": "DCR", "name": "DCR",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Series", "name": "Series",
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
        "name": "Murata BLM Ferrite EMI Suppression Beads",
        "description": ("Murata BLM-series ferrite EMI suppression bead "
                         "library (0603/0805/1206, KiCad standard "
                         "footprints)"),
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
                "name": "BLM",
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
        description="Import Murata BLM-series ferrite EMI bead CSV "
                     "export(s) into a KiCad database-library SQLite "
                     "file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s). Multiple "
                              "values are merged into one library.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. bead_emi_murata_blm.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def main():
    args = parse_args()
    beads = []
    for csv_path in args.csv:
        beads.extend(load_beads(csv_path))
    write_database(args.db, args.table, beads)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(beads)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
