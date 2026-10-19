# Imports Murata GQM (Murata product-table CSV export,
# data/cap_rfmw_murata_gqm.csv) into the cap_rfmw_murata_gqm KiCad database
# library: high-Q RF/microwave MLCCs.
#
# Written 2026-10-19 (cleanup review A4.1): the library had no importer
# (it was built by the generic import_murata_cap.py) and its .kicad_dbl
# was hand-written. The CSV was data/cap_mlcc_murata_gqm.csv, renamed to
# match the library. Parsing, field style and footprints live in
# murata_cap.py (see its header); the rows are identical to the old .db.
#
# Run with no arguments to regenerate library/cap_rfmw_murata_gqm.db and .kicad_dbl.
from murata_cap import run

if __name__ == "__main__":
    run(library="cap_rfmw_murata_gqm", csv_name="cap_rfmw_murata_gqm.csv",
        chooser_name="GQM", title="Murata GQM rfmw Capacitor Library")
