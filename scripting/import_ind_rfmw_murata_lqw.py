# Imports Murata LQW-series high-Q RF wire-wound (non-magnetic core)
# chip inductor data (Murata's own product-table CSV export, one file
# per DigiKey/Murata pull) into a KiCad database-library SQLite file.
#
# Sibling library to ind_rfmw_murata_lqg (LQG15H/LQG18H) - same "rfmw"
# subtype, same vendor, confusingly similar part-number prefix (LQW vs
# LQG), but LQW is wire-wound rather than multilayer construction.
# Checked "Applicable circuit classification" (all 497 rows say
# "High frequency circuits") and "Characteristic" (all say
# "Wire wound type (Non mag)" - non-magnetic core) before assuming this
# belongs under rfmw rather than the OTHER Murata LQW library already in
# this repo, ind_choke_murata_lqw - that one's source data is
# "Wire wound type (Ferrite)" / "Power lines circuits", a genuinely
# different product class (ferrite-core power-line choke) despite
# sharing the LQW part-number prefix. Don't confuse the two when
# extending either.
#
# Four source CSVs (ind_rfmw_murata_LQW_1-4.csv) merged into one library
# the same way ind_rfmw_murata_lqg merged LQG15H/LQG18H - each file is a
# separate DigiKey/Murata pull covering a different LQW sub-series and
# case size:
#   - LQW_1 (36 rows):  LQW15AW_80, EIA 0402, up to 140C
#   - LQW_2 (296 rows): LQW15AN_80, EIA 0402, up to 125C (HiQtype/Low Rdc
#     variant - same case as LQW15AW but a distinct sub-series; verified
#     zero id collisions between the two despite sharing a case size)
#   - LQW_3 (99 rows):  LQW18AN_00, EIA 0603, up to 125C
#   - LQW_4 (66 rows):  LQW2BAS_0C, EIA 0805, up to 85C
# Same per-row Series/Max Op Temp handling as ind_rfmw_murata_lqg and
# ind_choke_murata_lqw since these vary by sub-series within the merged
# library.
#
# Same RF-inductor-trim field style as ind_rfmw_murata_lqg /
# ind_choke_murata_lqw (Device:L, Inductance/Tolerance/Rated Current/
# DCR/SRF/Max Op Temp/Series/Manufacturer/Part Number/Value, no
# Saturation Current - only "Rated Current (Temperature Rise) / Max." is
# ever populated across all 497 rows, same as both sibling libraries).
#
# format_srf() gained GHz support this library needed - unlike
# ind_rfmw_murata_lqg/ind_choke_murata_lqw (MHz only, some with
# thousands-comma), a meaningful fraction of this dataset's SRF values
# are given directly in GHz (e.g. "2.1GHz", "12.5GHz"). Normalized
# everything to MHz for consistency with the sibling libraries' SRF
# field (1GHz = 1000MHz) rather than storing a mixed-unit column.
#
# Id format follows NAMING.md's inductor pattern: L<case>_<value>_
# <tolerance>_<current>, same format_inductance()/format_current()
# helpers as the sibling libraries. Verified zero id collisions across
# all 497 rows from the four files combined.
#
# All three case sizes (0402, 0603, 0805) are standard EIA metric cases
# with an exact dimensional match in KiCad's own Inductor_SMD.pretty -
# no custom footprint needed.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "Murata"

# EIA case code (from the "Size code in mm(inch)" column, e.g.
# "1005/0402" -> "0402") -> (footprint library nickname, footprint name).
# All standard KiCad footprints.
footprint_mapping = {
    "0402": ("Inductor_SMD", "L_0402_1005Metric"),
    "0603": ("Inductor_SMD", "L_0603_1608Metric"),
    "0805": ("Inductor_SMD", "L_0805_2012Metric"),
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
INDUCTANCE_RE = re.compile(r"^([\d,.]+)(nH|μH|uH)\s*\xb1([\d,.]+)(%|nH|μH|uH)$")
CURRENT_RE = re.compile(r"^([\d,]+)mA$")
SRF_RE = re.compile(r"^([\d,.]+)(MHz|GHz)$")


def parse_case(raw):
    # "1005/0402" -> "0402"
    return raw.split("/")[1]


def _to_henries(num_str, unit):
    num = float(num_str.replace(",", ""))
    return num * 1e-9 if unit == "nH" else num * 1e-6  # uH/μH


def parse_inductance(raw):
    # "51nH \xb12%" -> (5.1e-8, 2.0, "%")
    m = INDUCTANCE_RE.match(raw.strip())
    if not m:
        raise ValueError(f"could not parse inductance from {raw!r}")
    value_h = _to_henries(m.group(1), m.group(2))
    if m.group(4) == "%":
        return value_h, float(m.group(3)), "%"
    tol_h = _to_henries(m.group(3), m.group(4))
    return value_h, tol_h, "abs"


def format_inductance(henries):
    # Returns (id_short, display_str), e.g. 51e-9 -> ("51n0", "51nH").
    # Same IEC-60062-style formatter as ind_rfmw_murata_lqg /
    # ind_choke_murata_lqw - always keeps a digit after the unit letter,
    # matching NAMING.md's own "10n0"/"2u2" examples.
    if henries < 1000e-9:
        unit_id, unit_disp, factor = "n", "nH", 1e-9
    else:
        unit_id, unit_disp, factor = "u", "μH", 1e-6

    mantissa = henries / factor
    formatted = f"{mantissa:.1f}"
    int_str, dec_str = formatted.split(".")
    id_short = f"{int_str}{unit_id}{dec_str}"

    if mantissa == int(mantissa):
        disp_val = str(int(mantissa))
    else:
        disp_val = f"{mantissa:.1f}".rstrip("0").rstrip(".")
    display_str = f"{disp_val}{unit_disp}"

    return id_short, display_str


def parse_current(raw):
    # "600mA" -> 0.6, "1,400mA" -> 1.4 (amps)
    m = CURRENT_RE.match(raw.strip().replace(",", ""))
    if not m:
        raise ValueError(f"could not parse current from {raw!r}")
    return float(m.group(1)) / 1000


def format_current(amps):
    # 0.6 -> "0A6", 1.4 -> "1A4" - matches NAMING.md's own inductor
    # example ("1A2").
    s = f"{amps:.1f}"
    int_part, dec_part = s.split(".")
    return f"{int_part}A{dec_part}"


def format_srf(raw):
    # "6,000MHz" -> "6000MHz", "2.1GHz" -> "2100MHz" - normalized to MHz
    # (see header comment) so this matches the sibling libraries' SRF
    # field even though the source mixes units.
    m = SRF_RE.match(raw.strip().replace(",", ""))
    if not m:
        raise ValueError(f"could not parse SRF from {raw!r}")
    value = float(m.group(1))
    if m.group(2) == "GHz":
        value *= 1000
    return f"{int(round(value))}MHz"


def load_inductors(csv_path):
    count = 0
    skipped_footprint = {}
    inductors = []
    seen_ids = {}

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            part_number = row["Part Number"]
            case = parse_case(row["Size code in mm(inch)"])

            if case not in footprint_mapping:
                skipped_footprint[case] = skipped_footprint.get(case, 0) + 1
                continue

            lib_nickname, footprint_name = footprint_mapping[case]
            footprint = f"{lib_nickname}:{footprint_name}"

            value_h, tol_value, tol_kind = parse_inductance(row["Inductance"])
            value_id, value_disp = format_inductance(value_h)

            if tol_kind == "%":
                tol_token = (str(int(tol_value)) if tol_value == int(tol_value)
                             else str(tol_value))
                tol_disp = f"\xb1{tol_token}%"
            else:
                tol_id_short, tol_id_disp = format_inductance(tol_value)
                tol_token = tol_id_short
                tol_disp = f"\xb1{tol_id_disp}"

            irated = parse_current(row["Rated Current (Temperature Rise) / Max."])
            current_str = format_current(irated)
            dcr = row["DC Resistance(max.)"].strip()
            srf = format_srf(row["Self-resonant frequency(min.)"])
            max_temp = row["Maximum operating temperature"].strip()
            series = row["Series"].split("_")[0]

            id_str = f"L{case}_{value_id}_{tol_token}_{current_str}"
            if id_str in seen_ids:
                print(f"WARNING: duplicate id '{id_str}' - "
                      f"{part_number} collides with {seen_ids[id_str]}, "
                      f"skipping")
                continue
            seen_ids[id_str] = part_number

            count += 1
            current_disp = f"{irated:.2f}".rstrip("0").rstrip(".") + "A"
            description = (f"{value_disp}, {tol_disp}, {current_disp}, "
                            f"DCR {dcr}, SRF {srf}, EIA {case}, {series}, "
                            f"high-Q RF")

            print(f"{count} {id_str} {part_number}, {case}, {value_disp}, "
                  f"{tol_disp}, {current_str}, DCR {dcr}, SRF {srf}")

            inductor = (id_str, value_disp, footprint, "Device:L",
                        value_disp, tol_disp, current_str, dcr, srf,
                        max_temp, series, description, part_number,
                        MANUFACTURER)
            inductors.append(inductor)

    if skipped_footprint:
        total_skipped = sum(skipped_footprint.values())
        print(f"\nSkipped {total_skipped} rows with no matching footprint:")
        for code, n in sorted(skipped_footprint.items(), key=lambda x: -x[1]):
            print(f"  case {code}: {n} parts")

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
        Inductance TEXT,
        Tolerance TEXT,
        "Rated Current" TEXT,
        DCR TEXT,
        SRF TEXT,
        "Max Op Temp" TEXT,
        Series TEXT,
        Description TEXT,
        "Part Number" TEXT,
        Manufacturer TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, Inductance, Tolerance,
         "Rated Current", DCR, SRF, "Max Op Temp", Series, Description,
         "Part Number", Manufacturer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, inductors)

    conn.commit()
    conn.close()


def build_field_defs():
    # Same RF-inductor-trim style as ind_rfmw_murata_lqg /
    # ind_choke_murata_lqw.
    return [
        {"column": "Inductance", "name": "Inductance",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Tolerance", "name": "Tolerance",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        {"column": "Rated Current", "name": "Rated Current",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "DCR", "name": "DCR",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "SRF", "name": "SRF",
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
         "visible_on_add": True, "visible_in_chooser": True},
    ]


def write_kicad_dbl(dbl_path, db_path, table):
    content = {
        "meta": {"version": 0},
        "name": "Murata LQW High-Q RF Wire-Wound Chip Inductors",
        "description": ("Murata LQW15A/LQW18A/LQW2B High-Q RF Wire-Wound "
                         "(Non-Magnetic Core) Chip Inductor Library"),
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
                "name": "LQW",
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
        description="Import Murata LQW-family high-Q RF wire-wound chip "
                     "inductor CSV export(s) into a KiCad "
                     "database-library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s). Multiple "
                              "values are merged into one library.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. ind_rfmw_murata_lqw. Must "
                              "match the corresponding .kicad_dbl 'table' "
                              "field.")
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
