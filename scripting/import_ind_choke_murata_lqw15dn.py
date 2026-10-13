# Imports Murata LQW15DN (Murata product-table CSV export,
# data/ind_choke_murata_lqw15dn.csv) into the ind_choke_murata_lqw15dn KiCad database library.
#
# LQW15DN_00, EIA 0402 (1005), up to 85C, 10-15uH, 2 parts.
#
# Split out of the merged ind_choke_murata_lqw library on 2026-10-13 (cleanup
# review A4.3: one library per series, chooser name = series). The CSV
# is the former data/ind_choke_murata_LQW_2.csv, renamed. Parsing, field style, id format
# and footprint mapping live in murata_lqw.py (see its header); the rows
# are identical to the LQW15DN rows of the old merged library.
#
# Run with no arguments to regenerate library/ind_choke_murata_lqw15dn.db and .kicad_dbl.
from murata_lqw import run

if __name__ == "__main__":
    run(library="ind_choke_murata_lqw15dn", kind="choke", series="LQW15DN",
        title="Murata LQW15DN Ferrite Wire-Wound Power-Line Choke Inductors",
        description="Murata LQW15DN (0402) ferrite wire-wound power-line choke inductor library")
