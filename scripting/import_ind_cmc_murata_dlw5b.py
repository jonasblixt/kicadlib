# Imports Murata DLW5B-series chip common-mode choke data (Murata's own
# product-table CSV export, split across two files by sub-series) into a
# KiCad database-library SQLite file.
#
# This is a genuine common-mode choke per NAMING.md's `cmc` inductor
# subtype (two coupled windings, 4 terminals) - unlike the sibling
# ind_choke_murata_lqw library, which despite the similar part-number
# look (LQW vs DLW) is actually a plain 2-terminal ferrite choke. See
# that script's header for the reasoning on why `choke` and `cmc` are
# kept as separate subtype codes.
#
# Two source CSVs (both "5050"/"2020" size, same package/footprint,
# different sub-series):
#   - ind_cmc_murata_dlw5b_1.csv: DLW5BSM* (8 rows) - "Thickness(max.)
#     4.5mm Max." variant.
#   - ind_cmc_murata_dlw5b_2.csv: DLW5BTM* (10 rows, as SQ2/TQ2 voltage-
#     grade pairs - see id-collision note below) - "Thickness(max.)
#     2.5mm" variant.
# Thickness only affects the component's Z-height (and so a 3D model, not
# built here - see footprints/Murata_DLW5B.pretty/DLW5B_5050.kicad_mod's
# generator script for why), not the 2D land pattern, so both sub-series
# share one footprint - per NAMING.md section 5.
#
# FIELD STYLE: this doesn't fit either of the two capacitor field styles
# in references/field_styles.md (this is an inductor, not a capacitor),
# and it also departs from the sibling ind_* inductor scripts'
# Inductance-centric field set: every row's "Common Mode Inductance"
# column is blank in the source data (Murata doesn't publish it for this
# family) while "Common Mode Impedance" at 10MHz/100MHz is fully
# populated and is how these parts are actually spec'd and selected in
# practice - so Impedance @ 100MHz is the headline Value here, with
# Impedance @ 10MHz (a Min. spec, vs. the 100MHz Typ.) as a secondary
# field. Common Mode Impedance @ 1GHz is blank for every row in this
# dataset and is dropped entirely rather than added as an always-empty
# column.
#
# ID COLLISION NOTE: the DLW5BTM rows come in explicit SQ2/TQ2 pairs -
# same impedance, same (or very close) rated current, but a genuinely
# different voltage/temperature grade (50Vdc/85C vs 100Vdc/105C - e.g.
# DLW5BTM101SQ2# and DLW5BTM101TQ2# are both 100R/6A but one is a 50V
# part and the other a 100V part). An id built from just case/impedance/
# current would silently collide on 3 of these 5 pairs (101, 251, 501 -
# same current on both sides; 102 and 142 already differ by current
# alone). Rated Voltage is folded into the id for all rows (not just the
# colliding ones) for consistency - same conditional-vs-uniform tradeoff
# discussed in import_ind_power_vishay_ihlp.py, resolved the other way
# here since voltage is already a meaningful selection criterion for
# every row, not just an edge case. Verified zero id collisions across
# all 18 rows (8 SM + 10 TM).
#
# FOOTPRINT: no official KiCad footprint matches this package (checked
# Inductor_SMD.pretty's common-mode-choke entries - all smaller EIA
# cases: Coilcraft 0603USB/0805USB/1812CAN, Wuerth WE-SL2/WE-SL5).
# footprints/Murata_DL.pretty/DLW5B_5050.kicad_mod is Jonas's own
# imported footprint (custom-shaped pads reproducing Murata's actual
# notched land pattern, plus a matching Murata_DL.3dshapes/
# DLW5B_5050.step 3D model) - it replaces this script's original,
# self-generated rectangular-pad approximation (previously
# footprints/Murata_DLW5B.pretty/DLW5B_5050.kicad_mod, built by
# scripting/gen_dlw5b_footprint.py; both the folder and that generator
# script are gone now that the imported footprint supersedes them).
#
# SYMBOL: Device:Filter_EMI_CommonMode (KiCad's stock "EMI 2-inductor
# common mode filter" symbol) - the closest built-in match for a 4-pin
# common-mode choke. Its default pin-to-winding pairing has NOT been
# cross-checked against Murata's own pin-connection diagram for this
# part; verify before relying on winding polarity/pairing in a design.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "Murata"
FOOTPRINT = "Murata_DL:DLW5B_5050"
SYMBOL = "Device:Filter_EMI_CommonMode"

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
IMPEDANCE_RE = re.compile(r"^([\d,]+)\xce\xa9")
CURRENT_RE = re.compile(r"^([\d.]+)(m?A)$")
VOLTAGE_RE = re.compile(r"^([\d.]+)Vdc$")


def parse_case(raw):
    # "5050/2020" -> "5050"
    return raw.split("/")[0]


def parse_impedance_ohms(raw):
    # "1,000Ω Typ." -> 1000, "190Ω Min." -> 190,
    # "2,800Ω ±40%" -> 2800
    m = re.match(r"^([\d,]+)Ω", raw.strip())
    if not m:
        raise ValueError(f"could not parse impedance from {raw!r}")
    return int(m.group(1).replace(",", ""))


def format_impedance_id(ohms):
    # 1000 -> "1000R" (kept as a plain integer-ohms token, not the k-scaled
    # NAMING.md resistor style, since these values are always whole ohms
    # in the source data and a plain integer reads unambiguously).
    return f"{ohms}R"


def format_impedance_disp(ohms):
    # 1000 -> "1kΩ", 190 -> "190Ω", 2800 -> "2.8kΩ"
    if ohms >= 1000:
        val = ohms / 1000
        s = f"{val:.1f}".rstrip("0").rstrip(".")
        return f"{s}kΩ"
    return f"{ohms}Ω"


def parse_current(raw):
    # "1.5A" -> 1.5, "500mA" -> 0.5 (amps)
    m = CURRENT_RE.match(raw.strip())
    if not m:
        raise ValueError(f"could not parse current from {raw!r}")
    val = float(m.group(1))
    return val / 1000 if m.group(2) == "mA" else val


def format_current_id(amps):
    # 0.5 -> "0A5", 1.5 -> "1A5" - same "." -> unit-letter substitution as
    # the rest of the repo's inductor ids.
    s = f"{amps:.1f}"
    int_part, dec_part = s.split(".")
    return f"{int_part}A{dec_part}"


def format_current_disp(amps):
    s = f"{amps:.2f}".rstrip("0").rstrip(".")
    return f"{s}A"


def parse_voltage(raw):
    # "50Vdc" -> 50
    m = VOLTAGE_RE.match(raw.strip())
    if not m:
        raise ValueError(f"could not parse voltage from {raw!r}")
    v = float(m.group(1))
    return int(v) if v == int(v) else v


def load_inductors(csv_path):
    inductors = []
    seen_ids = {}

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            part_number = row["Part Number"].rstrip("#")
            case = parse_case(row["Size code in mm(inch)"])

            z100_ohms = parse_impedance_ohms(row["Common Mode Impedance (at 100MHz)"])
            z10_raw = row["Common Mode Impedance (at 10MHz)"].strip()

            irated = parse_current(row["Rated Current"])
            current_id = format_current_id(irated)
            current_disp = format_current_disp(irated)

            voltage = parse_voltage(row["Rated Voltage"])
            voltage_str = str(voltage).rstrip("0").rstrip(".") if isinstance(voltage, float) else str(voltage)

            dcr = row["DC Resistance(max.)"].strip()
            max_temp = row["Maximum operating temperature"].strip()
            derating = row["Derating of Rated Current"].strip()
            num_circuit = row["Number of Circuit"].strip()

            m = re.match(r"^(DLW5B[A-Z]{2})", part_number)
            series = m.group(1) if m else "DLW5B"

            id_str = (f"L{case}_{format_impedance_id(z100_ohms)}_"
                      f"{current_id}_{voltage_str}V")
            if id_str in seen_ids:
                print(f"WARNING: duplicate id '{id_str}' - "
                      f"{part_number} collides with {seen_ids[id_str]}, "
                      f"skipping")
                continue
            seen_ids[id_str] = part_number

            value_disp = format_impedance_disp(z100_ohms)
            derating_note = "" if derating == "No" else f", derating {derating.split('/')[0]}"
            description = (f"{value_disp} @100MHz ({z10_raw} @10MHz), "
                            f"{current_disp}, DCR {dcr} Max., {voltage_str}V, "
                            f"{max_temp} Max., EIA {case}, {series}, "
                            f"{num_circuit}-circuit common-mode choke"
                            f"{derating_note}")

            print(f"{len(inductors) + 1} {id_str} {part_number}, "
                  f"{value_disp}@100MHz, {current_disp}, {voltage_str}V")

            inductor = (id_str, value_disp, FOOTPRINT, SYMBOL, value_disp,
                        z10_raw, current_disp, dcr, f"{voltage_str}V",
                        max_temp, series, description, part_number,
                        MANUFACTURER)
            inductors.append(inductor)

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
        "Impedance @100MHz" TEXT,
        "Impedance @10MHz" TEXT,
        "Rated Current" TEXT,
        DCR TEXT,
        "Rated Voltage" TEXT,
        "Max Op Temp" TEXT,
        Series TEXT,
        Description TEXT,
        "Part Number" TEXT,
        Manufacturer TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, "Impedance @100MHz",
         "Impedance @10MHz", "Rated Current", DCR, "Rated Voltage",
         "Max Op Temp", Series, Description, "Part Number", Manufacturer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, inductors)

    conn.commit()
    conn.close()


def build_field_defs():
    return [
        {"column": "Impedance @100MHz", "name": "Impedance @100MHz",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Impedance @10MHz", "name": "Impedance @10MHz",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Rated Current", "name": "Rated Current",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "DCR", "name": "DCR",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Rated Voltage", "name": "Rated Voltage",
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
         "visible_on_add": True, "visible_in_chooser": True, "show_name": False},
    ]


def write_kicad_dbl(dbl_path, db_path, table):
    content = {
        "meta": {"version": 0},
        "name": "Murata DLW5B Chip Common-Mode Chokes",
        "description": ("Murata DLW5B-series 5050/2020-size chip common-mode "
                         "choke library (4-terminal, custom footprint)"),
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
                "name": "DLW5B",
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
        description="Import Murata DLW5B-series chip common-mode choke "
                     "CSV export(s) into a KiCad database-library SQLite "
                     "file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s). Multiple "
                              "values are merged into one library.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. ind_cmc_murata_dlw5b.")
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
