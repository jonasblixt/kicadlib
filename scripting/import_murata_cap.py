# This can import muratas official CSV exports
import argparse
import csv
import re
import sqlite3

case_mapping = {
    "0.6mm0.3mm": "0201",
    "1mm0.5mm": "0402",
    "1.6mm0.8mm": "0603",
    "2mm1.25mm": "0805",
    "3.2mm1.6mm": "1206",
    "3.2mm2.5mm": "1210",
    "4.5mm3.2mm": "1812"
}

footprint_mapping = {
    "0.6mm0.3mm": "C_0201_0603Metric",
    "1mm0.5mm": "C_0402_1005Metric",
    "1.6mm0.8mm": "C_0603_1608Metric",
    "2mm1.25mm": "C_0805_2012Metric",
    "3.2mm1.6mm": "C_1206_3216Metric",
    "3.2mm2.5mm": "C_1210_3225Metric",
    "4.5mm3.2mm": "C_1812_4532Metric"
}

# Table/column names can't be parameterized with sqlite3 placeholders, so
# validate the table name is a plain identifier before it goes into an
# f-string.
TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import a Murata product-list CSV into a "
                     "KiCad database-library SQLite file.")
    parser.add_argument("--csv", required=True,
                         help="Path to the input CSV (e.g. Murata GRM "
                              "series product list export).")
    parser.add_argument("--db", required=True,
                         help="Path to the output .db SQLite file. Created "
                              "if it doesn't exist.")
    parser.add_argument("--table", required=True,
                         help="Name of the table to (re)create inside the "
                              "database, e.g. cap_mlcc_murata_grm. Must "
                              "match what the corresponding .kicad_dbl "
                              "'table' field references.")
    return parser.parse_args()


def load_capacitors(csv_path):
    count = 0
    capacitors = []

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for row in reader:
            part_number = row[0].replace("#", "")
            length = row[4].split(" ")[0]
            width = row[5].split(" ")[0]
            dielectric = row[9]
            capacitance_input_str = row[11].replace("μ", "u").replace(",", "")
            tolerance = row[12].replace("±", "")
            voltage = row[13].replace("Vdc", "").replace(",", "")

            # The input data only uses pF or uF, convert it to 'F'
            if "uF" in capacitance_input_str:
                capacitance = round(float(capacitance_input_str.replace("uF", "")) * 1e-6, 9)
            elif "pF" in capacitance_input_str:
                capacitance = round(float(capacitance_input_str.replace("pF", "")) * 1e-12, 15)
            else:
                continue

            # We only want X7R, X5R and C0G
            if dielectric not in ("X7R", "X5R", "C0G"):
                continue

            # Translate case size
            case_size_metric_str = f"{length}{width}"

            if case_size_metric_str not in case_mapping:
                continue

            case_size = case_mapping[case_size_metric_str]
            footprint = f"Capacitor_SMD:{footprint_mapping[case_size_metric_str]}"

            count += 1

            # C0603_2u2_10V_X7R_5%
            # pF < 1000pF
            # nF >= 1000pF
            # uF >= 1000nF

            if capacitance >= 1000e-9:
                capacitance_uf = capacitance * 1e6
                frac = int(round(capacitance_uf % 1.0, 1) * 10)
                if frac > 0:
                    short_str = f"{int(capacitance_uf)}u{frac}"
                else:
                    short_str = f"{int(capacitance_uf)}u"
                capacitance_str = f"{capacitance_uf:.1f}uF"
            elif capacitance >= 1000e-12:
                capacitance_nf = capacitance * 1e9
                frac = int(round(capacitance_nf % 1.0, 1) * 10)
                if frac > 0:
                    short_str = f"{int(capacitance_nf)}n{frac}"
                else:
                    short_str = f"{int(capacitance_nf)}n"
                capacitance_str = f"{capacitance_nf:.1f}nF"
            else:
                capacitance_pf = capacitance * 1e12
                frac = int(round(capacitance_pf % 1.0, 1) * 10)
                if frac > 0:
                    short_str = f"{int(capacitance_pf)}p{frac}"
                else:
                    short_str = f"{int(capacitance_pf)}p"
                capacitance_str = f"{capacitance_pf:.1f}pF"

            id_str = f"C{case_size}_{short_str}_{voltage}V_{dielectric}_{tolerance}"

            print(f"{count} {id_str} {part_number}, {case_size}, {dielectric}, "
                  f"{capacitance_input_str} ({capacitance_str}) [{short_str}], "
                  f"{capacitance} {tolerance}, {voltage}V")

            cap = (id_str, "${Capacitance}", footprint, "Device:C",
                   capacitance_str, f"{voltage}V", dielectric,
                   f"{capacitance_str}, {voltage}V, {dielectric}, Tol: {tolerance}",
                   part_number, "Murata")
            capacitors.append(cap)

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
        Manufacturer TEXT
    )
    """)

    cursor.executemany(f"""
    INSERT OR REPLACE INTO {table}
        (id, Value, Footprints, Symbol, Capacitance, Voltage, Dielectric, Description, "Part Number", Manufacturer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, capacitors)

    conn.commit()
    conn.close()


def main():
    args = parse_args()
    capacitors = load_capacitors(args.csv)
    write_database(args.db, args.table, capacitors)
    print(f"Imported {len(capacitors)} parts into {args.db} ({args.table})")


if __name__ == "__main__":
    main()
