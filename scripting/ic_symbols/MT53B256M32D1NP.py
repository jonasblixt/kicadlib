# Micron automotive LPDDR4 SDRAM MT53B256M32D1NP (Z01M die): 8 Gbit,
# 256M x 32 as two x16 channels (A, B), single die, single rank,
# 200-ball WFBGA 10 x 14.5 x 0.8 mm (package code NP), 0.8 x 0.65 mm pitch.
# Orderable: MT53B256M32D1NP-062 AIT:C (-062 = 1600 MHz / 3200 MT/s, AIT
# = automotive -40..+95 C, :C = revision).
# Pinout: Micron data sheet "200b_z01m-sdp_ddp_auto_lpddr4", Rev. F 3/20
# (Confidential), Figure 4 "200-Ball Dual-Channel, Single-Rank Discrete
# FBGA" and Table 2 (ball types). Package: Figure 6; the stock
# BGA-200_10x14.5mm_Layout12x22_P0.8x0.65mm footprint matches (checked in
# review F7.2).
# Replaces an older symbol of the same name that used a superset pinout
# for all rank/die options (ZQ1, ZQ2, CS1/CS2, CKE1/CKE2 on balls that are
# NC on this single-rank part: A8, G11, H3, J5, K5, K8, N5, N8, P5, R3)
# with every pin bidirectional.
# Design notes (Table 2): ZQ0 to VDDQ through 240 ohm 1%; ODT_CA is bonded
# per rank, tie it per the controller's guidance (VDD2 for the
# terminating rank); DNU balls must be grounded or left floating.
# Four units: channel A (with RESET_n and ZQ0), channel B, supplies, and
# ground plus DNU/NC.
NAME = "MT53B256M32D1NP"

PROPS = {
    "Footprint": "Package_BGA:BGA-200_10x14.5mm_Layout12x22_P0.8x0.65mm",
    "Datasheet": "",
    "Description": "LPDDR4 SDRAM, 8 Gbit (256M x 32, 2 channels x16), single die, single rank, automotive, WFBGA-200 10x14.5 mm",
    "Manufacturer": "Micron",
    "Part Number": "MT53B256M32D1NP-062 AIT:C",
    "ki_fp_filters": "*BGA*200*10x14.5mm*",
}

ROWS = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K",
        "N", "P", "R", "T", "U", "V", "W", "Y", "AA", "AB"]
BALLS = [f"{r}{c}" for r in ROWS for c in (1, 2, 3, 4, 5, 8, 9, 10, 11, 12)]
assert len(BALLS) == 200

# Figure 4, channel A half (rows A-K); channel B mirrors it in rows AB-N.
CH = {
    "A": dict(CK_t="J8", CK_c="J9", CKE0="J4", CS0="H4", ODT_CA="G2",
              CA0="H2", CA1="J2", CA2="H9", CA3="H10", CA4="H11", CA5="J11",
              DQ0="B2", DQ1="C2", DQ2="E2", DQ3="F2", DQ4="F4", DQ5="E4", DQ6="C4", DQ7="B4",
              DMI0="C3", DQS0_t="D3", DQS0_c="E3",
              DQ8="B11", DQ9="C11", DQ10="E11", DQ11="F11", DQ12="F9", DQ13="E9", DQ14="C9", DQ15="B9",
              DMI1="C10", DQS1_t="D10", DQS1_c="E10"),
    "B": dict(CK_t="P8", CK_c="P9", CKE0="P4", CS0="R4", ODT_CA="T2",
              CA0="R2", CA1="P2", CA2="R9", CA3="R10", CA4="R11", CA5="P11",
              DQ0="AA2", DQ1="Y2", DQ2="V2", DQ3="U2", DQ4="U4", DQ5="V4", DQ6="Y4", DQ7="AA4",
              DMI0="Y3", DQS0_t="W3", DQS0_c="V3",
              DQ8="AA11", DQ9="Y11", DQ10="V11", DQ11="U11", DQ12="U9", DQ13="V9", DQ14="Y9", DQ15="AA9",
              DMI1="Y10", DQS1_t="W10", DQS1_c="V10"),
}


def sig(ch, names, typ):
    return [(CH[ch][n], f"{n}_{ch}", typ) for n in names]


def channel(ch):
    left = [
        ("Clock / Control", sig(ch, ["CK_t", "CK_c", "CKE0", "CS0", "ODT_CA"], "input")),
        ("Byte 0", sig(ch, [f"DQ{i}" for i in range(8)] + ["DMI0", "DQS0_t", "DQS0_c"], "bidirectional")),
    ]
    right = [
        ("Command / Address", sig(ch, [f"CA{i}" for i in range(6)], "input")),
        ("Byte 1", sig(ch, [f"DQ{i}" for i in range(8, 16)] + ["DMI1", "DQS1_t", "DQS1_c"], "bidirectional")),
    ]
    return left, right


def pw(name, balls, typ="power_in"):
    return [(b, name, typ) for b in balls]


VDD1 = ["F1", "F12", "G4", "G9", "T4", "T9", "U1", "U12"]
VDD2 = ["A4", "A9", "F5", "F8", "H1", "H5", "H8", "H12", "K1", "K3", "K10", "K12",
        "N1", "N3", "N10", "N12", "R1", "R5", "R8", "R12", "U5", "U8", "AB4", "AB9"]
VDDQ = ["B3", "B5", "B8", "B10", "D1", "D5", "D8", "D12", "F3", "F10",
        "U3", "U10", "W1", "W5", "W8", "W12", "AA3", "AA5", "AA8", "AA10"]
DNU = ["A1", "A2", "A11", "A12", "B1", "B12", "AA1", "AA12", "AB1", "AB2", "AB11", "AB12"]
NC = ["A8", "G11", "H3", "J5", "K5", "K8", "N5", "N8", "P5", "R3"]

a_left, a_right = channel("A")
a_left.append(("Reset / ZQ", [("T11", "RESET_n", "input"), ("A5", "ZQ0", "passive")]))
b_left, b_right = channel("B")

_named = ({p[0] for col in (a_left, a_right, b_left, b_right) for _, ps in col for p in ps}
          | set(VDD1) | set(VDD2) | set(VDDQ) | set(DNU) | set(NC))
VSS = [b for b in BALLS if b not in _named]
assert len(VDD1) == 8 and len(VDD2) == 24 and len(VDDQ) == 20 and len(VSS) == 58

UNITS = [
    ("LPDDR4 Channel A", a_left, a_right),
    ("LPDDR4 Channel B", b_left, b_right),
    ("LPDDR4 Supplies", [("VDD1 (1.8 V)", pw("VDD1", VDD1)), ("VDD2 (1.1 V)", pw("VDD2", VDD2))],
                        [("VDDQ (1.1 V)", pw("VDDQ", VDDQ))]),
    ("LPDDR4 Ground / NC", [("Ground", pw("VSS", VSS[:29])), ("Do Not Use", pw("DNU", DNU, "no_connect"))],
                           [("Ground", pw("VSS", VSS[29:])), ("Not Connected", pw("NC", NC, "no_connect"))]),
]
