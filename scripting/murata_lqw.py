# Shared code for the Murata LQW per-series importers
# (import_ind_choke_murata_lqw*.py, import_ind_rfmw_murata_lqw*.py).
#
# Until 2026-10-13 these were two merged libraries, ind_choke_murata_lqw
# (LQW15CN/LQW15DN/LQW18CN) and ind_rfmw_murata_lqw (LQW15AN/LQW15AW/
# LQW18AN/LQW2BAS), both showing up as "LQW" in the symbol chooser. Per
# Jonas (cleanup review A4.3) they are not merged but split into one
# library per series, named after the series (LQW15 is the case size,
# the next two letters the product line), with the series as chooser
# name. The parsing below is carried over unchanged from the two old
# importers, which differed only in comments, the description suffix and
# the .kicad_dbl texts; the split libraries contain exactly the same rows
# (same ids, same values) as the old merged ones.
#
# Source data is Murata's own product-table CSV export. Two product
# classes share the LQW prefix and must not be mixed:
#   - choke: "Wire wound type (Ferrite)", "Power lines circuits"
#     (LQW15CN, LQW15DN, LQW18CN) - ferrite-core power-line chokes;
#     "choke" is this repo's subtype code for them (not cmc: single
#     2-terminal winding; not power: not DC-DC inductors).
#   - rfmw: "Wire wound type (Non mag)", "High frequency circuits"
#     (LQW15AN, LQW15AW, LQW18AN, LQW2BAS, LQW2UAS) - high-Q RF inductors, sibling
#     of ind_rfmw_murata_lqg (multilayer).
#
# Field style: the RF-inductor-trim style of ind_rfmw_murata_lqg
# (Device:L, Inductance/Tolerance/Rated Current/DCR/SRF/Max Op Temp/
# Series/Manufacturer/Part Number/Value, no Saturation Current: only
# "Rated Current (Temperature Rise) / Max." is populated in this data).
#
# Units: inductance >= 1uH formats on the "u" scale (LQW15DN goes up to
# 15uH); tolerance is a percentage except below 10nH, where Murata gives
# an absolute value (e.g. LQW18CN4N9D00#, 4.9nH +/-0.5nH) which reuses
# format_inductance(). SRF is normalized to MHz: some RF rows give GHz
# ("2.1GHz" -> "2100MHz"), and thousands commas are dropped.
#
# Id format follows NAMING.md's inductor pattern:
# L<case>_<value>_<tolerance>_<current>. Ids are unique within every
# series (verified when the libraries were merged and again at the split).
#
# Footprints: 0402, 0603, 0805 are standard EIA metric cases with a match
# in KiCad's Inductor_SMD.pretty. 1008 (LQW2UAS, added 2026-10-19, A4.6)
# uses Inductor_SMD:L_Coilcraft_1008HQ_2520Metric: Murata's standard land
# for LQW2UA (O05E catalog, RF Inductors Soldering and Mounting: a=1.27 gap,
# b=3.3 overall, c=2.54 wide, i.e. 1.015x2.54 pads at +-1.1425) matches
# it within 0.005 mm. The generic L_1008_2520Metric (1.25x2.2 pads, 0.9 gap)
# is 0.35 mm off and Murata stresses that the land should not project
# beyond the electrode for high Q. The Coilcraft body (2.92x2.79x2.03) is
# slightly larger than LQW2UAS (2.62x2.45x1.83); KiCad ships no 3D model
# for it.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "Murata"
REPO = Path(__file__).resolve().parent.parent

# EIA case code (from the "Size code in mm(inch)" column, e.g.
# "1005/0402" -> "0402") -> (footprint library nickname, footprint name).
footprint_mapping = {
    "0402": ("Inductor_SMD", "L_0402_1005Metric"),
    "0603": ("Inductor_SMD", "L_0603_1608Metric"),
    "0805": ("Inductor_SMD", "L_0805_2012Metric"),
    "1008": ("Inductor_SMD", "L_Coilcraft_1008HQ_2520Metric"),
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
INDUCTANCE_RE = re.compile(r"^([\d,.]+)(nH|μH|uH)\s*\xb1([\d,.]+)(%|nH|μH|uH)$")
CURRENT_RE = re.compile(r"^([\d,]+)mA$")
SRF_RE = re.compile(r"^([\d,.]+)(MHz|GHz)$")

# Description suffix per product class (kept from the old importers).
KIND_TEXT = {
    "choke": "power-line choke",
    "rfmw": "high-Q RF",
}


def parse_case(raw):
    # "1005/0402" -> "0402"
    return raw.split("/")[1]


def _to_henries(num_str, unit):
    num = float(num_str.replace(",", ""))
    return num * 1e-9 if unit == "nH" else num * 1e-6  # uH/μH


def parse_inductance(raw):
    # "51nH \xb12%" -> (5.1e-8, 2.0, "%")
    # "4.9nH \xb10.5nH" -> (4.9e-9, 0.5e-9, "abs")
    m = INDUCTANCE_RE.match(raw.strip())
    if not m:
        raise ValueError(f"could not parse inductance from {raw!r}")
    value_h = _to_henries(m.group(1), m.group(2))
    if m.group(4) == "%":
        return value_h, float(m.group(3)), "%"
    tol_h = _to_henries(m.group(3), m.group(4))
    return value_h, tol_h, "abs"


def format_inductance(henries):
    # Returns (id_short, display_str), e.g. 51e-9 -> ("51n0", "51nH"),
    # 3.3e-6 -> ("3u3", "3.3μH"). IEC-60062 style, always keeps a digit
    # after the unit letter, matching NAMING.md's "10n0"/"2u2" examples.
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
    # 0.6 -> "0A6", 1.4 -> "1A4" - matches NAMING.md's inductor example.
    s = f"{amps:.1f}"
    int_part, dec_part = s.split(".")
    return f"{int_part}A{dec_part}"


def format_srf(raw):
    # "6,000MHz" -> "6000MHz", "2.1GHz" -> "2100MHz"
    m = SRF_RE.match(raw.strip().replace(",", ""))
    if not m:
        raise ValueError(f"could not parse SRF from {raw!r}")
    value = float(m.group(1))
    if m.group(2) == "GHz":
        value *= 1000
    return f"{int(round(value))}MHz"


def load_inductors(csv_path, kind, series):
    """Read one Murata CSV; refuse rows that aren't the expected series."""
    count = 0
    skipped_footprint = {}
    inductors = []
    seen_ids = {}

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            part_number = row["Part Number"]
            row_series = row["Series"].split("_")[0]
            if row_series != series:
                raise ValueError(f"{csv_path}: {part_number} is series "
                                 f"{row_series}, expected {series}")
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
                           f"{KIND_TEXT[kind]}")

            print(f"{count} {id_str} {part_number}, {case}, {value_disp}, "
                  f"{tol_disp}, {current_str}, DCR {dcr}, SRF {srf}")

            inductors.append((id_str, value_disp, footprint, "Device:L",
                              value_disp, tol_disp, current_str, dcr, srf,
                              max_temp, series, description, part_number,
                              MANUFACTURER))

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
    # RF-inductor-trim style, same as ind_rfmw_murata_lqg.
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


def write_kicad_dbl(dbl_path, db_path, table, chooser_name, title, description):
    content = {
        "meta": {"version": 0},
        "name": title,
        "description": description,
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


def run(library, kind, series, title, description):
    """Entry point for a per-series importer. Defaults reproduce the repo files."""
    parser = argparse.ArgumentParser(
        description=f"Import the Murata {series} CSV export into the "
                    f"{library} KiCad database library.")
    parser.add_argument("--csv", default=str(REPO / "data" / f"{library}.csv"),
                        help="input CSV (default: data/<library>.csv)")
    parser.add_argument("--db", default=str(REPO / "library" / f"{library}.db"),
                        help="output SQLite file (default: library/<library>.db)")
    parser.add_argument("--table", default=library,
                        help="table name; must match the .kicad_dbl 'table' field")
    parser.add_argument("--kicad-dbl", default=str(REPO / "library" / f"{library}.kicad_dbl"),
                        help="output .kicad_dbl (default: library/<library>.kicad_dbl)")
    args = parser.parse_args()

    inductors = load_inductors(args.csv, kind, series)
    write_database(args.db, args.table, inductors)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table, series, title, description)

    print(f"\nImported {len(inductors)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")
