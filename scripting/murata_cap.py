# Shared code for the Murata MLCC importers (import_cap_mlcc_murata_grm.py,
# import_cap_rfmw_murata_gqm.py), which read Murata's own product-table
# CSV exports. Until 2026-10-19 this was the generic, argument-driven
# import_murata_cap.py; it only wrote the .db, and the arguments used were
# never recorded (cleanup review A4.1). The parsing below is unchanged, so
# both libraries come out with exactly the rows they had before.
#
# Field style: ceramic/MLCC (Device:C, Value = "${Capacitance}",
# Capacitance/Voltage/Dielectric/Manufacturer/Part Number). The
# .kicad_dbl writer here reproduces the hand-written files of GRM, GQM and
# cap_rfmw_kyocera_accup, which share this field set, so the Kyocera
# importer reuses it.
#
# Only X7R, X5R and C0G rows are imported, in the cases listed in
# case_mapping (KiCad stock Capacitor_SMD footprints).
#
# Duplicate ids: the id (case/value/voltage/dielectric/tolerance) does not
# include thickness, so thickness variants of one part collide (e.g.
# GRM031R60J104MG01 vs GRM033R60J104ME19; 101 rows in GRM, all differing
# only in part number). INSERT OR REPLACE keeps the last such row; that
# behaviour is kept so the libraries stay identical, and each collision is
# now printed.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

case_mapping = {
    "0.6mm0.3mm": "0201",
    "1mm0.5mm": "0402",
    "1.6mm0.8mm": "0603",
    "2mm1.25mm": "0805",
    "3.2mm1.6mm": "1206",
    "3.2mm2.5mm": "1210",
    "4.5mm3.2mm": "1812"
}

footprint_mapping = {
    "0.6mm0.3mm": "C_0201_0603Metric",
    "1mm0.5mm": "C_0402_1005Metric",
    "1.6mm0.8mm": "C_0603_1608Metric",
    "2mm1.25mm": "C_0805_2012Metric",
    "3.2mm1.6mm": "C_1206_3216Metric",
    "3.2mm2.5mm": "C_1210_3225Metric",
    "4.5mm3.2mm": "C_1812_4532Metric"
}

# Table/column names can't be parameterized with sqlite3 placeholders, so
# validate the table name is a plain identifier before it goes into an
# f-string.
TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_capacitors(csv_path):
    count = 0
    capacitors = []
    seen_ids = {}

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for row in reader:
            part_number = row[0].replace("#", "")
            length = row[4].split(" ")[0]
            width = row[5].split(" ")[0]
            dielectric = row[9]
            capacitance_input_str = row[11].replace("μ", "u").replace(",", "")
            tolerance = row[12].replace("±", "")
            voltage = row[13].replace("Vdc", "").replace(",", "")

            # The input data only uses pF or uF, convert it to 'F'
            if "uF" in capacitance_input_str:
                capacitance = round(float(capacitance_input_str.replace("uF", "")) * 1e-6, 9)
            elif "pF" in capacitance_input_str:
                capacitance = round(float(capacitance_input_str.replace("pF", "")) * 1e-12, 15)
            else:
                continue

            # We only want X7R, X5R and C0G
            if dielectric not in ("X7R", "X5R", "C0G"):
                continue

            # Translate case size
            case_size_metric_str = f"{length}{width}"

            if case_size_metric_str not in case_mapping:
                continue

            case_size = case_mapping[case_size_metric_str]
            footprint = f"Capacitor_SMD:{footprint_mapping[case_size_metric_str]}"

            count += 1

            # C0603_2u2_10V_X7R_5%
            # pF < 1000pF
            # nF >= 1000pF
            # uF >= 1000nF

            if capacitance >= 1000e-9:
                capacitance_uf = capacitance * 1e6
                frac = int(round(capacitance_uf % 1.0, 1) * 10)
                if frac > 0:
                    short_str = f"{int(capacitance_uf)}u{frac}"
                else:
                    short_str = f"{int(capacitance_uf)}u"
                capacitance_str = f"{capacitance_uf:.1f}uF"
            elif capacitance >= 1000e-12:
                capacitance_nf = capacitance * 1e9
                frac = int(round(capacitance_nf % 1.0, 1) * 10)
                if frac > 0:
                    short_str = f"{int(capacitance_nf)}n{frac}"
                else:
                    short_str = f"{int(capacitance_nf)}n"
                capacitance_str = f"{capacitance_nf:.1f}nF"
            else:
                capacitance_pf = capacitance * 1e12
                frac = int(round(capacitance_pf % 1.0, 1) * 10)
                if frac > 0:
                    short_str = f"{int(capacitance_pf)}p{frac}"
                else:
                    short_str = f"{int(capacitance_pf)}p"
                capacitance_str = f"{capacitance_pf:.1f}pF"

            id_str = f"C{case_size}_{short_str}_{voltage}V_{dielectric}_{tolerance}"
            if id_str in seen_ids:
                print(f"WARNING: duplicate id '{id_str}' - {part_number} "
                      f"replaces {seen_ids[id_str]}")
            seen_ids[id_str] = part_number

            print(f"{count} {id_str} {part_number}, {case_size}, {dielectric}, "
                  f"{capacitance_input_str} ({capacitance_str}) [{short_str}], "
                  f"{capacitance} {tolerance}, {voltage}V")

            cap = (id_str, "${Capacitance}", footprint, "Device:C",
                   capacitance_str, f"{voltage}V", dielectric,
                   f"{capacitance_str}, {voltage}V, {dielectric}, Tol: {tolerance}",
                   part_number, "Murata")
            capacitors.append(cap)

    return capacitors


def write_database(db_path, table, capacitors):
    if not TABLE_NAME_RE.match(table):
        raise ValueError(f"'{table}' is not a valid SQLite table name")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Drop every table, not just ours, so nothing else survives (the old
    # GRM .db still carried a stale cap_mlcc_murata table from a rename).
    # Dropping rather than deleting the file works while KiCad has it open.
    for (old,) in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall():
        cursor.execute(f'DROP TABLE "{old}"')

    cursor.execute(f"""
    CREATE TABLE {table} (
        id TEXT PRIMARY KEY,
        Value TEXT,
        Footprints TEXT,
        Symbol TEXT,
        Capacitance TEXT,
        Voltage TEXT,
        Dielectric TEXT,
        Description TEXT,
        "Part Number" TEXT,
        Manufacturer TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, Capacitance, Voltage, Dielectric, Description, "Part Number", Manufacturer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, capacitors)

    conn.commit()
    conn.close()


def build_field_defs():
    # Ceramic/MLCC style.
    return [
        {"column": "Capacitance", "name": "Capacitance",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Voltage", "name": "Voltage",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        {"column": "Dielectric", "name": "Dielectric",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        {"column": "Manufacturer", "name": "Manufacturer",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Part Number", "name": "Part Number",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Value", "name": "Value",
         "visible_on_add": True, "visible_in_chooser": True},
    ]


def write_kicad_dbl(dbl_path, db_path, table, chooser_name, title):
    content = {
        "meta": {"version": 0},
        "name": title,
        "description": title,
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
                "name": chooser_name,
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


def run(library, csv_name, chooser_name, title):
    """Entry point for a per-series importer. Defaults reproduce the repo files."""
    parser = argparse.ArgumentParser(
        description=f"Import the Murata {chooser_name} CSV export into the "
                    f"{library} KiCad database library.")
    parser.add_argument("--csv", default=str(REPO / "data" / csv_name),
                        help=f"input CSV (default: data/{csv_name})")
    parser.add_argument("--db", default=str(REPO / "library" / f"{library}.db"),
                        help="output SQLite file (default: library/<library>.db)")
    parser.add_argument("--table", default=library,
                        help="table name; must match the .kicad_dbl 'table' field")
    parser.add_argument("--kicad-dbl", default=str(REPO / "library" / f"{library}.kicad_dbl"),
                        help="output .kicad_dbl (default: library/<library>.kicad_dbl)")
    args = parser.parse_args()

    capacitors = load_capacitors(args.csv)
    write_database(args.db, args.table, capacitors)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table, chooser_name, title)
    print(f"Imported {len(capacitors)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")
