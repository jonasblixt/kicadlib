# Imports KOA Speer SR73 automotive-grade current-sense thick-film chip
# resistor data (a DigiKey product-table CSV export) into a KiCad
# database-library SQLite file.
#
# NAMING.md categorizes this under res_sense_ ("Current-sense / shunt
# (low-ohm, 4-terminal Kelvin)") alongside Vishay WSL/Susumu KRL/Bourns.
# SR73 is 2-terminal, not 4-terminal Kelvin (Number of Terminations = 2
# for every row) - it's still a genuine low-ohm current-sense part
# (KOA's own "Features" column says "Current Sense" on every row, values
# run 30mOhm-10R), just the simpler/cheaper 2-terminal style rather than
# a true Kelvin-sense part. Filed under res_sense_ anyway since that's
# what the part actually is, not res_chip_, with this note here so a
# future reader isn't confused when they don't find 4 pads.
#
# Field style follows the res_pulse_panasonic_erj14t / res_chip_vishay_crcw
# precedent: Device:R symbol, Resistance/Power/Tolerance/TCR/Manufacturer/
# Part Number/Value fields, TCR broken out as its own visible-in-chooser
# field.
#
# Id format follows NAMING.md's resistor pattern: R<case>_<value>_
# <tolerance>_<power>. Resistance uses IEC-60062 unit-as-decimal-point
# notation (10R0 = 10.0 ohm, 0R649 = 0.649 ohm) via format_resistance()
# below - note this needed 3 decimal digits for the sub-1-ohm range (not
# CRCW's 2), since this dataset's E96 sense values are dense enough down
# there that 2 digits collide (150/154/158 mOhm would all round to the
# same "0R15" at 2-digit precision - verified against all 107 distinct
# resistance values in the source CSV with 3 digits, zero collisions).
#
# Duplicate ids: 7 of 210 rows collide on (case, value, tolerance, power)
# - all 7 are "...TTD..." vs "...TTE..." part-number pairs, e.g.
# SR732BTTD1R00F / SR732BTTE1R00F. Fetched KOA's own SR73.pdf datasheet
# (linked from every row's Datasheet column) to check whether this was a
# real electrical/mechanical distinction worth encoding in the id (the
# POSCAP-style pitfall this skill warns about) before assuming it's safe
# to skip - it isn't: the datasheet's ordering-information section
# defines D and E as tape-and-reel packaging format codes ("TD: 4mm pitch
# punch paper" vs "TE: 4mm pitch plastic embossed"), not a package-height
# or electrical variant, even though DigiKey's own "Height - Seated
# (Max)" column disagrees by 0.10mm between the two rows of each pair -
# that looks like noise/inconsistency in DigiKey's own scraped data
# rather than a real physical difference, given the datasheet defines no
# such distinction. So these are treated as ordinary packaging-SKU
# duplicates: kept-first, skipped-and-warned, same as any other packaging
# suffix collision - not disambiguated in the id.
#
# All 7 case sizes present (0402/0603/0805/1206/1210/2010/2512) are
# standard EIA metric cases with an exact dimensional match in KiCad's
# own Resistor_SMD.pretty - no custom footprint needed.
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
    "1210": ("Resistor_SMD", "R_1210_3225Metric"),
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
    # "100 mOhms" -> 0.1, "1 Ohms" -> 1.0, "1.18 Ohms" -> 1.18
    m = RESISTANCE_RE.match(raw.strip())
    if not m:
        raise ValueError(f"could not parse resistance from {raw!r}")
    value, unit = float(m.group(1)), m.group(2)
    return value / 1000 if unit == "mOhms" else value


def format_resistance(ohms):
    # Returns (id_short, display_str), e.g. 0.649 -> ("0R649", "0.649Ω"),
    # 10.0 -> ("10R0", "10Ω"). Same IEC-60062-style scheme as the
    # other res_* imports, but with 3 decimal digits below 1 ohm instead
    # of CRCW's 2 - see header comment for why.
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
    # 0.5 -> "500mW", 1.0 -> "1W", 0.167 -> "167mW"
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
    # "\xb1100ppm/\xb0C" -> "\xb1100ppm/K" (ppm/\xb0C and ppm/K are the
    # same magnitude for a coefficient - just the unit-name convention
    # already used by the other res_* imports).
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
                      f"skipping (packaging-format SKU variant, see "
                      f"header comment)")
                continue
            seen_ids[id_str] = part_number

            count += 1
            description = (f"{value_disp}, {tolerance}%, {power_str}, "
                            f"TCR {tcr_str}, EIA {case}, AEC-Q200 "
                            f"automotive, current sense")

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
    # Ceramic/MLCC-style extrapolation for a non-polarized chip resistor
    # (same as res_pulse_panasonic_erj14t / res_chip_vishay_crcw): Value
    # shown normally, Power/Tolerance visible-on-add without a label, TCR
    # broken out as its own visible-in-chooser field since it's a genuine
    # row-varying spec (low-ohm values carry a wider TCR band).
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
        "name": "KOA Speer SR73 Current Sense Chip Resistors",
        "description": ("KOA Speer SR73 AEC-Q200 Automotive Current "
                         "Sense Thick Film Chip Resistor Library"),
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
                "name": "SR73",
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
        description="Import a KOA Speer SR73 current-sense chip resistor "
                     "CSV export into a KiCad database-library SQLite "
                     "file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s). Multiple "
                              "values are merged into one library.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. res_sense_koaspeer_sr73. "
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
