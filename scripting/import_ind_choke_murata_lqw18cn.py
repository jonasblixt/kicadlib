# Imports Murata LQW18CN (Murata product-table CSV export,
# data/ind_choke_murata_lqw18cn.csv) into the ind_choke_murata_lqw18cn KiCad database library.
#
# LQW18CN_00, EIA 0603 (1608), up to 85C, 4.9-650nH, 15 parts.
#
# Split out of the merged ind_choke_murata_lqw library on 2026-10-13 (cleanup
# review A4.3: one library per series, chooser name = series). The CSV
# is the former data/ind_choke_murata_LQW_3.csv, renamed. Parsing, field style, id format
# and footprint mapping live in murata_lqw.py (see its header); the rows
# are identical to the LQW18CN rows of the old merged library.
#
# Run with no arguments to regenerate library/ind_choke_murata_lqw18cn.db and .kicad_dbl.
from murata_lqw import run

if __name__ == "__main__":
    run(library="ind_choke_murata_lqw18cn", kind="choke", series="LQW18CN",
        title="Murata LQW18CN Ferrite Wire-Wound Power-Line Choke Inductors",
        description="Murata LQW18CN (0603) ferrite wire-wound power-line choke inductor library")
