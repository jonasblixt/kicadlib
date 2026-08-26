# Imports Panasonic's official POSCAP (conductive polymer tantalum solid)
# chip capacitor CSV exports into a single KiCad database-library SQLite
# file, following the same scheme as the cap_alel_chemicon / cap_alpoly_
# panasonic_oscon importers: same field set (Capacitance/Voltage/
# Dielectric/Manufacturer/Part Number/Value/ESR/Leakage Current/
# Endurance/Temp Range/Ripple Current), same "${Capacitance}" Value
# trick, same Device:C_Polarized_US symbol, same hidden-on-schematic
# Series field.
#
# Panasonic splits the POSCAP catalog across several CSV exports that all
# share the exact same column layout (cap_tapoly_panasonic_poscap_1.csv..
# _6.csv as provided) - this script takes one or more --csv files and
# merges them into one table/one .kicad_dbl library entry.
#
# "Dielectric" carries the POSCAP series code (TA, TPE, TC, ...), same
# repurposing as the Chemi-Con/OS-CON importers' Series field.
#
# POSCAP is a rectangular (not cylindrical-can) chip part, so case size
# here is Panasonic's own EIA-style Size Code (B2, D3L, ...) rather than
# a diameter x length pair. That code, plus the part's Length/Width/
# Height, is matched against KiCad's own tantalum footprint library
# (Capacitor_Tantalum_SMD.pretty, checked against C:\Program Files\
# KiCad\10.0\share\kicad\footprints\Capacitor_Tantalum_SMD.pretty), whose
# CP_EIA-<LW><H>_<Vendor> names already encode length/width/height in
# 0.1mm units. All 10 (Length, Width, Height) combinations in this
# dataset land on an EIA-3528 (3.5x2.8mm) or EIA-7343 (7.3x4.3mm) body -
# both exact length/width matches in KiCad's set - so only height needs a
# nearest-available pick, and the worst case is 0.2mm off:
#   3.5x2.8x1.1mm (B1S)        -> CP_EIA-3528-12_Kemet-T   (1.2mm, +0.1mm)
#   3.5x2.8x1.9mm (B2, B2S)    -> CP_EIA-3528-21_Kemet-B   (2.1mm, +0.2mm)
#   7.3x4.3x1.4mm (D15, D15S)  -> CP_EIA-7343-15_Kemet-W   (1.5mm, +0.1mm)
#   7.3x4.3x1.8mm (D2E)        -> CP_EIA-7343-20_Kemet-V   (2.0mm, +0.2mm)
#   7.3x4.3x1.9mm (D2, D2S)    -> CP_EIA-7343-20_Kemet-V   (2.0mm, +0.1mm)
#   7.3x4.3x2.8mm (D3L)        -> CP_EIA-7343-30_AVX-N     (3.0mm, +0.2mm)
#   7.3x4.3x3.8mm (D4)         -> CP_EIA-7343-40_Kemet-Y   (4.0mm, +0.2mm)
# All 10 size codes have a match, so nothing is dropped here.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

FOOTPRINT_LIB_NICKNAME = "Capacitor_Tantalum_SMD"

# (Length, Width, Height) in mm, formatted with trailing zeros stripped ->
# the footprint name within Capacitor_Tantalum_SMD.pretty to use. See the
# module docstring above for how each was picked.
footprint_mapping = {
    ("3.5", "2.8", "1.1"): "CP_EIA-3528-12_Kemet-T",
    ("3.5", "2.8", "1.9"): "CP_EIA-3528-21_Kemet-B",
    ("7.3", "4.3", "1.4"): "CP_EIA-7343-15_Kemet-W",
    ("7.3", "4.3", "1.8"): "CP_EIA-7343-20_Kemet-V",
    ("7.3", "4.3", "1.9"): "CP_EIA-7343-20_Kemet-V",
    ("7.3", "4.3", "2.8"): "CP_EIA-7343-30_AVX-N",
    ("7.3", "4.3", "3.8"): "CP_EIA-7343-40_Kemet-Y",
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Same extra columns as the Chemi-Con / OS-CON importers, in the same order.
EXTRA_COLUMNS = ["ESR", "Leakage Current", "Endurance", "Temp Range", "Ripple Current"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import one or more Panasonic POSCAP CSV exports into "
                     "a single KiCad database-library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV file(s) (Panasonic "
                              "POSCAP product-list exports, all sharing "
                              "the same column layout). All rows are "
                              "merged into one table.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. cap_tapoly_panasonic_poscap. "
                              "Must match what the corresponding "
                              ".kicad_dbl 'table' field references.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def format_dim(raw):
    # Strips the CSV's fixed "7.30" / "10.0" style formatting down to the
    # minimal representation used in ids and footprint lookups ("7.3", "10").
    value = float(raw)
    return f"{value:g}"


def format_capacitance(capacitance_uf):
    # Same pF/nF/uF-free formatter as the Chemi-Con/OS-CON importers -
    # POSCAP capacitance is also given directly in uF.
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
    # Ripple-current temp columns are plain numbers in this dataset, but
    # sanitized/guarded the same way as the OS-CON importer in case a
    # future export uses a threshold expression instead.
    token = sanitize_temp(raw)
    if not token or token == "-":
        return ""
    if token[-1].isdigit():
        token += "C"
    return token


def format_esr(row):
    # ESR (mOhm) + ESR Frequency (kHz) - no temperature is given for
    # POSCAP ESR, same as OS-CON.
    esr, freq = row[20].strip(), row[21].strip()
    if not esr or esr == "-":
        return ""
    if freq and freq != "-":
        return f"{esr}mOhm@{freq}kHz"
    return f"{esr}mOhm"


def format_leakage_current(row):
    # Leakage Current [Max.] (uA) - a single max-spec figure.
    value = row[22].strip()
    if not value or value == "-":
        return ""
    return f"{value}uA (Max)"


def format_endurance_entry(raw):
    value = sanitize_temp(raw)
    if not value or value == "-":
        return ""
    if "@" in value:
        hours, temp = value.split("@", 1)
        # POSCAP writes this as "1000h@105C" (Chemi-Con/OS-CON write
        # "1000@125C" with no "h") - strip any existing h/H suffix before
        # appending "hrs" so both styles come out the same.
        hours = hours.rstrip("hH")
        return f"{hours}hrs@{temp}"
    return value


def format_endurance(row):
    # Endurance@Temp.-1 alone, or -1 and -2 as two rated conditions.
    parts = [format_endurance_entry(row[12]), format_endurance_entry(row[13])]
    return " / ".join(p for p in parts if p)


def format_temp_range(row):
    # Category Temperature Range (deg.C), e.g. "-55 - 105".
    value = row[10].strip()
    if not value or value == "-":
        return ""
    parts = value.split(" - ")
    if len(parts) == 2:
        return f"{parts[0]}C to {parts[1]}C"
    return sanitize_temp(value)


def format_ripple_current(row):
    # Rated Ripple Current-1 alone, or -1 and -2 as two rated conditions.
    # NOTE: the CSV's RC1 columns are ordered value/temp/freq (14,15,16)
    # but its RC2 columns are ordered value/freq/temp (17,18,19) - the
    # column *names* differ in order too, so this isn't a copy/paste bug,
    # it's how Panasonic laid out this particular export.
    conditions = ((14, 15, 16), (17, 19, 18))
    parts = []
    for value_idx, temp_idx, freq_idx in conditions:
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
                voltage = format_dim(row[7])
                capacitance_uf = float(row[8])
                tolerance = parse_tolerance(row[9])
                length = format_dim(row[25])
                width = format_dim(row[26])
                height = format_dim(row[27])
                size_code = row[30].strip()

                dim_key = (length, width, height)
                if dim_key not in footprint_mapping:
                    skipped_footprint[(size_code, dim_key)] = (
                        skipped_footprint.get((size_code, dim_key), 0) + 1)
                    continue

                footprint = f"{FOOTPRINT_LIB_NICKNAME}:{footprint_mapping[dim_key]}"

                count += 1
                short_str, capacitance_str = format_capacitance(capacitance_uf)
                esr_raw = row[20].strip()

                # POSCAP commonly offers several ESR grades (standard,
                # low-ESR, ultra-low-ESR, ...) at the exact same case
                # size/capacitance/voltage/series/tolerance - ESR has to
                # be in the id or those variants collide. Confirmed
                # against this dataset: every row has an ESR value.
                # CB2_47u_10V_TA_70mOhm_20
                id_str = f"C{size_code}_{short_str}_{voltage}V_{series}_{esr_raw}mOhm_{tolerance}"
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

                print(f"{count} {id_str} {part_number}, {size_code} "
                      f"({length}x{width}x{height}mm), {series}, "
                      f"{capacitance_str}, {voltage}V, tol {tolerance}%, "
                      f"ESR {esr or '-'}, Ileak {leakage_current or '-'}, "
                      f"Endurance {endurance or '-'}, Temp {temp_range or '-'}, "
                      f"Iripple {ripple_current or '-'}")

                # "Dielectric" carries the POSCAP series code (TA, TPE, ...)
                # - same repurposing as the Chemi-Con/OS-CON importers'
                # Series field.
                cap = (id_str, "${Capacitance}", footprint, "Device:C_Polarized_US",
                       capacitance_str, f"{voltage}V", series,
                       f"{capacitance_str}, {voltage}V, {series}, Tol: {tolerance}%",
                       part_number, "Panasonic", esr, leakage_current, endurance,
                       temp_range, ripple_current)
                capacitors.append(cap)

    if skipped_footprint:
        total_skipped = sum(skipped_footprint.values())
        print(f"\nSkipped {total_skipped} rows with no matching footprint:")
        for (code, (l, w, h)), n in sorted(skipped_footprint.items(), key=lambda x: -x[1]):
            print(f"  {code} ({l}x{w}x{h}mm): {n} parts")

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
        # resolved value (e.g. "47.0uF") instead of "Value: 47.0uF" - the
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
        "name": "Panasonic POSCAP Conductive Polymer Tantalum Solid Capacitor Library",
        "description": "Panasonic POSCAP Conductive Polymer Tantalum Solid Capacitor Library",
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
                "name": "POSCAP",
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
