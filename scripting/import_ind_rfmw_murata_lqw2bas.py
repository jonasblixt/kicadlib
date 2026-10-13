# Imports Murata LQW2BAS (Murata product-table CSV export,
# data/ind_rfmw_murata_lqw2bas.csv) into the ind_rfmw_murata_lqw2bas KiCad database library.
#
# LQW2BAS_0C, EIA 0805 (2012), up to 85C, 66 parts.
#
# Split out of the merged ind_rfmw_murata_lqw library on 2026-10-13 (cleanup
# review A4.3: one library per series, chooser name = series). The CSV
# is the former data/ind_rfmw_murata_LQW_4.csv, renamed. Parsing, field style, id format
# and footprint mapping live in murata_lqw.py (see its header); the rows
# are identical to the LQW2BAS rows of the old merged library.
#
# Run with no arguments to regenerate library/ind_rfmw_murata_lqw2bas.db and .kicad_dbl.
from murata_lqw import run

if __name__ == "__main__":
    run(library="ind_rfmw_murata_lqw2bas", kind="rfmw", series="LQW2BAS",
        title="Murata LQW2BAS High-Q RF Wire-Wound Chip Inductors",
        description="Murata LQW2BAS (0805) high-Q RF wire-wound (non-magnetic core) chip inductor library")
