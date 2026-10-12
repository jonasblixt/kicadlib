# Imports Vishay CRCW e3 standard thick-film chip resistor data into a
# KiCad database-library SQLite file.
#
# Source data (data/res_chip_vishay_crcw.csv) was itself derived from the
# repo's legacy hand-authored data/vishay_resistors.lib (3,156 DEF blocks,
# one per part) - see the conversion history in this session. That first
# pass only carried Resistance/Tolerance/Power (parsed from the legacy
# lib's free-text "Description" field, e.g. "1, ±1%, 0.063W"); it did NOT
# carry T.C.R., because the legacy Description field never recorded it.
#
# The Vishay/Draloric part number itself does encode TCR, though. Per the
# "PART NUMBER AND PRODUCT DESCRIPTION" table (CRCW-HP e3 datasheet, doc
# 20043, page 3 - the CRCW-HP e3 datasheet was on hand; the base CRCW e3
# uses the identical global Vishay/Draloric numbering scheme, just without
# the trailing "HP" special-code suffix), the part number breaks down as:
#   CRCW<size:4><value:4><tolerance:1><tcr:1><packaging:rest>
# with tolerance codes D=±0.5%, F=±1%, J=±5%, Z=jumper, and TCR codes
# K=±100ppm/K, N=±200ppm/K, 0=jumper. Decoding every part number in the
# CSV this way confirmed: tolerance is F (±1%) for all 3,156 parts
# (agreeing with the legacy Description field), but TCR is K (±100ppm/K)
# for all but 4 parts, which are N (±200ppm/K) - see the CSV's own
# "T.C.R (ppm/K)" column, added in the same pass that decoded tolerance
# from the part number instead of trusting the legacy Description text.
#
# Those 4 N-coded parts share an otherwise-identical case/value/tolerance/
# power with an existing K-coded part (e.g. CRCW08051R00FKED vs
# CRCW08051R00FNEA - both 0805, 1R, ±1%, 0.125W). The legacy .lib
# resolved this collision by blindly suffixing the second symbol's NAME
# with "_2" (R0805_1R vs R0805_1R_2) without recording *why* they
# differed - which is exactly the kind of silent, undocumented collision
# the id-building step in this repo's import convention exists to avoid.
# Per Jonas's instruction, TCR is folded into the id ONLY for the rows
# where it's actually needed to keep ids unique - i.e. both members of a
# colliding (case, value, tolerance, power) group get a "_<tcr>ppm"
# suffix, and every other row (the other 3,148 - 4 = 3,148 K-coded rows
# with no colliding N-coded sibling) keeps the plain
# R<case>_<value>_<tolerance>_<power> id from NAMING.md section 4. Both
# members of a colliding pair get the suffix (not just the second) so a
# reader isn't left wondering why one sibling has an unmarked TCR.
#
# Field style, symbol (Device:R) and column shape mirror the repo's other
# resistor library, res_pulse_panasonic_erj14t (see that importer's
# header for the ceramic/MLCC-style extrapolation this was based on).
#
# Footprints: all 4 EIA cases (0402/0603/0805/1206) are exact matches for
# KiCad's standard Resistor_SMD.pretty - no custom footprint needed.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "Vishay"

# EIA case code -> (footprint library nickname, footprint name). All
# standard KiCad footprints.
footprint_mapping = {
    "0402": ("Resistor_SMD", "R_0402_1005Metric"),
    "0603": ("Resistor_SMD", "R_0603_1608Metric"),
    "0805": ("Resistor_SMD", "R_0805_2012Metric"),
    "1206": ("Resistor_SMD", "R_1206_3216Metric"),
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def format_resistance(ohms):
    # Returns (id_short, display_str), e.g. 10.0 -> ("10R0", "10Ω"),
    # 4700.0 -> ("4k7", "4.7kΩ"), 1000000.0 -> ("1M0", "1MΩ"). Same
    # IEC-60062-style formatter as import_res_pulse_panasonic_erj14t.py,
    # for consistency across the repo's resistor libraries.
    if ohms < 1000:
        unit_id, unit_disp, factor = "R", "Ω", 1
    elif ohms < 1e6:
        unit_id, unit_disp, factor = "k", "kΩ", 1e3
    else:
        unit_id, unit_disp, factor = "M", "MΩ", 1e6

    mantissa = ohms / factor

    # id form: up to 2 decimal digits, "." replaced by the unit letter.
    # This dataset's E96 values need 2 decimal digits of precision, unlike
    # the 1-decimal ERJ-T14 dataset - e.g. 4.99 ohm must stay "4R99", not
    # round to "5R0" - so keep 2 digits, trimming trailing zeros but
    # always leaving at least one digit after the unit letter.
    dec_str = f"{mantissa:.2f}".split(".")[1].rstrip("0")
    if not dec_str:
        dec_str = "0"
    int_str = f"{mantissa:.2f}".split(".")[0]
    id_short = f"{int_str}{unit_id}{dec_str}"

    if mantissa == int(mantissa):
        disp_val = str(int(mantissa))
    else:
        disp_val = f"{mantissa:.2f}".rstrip("0").rstrip(".")
    display_str = f"{disp_val}{unit_disp}"

    return id_short, display_str


def format_power(watts):
    # 0.5 -> "500mW", 1.0 -> "1W", 0.063 -> "63mW"
    mw = watts * 1000
    if mw < 1000:
        if mw == round(mw):
            return f"{round(mw)}mW"
        return f"{mw:.1f}mW"
    w = watts
    if w == int(w):
        return f"{int(w)}W"
    return f"{w:.2f}W".rstrip("0").rstrip(".")


def format_tcr(pn_tcr):
    # CSV's "T.C.R (ppm/K)" column is already "±100" / "±200" (decoded
    # from the part number's TCR letter, see header comment) - just add
    # the unit.
    return f"{pn_tcr}ppm/K"


def load_resistors(csv_paths):
    raw_rows = []
    for csv_path in csv_paths:
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            raw_rows.extend(csv.DictReader(csvfile))

    # Pass 1: compute the base id (without TCR) for every row, and figure
    # out which base ids are shared by rows with different TCR - those
    # are the only ones that need the TCR folded into the id.
    prepared = []
    skipped_footprint = {}
    for row in raw_rows:
        case = row["EIA Case"]
        if case not in footprint_mapping:
            skipped_footprint[case] = skipped_footprint.get(case, 0) + 1
            continue

        ohms = float(row["Resistance (Ohm)"])
        value_id, value_disp = format_resistance(ohms)
        tolerance = row["Resistance Tolerance (%)"].strip()
        power_str = format_power(float(row["Power Rating (W)"]))
        tcr_pn = row["T.C.R (ppm/K)"].strip()
        tcr_str = format_tcr(tcr_pn)
        part_number = row["Part Number"]

        base_id = f"R{case}_{value_id}_{tolerance}_{power_str}"
        prepared.append({
            "base_id": base_id, "case": case, "value_disp": value_disp,
            "power_str": power_str, "tolerance": tolerance,
            "tcr_pn": tcr_pn, "tcr_str": tcr_str,
            "part_number": part_number,
        })

    base_id_tcrs = {}
    for r in prepared:
        base_id_tcrs.setdefault(r["base_id"], set()).add(r["tcr_pn"])
    needs_tcr_suffix = {bid for bid, tcrs in base_id_tcrs.items() if len(tcrs) > 1}

    count = 0
    resistors = []
    seen_ids = {}
    tcr_disambiguated = 0
    for r in prepared:
        if r["base_id"] in needs_tcr_suffix:
            ppm = r["tcr_pn"].lstrip("±")
            id_str = f"{r['base_id']}_{ppm}ppm"
            tcr_disambiguated += 1
        else:
            id_str = r["base_id"]

        if id_str in seen_ids:
            print(f"WARNING: duplicate id '{id_str}' - "
                  f"{r['part_number']} collides with {seen_ids[id_str]}, skipping")
            continue
        seen_ids[id_str] = r["part_number"]

        lib_nickname, footprint_name = footprint_mapping[r["case"]]
        footprint = f"{lib_nickname}:{footprint_name}"

        count += 1
        description = (f"{r['value_disp']}, {r['tolerance']}%, "
                        f"{r['power_str']}, TCR {r['tcr_str']}, "
                        f"EIA {r['case']}")

        resistor = (id_str, r["value_disp"], footprint, "Device:R",
                    r["value_disp"], r["power_str"], f"{r['tolerance']}%",
                    r["tcr_str"], description, r["part_number"], MANUFACTURER)
        resistors.append(resistor)

    print(f"\n{tcr_disambiguated} parts needed a TCR suffix to stay unique "
          f"({len(needs_tcr_suffix)} colliding case/value/tolerance/power "
          f"group(s))")

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
    # Same shape as import_res_pulse_panasonic_erj14t.py's resistor style
    # (ceramic/MLCC-style extrapolation: Value shown normally, no
    # ESR/Endurance-style fields, TCR surfaced in the chooser since it's
    # a genuine per-row electrical distinction here too).
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
        "name": "Vishay CRCW e3 Chip Resistors",
        "description": "Vishay CRCW e3 Standard Thick Film Chip Resistor Library",
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
                "name": "CRCW",
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
        description="Import a Vishay CRCW e3 chip resistor CSV (derived "
                     "from the legacy vishay_resistors.lib, with "
                     "Tolerance/TCR decoded from the part number) into a "
                     "KiCad database-library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s). Multiple "
                              "values are merged into one library.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. res_chip_vishay_crcw. Must "
                              "match the corresponding .kicad_dbl 'table' "
                              "field.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def main():
    args = parse_args()
    resistors = load_resistors(args.csv)
    write_database(args.db, args.table, resistors)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(resistors)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
