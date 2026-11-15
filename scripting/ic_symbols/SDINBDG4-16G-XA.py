# SanDisk (Western Digital) iNAND 7250A automotive e.MMC 5.1, 16 GB,
# -40..+85 C ambient (-XA; -ZA is the -40..+105 C grade), 153-ball TFBGA
# 11.5 x 13 x 0.8 mm, 0.5 mm pitch, 14 x 14 layout.
# Pinout: SanDisk iNAND 7250A data sheet DOC-80-36-08339 Rev 1.2 (Aug 2017,
# Confidential), Figure 3 (ball array, top view) and Table 18 (functional
# pin assignment). Ordering: Table 24. Package: Figure 2 / Table 17; it is
# the JEDEC MO-276 e.MMC ballout, so the stock
# LFBGA-153_11.5x13mm_Layout14x14_P0.5mm footprint fits (all 37 functional
# balls checked against its pads; the stock name says LFBGA, the 16 GB part
# is 0.8 mm high, which only matters for the 3D model).
# Design notes (section 6.1): 0.1 uF + 4.7 uF per supply rail; VDDi needs
# 0.1-2.2 uF to ground; VSF1-4 float, brought out to test pads with GND
# nearby; NC balls may be grounded or left floating. RCLK is the e.MMC Data
# Strobe (DS) for HS400. The 116 NC balls are a second unit so the main
# unit stays readable; every ball appears once (docs/symbol-style.md rule 8).
NAME = "SDINBDG4-16G-XA"

PROPS = {
    "Footprint": "Package_BGA:LFBGA-153_11.5x13mm_Layout14x14_P0.5mm",
    "Datasheet": "",
    "Description": "e.MMC 5.1 HS400 managed NAND, 16 GB eMLC, iNAND 7250A automotive (AEC-Q100), -40..+85 C, TFBGA-153 11.5x13x0.8 mm P0.5 mm",
    "Manufacturer": "SanDisk",
    "Part Number": "SDINBDG4-16G-XA",
    "ki_fp_filters": "*BGA*153*11.5x13mm*P0.5mm*",
}

ROWS = "ABCDEFGHJKLMNP"
# depopulated positions in the 14 x 14 grid (Figure 3)
EMPTY = ({f"D{c}" for c in range(5, 12)} | {"E4", "E11", "K4", "K11"}
         | {f"{r}{c}" for r in "FGHJ" for c in (4, 6, 7, 8, 9, 11)}
         | {f"L{c}" for c in range(4, 12)})
BALLS = [f"{r}{c}" for r in ROWS for c in range(1, 15) if f"{r}{c}" not in EMPTY]
assert len(BALLS) == 153

LEFT = [
    ("Clock / Control", [
        ("M6", "CLK", "input"), ("M5", "CMD", "bidirectional"),
        ("H5", "RCLK", "output"), ("K5", "RST_n", "input"),
    ]),
    ("Data", [(b, f"DAT{i}", "bidirectional") for i, b in
              enumerate(["A3", "A4", "A5", "B2", "B3", "B4", "B5", "B6"])]),
    ("Test (VSF)", [("E9", "VSF1", "passive"), ("E10", "VSF2", "passive"),
                    ("F10", "VSF3", "passive"), ("K10", "VSF4", "passive")]),
]
RIGHT = [
    ("Power", [(b, "VCC", "power_in") for b in ["E6", "F5", "J10", "K9"]]
     + [(b, "VCCQ", "power_in") for b in ["C6", "M4", "N4", "P3", "P5"]]
     + [("C2", "VDDi", "power_out"), None]
     + [(b, "VSS", "power_in") for b in ["A6", "E7", "G5", "H10", "J5", "K8"]]
     + [(b, "VSSQ", "power_in") for b in ["C4", "N2", "N5", "P4", "P6"]]),
]

_used = {p[0] for col in (LEFT, RIGHT) for _, pins in col for p in pins if p}
assert len(_used) == 37 and _used <= set(BALLS)
_nc = [b for b in BALLS if b not in _used]
assert len(_nc) == 116

UNITS = [
    ("iNAND 7250A e.MMC", LEFT, RIGHT),
    ("iNAND NC Balls", [("NC", [(b, "NC", "no_connect") for b in _nc[:58]])],
                       [("NC", [(b, "NC", "no_connect") for b in _nc[58:]])]),
]
