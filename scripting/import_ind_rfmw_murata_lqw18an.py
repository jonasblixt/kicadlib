# Imports Murata LQW18AN (Murata product-table CSV export,
# data/ind_rfmw_murata_lqw18an.csv) into the ind_rfmw_murata_lqw18an KiCad database library.
#
# LQW18AN_00, EIA 0603 (1608), up to 125C, 99 parts.
#
# Split out of the merged ind_rfmw_murata_lqw library on 2026-10-13 (cleanup
# review A4.3: one library per series, chooser name = series). The CSV
# is the former data/ind_rfmw_murata_LQW_3.csv, renamed. Parsing, field style, id format
# and footprint mapping live in murata_lqw.py (see its header); the rows
# are identical to the LQW18AN rows of the old merged library.
#
# Run with no arguments to regenerate library/ind_rfmw_murata_lqw18an.db and .kicad_dbl.
from murata_lqw import run

if __name__ == "__main__":
    run(library="ind_rfmw_murata_lqw18an", kind="rfmw", series="LQW18AN",
        title="Murata LQW18AN High-Q RF Wire-Wound Chip Inductors",
        description="Murata LQW18AN (0603) high-Q RF wire-wound (non-magnetic core) chip inductor library")
