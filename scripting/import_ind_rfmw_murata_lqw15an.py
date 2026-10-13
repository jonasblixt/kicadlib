# Imports Murata LQW15AN (Murata product-table CSV export,
# data/ind_rfmw_murata_lqw15an.csv) into the ind_rfmw_murata_lqw15an KiCad database library.
#
# LQW15AN_80, EIA 0402 (1005), up to 125C, 296 parts.
#
# Split out of the merged ind_rfmw_murata_lqw library on 2026-10-13 (cleanup
# review A4.3: one library per series, chooser name = series). The CSV
# is the former data/ind_rfmw_murata_LQW_2.csv, renamed. Parsing, field style, id format
# and footprint mapping live in murata_lqw.py (see its header); the rows
# are identical to the LQW15AN rows of the old merged library.
#
# Run with no arguments to regenerate library/ind_rfmw_murata_lqw15an.db and .kicad_dbl.
from murata_lqw import run

if __name__ == "__main__":
    run(library="ind_rfmw_murata_lqw15an", kind="rfmw", series="LQW15AN",
        title="Murata LQW15AN High-Q RF Wire-Wound Chip Inductors",
        description="Murata LQW15AN (0402) high-Q RF wire-wound (non-magnetic core) chip inductor library")
