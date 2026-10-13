# Imports Murata LQW15AW (Murata product-table CSV export,
# data/ind_rfmw_murata_lqw15aw.csv) into the ind_rfmw_murata_lqw15aw KiCad database library.
#
# LQW15AW_80, EIA 0402 (1005), up to 140C, 36 parts (HiQ/low-Rdc sibling of LQW15AN).
#
# Split out of the merged ind_rfmw_murata_lqw library on 2026-10-13 (cleanup
# review A4.3: one library per series, chooser name = series). The CSV
# is the former data/ind_rfmw_murata_LQW_1.csv, renamed. Parsing, field style, id format
# and footprint mapping live in murata_lqw.py (see its header); the rows
# are identical to the LQW15AW rows of the old merged library.
#
# Run with no arguments to regenerate library/ind_rfmw_murata_lqw15aw.db and .kicad_dbl.
from murata_lqw import run

if __name__ == "__main__":
    run(library="ind_rfmw_murata_lqw15aw", kind="rfmw", series="LQW15AW",
        title="Murata LQW15AW High-Q RF Wire-Wound Chip Inductors",
        description="Murata LQW15AW (0402) high-Q RF wire-wound (non-magnetic core) chip inductor library")
