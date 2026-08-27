# Imports Panasonic ERJ-T14 "Anti-Pulse High Power" thick-film chip
# resistor data (Panasonic's own product-table CSV export) into a KiCad
# database-library SQLite file.
#
# This is the first RESISTOR database library in the repo, so there was no
# existing res_* field-style precedent to copy the way cap_xy_murata_ga3
# copies cap_mlcc_murata_GRM. The style below extrapolates the established
# ceramic/MLCC capacitor convention (non-polarized part, Device:<part>
# symbol, Value shown normally, no ESR/Endurance-style fields) to
# resistors: Symbol is Device:R, and Resistance/Power/Tolerance/TCR stand
# in for Capacitance/Voltage/Dielectric. TCR is kept as its own
# visible-in-chooser field (not folded into the id) because it's a real,
# row-varying electrical spec in this dataset: the sub-10 ohm values
# (1.0-3.9R, 15 of 100 rows) carry a wider "-100 to +600 ppm/K" TCR than
# the "+/-200 ppm/K" used from 10R up - typical for thick-film chip
# resistors, where low-ohm values are harder to trim tightly. It doesn't
# need to be part of the id since every resistance value in this dataset
# is already unique across the whole series.
#
# Id format follows NAMING.md section 4's resistor pattern exactly:
# R<case>_<value>_<tolerance>_<power>, e.g. R1210_10R0_5_500mW. Resistance
# values use the same IEC-60062 unit-as-decimal-point notation as the
# capacitor imports (10R0 = 10.0ohm, 4k7 = 4.7kohm, 1M0 = 1.0Mohm).
#
# All 100 rows in the source CSV share one EIA 1210 case (3.2 x 2.5mm),
# one power rating (0.5W) and one tolerance (5%) - only the resistance
# value and TCR band vary - and all 100 part numbers are already unique,
# so the seen_ids dedup path is exercised only defensively here.
#
# Footprint: EIA 1210 = 3.2mm x 2.5mm is an exact match for KiCad's
# standard Resistor_SMD:R_1210_3225Metric ("3225" = 3.2mm x 2.5mm in
# KiCad's metric-code naming) - no custom footprint needed.
#
# Despite the library/CSV being named "erj14t", Panasonic's own part
# numbers use the prefix "ERJT14" (i.e. this is the ERJ-T14 series) - the
# 14t naming is just the vendor's series stripped of the hyphen.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "Panasonic"

# EIA case code (parsed out of the "3.2 x 2.5 (EIA:1210)" column) ->
# (footprint library nickname, footprint name). All standard KiCad
# footprints - no custom footprint needed for this dataset.
footprint_mapping = {
    "1210": ("Resistor_SMD", "R_1210_3225Metric"),
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CASE_RE = re.compile(r"EIA:(\d+)")


def parse_case(raw):
    # "3.2 x 2.5 (EIA:1210)" -> "1210"
    m = CASE_RE.search(raw)
    if not m:
        raise ValueError(f"could not parse EIA case code from {raw!r}")
    return m.group(1)


def format_resistance(ohms):
    # Returns (id_short, display_str), e.g. 10.0 -> ("10R0", "10Ω"),
    # 4700.0 -> ("4k7", "4.7kΩ"), 1000000.0 -> ("1M0", "1MΩ").
    if ohms < 1000:
        unit_id, unit_disp, factor = "R", "Ω", 1
    elif ohms < 1e6:
        unit_id, unit_disp, factor = "k", "kΩ", 1e3
    else:
        unit_id, unit_disp, factor = "M", "MΩ", 1e6

    mantissa = ohms / factor

    # id form: always exactly one decimal digit, "." replaced by the unit
    # letter (IEC-60062 style, matching the existing capacitor imports).
    int_part, dec_part = f"{mantissa:.1f}".split(".")
    id_short = f"{int_part}{unit_id}{dec_part}"

    # display form: human-readable, trailing ".0"/".00" trimmed.
    if mantissa == int(mantissa):
        disp_val = str(int(mantissa))
    else:
        disp_val = f"{mantissa:.2f}".rstrip("0").rstrip(".")
    display_str = f"{disp_val}{unit_disp}"

    return id_short, display_str


def format_power(watts):
    # 0.5 -> "500mW", 1.0 -> "1W", 0.0625 -> "62.5mW"
    mw = watts * 1000
    if mw < 1000:
        if mw == int(mw):
            return f"{int(mw)}mW"
        return f"{mw:.1f}mW"
    w = watts
    if w == int(w):
        return f"{int(w)}W"
    return f"{w:.2f}W".rstrip("0").rstrip(".")


def format_tcr(raw):
    # "±200" -> "±200ppm/K", "-100 to +600" -> "-100/+600ppm/K"
    raw = raw.strip()
    if raw.startswith("±"):
        return f"{raw}ppm/K"
    return f"{raw.replace(' to ', '/')}ppm/K"


def load_resistors(csv_path):
    count = 0
    skipped_footprint = {}
    resistors = []
    seen_ids = {}

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        # Index by position rather than typing the header strings' Greek/
        # exponent characters (Omega, multiplication sign, superscript
        # minus/six) verbatim - avoids any encoding mismatch with the
        # actual CSV header text.
        fields = reader.fieldnames
        # ['Parts no', 'Product', 'Product status', 'Catalog / Datasheet',
        #  'Series/Type', 'Power Rating (W)',
        #  'Chip Size (LxW(EIA)) (mm)', 'Resistance Values (Ohm)',
        #  'Resistance Tolerance (%)', 'Packaging', 'T.C.R (x10^-6/K)']
        F_PART, F_POWER, F_CASE, F_RES, F_TOL, F_TCR = (
            fields[0], fields[5], fields[6], fields[7], fields[8], fields[10])

        for row in reader:
            part_number = row[F_PART]
            case = parse_case(row[F_CASE])

            if case not in footprint_mapping:
                skipped_footprint[case] = skipped_footprint.get(case, 0) + 1
                continue

            lib_nickname, footprint_name = footprint_mapping[case]
            footprint = f"{lib_nickname}:{footprint_name}"

            ohms = float(row[F_RES])
            value_id, value_disp = format_resistance(ohms)
            power_str = format_power(float(row[F_POWER]))
            tolerance = row[F_TOL].strip()
            tcr_str = format_tcr(row[F_TCR])

            count += 1
            # R1210_10R0_5_500mW
            id_str = f"R{case}_{value_id}_{tolerance}_{power_str}"
            if id_str in seen_ids:
                print(f"WARNING: duplicate id '{id_str}' - "
                      f"{part_number} collides with {seen_ids[id_str]}, skipping")
                continue
            seen_ids[id_str] = part_number

            description = (f"{value_disp}, {tolerance}%, {power_str}, "
                            f"TCR {tcr_str}, EIA {case}")

            print(f"{count} {id_str} {part_number}, {case}, {value_disp}, "
                  f"{power_str}, tol {tolerance}%, TCR {tcr_str}")

            resistor = (id_str, value_disp, footprint, "Device:R",
                        value_disp, power_str, f"{tolerance}%", tcr_str,
                        description, part_number, MANUFACTURER)
            resistors.append(resistor)

    if skipped_footprint:
        total_skipped = sum(skipped_footprint.values())
        print(f"\nSkipped {total_skipped} rows with no matching footprint:")
        for code, n in sorted(skipped_footprint.items(), key=lambda x: -x[1]):
            print(f"  case {code}: {n} parts")

    return resistors


def write_database(db_path, table, resistors):
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
        Resistance TEXT,
        Power TEXT,
        Tolerance TEXT,
        TCR TEXT,
        Description TEXT,
        "Part Number" TEXT,
        Manufacturer TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, Resistance, Power, Tolerance, TCR,
         Description, "Part Number", Manufacturer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, resistors)

    conn.commit()
    conn.close()


def build_field_defs():
    # Ceramic/MLCC-style extrapolation for a non-polarized chip resistor:
    # Value shown normally on the schematic (no ESR/Endurance-style
    # fields - those belong to the polarized-electrolytic capacitor
    # style, not resistors). Power and Tolerance show on add (no label,
    # like Voltage/Dielectric do for MLCCs); TCR is a genuine per-row
    # electrical distinction in this dataset so it's surfaced in the
    # chooser rather than only in Description.
    return [
        {"column": "Resistance", "name": "Resistance",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Power", "name": "Power",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        {"column": "Tolerance", "name": "Tolerance",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        {"column": "TCR", "name": "T.C.R",
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
        "name": "Panasonic ERJ-T14 Anti-Pulse High Power Chip Resistors",
        "description": ("Panasonic ERJ-T14 Anti-Pulse High Power Thick "
                         "Film Chip Resistor Library"),
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
                "name": "ERJ-T14",
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
        description="Import a Panasonic ERJ-T14 anti-pulse high-power "
                     "chip resistor CSV export into a KiCad database-"
                     "library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s). Multiple "
                              "values are merged into one library.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. res_pulse_panasonic_erj14t. "
                              "Must match the corresponding .kicad_dbl "
                              "'table' field.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def main():
    args = parse_args()
    resistors = []
    for csv_path in args.csv:
        resistors.extend(load_resistors(csv_path))
    write_database(args.db, args.table, resistors)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(resistors)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
