# Imports Littelfuse SMAJ/SMBJ/SMCJ-series TVS (transient-voltage-
# suppression) protection diode data into a KiCad database-library
# SQLite file.
#
# NEW CATEGORY: this is kicadlib's first `diode_` database library.
# NAMING.md doesn't document a diode section - it explicitly lists
# `diodes` among the small hand-maintained libraries considered out of
# scope for the database-library scheme. Jonas asked for this one as a
# database library anyway (630 SKUs is well past the "hand-author one
# symbol per part" threshold the other database libraries use as their
# bar), so this follows the same `<type>_<subtype>_<vendor>` naming
# shape as the rest of the repo (`diode_tvs_littlefuse`) without an
# established NAMING.md section to match against - a future addition to
# NAMING.md documenting a `diode_tvs` (and maybe `diode_rect`/
# `diode_zener`/...) type-code table would be a reasonable follow-up if
# more diode libraries get added later.
#
# SOURCE DATA: one CSV, three series merged (Littelfuse's own product
# table export) - SMAJ (400-600W, DO-214AC / "SMA" package), SMBJ
# (600-800W, DO-214AA / "SMB"), SMCJ (1500-2000W, DO-214AB / "SMC"). The
# "Watts (W)" figure is NOT constant per series - a handful of very
# high-standoff-voltage SMAJ parts (300-440V, 10 rows) are rated 600W
# instead of the series' usual 400W - so it's read per-row from the CSV,
# never assumed from the series name.
#
# DIRECTIONALITY: the CSV's own "Uni / Bi-Directional" column is blank
# for 422 of 630 rows (Littelfuse's export just doesn't fill it in
# consistently) - so this derives directionality from the part-number
# suffix instead: "...CA" = bidirectional, plain "...A" = unidirectional
# (standard TVS part-numbering convention, and Littelfuse's SMAJ/SMBJ/
# SMCJ families always come in exactly these two suffix forms - "-E" /
# "-E3/61" tape-and-reel packaging suffixes are stripped first). This was
# cross-checked against every row where the CSV column IS populated
# (208 rows) - zero mismatches - before trusting it for the 422 blank
# rows too.
#
# SYMBOL: per Jonas's explicit direction - Device:D_TVS (KiCad's stock
# bidirectional TVS symbol) for the "...CA" parts, diode_misc:D_TVS_Uni
# (this repo's own hand-drawn unidirectional TVS symbol, in
# library/diode_misc.kicad_sym - renamed from the original
# diodes_misc.kicad_sym, kept as diodes_misc.bak) for the plain "...A"
# parts. This is a real split by SYMBOL, not just a field - directionality isn't
# exposed as its own always-shown field for that reason, though a `Type`
# column is still in the database (visible in the chooser, hidden on the
# schematic) so it's searchable/filterable there.
#
# ID: per Jonas's explicit direction, the id is the exact CSV part
# number, unmodified - no synthesized code. Rows whose part number ends
# in a "-E"/"-E3/61" tape-and-reel packaging suffix are dropped entirely
# (not merged into their base-part sibling's row, just excluded) -
# Jonas's final call after first trying "keep every row, id = literal
# part number" (630 rows) and then deciding the packaging variants
# shouldn't be in the library at all. Verified every one of the 302
# suffixed part numbers in the source CSV has a non-suffixed sibling row
# supplying the same part, so nothing is lost by dropping them outright
# - this leaves the same 328 parts the very first cut of this importer
# produced (back when packaging variants were merged rather than
# dropped), just reached by exclusion instead of dedup. The 328
# remaining "Part Number" values are already unique strings in the
# source CSV, so ids never collide - the seen_ids check below is a
# safety net only, not expected to ever fire on this dataset.
#
# FOOTPRINT: package -> KiCad's own standard Diode_SMD.pretty footprints
# (exact matches, no custom footprint needed) - SMA (DO-214AC) ->
# Diode_SMD:D_SMA, SMB (DO-214AA) -> Diode_SMD:D_SMB, SMC (DO-214AB) ->
# Diode_SMD:D_SMC.
#
# FIELD VISIBILITY: Value (breakdown voltage) and Power Rating are shown
# on the schematic (Jonas named both as important metrics, and this
# mirrors the bead_emi_murata_blm precedent of surfacing the metrics
# that matter for part selection rather than tucking everything into the
# chooser). Standoff Voltage, Type (Uni/Bi), Agency Approvals, and Part
# Number are chooser-visible only.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "Littelfuse"

FOOTPRINT_MAP = {
    "SMA": "Diode_SMD:D_SMA",
    "SMB": "Diode_SMD:D_SMB",
    "SMC": "Diode_SMD:D_SMC",
}
SYMBOL_BI = "Device:D_TVS"
SYMBOL_UNI = "diode_misc:D_TVS_Uni"

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PART_SUFFIXES = ["-E3/61", "-E3", "-E"]


def strip_packaging_suffix(pn):
    pn = pn.strip()
    for suf in PART_SUFFIXES:
        if pn.endswith(suf):
            return pn[: -len(suf)]
    return pn


def is_bidirectional(part_number):
    base = strip_packaging_suffix(part_number)
    return base.endswith("CA")


def format_voltage_disp(volts):
    s = f"{volts:g}"
    return f"{s}V"


def load_diodes(csv_path):
    diodes = []
    seen_ids = {}

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            part_number = row["Part Number"].strip()

            if part_number != strip_packaging_suffix(part_number):
                # Tape-and-reel packaging variant of another row in this
                # CSV - excluded entirely, per Jonas's direction (see
                # header comment).
                continue

            series = row["Series"].strip()
            package = series[:-1] if series.endswith("J") else series

            if package not in FOOTPRINT_MAP:
                print(f"WARNING: no footprint mapped for package "
                      f"{package!r} (series {series!r}) - {part_number}, "
                      f"skipping")
                continue
            footprint = FOOTPRINT_MAP[package]

            bidirectional = is_bidirectional(part_number)
            symbol = SYMBOL_BI if bidirectional else SYMBOL_UNI
            type_str = "Bidirectional" if bidirectional else "Unidirectional"

            vbr = float(row["MIN VBR@IT  (V)"])
            vr = row["VR (Vstandoff)"].strip()
            watts = row["Watts (W)"].strip()
            ipp_8x20 = row["I PP 8x20µs (A)"].strip()
            ipp_10x1000 = row["I PP 10x1000µs (A)"].strip()
            approvals = row["Agency Approvals "].strip()

            id_str = part_number
            if id_str in seen_ids:
                print(f"WARNING: duplicate part number '{id_str}' in the "
                      f"source CSV (unexpected - this dataset was verified "
                      f"to have no duplicates), skipping")
                continue
            seen_ids[id_str] = part_number

            value_disp = format_voltage_disp(vbr)
            ipp_bits = []
            if ipp_8x20:
                ipp_bits.append(f"Ipp(8x20us) {ipp_8x20}A")
            if ipp_10x1000:
                ipp_bits.append(f"Ipp(10x1000us) {ipp_10x1000}A")
            ipp_str = ", ".join(ipp_bits)
            approval_str = f", {approvals} listed" if approvals else ""
            description = (f"{value_disp} min. breakdown, {vr}V standoff, "
                            f"{watts}W peak pulse power, "
                            f"{type_str.lower()}"
                            f"{', ' + ipp_str if ipp_str else ''}, "
                            f"{package} ({series}){approval_str}")

            print(f"{len(diodes) + 1} {id_str}, "
                  f"{value_disp} VBR, {watts}W, {type_str}")

            diode = (id_str, value_disp, footprint, symbol, value_disp,
                      f"{vr}V", f"{watts}W", type_str, approvals,
                      description, part_number, MANUFACTURER)
            diodes.append(diode)

    return diodes


def write_database(db_path, table, diodes):
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
        "Breakdown Voltage" TEXT,
        "Standoff Voltage" TEXT,
        "Power Rating" TEXT,
        Type TEXT,
        "Agency Approvals" TEXT,
        Description TEXT,
        "Part Number" TEXT,
        Manufacturer TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, "Breakdown Voltage",
         "Standoff Voltage", "Power Rating", Type, "Agency Approvals",
         Description, "Part Number", Manufacturer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, diodes)

    conn.commit()
    conn.close()


def build_field_defs():
    return [
        {"column": "Breakdown Voltage", "name": "Breakdown Voltage",
         "visible_on_add": True, "visible_in_chooser": True, "show_name": False},
        {"column": "Standoff Voltage", "name": "Standoff Voltage",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Power Rating", "name": "Power Rating",
         "visible_on_add": True, "visible_in_chooser": True, "show_name": False},
        {"column": "Type", "name": "Type",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": False},
        {"column": "Agency Approvals", "name": "Agency Approvals",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Manufacturer", "name": "Manufacturer",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Part Number", "name": "Part Number",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Value", "name": "Value",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": False},
    ]


def write_kicad_dbl(dbl_path, db_path, table):
    content = {
        "meta": {"version": 0},
        "name": "Littelfuse SMAJ/SMBJ/SMCJ TVS Diodes",
        "description": ("Littelfuse SMAJ/SMBJ/SMCJ-series TVS protection "
                         "diode library (uni- and bi-directional, KiCad "
                         "standard DO-214 footprints)"),
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
                "name": "TVS",
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
        description="Import Littelfuse SMAJ/SMBJ/SMCJ TVS diode CSV "
                     "export into a KiCad database-library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s).")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file.")
    parser.add_argument("--table", required=True,
                         help="Table name, e.g. diode_tvs_littlefuse.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def main():
    args = parse_args()
    diodes = []
    for csv_path in args.csv:
        diodes.extend(load_diodes(csv_path))
    write_database(args.db, args.table, diodes)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(diodes)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
