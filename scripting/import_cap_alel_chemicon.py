# Imports Chemi-Con's official chip (SMD can-type) aluminum electrolytic
# capacitor CSV export (columns: Parts Number, Production Status,
# Successor Model, Series, ... Rated Voltage[Vdc], Capacitance[uF],
# Capacitance Tolerance Code, Dimensions D[mm]/L[mm]/T[mm], ... ESR1/2,
# Leakage Current, Endurance1/2, ...) into a KiCad database-library
# SQLite file, following the same id scheme as the cap_mlcc_murata_GRM /
# cap_rfmw_* importers.
#
# All series live in a single table (a per-series split was tried and
# reverted - it didn't work well). "Dielectric" carries the Chemi-Con
# series code (MHU, MVY, ...) as before.
#
# Case size here is cylindrical can diameter x height (mm), not an EIA
# 4-digit code - Chemi-Con's own naming already uses this (e.g.
# "CP_Elec_10x10.5"), so footprints are looked up the same way.
#
# Footprints come from KiCad's own system library (Capacitor_SMD.pretty,
# ships with every KiCad install - checked against
# C:\Program Files\KiCad\10.0\share\kicad\footprints\Capacitor_SMD.pretty)
# rather than a local one, so no fp-lib-table entry is needed for these
# parts to resolve on any machine with a stock KiCad install.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

FOOTPRINT_LIB_NICKNAME = "Capacitor_SMD"

# Diameter x height (mm) -> footprint name within Capacitor_SMD.pretty.
# Most are exact matches. The 16mm/18mm-diameter entries are accepted
# near-misses (Chemi-Con's actual can height vs. what KiCad ships):
#   16x16.5 -> CP_Elec_16x17.5  (1.0mm taller)
#   16x21.5 -> CP_Elec_16x22    (0.5mm taller)
#   18x16.5 -> CP_Elec_18x17.5  (1.0mm taller)
#   18x21.5 -> CP_Elec_18x22    (0.5mm taller)
# 12.5mm-diameter parts have no match at all in the system library (no
# 12.5mm entries at any height) and are intentionally left out - those
# rows are dropped, not substituted.
footprint_mapping = {
    ("5", "5.8"): "CP_Elec_5x5.8",
    ("6.3", "5.2"): "CP_Elec_6.3x5.2",
    ("6.3", "5.8"): "CP_Elec_6.3x5.8",
    ("6.3", "7.7"): "CP_Elec_6.3x7.7",
    ("8", "10"): "CP_Elec_8x10",
    ("10", "10"): "CP_Elec_10x10",
    ("10", "10.5"): "CP_Elec_10x10.5",
    ("16", "16.5"): "CP_Elec_16x17.5",
    ("16", "21.5"): "CP_Elec_16x22",
    ("18", "16.5"): "CP_Elec_18x17.5",
    ("18", "21.5"): "CP_Elec_18x22",
}

# JIS/EIA capacitance tolerance letter codes seen on Chemi-Con parts.
tolerance_mapping = {
    "J": "5",
    "K": "10",
    "M": "20",
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Columns beyond id/Value/Footprints/Symbol/Capacitance/Voltage/
# Dielectric/Description/Part Number/Manufacturer - ESR/Leakage Current/
# Endurance were added for the series-split request; Temp Range and
# Ripple Current were added afterward as their own fields.
EXTRA_COLUMNS = ["ESR", "Leakage Current", "Endurance", "Temp Range", "Ripple Current"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import a Chemi-Con chip aluminum electrolytic CSV "
                     "export into a KiCad database-library SQLite file.")
    parser.add_argument("--csv", required=True,
                         help="Path to the input CSV (Chemi-Con product "
                              "list export).")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. cap_alel_chemicon. Must "
                              "match what the corresponding .kicad_dbl "
                              "'table' field references.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def format_capacitance(capacitance_uf):
    # Chemi-Con gives capacitance directly in uF, so this only needs the
    # single branch of the pF/nF/uF formatter the ceramic importers use.
    frac = int(round(capacitance_uf % 1.0, 1) * 10)
    if frac > 0:
        short_str = f"{int(capacitance_uf)}u{frac}"
    else:
        short_str = f"{int(capacitance_uf)}u"
    capacitance_str = f"{capacitance_uf:.1f}uF" if frac else f"{int(capacitance_uf)}uF"
    return short_str, capacitance_str


def format_esr(row):
    # ESR1 alone (136 rows), ESR1+ESR2 as two conditions - e.g. room
    # temp and cold temp (253 rows), or neither (411 rows). ESR2-only
    # never occurs in this dataset.
    esr1, esr1_temp, esr1_freq = row[18].strip(), row[19].strip(), row[20].strip()
    esr2, esr2_temp, esr2_freq = row[21].strip(), row[22].strip(), row[23].strip()
    parts = []
    if esr1:
        parts.append(f"{esr1}mOhm@{esr1_temp}C,{esr1_freq}")
    if esr2:
        parts.append(f"{esr2}mOhm@{esr2_temp}C,{esr2_freq}")
    return " / ".join(parts)


def format_leakage_current(row):
    # Only the 1min and 2min columns are ever populated in this dataset
    # (47 and 753 rows respectively, no overlap) - 3min/5min are always
    # empty but checked anyway in case a future export uses them.
    lc_temp = row[37].strip()
    for minutes, idx in ((1, 33), (2, 34), (3, 35), (5, 36)):
        value = row[idx].strip()
        if value:
            suffix = f", {lc_temp}C" if lc_temp else ""
            return f"{value}uA ({minutes}min{suffix})"
    return ""


def format_endurance(row):
    # Endurance2 is never populated in this dataset - only Endurance1
    # is used, but both are checked in case a future export differs.
    for temp_idx, hrs_idx, load_idx in ((38, 39, 40), (41, 42, 43)):
        hrs = row[hrs_idx].strip()
        if hrs:
            temp = row[temp_idx].strip()
            load = row[load_idx].strip()
            result = f"{hrs}hrs@{temp}C"
            if load:
                result += f" ({load})"
            return result
    return ""


def format_temp_range(row):
    # Min/Max Category Temperature - the part's rated operating range.
    min_temp, max_temp = row[4].strip(), row[5].strip()
    if min_temp and max_temp:
        return f"{min_temp}C to {max_temp}C"
    return ""


def format_ripple_current(row):
    # Rated Ripple Current1 alone, or Ripple Current1+2 as two rated
    # conditions - mirrors the ESR1/ESR2 pattern above.
    rc1, rc1_temp, rc1_freq = row[12].strip(), row[13].strip(), row[14].strip()
    rc2, rc2_temp, rc2_freq = row[15].strip(), row[16].strip(), row[17].strip()
    parts = []
    if rc1:
        parts.append(f"{rc1}mArms@{rc1_temp}C,{rc1_freq}")
    if rc2:
        parts.append(f"{rc2}mArms@{rc2_temp}C,{rc2_freq}")
    return " / ".join(parts)


def load_capacitors(csv_path):
    count = 0
    skipped_footprint = {}
    skipped_tolerance = {}
    capacitors = []

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        header = next(reader)

        for row in reader:
            part_number = row[0]
            series = row[3]
            voltage = row[6]
            capacitance_uf = float(row[7])
            tolerance_code = row[8]
            diameter = row[9]
            length = row[10]

            size_key = (diameter, length)
            if size_key not in footprint_mapping:
                skipped_footprint[size_key] = skipped_footprint.get(size_key, 0) + 1
                continue

            if tolerance_code not in tolerance_mapping:
                skipped_tolerance[tolerance_code] = skipped_tolerance.get(tolerance_code, 0) + 1
                continue

            tolerance = tolerance_mapping[tolerance_code]
            footprint = f"{FOOTPRINT_LIB_NICKNAME}:{footprint_mapping[size_key]}"
            case_size = f"{diameter}x{length}"

            count += 1
            short_str, capacitance_str = format_capacitance(capacitance_uf)

            # C10x10.5_470u_25V_MHU_20
            id_str = f"C{case_size}_{short_str}_{voltage}V_{series}_{tolerance}"

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

            # "Dielectric" is repurposed here to carry the Chemi-Con series
            # code (MHU, MVY, ...) since aluminum electrolytics don't have
            # a dielectric class the way ceramics do - it's the closest
            # equivalent "which sub-family is this" field Chemi-Con gives.
            cap = (id_str, "${Capacitance}", footprint, "Device:C_Polarized_US",
                   capacitance_str, f"{voltage}V", series,
                   f"{capacitance_str}, {voltage}V, {series}, Tol: {tolerance}%",
                   part_number, "Chemi-Con", esr, leakage_current, endurance,
                   temp_range, ripple_current)
            capacitors.append(cap)

    if skipped_footprint:
        total_skipped = sum(skipped_footprint.values())
        print(f"\nSkipped {total_skipped} rows with no matching footprint "
              f"(12.5mm-diameter parts - not available in Capacitor_SMD.pretty):")
        for (d, l), n in sorted(skipped_footprint.items(), key=lambda x: -x[1]):
            print(f"  {d}x{l}mm: {n} parts")

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
        # resolved value (e.g. "470.0uF") instead of "Value: 470.0uF" -
        # the Value column itself stays "${Capacitance}" so it tracks the
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
        "name": "Chemi-Con Chip Aluminum Electrolytic Capacitor Library",
        "description": "Chemi-Con Chip Aluminum Electrolytic Capacitor Library",
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
                "name": "AlEl",
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
