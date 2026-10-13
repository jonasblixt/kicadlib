# Imports Murata LQW15CN (Murata product-table CSV export,
# data/ind_choke_murata_lqw15cn.csv) into the ind_choke_murata_lqw15cn KiCad database library.
#
# LQW15CN_10, EIA 0402 (1005), up to 125C, 15nH-3.3uH, 34 parts.
#
# Split out of the merged ind_choke_murata_lqw library on 2026-10-13 (cleanup
# review A4.3: one library per series, chooser name = series). The CSV
# is the former data/ind_choke_murata_LQW_1.csv, renamed. Parsing, field style, id format
# and footprint mapping live in murata_lqw.py (see its header); the rows
# are identical to the LQW15CN rows of the old merged library.
#
# Run with no arguments to regenerate library/ind_choke_murata_lqw15cn.db and .kicad_dbl.
from murata_lqw import run

if __name__ == "__main__":
    run(library="ind_choke_murata_lqw15cn", kind="choke", series="LQW15CN",
        title="Murata LQW15CN Ferrite Wire-Wound Power-Line Choke Inductors",
        description="Murata LQW15CN (0402) ferrite wire-wound power-line choke inductor library")
