#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Converts the legacy hand-maintained library/xtal_NDK.kicad_sym (222
# per-part symbols) into the xtal_ndk KiCad database library.
#
# SOURCE: this reads library/xtal_NDK.kicad_sym directly - NOT
# data/xtal_ndk.csv. That CSV (uploaded separately, 297 rows across only
# 7 of the 21 package families the legacy symbols cover, part number only
# recoverable from a URL query string, no clean overlap with the legacy
# library's contents) turned out to be unrelated staged data, not a
# source for this conversion - confirmed against the original importer
# that built xtal_NDK (scripting/old_stuff/digikey_import_NDK.py), which
# used a Digikey export no longer present in the repo. Per Jonas's
# decision, only the 222 existing symbols are converted; xtal_ndk.csv is
# left untouched for a possible separate future task.
#
# Every legacy symbol's Value / Part Number property and the symbol name
# itself are identical (spot-checked across all 222), and all 222 are
# distinct, so the part number is used directly as the database id - no
# synthesized code, matching how the legacy library already keyed parts.
#
# The legacy "Description" property is a machine-generated string in a
# fixed format ("f=%s, Stability:%s, Tol:%s,Load capacitance:%s,esr:%s,
# Temp:%s" - see digikey_import_NDK.py's template), so it's parsed back
# into separate Frequency Stability / Frequency Tolerance / Load
# Capacitance / ESR / Operating Temperature columns rather than kept as
# one opaque blob - this parses cleanly for all 222 parts (verified).
#
# SYMBOL: every part uses the single stock Device:Crystal_GND24 symbol
# (4 pins: 1/3 = crystal terminals, 2/4 = GND), replacing the legacy
# per-part 2-pin symbols (pins numbered "1"/"3" there too - Crystal_GND24
# is a drop-in pin-numbering upgrade, not a renumbering). Per Jonas's
# direction. EXCEPTION: NX3215SA (4 parts) uses the plain 2-pin
# Device:Crystal symbol instead, per Jonas's explicit follow-up - see
# SYMBOL_MAP below.
#
# FOOTPRINT: the legacy symbols' "Footprint" property was never a real
# footprint reference - digikey_import_NDK.py actually populated it from
# the Digikey "Series" column (e.g. "NX2016AB"), a package/series code,
# not a library:footprint string. Of the 21 distinct codes used across
# the 222 parts, only 6 had a matching file in modules/footprints.pretty
# at all (NX1255, NX2012, NX2520, NX2520SA, NX3225, NX3225SA), and two of
# those six (NX2520, NX3225) turned out to be byte-for-byte geometric
# duplicates of their "SA" sibling - just an older generic name for the
# same land pattern - so they're dropped rather than migrated twice.
# NX2012 is only a 2-pad footprint (no GND pads) and can't fit
# Crystal_GND24 at all, so it's not used either. That leaves 3 footprints
# actually migrated (via scripting/gen_ndk_footprints.py) into the new
# footprints/NDK.pretty/: NX1255GB, NX2520SA, NX3225SA.
#
# Per Jonas's direction, other package families reuse one of those 3
# where the land pattern is genuinely the same size (NX3225GA/GB/GD/SC
# -> NX3225SA - confirmed against
# data/xtal_ndk.csv's own Package size(LxW) column, which lists the same
# 3.2x2.5mm for every NX3225* row it has), or map to a stock KiCad
# Crystal footprint where the size has an exact 4-pin match and no local
# file exists (NX2016* -> Crystal_SMD_2016-4Pin_2.0x1.6mm; NX5032GB/GC/SA
# -> Crystal_SMD_5032-4Pin_5.0x3.2mm; see below for NX5032GA). The
# remaining families - NX1612* (1.6x1.2mm), NX2012SA (2-pad), NX4025DA
# (4.0x2.5mm), NX8045GB (8.0x4.5mm) - have neither a local footprint nor
# an exact-size stock
# match, so those 35 parts are imported with an empty Footprints value
# (KiCad will show them in the chooser with no preview/assigned
# footprint) rather than guessing a near-size substitute. See the
# FOOTPRINT_MAP below and the console output's "no footprint assigned"
# summary for the exact list.
#
# NX3215SA (3.2x1.5mm, 4 parts) was originally in that unmapped group
# too - no local footprint, and no exact-size stock 4-pin match. Per
# Jonas's follow-up it now uses the 2-pin Device:Crystal symbol instead
# of Crystal_GND24 (see SYMBOL_MAP above). It briefly pointed at the
# stock Crystal_SMD_G8-2Pin_3.2x1.5mm footprint (a generic 2-pad match
# confirmed against KiCad's own Crystal.pretty listing), then switched
# to a real local footprint per Jonas's direction once he placed
# footprints/NDK.pretty/NX3215SA.kicad_mod (+ matching NX3215SA.step in
# NDK.3dshapes/) - see FOOTPRINT_MAP below.
#
# NX5032GA (5.0x3.2mm, part of the default Crystal_GND24/4-pin-footprint
# group above) is a further exception per Jonas's direction: it now uses
# the 2-pin Device:Crystal symbol (see SYMBOL_MAP below) instead of
# Crystal_GND24. This is a correctness fix, not just a style choice -
# RS Components lists "Pin Count: 2" for NX5032GA (and for NX5032GB),
# unlike its NX5032GC ("4-SMD, No Lead") and NX5032SA (4-pin metal-can)
# siblings, which keep the 4-pin default. The footprint is switched to
# match: Crystal_SMD_5032-2Pin_5.0x3.2mm, a stock KiCad Crystal.pretty
# footprint at the same 5.0x3.2mm land size (confirmed to exist upstream
# in kicad-footprints). NX5032GB looks like it may be 2-pin as well by
# the same source, but only NX5032GA was in scope for this change -
# worth revisiting NX5032GB the same way in a future pass.
#
# EXCLUDED FAMILIES: per Jonas's direction, any family whose code ends
# in S + D/F/G (NX2520SD, NX2520SG - the only two present in the 222
# legacy symbols today, 4 parts total; NX****SF is a placeholder for a
# suffix that doesn't currently appear but is excluded on the same
# basis if a future re-import adds one) is dropped entirely rather
# than imported - see EXCLUDE_FAMILY_RE below. These were previously
# aliased to the NX2520SA footprint like NX3225's siblings; Jonas
# wants them gone from the library rather than kept as aliases.
import argparse
import json
import re
import sqlite3

MANUFACTURER = "NDK"

# legacy Footprint-property code (family/series) -> symbol reference.
# Every family defaults to the 4-pin Device:Crystal_GND24 unless listed
# here explicitly (see header comment for the NX3215SA/NX5032GA exceptions).
DEFAULT_SYMBOL = "Device:Crystal_GND24"
SYMBOL_MAP = {
    "NX3215SA": "Device:Crystal",
    "NX5032GA": "Device:Crystal",
}

# legacy Footprint-property code (family/series) -> (footprint library
# nickname, footprint name), or None if no footprint is assigned.
FOOTPRINT_MAP = {
    "NX1255GB": ("Jonas", "NX1255GB"),
    "NX2520SA": ("Jonas", "NX2520SA"),
    "NX3225SA": ("Jonas", "NX3225SA"),
    "NX3225GA": ("Jonas", "NX3225SA"),
    "NX3225GB": ("Jonas", "NX3225SA"),
    "NX3225GD": ("Jonas", "NX3225SA"),
    "NX3225SC": ("Jonas", "NX3225SA"),
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
    "NX3215SA": ("Jonas", "NX3215SA"),
    "NX4025DA": None,
    "NX8045GB": None,
}

# Families dropped entirely - not imported at all, not even unmapped.
# See the "EXCLUDED FAMILIES" header note above.
EXCLUDE_FAMILY_RE = re.compile(r"^NX.{4}S[DFG]$")

SYMBOL_BLOCK_RE = re.compile(r'(?=^\t\(symbol ")', re.M)
NAME_RE = re.compile(r'^\t\(symbol "([^"]+)"')
DESC_RE = re.compile(
    r'^f=(?P<freq>[^,]*), Stability:(?P<stab>[^,]*), Tol:(?P<tol>[^,]*),'
    r'Load capacitance:(?P<loadcap>[^,]*),esr:(?P<esr>[^,]*),Temp:(?P<temp>.*)$')

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def prop(block, name):
    m = re.search(r'\n\t\t\(property "' + re.escape(name) + r'" "([^"]*)"', block)
    return m.group(1) if m else None


def load_parts(sym_path):
    text = open(sym_path, encoding="utf-8").read()
    blocks = SYMBOL_BLOCK_RE.split(text)[1:]

    parts = []
    seen_ids = {}
    footprint_counts = {}
    unmapped_families = {}
    excluded_families = {}

    for b in blocks:
        m = NAME_RE.match(b)
        if not m:
            continue
        name = m.group(1)

        part_number = prop(b, "Part Number") or name
        manufacturer = prop(b, "Manufacturer") or MANUFACTURER
        frequency = prop(b, "Frequency") or ""
        family_raw = prop(b, "Footprint") or ""
        # A couple of legacy rows have stray trailing text on this field
        # (e.g. "NX3225GB, Automotive") - not a different package, just
        # inconsistent manual entry; normalize to the bare family code.
        family = family_raw.split(",")[0].strip()

        if EXCLUDE_FAMILY_RE.match(family):
            excluded_families.setdefault(family, 0)
            excluded_families[family] += 1
            continue

        desc = prop(b, "Description") or ""
        dm = DESC_RE.match(desc)
        if dm:
            stability = dm.group("stab")
            tolerance = dm.group("tol")
            load_cap = dm.group("loadcap")
            esr = dm.group("esr")
            op_temp = dm.group("temp")
        else:
            print(f"WARNING: could not parse Description for {name}: {desc!r}")
            stability = tolerance = load_cap = esr = op_temp = ""

        id_str = part_number
        if id_str in seen_ids:
            print(f"WARNING: duplicate id '{id_str}' - skipping")
            continue
        seen_ids[id_str] = True

        fp_entry = FOOTPRINT_MAP.get(family)
        if family not in FOOTPRINT_MAP:
            unmapped_families.setdefault(family, 0)
            unmapped_families[family] += 1
        if fp_entry is None:
            footprint_str = ""
            footprint_counts.setdefault(f"(none: {family})", 0)
            footprint_counts[f"(none: {family})"] += 1
        else:
            fp_lib, fp_name = fp_entry
            footprint_str = f"{fp_lib}:{fp_name}"
            footprint_counts.setdefault(footprint_str, 0)
            footprint_counts[footprint_str] += 1

        symbol = SYMBOL_MAP.get(family, DEFAULT_SYMBOL)

        parts.append((
            id_str,
            frequency,           # Value
            footprint_str,       # Footprints
            symbol,               # Symbol
            frequency,
            stability,
            tolerance,
            load_cap,
            esr,
            op_temp,
            family,
            manufacturer,
            part_number,
        ))

    print(f"\nLoaded {len(parts)} parts from {len(blocks)} legacy symbols.")
    if excluded_families:
        n_excluded = sum(excluded_families.values())
        print(f"Excluded {n_excluded} parts from families matching EXCLUDE_FAMILY_RE:")
        for fam, n in sorted(excluded_families.items(), key=lambda x: -x[1]):
            print(f"  {fam!r}: {n} parts")
    if unmapped_families:
        print("ERROR: legacy Footprint codes with no FOOTPRINT_MAP entry "
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
        "description": "NDK quartz crystal resonators, converted from the legacy "
                        "xtal_NDK.kicad_sym hand-maintained library.",
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
                "name": "NDK",
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
        json.dump(content, f, indent=4)
        f.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert the legacy library/xtal_NDK.kicad_sym into the "
                     "xtal_ndk KiCad database library.")
    parser.add_argument("--sym", required=True,
                         help="Path to the legacy library/xtal_NDK.kicad_sym.")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def main():
    args = parse_args()
    parts = load_parts(args.sym)
    write_database(args.db, args.table, parts)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(parts)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
