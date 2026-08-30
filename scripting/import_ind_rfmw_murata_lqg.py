# Imports Murata LQG15H/LQG18H high-Q RF/microwave multilayer chip
# inductor data (Murata's own product-table CSV export, one file per
# case-size series) into a KiCad database-library SQLite file.
#
# Naming note: NAMING.md documents `rf` as the inductor subtype code for
# this part class (its own worked example is
# "ind_rf_murata_lqg15hn.kicad_dbl"), but Jonas asked for this library as
# ind_rfmw_murata_lqg - `rfmw`, not `rf`. That matches the capacitor side
# of NAMING.md exactly (`rfmw` = "High-Q RF/microwave ceramic",
# cap_rfmw_kyocera_accu_p), so this is treated as the same code reused
# consistently for RF-purposed parts across both cap_ and ind_, and
# NAMING.md's inductor table is the one that's stale - it should probably
# be updated to say `rfmw` too, but that's a doc fix for Jonas to make,
# not something this script does.
#
# Two source CSVs, both Murata LQG-family 0402/0603 multilayer RF chip
# inductors differing mainly by case size, merged into one umbrella
# library the same way import_ind_power_vishay_ihlp.py merged
# IHLP1212/1616/2020/2525 into one ind_power_vishay_ihlp library:
#   - ind_rfmw_murata_lqg15h.csv: LQG15HS series, EIA 0402, up to 125C
#   - ind_rfmw_murata_lqg18h.csv: LQG18HN series, EIA 0603, up to 85C
# The two series differ in more than case size (rated-current range,
# tolerance grades stocked, max operating temp), so "Series" and
# "Max Op Temp" are kept as real per-row fields rather than collapsed
# into the library description.
#
# Field style is an RF-inductor trim of the ind_power_vishay_ihlp style:
# same Device:L symbol and general shape (Inductance/Tolerance/Rated
# Current/DCR/SRF/Series/Manufacturer/Part Number/Value), but no
# Saturation Current field - that's a power-inductor/core-saturation
# concept that doesn't apply to these small multilayer RF chip inductors
# (the source data has no such column at all, unlike IHLP where it was a
# real populated spec). Max Op Temp replaces IHLP's Temp Min/Temp Max
# pair since this source only gives a single maximum-temperature rating,
# not a range - not fabricating a minimum that isn't in the data.
#
# Inductance values mostly below 10nH are toleranced in absolute nH (e.g.
# "1.1nH +/-0.1nH") rather than percent (e.g. "10nH +/-2%") - standard
# for small chip inductors, where a percent tolerance isn't meaningful at
# these magnitudes - but it's not a strict magnitude cutoff: LQG18HN's
# 6.8nH and 8.2nH values are stocked with a +/-5% percent grade only, no
# absolute-nH grade, breaking the otherwise-clean "<10nH -> absolute"
# pattern the rest of both files follow. So parse_inductance() reads
# whichever suffix ("%" or "nH") is actually present in each row rather
# than assuming one by value magnitude. The id's tolerance token reflects
# this: percent tolerances use a bare number (matching NAMING.md's
# res_*/cap_* convention, "5" for 5%), absolute-nH tolerances reuse
# format_inductance()'s own IEC-60062 notation on the delta itself (e.g.
# "0n3" for +/-0.3nH) since there's no unitless convention for an
# absolute-nH tolerance elsewhere in the repo to copy - verified the two
# schemes never collide (nothing is toleranced both ways for the same
# nominal value) across all 150 rows.
#
# Id format follows NAMING.md's inductor pattern: L<case>_<value>_
# <tolerance>_<current>. Verified zero id collisions across all 150 rows
# from both files combined (each (case, value, tolerance, current)
# combination maps to exactly one part number).
#
# Both case sizes (0402, 0603) are standard EIA metric cases with an
# exact dimensional match in KiCad's own Inductor_SMD.pretty - no custom
# footprint needed.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "Murata"

# EIA case code (from the "Size code in mm(inch)" column, e.g.
# "1005/0402" -> "0402") -> (footprint library nickname, footprint name).
# All standard KiCad footprints.
footprint_mapping = {
    "0402": ("Inductor_SMD", "L_0402_1005Metric"),
    "0603": ("Inductor_SMD", "L_0603_1608Metric"),
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
INDUCTANCE_RE = re.compile(r"^([\d.]+)nH\s*\xb1([\d.]+)(%|nH)$")
CURRENT_RE = re.compile(r"^([\d,]+)mA$")
SRF_RE = re.compile(r"^([\d,]+)MHz$")


def parse_case(raw):
    # "1005/0402" -> "0402"
    return raw.split("/")[1]


def parse_inductance(raw):
    # "10nH \xb12%" -> (10.0, 2.0, "%"); "1.1nH \xb10.1nH" -> (1.1, 0.1, "nH")
    m = INDUCTANCE_RE.match(raw.strip())
    if not m:
        raise ValueError(f"could not parse inductance from {raw!r}")
    return float(m.group(1)), float(m.group(2)), m.group(3)


def format_inductance(nh_value):
    # Returns (id_short, display_str) for a value already in nH, e.g.
    # 10.0 -> ("10n0", "10nH"), 6.2 -> ("6n2", "6.2nH"). Always keeps a
    # digit after the unit letter, matching NAMING.md's own "10n0"
    # example (unlike the older cap_* formatters, which drop it for
    # whole values).
    formatted = f"{nh_value:.1f}"
    int_str, dec_str = formatted.split(".")
    id_short = f"{int_str}n{dec_str}"

    if nh_value == int(nh_value):
        disp_val = str(int(nh_value))
    else:
        disp_val = f"{nh_value:.1f}".rstrip("0").rstrip(".")
    display_str = f"{disp_val}nH"

    return id_short, display_str


def parse_current(raw):
    # "500mA" -> 0.5, "1,000mA" -> 1.0 (amps)
    m = CURRENT_RE.match(raw.strip().replace(",", ""))
    if not m:
        raise ValueError(f"could not parse current from {raw!r}")
    return float(m.group(1)) / 1000


def format_current(amps):
    # 0.5 -> "0A5", 1.0 -> "1A0" - same "." -> unit-letter substitution as
    # import_ind_power_vishay_ihlp.py, matching NAMING.md's own inductor
    # example ("1A2").
    s = f"{amps:.1f}"
    int_part, dec_part = s.split(".")
    return f"{int_part}A{dec_part}"


def format_srf(raw):
    # "3,400MHz" -> "3400MHz" (drop the thousands comma, keep MHz - values
    # top out at 10,000MHz/10GHz, not worth a GHz unit branch for that).
    m = SRF_RE.match(raw.strip().replace(",", ""))
    if not m:
        raise ValueError(f"could not parse SRF from {raw!r}")
    return f"{m.group(1)}MHz"


def load_inductors(csv_path):
    count = 0
    skipped_footprint = {}
    inductors = []
    seen_ids = {}

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            part_number = row["Part Number"]
            case = parse_case(row["Size code in mm(inch)"])

            if case not in footprint_mapping:
                skipped_footprint[case] = skipped_footprint.get(case, 0) + 1
                continue

            lib_nickname, footprint_name = footprint_mapping[case]
            footprint = f"{lib_nickname}:{footprint_name}"

            nh_value, tol_value, tol_unit = parse_inductance(row["Inductance"])
            value_id, value_disp = format_inductance(nh_value)

            if tol_unit == "%":
                tol_token = (str(int(tol_value)) if tol_value == int(tol_value)
                             else str(tol_value))
                tol_disp = f"\xb1{tol_token}%"
            else:
                tol_id_short, tol_id_disp = format_inductance(tol_value)
                tol_token = tol_id_short
                tol_disp = f"\xb1{tol_id_disp}"

            irated = parse_current(row["Rated Current (Temperature Rise) / Max."])
            current_str = format_current(irated)
            dcr = row["DC Resistance(max.)"].strip()
            srf = format_srf(row["Self-resonant frequency(min.)"])
            max_temp = row["Maximum operating temperature"].strip()
            series = row["Series"].split("_")[0]

            id_str = f"L{case}_{value_id}_{tol_token}_{current_str}"
            if id_str in seen_ids:
                print(f"WARNING: duplicate id '{id_str}' - "
                      f"{part_number} collides with {seen_ids[id_str]}, "
                      f"skipping")
                continue
            seen_ids[id_str] = part_number

            count += 1
            current_disp = f"{irated:.2f}".rstrip("0").rstrip(".") + "A"
            description = (f"{value_disp}, {tol_disp}, {current_disp}, "
                            f"DCR {dcr}, SRF {srf}, EIA {case}, {series}")

            print(f"{count} {id_str} {part_number}, {case}, {value_disp}, "
                  f"{tol_disp}, {current_str}, DCR {dcr}, SRF {srf}")

            inductor = (id_str, value_disp, footprint, "Device:L",
                        value_disp, tol_disp, current_str, dcr, srf,
                        max_temp, series, description, part_number,
                        MANUFACTURER)
            inductors.append(inductor)

    if skipped_footprint:
        total_skipped = sum(skipped_footprint.values())
        print(f"\nSkipped {total_skipped} rows with no matching footprint:")
        for code, n in sorted(skipped_footprint.items(), key=lambda x: -x[1]):
            print(f"  case {code}: {n} parts")

    return inductors


def write_database(db_path, table, inductors):
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
        Inductance TEXT,
        Tolerance TEXT,
        "Rated Current" TEXT,
        DCR TEXT,
        SRF TEXT,
        "Max Op Temp" TEXT,
        Series TEXT,
        Description TEXT,
        "Part Number" TEXT,
        Manufacturer TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, Inductance, Tolerance,
         "Rated Current", DCR, SRF, "Max Op Temp", Series, Description,
         "Part Number", Manufacturer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, inductors)

    conn.commit()
    conn.close()


def build_field_defs():
    # RF-inductor trim of the ind_power_vishay_ihlp style - see header
    # comment for why Saturation Current is dropped and Max Op Temp
    # replaces the Temp Min/Max pair.
    return [
        {"column": "Inductance", "name": "Inductance",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Tolerance", "name": "Tolerance",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        {"column": "Rated Current", "name": "Rated Current",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "DCR", "name": "DCR",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "SRF", "name": "SRF",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Max Op Temp", "name": "Max Op Temp",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Series", "name": "Series",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Manufacturer", "name": "Manufacturer",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Part Number", "name": "Part Number",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Value", "name": "Value",
         "visible_on_add": True, "visible_in_chooser": True},
    ]


def write_kicad_dbl(dbl_path, db_path, table):
    content = {
        "meta": {"version": 0},
        "name": "Murata LQG High-Q RF Multilayer Chip Inductors",
        "description": ("Murata LQG15H/LQG18H High-Q RF/Microwave "
                         "Multilayer Chip Inductor Library"),
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
                "name": "LQG",
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
        description="Import Murata LQG-family high-Q RF multilayer chip "
                     "inductor CSV export(s) into a KiCad "
                     "database-library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s). Multiple "
                              "values are merged into one library.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. ind_rfmw_murata_lqg. Must "
                              "match the corresponding .kicad_dbl 'table' "
                              "field.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def main():
    args = parse_args()
    inductors = []
    for csv_path in args.csv:
        inductors.extend(load_inductors(csv_path))
    write_database(args.db, args.table, inductors)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(inductors)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
