import csv
import sqlite3

footprint_mapping = {
    "0201": "C_0201_0603Metric",
    "0402": "C_0402_1005Metric",
    "0603": "C_0603_1608Metric",
    "0805": "C_0805_2012Metric",
    "1206": "C_1206_3216Metric",
    "1210": "C_1210_3225Metric"
}

count = 0
capacitors = []

with open("..\\data\\cap_rfmw_kyocera_accu_p.csv", newline="", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile, delimiter=",")
    for row in reader:
        print(row)
        count += 1

        if count == 1:
            continue

        part_number = row[0].replace("#", "")
        size_code = row[2]
        dielectric = "C0G"
        capacitance = float(row[6])*1e-12
        tolerance = row[12]
        voltage = row[8]

        case_size = size_code
        footprint = f"Capacitor_SMD:{footprint_mapping[size_code]}"




        # C0603_2u2_10V_X7R_5%
        # pF < 1000pF
        # nF >= 1000pF
        # uF >= 1000nF

        if capacitance >= 1000e-9:
            capacitance_uf = capacitance * 1e6
            frac = int(round(capacitance_uf % 1.0, 1)*10)
            if frac > 0:
                short_str = f"{int(capacitance_uf)}u{frac}"
            else:
                short_str = f"{int(capacitance_uf)}u"
            capacitance_str =  f"{capacitance_uf:.1f}uF"
        elif capacitance >= 1000e-12:
            capacitance_nf = capacitance * 1e9
            frac = int(round(capacitance_nf % 1.0, 1)*10)
            if frac > 0:
                short_str = f"{int(capacitance_nf)}n{frac}"
            else:
                short_str = f"{int(capacitance_nf)}n"
            capacitance_str =  f"{capacitance_nf:.1f}nF"
        else:
            capacitance_pf = capacitance * 1e12
            frac = int(round(capacitance_pf % 1.0, 1)*10)
            if frac > 0:
                short_str = f"{int(capacitance_pf)}p{frac}"
            else:
                short_str = f"{int(capacitance_pf)}p"
            capacitance_str = f"{capacitance_pf:.1f}pF"

        id_str = f"C{case_size}_{short_str}_{voltage}V_{dielectric}_{tolerance}"



        print(f"{count} {id_str} {part_number}, {case_size}, {dielectric}, {capacitance_str} ({capacitance_str}) [{short_str}], {capacitance} {tolerance}, {voltage}V")

        cap = (id_str, "${Capacitance}", f"{footprint}", "Device:C", f"{capacitance_str}", f"{voltage}V", f"{dielectric}", f"{capacitance_str}, {voltage}V, {dielectric}, Tol: {tolerance}", part_number, "Kyocera")
        capacitors.append(cap)


# Connect to database (creates it if it doesn't exist)
conn = sqlite3.connect("..\library\\cap_rfmw_kyocera_accu_p.db")
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS cap_rfmw_kyocera_accu_p")

# 1. Create the table
cursor.execute("""
CREATE TABLE cap_rfmw_kyocera_accu_p (
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

# 3. Insert into DB
cursor.executemany("""
INSERT OR REPLACE INTO cap_rfmw_kyocera_accu_p (id, Value, Footprints, Symbol, Capacitance, Voltage, Dielectric, Description, "Part Number", Manufacturer)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", capacitors)

conn.commit()
conn.close()