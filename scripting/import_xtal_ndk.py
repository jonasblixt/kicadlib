#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Builds the xtal_ndk KiCad database library from data/xtal_ndk_parts.csv.
#
# Chooser name NDK -> NX on 2026-10-19 (cleanup review A4.4): every package
# in the library is an NX-series crystal.
#
# SOURCE (since the 2026-10-08 review): data/xtal_ndk_parts.csv, a
# hand-maintained table with one row per orderable part. Its "Source"
# column records where each row's electrical data comes from; it is not
# imported into the database. The CSV was created by exporting the
# previous xtal_ndk.db (218 parts) and then applying the review below.
#
# Before that, this script read library/xtal_NDK.kicad_sym, the legacy
# per-part symbol library built from a Digikey export by
# scripting/old_stuff/digikey_import_NDK.py. That file was deleted in
# commit a793421 once it had been converted, which left this importer
# unable to run. Everything the old importer derived from it (the Value/
# Part Number, the parsed Description fields, the family code from the
# legacy "Footprint" property) is now carried directly as CSV columns.
#
# data/xtal_ndk.csv is a different file: an export of NDK's own product
# search (Shift-JIS/cp932 encoded, 297 rows, 7 families, current NDK
# standard specifications only). It is not read by this script. It was
# used during the 2026-10-08 review as the reference for NDK's current
# data, and as the source for the NX3225SA STD-CQS-1 / STD-CQR-1 rows.
#
# 2026-10-08 REVIEW against NDK's own data (ndk.com catalog sheets, the
# STD-CSR-1 spec sheet, and data/xtal_ndk.csv):
#   Verified, no change: NX3225SA STD-CSR-1 (all frequencies, ESR per
#     the NDK spec sheet table, -10..+75 C - this is NOT an automotive or
#     extended-temperature part); NX3215SA STD-MUA-8/-9/-14 (12.5/9/6 pF,
#     70 kOhm, -40..+85 C, standard grade); NX2012SA STD-MUB-1 (12.5 pF,
#     80 kOhm); NX3225GA STD-CRG-2 and the remaining STD-CRA-1/-2/-3 rows.
#   Corrected:
#     - NX3215SA-32.768K-STD-MUS-2 ESR 70 -> 80 kOhm (automotive column
#       of the NX3215SA sheet is Max. 80 kOhm).
#     - ESR per NDK's current per-frequency data: NX3225GA-12.000M-STD-
#       CRA-1 300 -> 120 Ohm, NX3225GB-16M-STD-CRA-2 100 -> 120 Ohm,
#       NX3225GD-10.000M-STD-CRA-3 500 -> 300 Ohm.
#     - The four NX5032SD-...-STD-CSY-1 parts were filed under package
#       NX3225SC and so got the 3.2x2.5mm NX3225SA footprint. They are
#       5.0x3.2mm parts. Package corrected to NX5032SD, which the
#       existing S[DFG] family exclusion (see below) now drops, the same
#       way it already drops NX2520SD/SG.
#     - 2-terminal packages that were on the 4-pin Crystal_GND24 symbol:
#       NX2012SA, NX3225GB, NX3225GD, NX8045GB (terminal counts from
#       NDK's crystal unit index, crystal_e.pdf) now use Device:Crystal.
#       NX3225GB/GD also lose the 4-pad Jonas:NX3225SA footprint they
#       were aliased to: a 2-terminal part must not sit on that land
#       pattern. They are left without a footprint until a 2-pad 3225
#       footprint exists.
#   Added:
#     - NX3225SA STD-CQS-1 (automotive, AEC-Q200, -40..+125 C, +-15 ppm
#       tolerance, +-50 ppm over temperature, 8 pF) and STD-CQR-1
#       (standard, -40..+85 C, +-15/+-25 ppm, 8 pF): every frequency NDK
#       lists in data/xtal_ndk.csv. CQS-1 is NDK's current automotive
#       spec number for NX3225SA. The library's older STD-CRS-2 rows have
#       identical values; NDK no longer lists that spec number.
#     - NX3215SA STD-MUS-4 (6 pF) and STD-MUS-3 (9 pF), the automotive
#       -40..+125 C siblings of the existing STD-MUS-2.
#   Part numbers for the added rows follow the format NDK prints in its
#   own spec sheets (model-frequency-spec, e.g. NX3225SA-24.000M-STD-
#   CSR-1); they were not checked against a distributor listing.
#   Rows marked "Digikey (legacy ...)" in the Source column use spec
#   numbers or customer codes NDK does not publish, so they could not be
#   checked against ndk.com and are unchanged.
#
# SYMBOL: every part uses the stock Device:Crystal_GND24 symbol (4 pins:
# 1/3 = crystal terminals, 2/4 = GND) unless its package is a
# 2-terminal one, which uses the plain 2-pin Device:Crystal - see
# SYMBOL_MAP. NX3215SA and NX5032GA were switched earlier per Jonas's
# direction (RS Components lists "Pin Count: 2" for NX5032GA); the
# 2026-10-08 review added NX2012SA, NX3225GB, NX3225GD and NX8045GB on
# the basis of NDK's own terminal counts.
#
# FOOTPRINT: the legacy symbols' "Footprint" property was never a real
# footprint reference - digikey_import_NDK.py populated it from the
# Digikey "Series" column (e.g. "NX2016AB"), a package/series code. That
# code is the CSV's Package column. Of the 21 codes, only 6 had a
# matching file in modules/footprints.pretty (NX1255, NX2012, NX2520,
# NX2520SA, NX3225, NX3225SA); NX2520 and NX3225 were byte-for-byte
# duplicates of their "SA" siblings and were dropped. NX2012 is a 2-pad
# footprint and was not migrated. The rest live in footprints/
# Jonas.pretty (generated by scripting/gen_ndk_footprints.py, plus
# NX3215SA placed by Jonas).
#
# Per Jonas's direction, other 4-terminal package families reuse one of
# those where the land pattern is the same size (NX3225GA/SC ->
# NX3225SA, all 3.2x2.5mm), or map to a stock KiCad Crystal footprint
# where the size has an exact 4-pin match (NX2016* ->
# Crystal_SMD_2016-4Pin_2.0x1.6mm; NX5032GB/GC/SA ->
# Crystal_SMD_5032-4Pin_5.0x3.2mm; NX5032GA -> the 2-pin variant). The
# families with neither a local footprint nor an exact-size stock match
# - NX1612AA/SA (1.6x1.2mm), NX2012SA (2-pad), NX3225GB/GD (2-pad),
# NX4025DA (4.0x2.5mm), NX8045GB (8.0x4.5mm) - are imported with an
# empty Footprints value rather than a guessed substitute.
#
# EXCLUDED FAMILIES: per Jonas's direction, any family whose code ends
# in S + D/F/G (NX2520SD, NX2520SG, NX5032SD; NX****SF is excluded on
# the same basis if one is ever added) is dropped entirely - see
# EXCLUDE_FAMILY_RE. The rows stay in the CSV so the decision is
# reversible.
#
# The part number is used directly as the database id. All part numbers
# are distinct, so there is no duplicate-part handling beyond a check.
#
# Footprint names changed 2026-10-19 (footprints review F4.8, KiCad-stock /
# Vendor_Part naming): NX1255GB -> Crystal_SMD_NDK_NX1255GB-4Pin_12.5x5.5mm;
# NX2520SA -> Crystal_SMD_NDK_NX2520SA-4Pin_2.5x2.0mm; NX3215SA ->
# Crystal_SMD_NDK_NX3215SA-2Pin_3.2x1.5mm; NX3225SA ->
# Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm (models renamed to match).
# Older names in the comments above refer to the same files.
import argparse
import csv
import json
import re
import sqlite3

MANUFACTURER = "NDK"

DEFAULT_SYMBOL = "Device:Crystal_GND24"
SYMBOL_MAP = {
    "NX2012SA": "Device:Crystal",
    "NX3215SA": "Device:Crystal",
    "NX3225GB": "Device:Crystal",
    "NX3225GD": "Device:Crystal",
    "NX5032GA": "Device:Crystal",
    "NX8045GB": "Device:Crystal",
}

# package -> (footprint library nickname, footprint name), or None if no
# footprint is assigned.
FOOTPRINT_MAP = {
    "NX1255GB": ("Jonas", "Crystal_SMD_NDK_NX1255GB-4Pin_12.5x5.5mm"),
    "NX2520SA": ("Jonas", "Crystal_SMD_NDK_NX2520SA-4Pin_2.5x2.0mm"),
    "NX3215SA": ("Jonas", "Crystal_SMD_NDK_NX3215SA-2Pin_3.2x1.5mm"),
    "NX3225SA": ("Jonas", "Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm"),
    "NX3225GA": ("Jonas", "Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm"),
    "NX3225SC": ("Jonas", "Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm"),
    "NX2016AB": ("Crystal", "Crystal_SMD_2016-4Pin_2.0x1.6mm"),
    "NX2016SA": ("Crystal", "Crystal_SMD_2016-4Pin_2.0x1.6mm"),
    "NX5032GA": ("Crystal", "Crystal_SMD_5032-2Pin_5.0x3.2mm"),
    "NX5032GB": ("Crystal", "Crystal_SMD_5032-4Pin_5.0x3.2mm"),
    "NX5032GC": ("Crystal", "Crystal_SMD_5032-4Pin_5.0x3.2mm"),
    "NX5032SA": ("Crystal", "Crystal_SMD_5032-4Pin_5.0x3.2mm"),
    # No local footprint and no exact-size stock match - left unassigned.
    "NX1612AA": None,
    "NX1612SA": None,
    "NX2012SA": None,
    "NX3225GB": None,
    "NX3225GD": None,
    "NX4025DA": None,
    "NX8045GB": None,
}

EXCLUDE_FAMILY_RE = re.compile(r"^NX.{4}S[DFG]$")

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

CSV_COLUMNS = ["Part Number", "Frequency", "Frequency Stability",
               "Frequency Tolerance", "Load Capacitance", "ESR",
               "Operating Temperature", "Package", "Manufacturer", "Source"]


def load_parts(csv_path):
    with open(csv_path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in CSV_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise SystemExit(f"ERROR: {csv_path} is missing columns {missing}")
        rows = list(reader)

    parts = []
    seen_ids = {}
    footprint_counts = {}
    unmapped_families = {}
    excluded_families = {}

    for r in rows:
        part_number = r["Part Number"].strip()
        family = r["Package"].strip()

        if EXCLUDE_FAMILY_RE.match(family):
            excluded_families[family] = excluded_families.get(family, 0) + 1
            continue

        if part_number in seen_ids:
            print(f"WARNING: duplicate id '{part_number}' - skipping")
            continue
        seen_ids[part_number] = True

        if family not in FOOTPRINT_MAP:
            unmapped_families[family] = unmapped_families.get(family, 0) + 1
        fp_entry = FOOTPRINT_MAP.get(family)
        if fp_entry is None:
            footprint_str = ""
            key = f"(none: {family})"
        else:
            footprint_str = f"{fp_entry[0]}:{fp_entry[1]}"
            key = footprint_str
        footprint_counts[key] = footprint_counts.get(key, 0) + 1

        frequency = r["Frequency"].strip()
        parts.append((
            part_number,                      # id
            frequency,                        # Value
            footprint_str,                    # Footprints
            SYMBOL_MAP.get(family, DEFAULT_SYMBOL),
            frequency,
            r["Frequency Stability"].strip(),
            r["Frequency Tolerance"].strip(),
            r["Load Capacitance"].strip(),
            r["ESR"].strip(),
            r["Operating Temperature"].strip(),
            family,
            r["Manufacturer"].strip() or MANUFACTURER,
            part_number,
        ))

    print(f"\nLoaded {len(parts)} parts from {len(rows)} CSV rows.")
    if excluded_families:
        n_excluded = sum(excluded_families.values())
        print(f"Excluded {n_excluded} parts from families matching EXCLUDE_FAMILY_RE:")
        for fam, n in sorted(excluded_families.items(), key=lambda x: -x[1]):
            print(f"  {fam!r}: {n} parts")
    if unmapped_families:
        print("ERROR: packages with no FOOTPRINT_MAP entry "
              "(unrecognized, not just unmapped-by-design):")
        for fam, n in sorted(unmapped_families.items(), key=lambda x: -x[1]):
            print(f"  {fam!r}: {n} parts")

    print("\nFootprint assignment summary:")
    for fp, n in sorted(footprint_counts.items(), key=lambda x: -x[1]):
        print(f"  {fp}: {n} parts")

    return parts


def write_database(db_path, table, parts):
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
        Frequency TEXT,
        [Frequency Stability] TEXT,
        [Frequency Tolerance] TEXT,
        [Load Capacitance] TEXT,
        ESR TEXT,
        [Operating Temperature] TEXT,
        Package TEXT,
        Manufacturer TEXT,
        [Part Number] TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, Frequency, [Frequency Stability],
         [Frequency Tolerance], [Load Capacitance], ESR,
         [Operating Temperature], Package, Manufacturer, [Part Number])
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, parts)

    conn.commit()
    conn.execute("VACUUM")
    conn.close()


def build_field_defs():
    return [
        {"column": "Frequency", "name": "Frequency", "visible_on_add": False,
         "visible_in_chooser": True, "show_name": True},
        {"column": "Frequency Stability", "name": "Frequency Stability",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Frequency Tolerance", "name": "Frequency Tolerance",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Load Capacitance", "name": "Load Capacitance",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "ESR", "name": "ESR", "visible_on_add": False,
         "visible_in_chooser": True, "show_name": True},
        {"column": "Operating Temperature", "name": "Operating Temperature",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Package", "name": "Package", "visible_on_add": False,
         "visible_in_chooser": True, "show_name": True},
        {"column": "Manufacturer", "name": "Manufacturer", "visible_on_add": False,
         "visible_in_chooser": True, "show_name": False},
        {"column": "Part Number", "name": "Part Number", "visible_on_add": False,
         "visible_in_chooser": True, "show_name": False},
        {"column": "Value", "name": "Value", "visible_on_add": True,
         "visible_in_chooser": True, "show_name": False},
    ]


def write_kicad_dbl(dbl_path, db_path, table):
    content = {
        "meta": {"version": 0},
        "name": "NDK Crystals",
        "description": "NDK quartz crystal resonators, built from "
                        "data/xtal_ndk_parts.csv.",
        "source": {
            "type": "odbc",
            "dsn": "",
            "username": "",
            "password": "",
            "timeout_seconds": 2,
            "connection_string": (
                "Driver={SQLite3 ODBC Driver};"
                f"Database=${{CWD}}/xtal_ndk.db"
            ),
        },
        "libraries": [
            {
                "name": "NX",
                "table": table,
                "key": "id",
                "symbols": "Symbol",
                "footprints": "Footprints",
                "fields": build_field_defs(),
                "properties": {"description": "Package"},
            }
        ],
    }

    with open(dbl_path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=4, ensure_ascii=False)
        f.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build the xtal_ndk KiCad database library from "
                    "data/xtal_ndk_parts.csv.")
    parser.add_argument("--csv", required=True,
                        help="Path to data/xtal_ndk_parts.csv.")
    parser.add_argument("--db", required=True,
                        help="Path to the output .db SQLite file.")
    parser.add_argument("--table", required=True,
                        help="Name of the table to (re)create.")
    parser.add_argument("--kicad-dbl", required=True,
                        help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def main():
    args = parse_args()
    parts = load_parts(args.csv)
    write_database(args.db, args.table, parts)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(parts)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
