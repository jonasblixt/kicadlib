# Imports Murata LQW2UAS (Murata product-table CSV export,
# data/ind_rfmw_murata_lqw2uas.csv) into the ind_rfmw_murata_lqw2uas KiCad database library.
#
# LQW2UAS_0C, EIA 1008 (2520), up to 85C, 95 parts, 12nH to 6.8uH.
#
# Built 2026-10-19 (cleanup review A4.6). The CSV is the former
# data/ind_choke_murata_LQW_8.csv, renamed: despite the old name it is
# "Wire wound type (Non mag)", "High frequency circuits", so rfmw, not
# choke. Parsing, field style and id format live in murata_lqw.py (see its
# header); its 1008 footprint entry (Coilcraft 1008HQ land = Murata's
# LQW2UA land) was added for this series.
#
# Run with no arguments to regenerate library/ind_rfmw_murata_lqw2uas.db and .kicad_dbl.
from murata_lqw import run

if __name__ == "__main__":
    run(library="ind_rfmw_murata_lqw2uas", kind="rfmw", series="LQW2UAS",
        title="Murata LQW2UAS High-Q RF Wire-Wound Chip Inductors",
        description="Murata LQW2UAS (1008) high-Q RF wire-wound (non-magnetic core) chip inductor library")
