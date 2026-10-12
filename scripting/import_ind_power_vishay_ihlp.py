# Imports Vishay IHLP shielded power inductor data into a KiCad
# database-library SQLite file.
#
# SCOPE: this covers only the 4 case sizes (1212, 1616, 2020, 2525 - 103
# of the 222 parts in the legacy library/vishay_IHLP_inductors.kicad_sym)
# that already had a footprint in modules/footprints.pretty. The other 4
# case sizes present in the legacy symbol library (3232, 4040, 5050,
# 6767) are NOT included: building accurate footprints for them requires
# Vishay's official recommended-land-pattern dimensions, and the web
# tools available in this session could not reliably extract those
# numbers from Vishay's PDFs (repeated re-reads of the same datasheet
# attributed the same numbers to different dimensions each time, and the
# 4040DZ datasheet's pad-layout diagram couldn't be found at all). Per
# Jonas's decision, those 4 case sizes are deferred rather than shipped
# with unverified geometry - extending this library to cover them is a
# separate follow-up once real land-pattern dimensions are available
# (either sourced from a cleaner PDF read, or supplied directly).
#
# Source data (data/ind_power_vishay_ihlp.csv) was decoded from the
# legacy .kicad_sym's per-part "Description" property (e.g. "1.2µH,
# ±20%, I=5A, I_sat=4A, DCR=27 mOhm Max, Self resonance: 65MHz, -55°C ~
# 125°C, ...") plus its "Part Number" property, from which the 2-letter
# Vishay series code (e.g. BZ, CZ, AB - right after IHLP<size> in the
# part number, e.g. "IHLP1212BZER1R2M11") was extracted. The IEC-style
# value token used in ids (e.g. "1u2", "100n") is taken directly from
# the legacy symbol's own name (e.g. "IHLP1212_1u2_4b") rather than
# re-derived, since it was already correct there.
#
# Id format follows NAMING.md section 4's inductor pattern:
# L<case>_<value>_<tolerance>_<current>. Within the 103 in-scope parts
# this collides for exactly 2 (case, value, tolerance, current) groups -
# both are BZ/CZ pairs sharing the same case/inductance/tolerance/rated-
# current but with genuinely different DCR/I_sat/SRF (e.g.
# IHLP2020BZERR10M11 vs IHLP2020CZERR10M11, both 100nH/±20%/21A but
# 2.9mOhm@266MHz vs 2.9mOhm@333MHz with different I_sat). Per Jonas's
# instruction, the 2-letter series code is folded into the id ONLY for
# those colliding groups (both members of each pair get the suffix, not
# just the second, so neither is left looking unmarked) - see
# import_res_chip_vishay_crcw.py for the same conditional-suffix pattern
# used on the resistor side.
#
# Footprints: per Jonas's explicit direction, footprints are built PER
# SERIES (not one shared footprint per case size), even though the 2D
# pad layout and body outline are identical across every series within
# a case (verified against this dataset - the Description field's body
# L x W is constant per case regardless of series). What differs per
# series is the 3D model. All 11 (case, series) footprints were built by
# scripting/gen_ihlp_footprints.py, which took the legacy pad geometry
# from modules/footprints.pretty verbatim, added a courtyard (pad/body
# bounding box + 0.25mm) and an F.Fab body outline (both missing from
# the legacy files), fixed the legacy silkscreen's vertical side lines
# (which ran straight through the pads' copper in the legacy files - a
# real DRC violation) by clipping them to the Y-gap outside the pads,
# and modernized the file format from KiCad v4's bare (module ...) to
# the current (footprint "...") s-expression format. 3D models were
# copied from modules/packages3d into footprints/Vishay_IHLP.3dshapes/
# (renamed to plain "IHLP<case><series>.step") and are referenced via
# ${JONAS_KICADLIB}/footprints/Vishay_IHLP.3dshapes/..., matching the
# path convention already used by the repo's other custom footprints
# (Murata_GA3, Panasonic_ECHU) - keeps the 3D model bundled with the
# footprint library instead of depending on modules/packages3d.
#
# CAVEATS to flag:
# - IHLP1212 has no per-series STEP model available (only a generic
#   model, copied in as "IHLP1212.step") - all 3 series (AB/AE/BZ)
#   share it.
# - IHLP2525BD's 3D model uses the "(1.5-10uH)" STEP variant (Vishay
#   publishes two body-height variants for this series depending on
#   inductance) - correct for all 3 BD parts in this dataset (3.3-10uH),
#   but would need the "(0.1-1.0uH)" variant if this library is ever
#   extended with lower-value BD parts.
# - IHLP2525's 3D model offset/rotate is UNCALIBRATED: the legacy
#   footprint referenced a hand-authored, inch-scaled WRL file with a
#   broken absolute path; there's no calibration reference for the new
#   mm-native STEP models, so a best-effort transform (matching the 2020
#   footprint's pattern) was used instead. Verify in KiCad's 3D viewer.
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

MANUFACTURER = "Vishay"

# (case, series) -> "LibraryNickname:FootprintName" - all built by
# scripting/gen_ihlp_footprints.py, originally into
# footprints/Vishay_IHLP.pretty/, later consolidated into the single
# footprints/Jonas.pretty/ custom-footprint library (fp-lib-table
# nickname "Jonas").
FOOTPRINT_MAP = {
    ("1212", "AB"): "Jonas:IHLP1212AB",
    ("1212", "AE"): "Jonas:IHLP1212AE",
    ("1212", "BZ"): "Jonas:IHLP1212BZ",
    ("1616", "AB"): "Jonas:IHLP1616AB",
    ("1616", "BZ"): "Jonas:IHLP1616BZ",
    ("2020", "AB"): "Jonas:IHLP2020AB",
    ("2020", "BZ"): "Jonas:IHLP2020BZ",
    ("2020", "CZ"): "Jonas:IHLP2020CZ",
    ("2525", "BD"): "Jonas:IHLP2525BD",
    ("2525", "CZ"): "Jonas:IHLP2525CZ",
    ("2525", "EZ"): "Jonas:IHLP2525EZ",
}

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def format_current(amps):
    # 5.0 -> "5A0", 21.0 -> "21A0", 3.8 -> "3A8" - same "." -> unit-letter
    # substitution as the rest of the repo's ids, matching NAMING.md's
    # own inductor example ("1A2").
    s = f"{float(amps):.1f}"
    int_part, dec_part = s.split(".")
    return f"{int_part}A{dec_part}"


def load_inductors(csv_paths):
    raw_rows = []
    for csv_path in csv_paths:
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            raw_rows.extend(csv.DictReader(csvfile))

    prepared = []
    skipped_footprint = {}
    for row in raw_rows:
        case, series = row["Case"], row["Series"]
        if (case, series) not in FOOTPRINT_MAP:
            skipped_footprint[(case, series)] = skipped_footprint.get((case, series), 0) + 1
            continue

        value_token = row["Value Token"]
        tolerance = row["Tolerance (%)"]
        irated = float(row["Rated Current (A)"])
        current_str = format_current(irated)

        base_id = f"L{case}_{value_token}_{tolerance}_{current_str}"
        prepared.append({
            "base_id": base_id, "case": case, "series": series,
            "value_disp": row["Inductance Display"],
            "value_h": row["Inductance (H)"],
            "tolerance": tolerance, "irated": row["Rated Current (A)"],
            "isat": row["Saturation Current (A)"],
            "dcr": row["DCR (mOhm)"], "dcr_grade": row["DCR Grade"],
            "srf": row["SRF (MHz)"], "tmin": row["Temp Min (C)"],
            "tmax": row["Temp Max (C)"], "part_number": row["Part Number"],
        })

    base_id_series = {}
    for r in prepared:
        base_id_series.setdefault(r["base_id"], set()).add(r["series"])
    needs_series_suffix = {bid for bid, s in base_id_series.items() if len(s) > 1}

    count = 0
    inductors = []
    seen_ids = {}
    disambiguated = 0
    for r in prepared:
        if r["base_id"] in needs_series_suffix:
            id_str = f"{r['base_id']}_{r['series']}"
            disambiguated += 1
        else:
            id_str = r["base_id"]

        if id_str in seen_ids:
            print(f"WARNING: duplicate id '{id_str}' - "
                  f"{r['part_number']} collides with {seen_ids[id_str]}, skipping")
            continue
        seen_ids[id_str] = r["part_number"]

        footprint = FOOTPRINT_MAP[(r["case"], r["series"])]
        srf = r["srf"] if r["srf"] != "-" else "N/A"
        count += 1
        description = (f"{r['value_disp']}, ±{r['tolerance']}%, "
                        f"I={r['irated']}A, Isat={r['isat']}A, "
                        f"DCR={r['dcr']}mOhm {r['dcr_grade']}, SRF={srf}, "
                        f"{r['tmin']}C to {r['tmax']}C, series {r['series']}, "
                        f"EIA {r['case']}")

        inductor = (id_str, r["value_disp"], footprint, "Device:L",
                    r["value_disp"], f"{r['tolerance']}%", r["irated"] + "A",
                    r["isat"] + "A", f"{r['dcr']}mOhm {r['dcr_grade']}", srf,
                    f"{r['tmin']}C to {r['tmax']}C", r["series"], description,
                    r["part_number"], MANUFACTURER)
        inductors.append(inductor)

    print(f"\n{disambiguated} parts needed a series suffix to stay unique "
          f"({len(needs_series_suffix)} colliding case/value/tolerance/"
          f"current group(s))")

    if skipped_footprint:
        total_skipped = sum(skipped_footprint.values())
        print(f"\nSkipped {total_skipped} rows with no footprint mapped:")
        for code, n in sorted(skipped_footprint.items(), key=lambda x: -x[1]):
            print(f"  {code}: {n} parts")

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
        "Saturation Current" TEXT,
        DCR TEXT,
        SRF TEXT,
        "Temp Range" TEXT,
        Series TEXT,
        Description TEXT,
        "Part Number" TEXT,
        Manufacturer TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, Inductance, Tolerance,
         "Rated Current", "Saturation Current", DCR, SRF, "Temp Range",
         Series, Description, "Part Number", Manufacturer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, inductors)

    conn.commit()
    conn.close()


def build_field_defs():
    return [
        {"column": "Inductance", "name": "Inductance",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Tolerance", "name": "Tolerance",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        {"column": "Rated Current", "name": "Rated Current",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Saturation Current", "name": "Saturation Current",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "DCR", "name": "DCR",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "SRF", "name": "SRF",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Temp Range", "name": "Temp Range",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Series", "name": "Series",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Manufacturer", "name": "Manufacturer",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Part Number", "name": "Part Number",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Value", "name": "Value",
         "visible_on_add": True, "visible_in_chooser": True, "show_name": False},
    ]


def write_kicad_dbl(dbl_path, db_path, table):
    content = {
        "meta": {"version": 0},
        "name": "Vishay IHLP Power Inductors (1212/1616/2020/2525)",
        "description": ("Vishay IHLP shielded power inductor library - "
                         "case sizes 1212, 1616, 2020, 2525 only (3232/"
                         "4040/5050/6767 pending verified land-pattern "
                         "dimensions, see importer header)"),
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
                "name": "IHLP",
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
        description="Import the Vishay IHLP power inductor CSV (decoded "
                     "from the legacy vishay_IHLP_inductors.kicad_sym) "
                     "into a KiCad database-library SQLite file.")
    parser.add_argument("--csv", required=True, nargs="+",
                         help="Path(s) to the input CSV(s).")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file.")
    parser.add_argument("--table", required=True,
                         help="Table name, e.g. ind_power_vishay_ihlp.")
    parser.add_argument("--kicad-dbl", required=True,
                         help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def main():
    args = parse_args()
    inductors = load_inductors(args.csv)
    write_database(args.db, args.table, inductors)
    write_kicad_dbl(args.kicad_dbl, args.db, args.table)

    print(f"\nImported {len(inductors)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
