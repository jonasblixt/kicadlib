# Imports Murata GA3 safety-certified (X1/Y2) MLCC capacitor data (Murata's
# own product-table CSV export) into a KiCad database-library SQLite file,
# following the ceramic-MLCC field convention used by
# cap_mlcc_murata_GRM / cap_rfmw_kyocera_accu_p / cap_rfmw_murata_gqm /
# cap_xy_vishay_vj - NOT the polarized-electrolytic convention
# (cap_alel_chemicon and friends): Symbol is Device:C (these are
# non-polarized ceramic caps), Value is shown normally with its label, and
# there's no ESR/Leakage Current/Endurance/Ripple Current. The one addition
# beyond the plain ceramic-MLCC schema is a "Safety Rating" field, same as
# the Vishay VJ library - GA3 is likewise an X1/Y2 safety-certified series
# (all 31 rows in this dataset carry X1 Rated Voltage DC/AC and Y2 Rated
# Voltage DC/AC populated, X2/Y1 always blank, so Safety Rating is a
# constant "X1+Y2" here).
#
# All 31 part numbers in the source CSV are already unique - there is no
# packaging-suffix duplication like the Digikey-exported libraries had, but
# the same id-collision dedup pattern (seen_ids dict, warn + skip) is kept
# for consistency/safety in case that ever changes.
#
# Footprints: two of the three case sizes have an exact match in KiCad's
# standard Capacitor_SMD.pretty - (4.5mm x 2.0mm) = C_1808_4520Metric,
# (5.7mm x 5.0mm) = C_2220_5750Metric. The third case, (5.7mm x 2.8mm,
# part-number prefix GA352, 8/31 parts), has NO standard KiCad match.
# Per user decision ("Build a custom footprint"), a custom footprint
# (footprints/Murata_GA3.pretty/C_Murata_GA3_5.7x2.8.kicad_mod, with a
# matching STEP/WRL 3D model in footprints/Murata_GA3.3dshapes/) was
# created instead, so this library needs an fp-lib-table entry for the
# "Murata_GA3" nickname (same pattern as Panasonic_ECHU and Vishay_VJ).
#
# NOTE ON THE 5.7x2.8mm FOOTPRINT: Murata's actual datasheet/recommended
# land pattern for this case could not be retrieved - Digikey, Murata's own
# FAQ page and PDF download API, alldatasheet.com, SnapEDA, and Octopart
# were all inaccessible (410/403/robots.txt-disallowed, or no usable table
# returned). The land pattern used here is INTERPOLATED from KiCad's own
# already-verified C_1808_4520Metric and C_2220_5750Metric footprints
# instead (see the .kicad_mod file's own descr field for the exact
# reasoning). The 3D STEP model was likewise hand-authored (no CAD library
# or STEP validator available to generate/check it), same caveat as the
# Vishay VJ 2008 model. Please verify both the pad layout and the 3D model
# in KiCad before relying on them, especially given these are
# safety-rated parts where the datasheet's land pattern matters for
# clearance.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "Murata"

# (Length, Width) in mm, parsed from the CSV's "4.5mm ±0.3mm" style
# strings -> (footprint library nickname, footprint name).
footprint_mapping = {
    (4.5, 2.0): ("Capacitor_SMD", "C_1808_4520Metric"),
    (5.7, 5.0): ("Capacitor_SMD", "C_2220_5750Metric"),
    (5.7, 2.8): ("Murata_GA3", "C_Murata_GA3_5.7x2.8"),
}

# Case label used inside the id string, keyed the same way as
# footprint_mapping.
case_labels = {
    (4.5, 2.0): "1808",
    (5.7, 5.0): "2220",
    (5.7, 2.8): "GA352",
}

# "Tolerance of capacitance" column, e.g. "±5%".
tolerance_mapping = {
    "±5%": "5",
    "±10%": "10",
    "±20%": "20",
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

DIM_RE = re.compile(r"^\s*([\d.]+)\s*mm")


def parse_dim_mm(raw):
    # "4.5mm ±0.3mm" -> 4.5, "5mm ±0.4mm" -> 5.0
    m = DIM_RE.match(raw)
    if not m:
        raise ValueError(f"could not parse dimension from {raw!r}")
    return float(m.group(1))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import a Murata GA3 safety-certified MLCC CSV export "
                     "into a KiCad database-library SQLite file.")
    parser.add_argument("--csv", required=True,
                         help="Path to the input CSV (Murata product-table "
                              "export for the GA3 series).")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. cap_xy_murata_ga3. Must match "
                              "what the corresponding .kicad_dbl 'table' "
                              "field references.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def parse_capacitance(raw):
    # "10pF" / "1,000pF" -> farads. This dataset is all pF (10pF-4700pF),
    # but the full pF/nF/uF handling from the Vishay/Kyocera importers is
    # kept for robustness in case future GA3 CSVs add bigger values.
    raw = raw.strip().replace(",", "")
    m = re.match(r"^([\d.]+)\s*(pF|nF|uF|µF)$", raw)
    if not m:
        raise ValueError(f"unrecognized capacitance value {raw!r}")
    value = float(m.group(1))
    unit = m.group(2)
    if unit in ("µF", "uF"):
        return value * 1e-6
    if unit == "nF":
        return value * 1e-9
    return value * 1e-12


def format_capacitance(farads):
    # Same 3-branch pF/nF/uF formatter used by the Vishay/Kyocera importers.
    if farads >= 1000e-9:
        value = farads * 1e6
        unit_short, unit_full = "u", "uF"
    elif farads >= 1000e-12:
        value = farads * 1e9
        unit_short, unit_full = "n", "nF"
    else:
        value = farads * 1e12
        unit_short, unit_full = "p", "pF"

    frac = int(round(value % 1.0, 1) * 10)
    if frac > 0:
        short_str = f"{int(value)}{unit_short}{frac}"
        full_str = f"{value:.1f}{unit_full}"
    else:
        short_str = f"{int(value)}{unit_short}"
        full_str = f"{int(value)}{unit_full}"
    return short_str, full_str


def normalize_voltage(raw):
    # "250Vac(r.m.s.)" -> "250VAC" - consistent with the Vishay VJ script's
    # convention of using the AC rating (the more relevant figure for a
    # shield-to-ground/line-filtering safety cap) for the Voltage field.
    raw = raw.strip()
    m = re.match(r"^([\d.,]+)\s*Vac", raw)
    if not m:
        raise ValueError(f"unrecognized AC voltage value {raw!r}")
    return f"{m.group(1).replace(',', '')}VAC"


def derive_safety_rating(row):
    # Which of X1/X2/Y1/Y2 are populated (checking the DC column is enough
    # - AC and DC are always populated together in this dataset).
    ratings = []
    for code in ("X1", "X2", "Y1", "Y2"):
        if row[f"{code} Rated Voltage DC"].strip():
            ratings.append(code)
    return "+".join(ratings)


def load_capacitors(csv_path):
    count = 0
    skipped_footprint = {}
    skipped_tolerance = {}
    capacitors = []
    seen_ids = {}

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            part_number = row["Part Number"]
            length = parse_dim_mm(row["Length"])
            width = parse_dim_mm(row["Width"])
            case_key = (length, width)
            tolerance_code = row["Tolerance of capacitance"]
            dielectric = row["Temperature characteristics"].strip()

            if case_key not in footprint_mapping:
                skipped_footprint[case_key] = skipped_footprint.get(case_key, 0) + 1
                continue
            if tolerance_code not in tolerance_mapping:
                skipped_tolerance[tolerance_code] = skipped_tolerance.get(tolerance_code, 0) + 1
                continue

            tolerance = tolerance_mapping[tolerance_code]
            case_label = case_labels[case_key]
            lib_nickname, footprint_name = footprint_mapping[case_key]
            footprint = f"{lib_nickname}:{footprint_name}"

            farads = parse_capacitance(row["Capacitance"])
            short_str, capacitance_str = format_capacitance(farads)

            voltage = normalize_voltage(row["X1 Rated Voltage AC"])
            rating = derive_safety_rating(row)

            count += 1
            # CGA352_10p_250VAC_SL_5_X1+Y2
            id_str = f"C{case_label}_{short_str}_{voltage}_{dielectric}_{tolerance}_{rating}"
            if id_str in seen_ids:
                print(f"WARNING: duplicate id '{id_str}' - "
                      f"{part_number} collides with {seen_ids[id_str]}, skipping")
                continue
            seen_ids[id_str] = part_number

            print(f"{count} {id_str} {part_number}, {case_label}, {dielectric}, "
                  f"{capacitance_str}, {voltage}, tol {tolerance}%, rating {rating}")

            cap = (id_str, capacitance_str, footprint, "Device:C",
                   capacitance_str, voltage, dielectric,
                   f"{capacitance_str}, {voltage}, {dielectric}, Tol: {tolerance}%, "
                   f"Rating: {rating}",
                   part_number, MANUFACTURER, rating)
            capacitors.append(cap)

    if skipped_footprint:
        total_skipped = sum(skipped_footprint.values())
        print(f"\nSkipped {total_skipped} rows with no matching footprint:")
        for code, n in sorted(skipped_footprint.items(), key=lambda x: -x[1]):
            print(f"  case {code}: {n} parts")

    if skipped_tolerance:
        total_skipped = sum(skipped_tolerance.values())
        print(f"\nSkipped {total_skipped} rows with unmapped tolerance code:")
        for code, n in sorted(skipped_tolerance.items(), key=lambda x: -x[1]):
            print(f"  '{code}': {n} parts")

    return capacitors


def write_database(db_path, table, capacitors):
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
        Capacitance TEXT,
        Voltage TEXT,
        Dielectric TEXT,
        Description TEXT,
        "Part Number" TEXT,
        Manufacturer TEXT,
        "Safety Rating" TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, Capacitance, Voltage, Dielectric,
         Description, "Part Number", Manufacturer, "Safety Rating")
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, capacitors)

    conn.commit()
    conn.close()


def build_field_defs():
    # Same shape as cap_xy_vishay_vj (plain ceramic-MLCC style: Value shown
    # normally, Dielectric surfaced under its own name, no ESR/Leakage/
    # Endurance/Ripple Current), plus "Safety Rating" for X1/X2/Y1/Y2.
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
        {"column": "Safety Rating", "name": "Safety Rating",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
    ]


def write_kicad_dbl(dbl_path, db_path, table):
    content = {
        "meta": {"version": 0},
        "name": "Murata GA3 Safety-Certified MLCC Library",
        "description": "Murata GA3 Safety-Certified (X1/Y2) MLCC Library",
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
                "name": "GA3",
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
    capacitors = load_capacitors(args.csv)
    write_database(args.db, args.table, capacitors)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(capacitors)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
