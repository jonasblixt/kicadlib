#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Builds the xtal_epson KiCad database library from data/xtal_epson.csv
# (MHz crystals) and data/xtal_epson_32k.csv (32.768 kHz crystals).
#
# Chooser name Epson -> TSX-FA-FC on 2026-10-19 (cleanup review A4.4): the
# series families in the library.
#
# SOURCE: data/xtal_epson.csv is a transcription of Epson's own crystal-
# unit parametric search (epsondevice.com/crystal/en/product-search/
# crystal-unit.html?model=...), captured 2026-10-08 for the three series
# in the datasheet Jonas saved (poetato datasheets/crystals/
# "FA-238(V),TSX-3225_Series_Rev_Dec_2015.pdf"): TSX-3225 (264 products),
# FA-238 (240) and FA-238V (88). Per Jonas, only parts rated for
# -40..+85 C or wider were kept: 124 TSX-3225, 53 FA-238, 19 FA-238V.
# The rows were checked against the live search pages (SHA-256 of every
# kept row, per series, matched). The columns keep Epson's own headings.
# The importer re-checks the temperature filter and refuses any row that
# does not meet it.
#
# One extra row is not in the parametric search: X1E0000210202, Epson's
# "custom product for IC reference" TSX-3225 24 MHz, 9 pF, +-10 ppm at
# 25 C, +-15 ppm over -40..+85 C, 40 Ohm, sold through distributors as
# "TSX-3225 24.0000MF15X-AC3" (Mouser lists X1E000021020212 as an alias).
# Its values come from its own Epson datasheet (TSX-3225_X1E0000210202_
# en.pdf). It is the PoEtato 24 MHz crystal candidate.
#
# data/xtal_epson_32k.csv (added 2026-10-08) is the same kind of
# transcription for every 32.768 kHz crystal in Epson's crystal-unit
# search (70 products), with the same -40..+85 C filter: 53 parts in
# FC-135, FC-135R, FC3215AN (3.2 x 1.5 mm), FC-12M, FC2012AN/AA/SN
# (2.05 x 1.2 mm) and FC1610AN/BN (1.65 x 1.05 mm). Checked against the
# live search the same way (SHA-256 of all kept rows matched). Left out
# on purpose: MC-146 (7 x 1.5 mm) and MC-306 (8 x 3.8 mm), larger
# packages with no footprint in this repo. These rows carry Epson's
# turnover-temperature and parabolic-coefficient columns instead of a
# ppm-over-temperature figure; Frequency Stability is "-" for them (as
# xtal_ndk does for its 32 kHz parts) and the two values go into the
# Description. X1A0001410006 (FC-135R, 6 pF, +-20 ppm, 50 kOhm) has
# Distributor Part Number "FC-135R 32.7680KA-E3": DigiKey lists that
# code as 6 pF / +-20 ppm / 50 kOhm / -40..+85 C, and it is the only
# FC-135R product with those values (matched by specification, not by an
# alias listing). It is the PoEtato 32 kHz crystal candidate.
#
# PART NUMBERS: Epson's product numbers (X1E000021xxxx for TSX-3225,
# Q22FA2380xxxx for FA-238, Q22FA23V0xxxx for FA-238V) as the search
# lists them, without the two-digit packaging suffix Epson appends when
# ordering direct (e.g. ...16 / ...17, see the series datasheet header).
# Distributors mostly sell under Epson's model-name codes instead (e.g.
# "TSX-3225 24.0000MF15X-AC3"); the search does not give those, so the
# "Distributor Part Number" column is filled only where it was confirmed
# (X1E0000210202). Product numbers are unique, so the product number is
# the database id, as in xtal_ndk. Electrically identical products (same
# series, frequency, CL, tolerance, stability, temperature and ESR) are
# reported but kept: they are separate orderable products.
#
# FIELD STYLE: neither capacitor style applies. The schema and field
# definitions copy the sibling xtal_ndk library (Frequency, Frequency
# Stability, Frequency Tolerance, Load Capacitance, ESR, Operating
# Temperature, Package, Manufacturer, Part Number, Value) so both crystal
# libraries look the same in KiCad, plus two extra columns: "Distributor
# Part Number", and "Description", which concatenates the important
# values into one line (frequency, load capacitance, tolerance, stability
# with its temperature range, ESR, drive level, series and size), e.g.
# "Crystal 24MHz, CL 9pF, ±10ppm @25°C, ±15ppm -40°C ~ 85°C, ESR 40 Ohm,
# DL 200µW, TSX-3225 3.2x2.5x0.6mm", or for a 32 kHz part
# "Crystal 32.768kHz, CL 6pF, ±20ppm @25°C, Ti +25°C ±5°C, B -0.04ppm/°C²,
# -40°C ~ 85°C, ESR 50 kOhm, DL 0.5µW, FC-135R 3.2x1.5x0.9mm" (Ti =
# turnover temperature, B = parabolic coefficient). The .kicad_dbl maps it to the
# symbol description, so it shows in the chooser and the Description
# field. Value is the frequency (e.g. "24MHz").
#
# SYMBOL and FOOTPRINT are chosen per series (SERIES_MAP).
#
# MHz series: Device:Crystal_GND24 (pins 1/3 crystal, 2/4 GND). All three
# are 4-pad packages; the datasheet's internal-connection drawing has
# #1/#3 as the crystal and #2/#4 tied to the cover, "please connect to
# ground". Footprint Jonas:NX3225SA for all three. That footprint has
# 1.4 x 1.2 mm pads on a 2.2 x 1.6 mm pitch, pad 1 bottom-left, numbered
# counter-clockwise (top view), the same as Epson's numbering. Epson's
# recommended land (series datasheet) is 1.4 x 1.2 mm on 2.2 x 1.6 mm for
# FA-238/FA-238V (exact match) and 1.4 x 1.15 mm on 2.2 x 1.6 mm for
# TSX-3225 (0.05 mm narrower pads, well under the 0.3 mm substitution
# threshold). Bodies are 3.2 x 2.5 mm, 0.6 mm (TSX) / 0.7 mm (FA) high;
# the footprint's 3D model is the 0.55 mm NDK body, which is cosmetic.
#
# 32 kHz series: all are 2-terminal, so Device:Crystal. FC-135, FC-135R
# and FC3215AN (3.2 x 1.5 mm) use Jonas:NX3215SA: 1.0 x 1.8 mm pads on a
# 2.5 mm pitch, the same three dimensions Epson's per-part datasheets
# give for the recommended land (1.0, 1.8, 2.5 mm; the drawing itself
# was not machine-readable, so check it once against the PDF). Bodies
# are 0.9 mm high against the NDK model's 0.8 mm. The 2.05 x 1.2 mm
# (FC-12M, FC2012AN/AA/SN) and 1.65 x 1.05 mm (FC1610AN/BN) series have
# no footprint in this repo, so they are imported without one, as
# xtal_ndk does for NX2012SA.
#
# Footprint names changed 2026-10-19 (footprints review F4.8, KiCad-stock /
# Vendor_Part naming): NX3215SA -> Crystal_SMD_NDK_NX3215SA-2Pin_3.2x1.5mm;
# NX3225SA -> Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm (models renamed to
# match).
# Older names in the comments above refer to the same files.
import argparse
import csv
import json
import re
import sqlite3

MANUFACTURER = "Epson"

# series (Model column) -> (symbol, footprint "lib:name" or "" for none)
SERIES_MAP = {
    "TSX-3225": ("Device:Crystal_GND24", "Jonas:Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm"),
    "FA-238": ("Device:Crystal_GND24", "Jonas:Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm"),
    "FA-238V": ("Device:Crystal_GND24", "Jonas:Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm"),
    "FC-135": ("Device:Crystal", "Jonas:Crystal_SMD_NDK_NX3215SA-2Pin_3.2x1.5mm"),
    "FC-135R": ("Device:Crystal", "Jonas:Crystal_SMD_NDK_NX3215SA-2Pin_3.2x1.5mm"),
    "FC3215AN": ("Device:Crystal", "Jonas:Crystal_SMD_NDK_NX3215SA-2Pin_3.2x1.5mm"),
    "FC-12M": ("Device:Crystal", ""),
    "FC2012AN": ("Device:Crystal", ""),
    "FC2012AA": ("Device:Crystal", ""),
    "FC2012SN": ("Device:Crystal", ""),
    "FC1610AN": ("Device:Crystal", ""),
    "FC1610BN": ("Device:Crystal", ""),
}

MIN_TEMP_LOW = -40   # Jonas: keep only parts rated -40..+85 C or wider
MIN_TEMP_HIGH = 85

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

COL_MODEL = "Model"
COL_PN = "Product Number"
COL_FREQ = "Frequency"
COL_CL = "Load Capacitance [pF]"
COL_ESR = "Motional Resistance Max."
COL_TEMP = "Operation Temperature Range [C]"
COL_TOL = "Frequency Tolerance 25C [x10-6]"
COL_STAB = "Frequency Tolerance Temperature Range [x10-6]"
COL_DIST = "Distributor Part Number"
COL_SIZE = "Size [mm]"
COL_DL = "Drive Level [uW Max.]"
COL_TURNOVER = "Turnover Temperature at 32kHz"          # 32 kHz CSV only
COL_PARABOLIC = "Parabolic Coefficient at 32kHz [x10-6/C2]"  # 32 kHz CSV only


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build the xtal_epson KiCad database library from "
                    "data/xtal_epson.csv and data/xtal_epson_32k.csv.")
    parser.add_argument("--csv", required=True, nargs="+",
                        help="Path(s) to the input CSV(s).")
    parser.add_argument("--db", required=True,
                        help="Path to the output .db SQLite file.")
    parser.add_argument("--table", required=True,
                        help="Name of the table to (re)create.")
    parser.add_argument("--kicad-dbl", required=True,
                        help="Path to (re)write the .kicad_dbl file.")
    return parser.parse_args()


def fmt_num(x):
    return f"{x:.6f}".rstrip("0").rstrip(".")


def parse_frequency(raw):
    """'24.000000 MHz' -> '24MHz', '32.768000 kHz' -> '32.768kHz'"""
    m = re.fullmatch(r"([\d.]+)\s*(MHz|kHz)", raw.strip())
    if not m:
        raise ValueError(f"unrecognized frequency {raw!r}")
    return fmt_num(float(m.group(1))) + m.group(2)


def parse_ppm(raw):
    """'+/-10' -> '±10ppm', '-18/+22' -> '-18/+22ppm', '-' -> '-'"""
    raw = raw.strip()
    if raw == "-":
        return "-"
    m = re.fullmatch(r"\+/-\s*([\d.]+)", raw)
    if m:
        return f"±{fmt_num(float(m.group(1)))}ppm"
    m = re.fullmatch(r"-\s*([\d.]+)\s*/\s*\+\s*([\d.]+)", raw)
    if m:
        return f"-{fmt_num(float(m.group(1)))}/+{fmt_num(float(m.group(2)))}ppm"
    raise ValueError(f"unrecognized ppm value {raw!r}")


def parse_esr(raw):
    """'40 Ω' -> '40 Ohm', '50 kΩ' -> '50 kOhm' (xtal_ndk spelling)"""
    m = re.fullmatch(r"([\d.]+)\s*(k?)Ω", raw.strip())
    if not m:
        raise ValueError(f"unrecognized ESR {raw!r}")
    return f"{fmt_num(float(m.group(1)))} {m.group(2)}Ohm"


def parse_turnover(raw):
    """'+25°C +/-5°C' -> '+25°C ±5°C'"""
    return re.sub(r"\+/-\s*", "±", raw.strip())


def parse_temp(raw):
    """'-40 to +85' -> (-40, 85, '-40°C ~ 85°C')"""
    m = re.fullmatch(r"(-?\d+)\s*to\s*\+?(-?\d+)", raw.strip())
    if not m:
        raise ValueError(f"unrecognized temperature range {raw!r}")
    lo, hi = int(m.group(1)), int(m.group(2))
    return lo, hi, f"{lo}°C ~ {hi}°C"


def load_parts(csv_paths):
    parts = []
    seen_ids = {}
    semantic = {}
    skipped_temp = []
    skipped_footprint = {}

    for csv_path in csv_paths:
        with open(csv_path, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                model = row[COL_MODEL].strip()
                pn = row[COL_PN].strip()

                lo, hi, temp_str = parse_temp(row[COL_TEMP])
                if lo > MIN_TEMP_LOW or hi < MIN_TEMP_HIGH:
                    skipped_temp.append(pn)
                    continue

                series = SERIES_MAP.get(model)
                if series is None:
                    skipped_footprint[model] = skipped_footprint.get(model, 0) + 1
                    continue
                symbol, footprint = series

                freq = parse_frequency(row[COL_FREQ])
                cl = fmt_num(float(row[COL_CL])) + "pF"
                tol = parse_ppm(row[COL_TOL])
                stab = parse_ppm(row[COL_STAB])
                esr = parse_esr(row[COL_ESR])

                if pn in seen_ids:
                    print(f"WARNING: duplicate product number '{pn}' - skipping")
                    continue
                seen_ids[pn] = True

                size = re.sub(r"\s*x\s*", "x", row[COL_SIZE].strip())
                dl = fmt_num(float(row[COL_DL]))
                turnover = row.get(COL_TURNOVER, "").strip()
                if stab == "-" and turnover and turnover != "-":
                    # 32 kHz tuning fork: specified by turnover temperature
                    # and parabolic coefficient, not ppm over temperature.
                    b = fmt_num(float(row[COL_PARABOLIC]))
                    drift = (f"Ti {parse_turnover(turnover)}, "
                             f"B {b}ppm/°C², {temp_str}")
                else:
                    drift = f"{stab} {temp_str}"
                description = (f"Crystal {freq}, CL {cl}, {tol} @25°C, "
                               f"{drift}, ESR {esr}, DL {dl}µW, "
                               f"{model} {size}mm")

                key = (model, freq, cl, tol, stab, temp_str, esr)
                semantic.setdefault(key, []).append(pn)

                parts.append((
                    pn,                      # id
                    freq,                    # Value
                    footprint,               # Footprints
                    symbol,                  # Symbol
                    freq,                    # Frequency
                    stab,                    # Frequency Stability
                    tol,                     # Frequency Tolerance
                    cl,                      # Load Capacitance
                    esr,                     # ESR
                    temp_str,                # Operating Temperature
                    model,                   # Package
                    MANUFACTURER,            # Manufacturer
                    pn,                      # Part Number
                    row.get(COL_DIST, "").strip(),  # Distributor Part Number
                    description,             # Description
                ))

    if skipped_temp:
        raise SystemExit(f"ERROR: {len(skipped_temp)} rows outside -40..+85 C: "
                         f"{skipped_temp[:10]} - the CSV should only hold parts that pass")
    if skipped_footprint:
        raise SystemExit(f"ERROR: series with no SERIES_MAP entry: {skipped_footprint}")

    same = {k: v for k, v in semantic.items() if len(v) > 1}
    if same:
        print(f"Note: {len(same)} groups of electrically identical products "
              "(kept, they are separate orderable parts):")
        for k, v in same.items():
            print(f"  {k[0]} {k[1]} {k[2]} {k[3]}/{k[4]} {k[5]} {k[6]}: {', '.join(v)}")

    print(f"\nLoaded {len(parts)} parts.")
    counts = {}
    for p in parts:
        counts[p[10]] = counts.get(p[10], 0) + 1
    for model, n in sorted(counts.items()):
        print(f"  {model}: {n}")
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
        [Part Number] TEXT,
        [Distributor Part Number] TEXT,
        Description TEXT
    )
    """)
    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, Frequency, [Frequency Stability],
         [Frequency Tolerance], [Load Capacitance], ESR,
         [Operating Temperature], Package, Manufacturer, [Part Number],
         [Distributor Part Number], Description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, parts)
    conn.commit()
    conn.execute("VACUUM")
    conn.close()


def build_field_defs():
    # Same as xtal_ndk, plus Distributor Part Number.
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
        {"column": "Distributor Part Number", "name": "Distributor Part Number",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": False},
        {"column": "Value", "name": "Value", "visible_on_add": True,
         "visible_in_chooser": True, "show_name": False},
    ]


def write_kicad_dbl(dbl_path, table):
    content = {
        "meta": {"version": 0},
        "name": "Epson Crystals",
        "description": "Epson quartz crystals rated -40..+85 C or wider: "
                       "TSX-3225 / FA-238 / FA-238V (MHz) and FC-series "
                       "32.768 kHz, built from data/xtal_epson.csv and "
                       "data/xtal_epson_32k.csv.",
        "source": {
            "type": "odbc",
            "dsn": "",
            "username": "",
            "password": "",
            "timeout_seconds": 2,
            "connection_string": (
                "Driver={SQLite3 ODBC Driver};"
                "Database=${CWD}/xtal_epson.db"
            ),
        },
        "libraries": [
            {
                "name": "TSX-FA-FC",
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
    parts = load_parts(args.csv)
    write_database(args.db, args.table, parts)
    write_kicad_dbl(args.kicad_dbl, args.table)
    print(f"\nImported {len(parts)} parts into {args.db} ({args.table})")
    print(f"Wrote {args.kicad_dbl}")


if __name__ == "__main__":
    main()
