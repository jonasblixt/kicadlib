# Imports Panasonic's official OS-CON (conductive polymer aluminum solid)
# chip capacitor CSV exports into a single KiCad database-library SQLite
# file, following the same scheme as the cap_alel_chemicon importer:
# same field set (Capacitance/Voltage/Dielectric/Manufacturer/Part Number/
# Value/ESR/Leakage Current/Endurance/Temp Range/Ripple Current), same
# "${Capacitance}" Value trick, same Device:C_Polarized_US symbol, same
# hidden-on-schematic Series field.
#
# Panasonic splits the OS-CON catalog across several CSV exports that all
# share the exact same column layout (cap_alpoly_panasonic_oscon_1.csv..
# _4.csv as provided) - this script takes one or more --csv files and
# merges them into one table/one .kicad_dbl library entry.
#
# "Dielectric" carries the OS-CON series code (SXV, SVPT, SVPC, ...), same
# repurposing as the Chemi-Con importer's Series field.
#
# Case size is body diameter x body length (mm), matched the same way as
# the Chemi-Con importer against KiCad's own Capacitor_SMD.pretty
# (checked against C:\Program Files\KiCad\10.0\share\kicad\footprints\
# Capacitor_SMD.pretty). 10 of the 13 diameter x length combinations in
# this dataset have an exact CP_Elec_<D>x<L> match; the remaining 3 use
# the nearest available footprint (per user decision - "use nearest
# footprint" rather than dropping, unlike the Chemi-Con 12.5mm case where
# no candidate existed at all):
#   6.3x6.4mm  (10 parts) -> CP_Elec_6.3x5.9   (0.5mm shorter)
#   6.3x7.9mm  ( 3 parts) -> CP_Elec_6.3x7.7   (0.2mm shorter)
#   6.3x10.4mm ( 1 part)  -> CP_Elec_6.3x9.9   (0.5mm shorter)
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

FOOTPRINT_LIB_NICKNAME = "Capacitor_SMD"

# (diameter, length) in mm, formatted with trailing zeros stripped -> the
# footprint name within Capacitor_SMD.pretty to use.
footprint_mapping = {
    ("8", "6.9"): "CP_Elec_8x6.9",
    ("6.3", "5.9"): "CP_Elec_6.3x5.9",
    ("8", "11.9"): "CP_Elec_8x11.9",
    ("10", "12.6"): "CP_Elec_10x12.6",
    ("5", "5.9"): "CP_Elec_5x5.9",
    ("10", "7.9"): "CP_Elec_10x7.9",
    ("6.3", "6.4"): "CP_Elec_6.3x5.9",   # near-miss, 0.5mm shorter
    ("10", "10"): "CP_Elec_10x10",
    ("6.3", "9.9"): "CP_Elec_6.3x9.9",
    ("8", "10"): "CP_Elec_8x10",
    ("6.3", "7.9"): "CP_Elec_6.3x7.7",   # near-miss, 0.2mm shorter
    ("5", "4.4"): "CP_Elec_5x4.4",
    ("6.3", "10.4"): "CP_Elec_6.3x9.9",  # near-miss, 0.5mm shorter
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Same extra columns as the Chemi-Con importer, in the same order.
EXTRA_COLUMNS = ["ESR", "Leakage Current", "Endurance", "Temp Range", "Ripple Current"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import one or more Panasonic OS-CON CSV exports into "
                     "a single KiCad database-library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV file(s) (Panasonic "
                              "OS-CON product-list exports, all sharing "
                              "the same column layout). All rows are "
                              "merged into one table.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. cap_alpoly_panasonic_oscon. "
                              "Must match what the corresponding "
                              ".kicad_dbl 'table' field references.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def format_dim(raw):
    # Strips the CSV's fixed "8.00" / "6.30" style formatting down to the
    # minimal representation used in ids and footprint names ("8", "6.3").
    value = float(raw)
    return f"{value:g}"


def format_capacitance(capacitance_uf):
    # Same pF/nF/uF-free formatter as the Chemi-Con importer - OS-CON
    # capacitance is also given directly in uF.
    frac = int(round(capacitance_uf % 1.0, 1) * 10)
    if frac > 0:
        short_str = f"{int(capacitance_uf)}u{frac}"
    else:
        short_str = f"{int(capacitance_uf)}u"
    capacitance_str = f"{capacitance_uf:.1f}uF" if frac else f"{int(capacitance_uf)}uF"
    return short_str, capacitance_str


def parse_tolerance(raw):
    # Always "-20 - 20" in this dataset (symmetric +/-20%) but parsed
    # generically in case a future export has a different spread.
    parts = raw.split(" - ")
    if len(parts) != 2:
        return raw.strip()
    lo, hi = abs(float(parts[0])), abs(float(parts[1]))
    tol = max(lo, hi)
    return str(int(tol)) if tol == int(tol) else str(tol)


def sanitize_temp(raw):
    return raw.replace("°C", "C").replace("≦", "<=").replace("＜", "<").strip()


def format_temp_token(raw):
    # Ripple-current temp columns are sometimes a plain number ("105")
    # and sometimes a threshold expression ("T≦105", "105＜T≦125") with no
    # trailing unit - append "C" only when the sanitized string still
    # ends in a digit.
    token = sanitize_temp(raw)
    if not token or token == "-":
        return ""
    if token[-1].isdigit():
        token += "C"
    return token


def format_esr(row):
    # ESR (mOhm) + ESR Frequency (kHz) - no temperature is given for OS-CON
    # ESR (unlike Chemi-Con's ESR1/ESR2), so it's omitted here.
    esr, freq = row[21].strip(), row[22].strip()
    if not esr or esr == "-":
        return ""
    if freq and freq != "-":
        return f"{esr}mOhm@{freq}kHz"
    return f"{esr}mOhm"


def format_leakage_current(row):
    # Leakage Current [Max.] (uA) - a single max-spec figure, not a timed
    # measurement like Chemi-Con's 1min/2min columns.
    value = row[23].strip()
    if not value or value == "-":
        return ""
    return f"{value}uA (Max)"


def format_endurance_entry(raw):
    value = sanitize_temp(raw)
    if not value or value == "-":
        return ""
    if "@" in value:
        hours, temp = value.split("@", 1)
        return f"{hours}hrs@{temp}"
    return value


def format_endurance(row):
    # Endurance@Temp.-1 alone, or -1 and -2 as two rated conditions.
    parts = [format_endurance_entry(row[13]), format_endurance_entry(row[14])]
    return " / ".join(p for p in parts if p)


def format_temp_range(row):
    # Category Temperature Range (deg.C), e.g. "-55 - 125".
    value = row[11].strip()
    if not value or value == "-":
        return ""
    parts = value.split(" - ")
    if len(parts) == 2:
        return f"{parts[0]}C to {parts[1]}C"
    return sanitize_temp(value)


def format_ripple_current(row):
    # Rated Ripple Current-1 alone, or -1 and -2 as two rated conditions -
    # mirrors the ESR1/ESR2 pattern used for Chemi-Con.
    parts = []
    for value_idx, temp_idx, freq_idx in ((15, 16, 17), (18, 19, 20)):
        value = row[value_idx].strip()
        if not value or value == "-":
            continue
        temp = format_temp_token(row[temp_idx])
        freq = row[freq_idx].strip()
        extras = []
        if temp:
            extras.append(temp)
        if freq and freq != "-":
            extras.append(f"{freq}kHz")
        piece = f"{value}mArms"
        if extras:
            piece += "@" + ",".join(extras)
        parts.append(piece)
    return " / ".join(parts)


def load_capacitors(csv_paths):
    count = 0
    skipped_footprint = {}
    capacitors = []
    seen_ids = {}

    for csv_path in csv_paths:
        with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            header = next(reader)

            for row in reader:
                part_number = row[0]
                series = row[4]
                voltage = format_dim(row[8])
                capacitance_uf = float(row[9])
                tolerance = parse_tolerance(row[10])
                diameter = format_dim(row[25])
                length = format_dim(row[26])

                size_key = (diameter, length)
                if size_key not in footprint_mapping:
                    skipped_footprint[size_key] = skipped_footprint.get(size_key, 0) + 1
                    continue

                footprint = f"{FOOTPRINT_LIB_NICKNAME}:{footprint_mapping[size_key]}"
                case_size = f"{diameter}x{length}"

                count += 1
                short_str, capacitance_str = format_capacitance(capacitance_uf)

                # C8x6.9_15u_100V_SXV_20
                id_str = f"C{case_size}_{short_str}_{voltage}V_{series}_{tolerance}"
                if id_str in seen_ids:
                    print(f"WARNING: duplicate id '{id_str}' - "
                          f"{part_number} collides with {seen_ids[id_str]}, skipping")
                    continue
                seen_ids[id_str] = part_number

                esr = format_esr(row)
                leakage_current = format_leakage_current(row)
                endurance = format_endurance(row)
                temp_range = format_temp_range(row)
                ripple_current = format_ripple_current(row)

                print(f"{count} {id_str} {part_number}, {case_size}, {series}, "
                      f"{capacitance_str}, {voltage}V, tol {tolerance}%, "
                      f"ESR {esr or '-'}, Ileak {leakage_current or '-'}, "
                      f"Endurance {endurance or '-'}, Temp {temp_range or '-'}, "
                      f"Iripple {ripple_current or '-'}")

                # "Dielectric" carries the OS-CON series code (SXV, SVPT, ...)
                # - same repurposing as the Chemi-Con importer's Series field.
                cap = (id_str, "${Capacitance}", footprint, "Device:C_Polarized_US",
                       capacitance_str, f"{voltage}V", series,
                       f"{capacitance_str}, {voltage}V, {series}, Tol: {tolerance}%",
                       part_number, "Panasonic", esr, leakage_current, endurance,
                       temp_range, ripple_current)
                capacitors.append(cap)

    if skipped_footprint:
        total_skipped = sum(skipped_footprint.values())
        print(f"\nSkipped {total_skipped} rows with no matching footprint:")
        for (d, l), n in sorted(skipped_footprint.items(), key=lambda x: -x[1]):
            print(f"  {d}x{l}mm: {n} parts")

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
        ESR TEXT,
        "Leakage Current" TEXT,
        Endurance TEXT,
        "Temp Range" TEXT,
        "Ripple Current" TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, Capacitance, Voltage, Dielectric,
         Description, "Part Number", Manufacturer, ESR, "Leakage Current", Endurance,
         "Temp Range", "Ripple Current")
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, capacitors)

    conn.commit()
    conn.close()


def build_field_defs():
    fields = [
        {"column": "Capacitance", "name": "Capacitance",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Voltage", "name": "Voltage",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        {"column": "Dielectric", "name": "Series",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": False},
        {"column": "Manufacturer", "name": "Manufacturer",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Part Number", "name": "Part Number",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        # show_name False so the chooser/property list shows just the
        # resolved value (e.g. "15.0uF") instead of "Value: 15.0uF" - the
        # Value column itself stays "${Capacitance}" so it tracks the
        # (hidden) Capacitance field automatically.
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
        "name": "Panasonic OS-CON Conductive Polymer Aluminum Solid Capacitor Library",
        "description": "Panasonic OS-CON Conductive Polymer Aluminum Solid Capacitor Library",
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
                "name": "OSCON",
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
