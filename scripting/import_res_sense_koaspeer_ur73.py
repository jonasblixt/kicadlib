# Imports KOA Speer UR73 ultra-low-ohm current-sense thick-film chip
# resistor data (a DigiKey product-table CSV export) into a KiCad
# database-library SQLite file.
#
# UR73 is a sibling series to res_sense_koaspeer_sr73 from the same
# vendor page family (SR73.pdf / UR73.pdf share the same ordering-info
# layout) - split into its own library rather than folded into SR73's
# because it's a genuinely distinct product line: UR73 only goes from
# 10 mOhm to 100 mOhm (vs SR73's 30 mOhm-10R), has a narrower tolerance
# selection (only 1% is stocked at DigiKey, vs SR73's 0.5/1/5%), and a
# narrower operating range (-55 to 125C vs SR73's -55 to 150C) - so it's
# a different tradeoff (more resolution at the very low end) rather than
# an overlapping SKU range. Same field style and id scheme as SR73 for
# consistency, reusing its format_resistance()/format_power()/format_tcr()
# verbatim.
#
# Part numbers here mix a plain size-code prefix (e.g. "UR732BTTD...")
# with a "D"-infixed one (e.g. "UR73D2BTTD..."). Checked whether this is
# a real electrical/mechanical distinction worth encoding in the id (the
# same question res_sense_koaspeer_sr73 had to answer for its D/E
# packaging-code pairs) by diffing (case, resistance, tolerance, power)
# across all 46 rows: zero collisions - KOA only offers the "D"-infixed
# construction (wider/lower-resistance terminal geometry, per the height
# column jumping noticeably at the same case+value boundary) for the
# lowest resistance values in each case, never as a second competing SKU
# at a value the plain part also covers. So it needs no id suffix here,
# but the seen_ids dedup path is still live as a safety net in case a
# future CSV addition (e.g. a wider DigiKey pull) does introduce a real
# collision.
#
# Id format follows NAMING.md's resistor pattern: R<case>_<value>_
# <tolerance>_<power>, same IEC-60062 notation as res_sense_koaspeer_sr73
# (down to 0R01 for the 10 mOhm parts here - verified no precision
# collisions across all 16 distinct resistance values with the 3-decimal
# sub-1-ohm formatting SR73 established).
#
# All 6 case sizes present (0402/0603/0805/1206/2010/2512) are standard
# EIA metric cases with an exact dimensional match in KiCad's own
# Resistor_SMD.pretty - no custom footprint needed.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "KOA Speer Electronics"

# EIA case code (from the "Package / Case" column, e.g.
# "1206 (3216 Metric)" -> "1206") -> (footprint library nickname,
# footprint name). All standard KiCad footprints.
footprint_mapping = {
    "0402": ("Resistor_SMD", "R_0402_1005Metric"),
    "0603": ("Resistor_SMD", "R_0603_1608Metric"),
    "0805": ("Resistor_SMD", "R_0805_2012Metric"),
    "1206": ("Resistor_SMD", "R_1206_3216Metric"),
    "2010": ("Resistor_SMD", "R_2010_5025Metric"),
    "2512": ("Resistor_SMD", "R_2512_6332Metric"),
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RESISTANCE_RE = re.compile(r"^([\d.]+)\s*(m?Ohms)$")
TCR_RE = re.compile(r"^(\xb1?\d+)ppm/\xb0C$")


def parse_case(raw):
    # "1206 (3216 Metric)" -> "1206"
    return raw.split(" ")[0]


def parse_ohms(raw):
    # "10 mOhms" -> 0.01, "100 mOhms" -> 0.1
    m = RESISTANCE_RE.match(raw.strip())
    if not m:
        raise ValueError(f"could not parse resistance from {raw!r}")
    value, unit = float(m.group(1)), m.group(2)
    return value / 1000 if unit == "mOhms" else value


def format_resistance(ohms):
    # Returns (id_short, display_str), e.g. 0.01 -> ("0R01", "0.01Ω"),
    # 0.1 -> ("0R1", "0.1Ω"). Same formatter as
    # import_res_sense_koaspeer_sr73.py (3 decimal digits below 1 ohm -
    # needed there for E96 precision, kept here for consistency even
    # though this dataset's values are mostly 2-sig-fig).
    if ohms < 1000:
        unit_id, unit_disp, factor = "R", "Ω", 1
    elif ohms < 1e6:
        unit_id, unit_disp, factor = "k", "kΩ", 1e3
    else:
        unit_id, unit_disp, factor = "M", "MΩ", 1e6

    mantissa = ohms / factor
    decimals = 3 if mantissa < 1 else 2
    formatted = f"{mantissa:.{decimals}f}"
    int_str, dec_str = formatted.split(".")
    dec_str = dec_str.rstrip("0") or "0"
    id_short = f"{int_str}{unit_id}{dec_str}"

    if mantissa == int(mantissa):
        disp_val = str(int(mantissa))
    else:
        disp_val = f"{mantissa:.3f}".rstrip("0").rstrip(".")
    display_str = f"{disp_val}{unit_disp}"

    return id_short, display_str


def parse_power(raw):
    # "0.333W, 1/3W" -> 0.333, "1W" -> 1.0 (first token is always the
    # decimal form; ignore the trailing fraction form entirely).
    first = raw.split(",")[0].strip().rstrip("W")
    return float(first)


def format_power(watts):
    # 0.5 -> "500mW", 1.0 -> "1W", 0.125 -> "125mW"
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
    # "\xb1100ppm/\xb0C" -> "\xb1100ppm/K"
    m = TCR_RE.match(raw.strip())
    if not m:
        raise ValueError(f"could not parse TCR from {raw!r}")
    return f"{m.group(1)}ppm/K"


def load_resistors(csv_path):
    count = 0
    skipped_footprint = {}
    resistors = []
    seen_ids = {}

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            part_number = row["Mfr Part #"]
            case = parse_case(row["Package / Case"])

            if case not in footprint_mapping:
                skipped_footprint[case] = skipped_footprint.get(case, 0) + 1
                continue

            lib_nickname, footprint_name = footprint_mapping[case]
            footprint = f"{lib_nickname}:{footprint_name}"

            ohms = parse_ohms(row["Resistance"])
            value_id, value_disp = format_resistance(ohms)
            power_str = format_power(parse_power(row["Power (Watts)"]))
            tolerance = row["Tolerance"].strip().lstrip("\xb1").rstrip("%")
            tcr_str = format_tcr(row["Temperature Coefficient"])

            id_str = f"R{case}_{value_id}_{tolerance}_{power_str}"
            if id_str in seen_ids:
                print(f"WARNING: duplicate id '{id_str}' - "
                      f"{part_number} collides with {seen_ids[id_str]}, "
                      f"skipping")
                continue
            seen_ids[id_str] = part_number

            count += 1
            description = (f"{value_disp}, {tolerance}%, {power_str}, "
                            f"TCR {tcr_str}, EIA {case}, current sense")

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
    # Same res_sense field style as res_sense_koaspeer_sr73: Device:R,
    # Value shown normally, Power/Tolerance visible-on-add without a
    # label, TCR broken out as its own visible-in-chooser field.
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
        "name": "KOA Speer UR73 Ultra-Low-Ohm Current Sense Chip Resistors",
        "description": ("KOA Speer UR73 Ultra-Low-Ohm (10-100 mOhm) "
                         "Current Sense Thick Film Chip Resistor Library"),
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
                "name": "UR73",
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
        description="Import a KOA Speer UR73 ultra-low-ohm current-sense "
                     "chip resistor CSV export into a KiCad "
                     "database-library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s). Multiple "
                              "values are merged into one library.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. res_sense_koaspeer_ur73. "
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
