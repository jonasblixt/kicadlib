# Imports Kyocera AVX Accu-P thin-film RF capacitors (hand-built CSV,
# data/cap_rfmw_kyocera_accu_p.csv) into the cap_rfmw_kyocera_accu_p KiCad
# database library. All parts are C0G-like thin film; the dielectric is
# fixed to "C0G" and cases map to KiCad stock Capacitor_SMD footprints.
# The CSV's file_path column names Kyocera's .s2p S-parameter files; they
# lived in simulation/ until A1.7 removed it and are not imported.
#
# Until 2026-10-19 this script used cwd-relative paths and wrote only the
# .db; the .kicad_dbl was hand-written (cleanup review A4.1/A4.5). It now
# reuses murata_cap.py's writers (same schema and field set as the Murata
# MLCC libraries) and regenerates both files with no arguments. The
# parsing is unchanged and the rows are identical.
import csv
from pathlib import Path

from murata_cap import write_database, write_kicad_dbl

LIBRARY = "cap_rfmw_kyocera_accu_p"
REPO = Path(__file__).resolve().parent.parent

footprint_mapping = {
    "0201": "C_0201_0603Metric",
    "0402": "C_0402_1005Metric",
    "0603": "C_0603_1608Metric",
    "0805": "C_0805_2012Metric",
    "1206": "C_1206_3216Metric",
    "1210": "C_1210_3225Metric"
}


def load_capacitors(csv_path):
    count = 0
    capacitors = []

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for row in reader:
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

    return capacitors


if __name__ == "__main__":
    db_path = REPO / "library" / f"{LIBRARY}.db"
    dbl_path = REPO / "library" / f"{LIBRARY}.kicad_dbl"
    capacitors = load_capacitors(REPO / "data" / f"{LIBRARY}.csv")
    write_database(str(db_path), LIBRARY, capacitors)
    write_kicad_dbl(str(dbl_path), str(db_path), LIBRARY, "AccuP",
                    "Kyocera Accu-P RFMW Capacitor Library")
    print(f"Imported {len(capacitors)} parts into {db_path} ({LIBRARY})")
    print(f"Wrote {dbl_path}")
