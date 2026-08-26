# Imports Panasonic's official ECHU(X) stacked metallized PPS film chip
# capacitor CSV exports into a single KiCad database-library SQLite file,
# following the same scheme as the cap_alel_chemicon / cap_alpoly_panasonic_oscon
# importers: same field set (Capacitance/Voltage/Dielectric/Manufacturer/
# Part Number/Value/ESR/Leakage Current/Endurance/Temp Range/Ripple Current),
# same "${Capacitance}" Value trick, same one-table/one-library layout.
#
# Panasonic splits the ECHU catalog across several CSV exports that share the
# exact same column layout (cap_film_panasonic_echux_1.csv.._2.csv as
# provided) - this script takes one or more --csv files and merges them into
# one table / one .kicad_dbl library entry, de-duplicating by part number.
#
# Differences from the Chemi-Con importer, and why:
#
#   * Symbol is Device:C, not Device:C_Polarized_US - film capacitors are
#     non-polar.
#
#   * "Dielectric" carries the actual dielectric, "PPS", and is surfaced under
#     its own name rather than being repurposed as "Series" the way the
#     Chemi-Con importer does. Chemi-Con needed the repurposing because
#     aluminum electrolytics have no dielectric class; ECHU(X) does, and the
#     library is single-series, so the series code would add nothing.
#
#   * ESR, Leakage Current, Endurance and Ripple Current are kept as columns
#     for schema parity with cap_alel_chemicon, but Panasonic's ECHU export
#     carries none of them, so they are empty for every part. Temp Range is
#     the one extra column with real data. Set KEEP_EMPTY_EXTRA_COLUMNS =
#     False below to drop the four empty ones.
#
# Footprints come from the local Panasonic_ECHU.pretty library (this repo's
# footprints/ directory), not from KiCad's system libraries: the ECHU(X)
# datasheet specifies its own reflow land patterns, which differ from the
# generic IPC-derived Capacitor_SMD ones, and several ECHU case codes share
# one EIA size at different body heights - so the 3D model has to differ even
# where the land pattern does not. That means this library DOES need an
# fp-lib-table entry (nickname "Panasonic_ECHU"), unlike the ceramic and
# electrolytic importers. See footprints/README.md.
#
# The (L, T, H) body dimensions in the CSV identify the Panasonic case size
# code exactly - all 14 codes appear in the export - so footprints are matched
# on dimensions rather than on the part number, which does NOT encode case
# size (in ECHU1H103JX5, "X5" is variant + tape width, not a case code).
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

FOOTPRINT_LIB_NICKNAME = "Panasonic_ECHU"
MANUFACTURER = "Panasonic"
DIELECTRIC = "PPS"

# Set False to drop ESR / Leakage Current / Endurance / Ripple Current, which
# the ECHU export has no data for. Temp Range is kept either way.
KEEP_EMPTY_EXTRA_COLUMNS = True

# (L, T, H) body dimensions in mm from the CSV -> (Panasonic case size code,
# EIA imperial size, footprint name in Panasonic_ECHU.pretty).
#
# The CSV's "T Dimension" is the body width (W in the datasheet table) and "H
# Dimension" the height. Height is part of the key because K1/J1/J2/H1/H2/H3/
# G1/G2/G3/E1/E2/D1/D3/D4 collapse onto only six EIA sizes - e.g. J1 and J2
# are both 0805 and share a land pattern, but are 0.9mm and 1.1mm tall.
#
# EIA sizes for the two large codes are the ones the distributors list:
# 4.8x3.3mm is 1913 (4833 metric) and 6.0x4.1mm is 2416.
footprint_mapping = {
    (1.6, 0.80, 0.7): ("K1", "0603", "C_Panasonic_ECHU_K1_1608Metric_H0.70mm"),
    (2.0, 1.25, 0.9): ("J1", "0805", "C_Panasonic_ECHU_J1_2012Metric_H0.90mm"),
    (2.0, 1.25, 1.1): ("J2", "0805", "C_Panasonic_ECHU_J2_2012Metric_H1.10mm"),
    (3.2, 1.60, 0.9): ("H1", "1206", "C_Panasonic_ECHU_H1_3216Metric_H0.90mm"),
    (3.2, 1.60, 1.1): ("H2", "1206", "C_Panasonic_ECHU_H2_3216Metric_H1.10mm"),
    (3.2, 1.60, 1.5): ("H3", "1206", "C_Panasonic_ECHU_H3_3216Metric_H1.50mm"),
    (3.2, 2.50, 1.1): ("G1", "1210", "C_Panasonic_ECHU_G1_3225Metric_H1.10mm"),
    (3.2, 2.50, 1.5): ("G2", "1210", "C_Panasonic_ECHU_G2_3225Metric_H1.50mm"),
    (3.2, 2.50, 2.1): ("G3", "1210", "C_Panasonic_ECHU_G3_3225Metric_H2.10mm"),
    (4.8, 3.30, 1.5): ("E1", "1913", "C_Panasonic_ECHU_E1_4833Metric_H1.50mm"),
    (4.8, 3.30, 2.1): ("E2", "1913", "C_Panasonic_ECHU_E2_4833Metric_H2.10mm"),
    (6.0, 4.10, 1.9): ("D1", "2416", "C_Panasonic_ECHU_D1_6041Metric_H1.90mm"),
    (6.0, 4.10, 2.5): ("D3", "2416", "C_Panasonic_ECHU_D3_6041Metric_H2.50mm"),
    (6.0, 4.10, 2.8): ("D4", "2416", "C_Panasonic_ECHU_D4_6041Metric_H2.80mm"),
}

# Panasonic writes the tolerance as a signed range rather than a code letter.
# The ordering-code letters are G = +/-2%, J = +/-5%, which is what these are.
tolerance_mapping = {
    "-2 - 2": "2",
    "-5 - 5": "5",
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Same extra columns as the Chemi-Con importer, in the same order.
ALL_EXTRA_COLUMNS = ["ESR", "Leakage Current", "Endurance", "Temp Range",
                     "Ripple Current"]
EXTRA_COLUMNS = (ALL_EXTRA_COLUMNS if KEEP_EMPTY_EXTRA_COLUMNS
                 else ["Temp Range"])

# CSV column indices (Panasonic "Film Capacitors (Electronic Equipment Use)"
# product-list export, 20 columns).
COL_PART_NUMBER = 0
COL_STATUS = 2
COL_SERIES = 4
COL_VOLTAGE = 7
COL_TEMP_RANGE = 8
COL_CAPACITANCE_UF = 9
COL_TOLERANCE = 10
COL_DIELECTRIC = 11
COL_L = 12
COL_T = 13
COL_H = 14


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import Panasonic ECHU(X) PPS film chip capacitor CSV "
                    "exports into a KiCad database-library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                        help="Path(s) to the input CSV file(s) (Panasonic "
                             "ECHU product-list exports, all sharing the same "
                             "column layout). All rows are merged into one "
                             "table; duplicate part numbers are dropped.")
    parser.add_argument("--db", required=True,
                        help="Path to the output .db SQLite file. Created if "
                             "it doesn't exist.")
    parser.add_argument("--table", required=True,
                        help="Name of the table to (re)create inside the "
                             "database, e.g. cap_film_panasonic_echux. Must "
                             "match what the corresponding .kicad_dbl 'table' "
                             "field references.")
    parser.add_argument("--kicad-dbl", required=True,
                        help="Path to (re)write the .kicad_dbl file.")
    parser.add_argument("--footprint-dir",
                        help="Optional path to Panasonic_ECHU.pretty. When "
                             "given, every footprint this import references "
                             "is checked to actually exist there before the "
                             "database is written.")
    parser.add_argument("--include-inactive", action="store_true",
                        help="Also import rows whose Product status is not "
                             "'Active' (discontinued / not-recommended "
                             "parts). Off by default.")
    return parser.parse_args()


def format_capacitance(capacitance_farads):
    """Return (short id token, human string) - e.g. (2u2, 2.2uF), (6n8, 6.8nF),
    (100p, 100.0pF). Same pF/nF/uF thresholds as the Murata importer.

    Note the rounding: scaling a decimal uF figure by 1e9 lands just under the
    intended value (0.12 uF -> 119.99999999999999 nF), and splitting that into
    int + fractional part directly yields "119n10" rather than "120n". Round to
    the one decimal that is actually displayed before splitting."""
    if capacitance_farads >= 1000e-9:
        scaled, unit = capacitance_farads * 1e6, "u"
    elif capacitance_farads >= 1000e-12:
        scaled, unit = capacitance_farads * 1e9, "n"
    else:
        scaled, unit = capacitance_farads * 1e12, "p"

    scaled = round(scaled, 1)
    whole = int(scaled)
    frac = int(round((scaled - whole) * 10))
    if frac > 0:
        short_str = f"{whole}{unit}{frac}"
    else:
        short_str = f"{whole}{unit}"
    return short_str, f"{scaled:.1f}{unit}F"


def format_temp_range(raw):
    """'-55 to 125' -> '-55C to 125C'.

    A trailing '(105)' marks the parts Panasonic derates above 105 C - the
    datasheet's note is 'derating of rated voltage by 1.25 %/C at more than
    105 C', which applies to the 0.12 uF and larger parts."""
    raw = raw.strip()
    note = ""
    m = re.search(r"\((\d+)\)\s*$", raw)
    if m:
        note = f" (derate above {m.group(1)}C)"
        raw = raw[:m.start()].strip()
    m = re.match(r"^(-?\d+)\s*to\s*(-?\d+)$", raw)
    if not m:
        return raw + note
    return f"{m.group(1)}C to {m.group(2)}C{note}"


def load_capacitors(csv_paths, include_inactive=False):
    count = 0
    seen_part_numbers = {}
    skipped_footprint = {}
    skipped_tolerance = {}
    skipped_status = {}
    duplicates = 0
    capacitors = []
    used_footprints = set()

    for csv_path in csv_paths:
        with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            next(reader)  # header

            for row in reader:
                part_number = row[COL_PART_NUMBER].strip()
                status = row[COL_STATUS].strip()
                tolerance_raw = row[COL_TOLERANCE].strip()

                if not include_inactive and status != "Active":
                    skipped_status[status] = skipped_status.get(status, 0) + 1
                    continue

                if part_number in seen_part_numbers:
                    duplicates += 1
                    continue

                try:
                    size_key = (float(row[COL_L]), float(row[COL_T]),
                                float(row[COL_H]))
                except ValueError:
                    size_key = None

                if size_key not in footprint_mapping:
                    key = (row[COL_L], row[COL_T], row[COL_H])
                    skipped_footprint[key] = skipped_footprint.get(key, 0) + 1
                    continue

                if tolerance_raw not in tolerance_mapping:
                    skipped_tolerance[tolerance_raw] = (
                        skipped_tolerance.get(tolerance_raw, 0) + 1)
                    continue

                seen_part_numbers[part_number] = csv_path

                case_code, case_size, footprint_name = footprint_mapping[size_key]
                footprint = f"{FOOTPRINT_LIB_NICKNAME}:{footprint_name}"
                used_footprints.add(footprint_name)

                tolerance = tolerance_mapping[tolerance_raw]
                voltage = f"{float(row[COL_VOLTAGE]):g}"
                capacitance = float(row[COL_CAPACITANCE_UF]) * 1e-6
                short_str, capacitance_str = format_capacitance(capacitance)
                temp_range = format_temp_range(row[COL_TEMP_RANGE])

                count += 1

                # C0805_10n_16V_PPS_5
                id_str = (f"C{case_size}_{short_str}_{voltage}V_"
                          f"{DIELECTRIC}_{tolerance}")

                print(f"{count} {id_str} {part_number}, {case_size} "
                      f"({case_code}), {DIELECTRIC}, {capacitance_str}, "
                      f"{voltage}V, tol {tolerance}%, Temp {temp_range}")

                values = {
                    "id": id_str,
                    "Value": "${Capacitance}",
                    "Footprints": footprint,
                    "Symbol": "Device:C",
                    "Capacitance": capacitance_str,
                    "Voltage": f"{voltage}V",
                    "Dielectric": DIELECTRIC,
                    "Description": (f"{capacitance_str}, {voltage}V, "
                                    f"{DIELECTRIC}, Tol: {tolerance}%"),
                    "Part Number": part_number,
                    "Manufacturer": MANUFACTURER,
                    # Panasonic's ECHU export carries none of these except
                    # Temp Range; the rest are here for schema parity with
                    # cap_alel_chemicon.
                    "ESR": "",
                    "Leakage Current": "",
                    "Endurance": "",
                    "Temp Range": temp_range,
                    "Ripple Current": "",
                }
                capacitors.append(values)

    if duplicates:
        print(f"\nSkipped {duplicates} duplicate part numbers already seen in "
              f"an earlier CSV.")

    if skipped_status:
        total_skipped = sum(skipped_status.values())
        print(f"\nSkipped {total_skipped} rows that are not Active "
              f"(pass --include-inactive to keep them):")
        for status, n in sorted(skipped_status.items(), key=lambda x: -x[1]):
            print(f"  '{status}': {n} parts")

    if skipped_footprint:
        total_skipped = sum(skipped_footprint.values())
        print(f"\nSkipped {total_skipped} rows whose (L, T, H) body size is "
              f"not in footprint_mapping - add the case code to "
              f"Panasonic_ECHU.pretty and to the table above:")
        for (l, t, h), n in sorted(skipped_footprint.items(), key=lambda x: -x[1]):
            print(f"  {l} x {t} x {h} mm: {n} parts")

    if skipped_tolerance:
        total_skipped = sum(skipped_tolerance.values())
        print(f"\nSkipped {total_skipped} rows with an unmapped tolerance:")
        for raw, n in sorted(skipped_tolerance.items(), key=lambda x: -x[1]):
            print(f"  '{raw}': {n} parts")

    return capacitors, used_footprints


def check_footprints(footprint_dir, used_footprints):
    directory = Path(footprint_dir)
    if not directory.is_dir():
        raise SystemExit(f"--footprint-dir '{footprint_dir}' is not a directory")
    missing = sorted(name for name in used_footprints
                     if not (directory / f"{name}.kicad_mod").is_file())
    if missing:
        raise SystemExit(
            f"{len(missing)} referenced footprint(s) missing from "
            f"{directory}:\n  " + "\n  ".join(missing))
    print(f"\nAll {len(used_footprints)} referenced footprints found in "
          f"{directory}")


def column_names():
    return (["id", "Value", "Footprints", "Symbol", "Capacitance", "Voltage",
             "Dielectric", "Description", "Part Number", "Manufacturer"]
            + EXTRA_COLUMNS)


def write_database(db_path, table, capacitors):
    if not TABLE_NAME_RE.match(table):
        raise ValueError(f"'{table}' is not a valid SQLite table name")

    columns = column_names()
    quoted = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join("?" for _ in columns)
    definitions = ",\n        ".join(
        f'"{c}" TEXT PRIMARY KEY' if c == "id" else f'"{c}" TEXT'
        for c in columns)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"DROP TABLE IF EXISTS {table}")
    cursor.execute(f"CREATE TABLE {table} (\n        {definitions}\n    )")
    cursor.executemany(
        f"INSERT OR REPLACE INTO {table} ({quoted}) VALUES ({placeholders})",
        [tuple(cap[c] for c in columns) for cap in capacitors])

    conn.commit()
    conn.close()


def build_field_defs():
    fields = [
        {"column": "Capacitance", "name": "Capacitance",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Voltage", "name": "Voltage",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        # Unlike the Chemi-Con importer, which renames this column to "Series"
        # because aluminum electrolytics have no dielectric class, ECHU(X) has
        # a real one and the library covers a single series.
        {"column": "Dielectric", "name": "Dielectric",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": False},
        {"column": "Manufacturer", "name": "Manufacturer",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Part Number", "name": "Part Number",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        # show_name False so the chooser/property list shows just the resolved
        # value (e.g. "10.0nF") instead of "Value: 10.0nF" - the Value column
        # itself stays "${Capacitance}" so it tracks the (hidden) Capacitance
        # field automatically.
        {"column": "Value", "name": "Value",
         "visible_on_add": True, "visible_in_chooser": True, "show_name": False},
    ]
    for column in EXTRA_COLUMNS:
        fields.append({
            "column": column,
            "name": column,
            "visible_on_add": False,
            "visible_in_chooser": True,
            "show_name": True,
        })
    return fields


def write_kicad_dbl(dbl_path, db_path, table):
    content = {
        "meta": {"version": 0},
        "name": "Panasonic ECHU(X) PPS Film Chip Capacitor Library",
        "description": "Panasonic ECHU(X) PPS Film Chip Capacitor Library",
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
                "name": "ECHU(X)",
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
    capacitors, used_footprints = load_capacitors(args.csv, args.include_inactive)

    if not capacitors:
        raise SystemExit("No parts imported - nothing written.")

    # id is the table's primary key and rows are written with INSERT OR
    # REPLACE, so a duplicate id would silently drop a part rather than fail.
    ids = [cap["id"] for cap in capacitors]
    if len(set(ids)) != len(ids):
        clashes = sorted({i for i in ids if ids.count(i) > 1})
        raise SystemExit(
            f"{len(clashes)} duplicate part id(s) - these would silently "
            f"overwrite each other:\n  " + "\n  ".join(clashes))

    if args.footprint_dir:
        check_footprints(args.footprint_dir, used_footprints)

    write_database(args.db, args.table, capacitors)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(capacitors)} parts into {args.db} ({args.table})")
    print(f"Using {len(used_footprints)} of {len(footprint_mapping)} "
          f"{FOOTPRINT_LIB_NICKNAME} footprints")
    print(f"Wrote {args.kicad_dbl}")
    print(f"\nThis library resolves footprints through the "
          f"'{FOOTPRINT_LIB_NICKNAME}' fp-lib-table nickname - unlike the "
          f"ceramic/electrolytic imports, it needs that entry to exist.")


if __name__ == "__main__":
    main()
