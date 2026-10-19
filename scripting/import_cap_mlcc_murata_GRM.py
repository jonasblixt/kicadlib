# Imports Murata GRM (Murata product-table CSV export,
# data/cap_mlcc_murata_grm.csv) into the cap_mlcc_murata_GRM KiCad database
# library: general-purpose MLCCs, X7R/X5R/C0G, 0201-1812.
#
# Written 2026-10-19 (cleanup review A4.1): the library used to be built by
# the generic import_murata_cap.py with unrecorded arguments, and its
# .kicad_dbl was hand-written. Parsing, field style and footprints live in
# murata_cap.py (see its header); the rows are identical to the old .db.
# 101 CSV rows are thickness variants that collide on the id and are
# replaced by the last one (printed as warnings).
#
# Run with no arguments to regenerate library/cap_mlcc_murata_GRM.db and .kicad_dbl.
from murata_cap import run

if __name__ == "__main__":
    run(library="cap_mlcc_murata_GRM", csv_name="cap_mlcc_murata_grm.csv",
        chooser_name="GRM", title="Murata GRM MLCC Capacitor Library")
