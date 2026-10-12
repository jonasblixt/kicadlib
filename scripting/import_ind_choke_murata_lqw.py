# Imports Murata LQW-series ferrite-core wire-wound power-line choke
# inductor data (Murata's own product-table CSV export, one file per
# DigiKey/Murata pull) into a KiCad database-library SQLite file.
#
# Naming note: "choke" isn't one of NAMING.md's four documented inductor
# subtype codes (power/rf/cmc/coupled). Jonas asked for this library as
# ind_choke_murata_lqw, and looking at the actual data it's a real
# distinct category, not a slip: every row here is
# "Wire wound type (Ferrite)" / "Power lines circuits" (Murata's own
# classification), not "High frequency circuits" like the sibling
# ind_rfmw_murata_lqg library's LQG15H/LQG18H parts - even though LQW and
# LQG are visually similar part numbers from the same vendor. It's also
# not a real common-mode choke (`cmc` - that needs two coupled windings /
# 4 terminals; every row here is a plain 2-terminal single inductor, same
# shape as ind_rfmw_murata_lqg) and not really a DC-DC "power" inductor
# either (`power` - Vishay IHLP etc - those are shielded/unshielded for
# switching regulators; these are small-body ferrite EMI/power-line
# chokes). So `choke` looks like a genuinely missing NAMING.md subtype
# code for this product class, not a mistake - worth Jonas adding it to
# NAMING.md's inductor table rather than shoehorning these into `power`
# or `rf`, but that's a doc decision for him, not something this script
# does.
#
# Three source CSVs (ind_choke_murata_LQW_1/2/3.csv) merged into one
# library the same way the sibling ind_rfmw_murata_lqg library merged
# LQG15H/LQG18H - each file is a separate DigiKey/Murata pull covering a
# different LQW sub-series and case size:
#   - LQW_1 (34 rows): LQW15CN_10, EIA 0402, up to 125C, 15nH-3.3uH
#   - LQW_2 (2 rows):  LQW15DN_00, EIA 0402, up to 85C, 10-15uH
#   - LQW_3 (15 rows): LQW18CN_00, EIA 0603, up to 85C, 4.9-650nH
# Same per-row Series/Max Op Temp handling as ind_rfmw_murata_lqg since
# these vary by sub-series within the merged library.
#
# Same RF-inductor-trim field style as ind_rfmw_murata_lqg (Device:L,
# Inductance/Tolerance/Rated Current/DCR/SRF/Max Op Temp/Series/
# Manufacturer/Part Number/Value, no Saturation Current) - reused as-is
# since it's the same source-data shape (Murata's own product-table CSV
# format) and the same "no saturation-current spec in the source" reason
# applies.
#
# format_inductance() gained a uH branch this library didn't need before
# - LQW15DN_00's values go up to 15uH, above ind_rfmw_murata_lqg's
# 270nH ceiling. Values >=1uH format in the "u" scale (e.g. "1u0" for
# 1000nH/1uH), matching NAMING.md's own "2u2 (2.2 uH)" example; below
# that, same "n" scale as before. Inductance tolerance is percent for
# every row except one (LQW18CN4N9D00#, 4.9nH +/-0.5nH - the same
# below-10nH absolute-tolerance convention seen in ind_rfmw_murata_lqg),
# handled by the same format_inductance()-reuse trick on the tolerance
# delta.
#
# Id format follows NAMING.md's inductor pattern: L<case>_<value>_
# <tolerance>_<current>. Verified zero id collisions across all 51 rows
# from the three files combined.
#
# Both case sizes (0402, 0603) are standard EIA metric cases with an
# exact dimensional match in KiCad's own Inductor_SMD.pretty - no custom
# footprint needed.
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
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
INDUCTANCE_RE = re.compile(r"^([\d,.]+)(nH|μH|uH)\s*\xb1([\d,.]+)(%|nH|μH|uH)$")
CURRENT_RE = re.compile(r"^([\d,]+)mA$")
SRF_RE = re.compile(r"^([\d,]+)MHz$")


def parse_case(raw):
    # "1005/0402" -> "0402"
    return raw.split("/")[1]


def _to_henries(num_str, unit):
    num = float(num_str.replace(",", ""))
    return num * 1e-9 if unit == "nH" else num * 1e-6  # uH/μH


def parse_inductance(raw):
    # "1,000nH \xb120%" -> (1e-6, 20.0, "%")
    # "4.9nH \xb10.5nH" -> (4.9e-9, 0.5e-9, "abs")
    # "10μH \xb120%" -> (1e-5, 20.0, "%")
    m = INDUCTANCE_RE.match(raw.strip())
    if not m:
        raise ValueError(f"could not parse inductance from {raw!r}")
    value_h = _to_henries(m.group(1), m.group(2))
    if m.group(4) == "%":
        return value_h, float(m.group(3)), "%"
    tol_h = _to_henries(m.group(3), m.group(4))
    return value_h, tol_h, "abs"


def format_inductance(henries):
    # Returns (id_short, display_str), e.g. 20e-9 -> ("20n0", "20nH"),
    # 1e-6 -> ("1u0", "1uH"), 3.3e-6 -> ("3u3", "3.3uH"). Same
    # IEC-60062-style formatter as import_ind_rfmw_murata_lqg.py, with a
    # uH branch added for this library's wider value range (see header
    # comment) - always keeps a digit after the unit letter, matching
    # NAMING.md's own "10n0"/"2u2" examples.
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
    # "500mA" -> 0.5, "1,000mA" -> 1.0 (amps)
    m = CURRENT_RE.match(raw.strip().replace(",", ""))
    if not m:
        raise ValueError(f"could not parse current from {raw!r}")
    return float(m.group(1)) / 1000


def format_current(amps):
    # 0.5 -> "0A5", 1.0 -> "1A0" - matches NAMING.md's own inductor
    # example ("1A2").
    s = f"{amps:.1f}"
    int_part, dec_part = s.split(".")
    return f"{int_part}A{dec_part}"


def format_srf(raw):
    # "3,000MHz" -> "3000MHz", "20MHz" -> "20MHz"
    m = SRF_RE.match(raw.strip().replace(",", ""))
    if not m:
        raise ValueError(f"could not parse SRF from {raw!r}")
    return f"{m.group(1)}MHz"


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
                            f"power-line choke")

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
    # Same RF-inductor-trim style as ind_rfmw_murata_lqg - see that
    # script's header comment for why Saturation Current is dropped and
    # Max Op Temp replaces a Temp Min/Max pair.
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
        "name": "Murata LQW Ferrite Wire-Wound Power-Line Choke Inductors",
        "description": ("Murata LQW15C/LQW15D/LQW18C Ferrite Wire-Wound "
                         "Power-Line Choke Inductor Library"),
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
        description="Import Murata LQW-family ferrite wire-wound "
                     "power-line choke inductor CSV export(s) into a "
                     "KiCad database-library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s). Multiple "
                              "values are merged into one library.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. ind_choke_murata_lqw. Must "
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
