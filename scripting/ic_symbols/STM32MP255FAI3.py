# STM32MP255FAI3: STM32MP255F (dual Cortex-A35 at 1.5 GHz + Cortex-M33,
# 3D GPU/NPU at 900 MHz, video codec, DSI + dual LVDS, 2x Gigabit
# Ethernet, USB 3.0 / PCIe combo PHY, secure boot and crypto) in TFBGA436
# 18 x 18 mm, 0.8 mm pitch (package code AI), Tj -40..125 C (3), tray (a
# trailing T orders tape and reel).
# Pinout: ST DS14284 Rev 5 (STM32MP25xC/F), Table 11 "STM32MP25xC/F ball
# definitions", TFBGA436 column: pin names and pin types. Extracted from
# the PDF by word position and cross-checked ball for ball against
# Figure 9 "STM32MP25xC/F TFBGA436 ballout" (all 436 agree). The stock
# Package_BGA:ST_TFBGA-436_18x18mm_Layout22x22_P0.8mm has exactly these
# 436 pads. Table 2/3: the STM32MP255 has the GPU, DSI and dual-link
# LVDS, so none of the balls note (2) marks "DNU in some part numbers" is
# DNU here; U16 is the only DNU ball. The datasheet has no DDR_A24.
# Electrical types: GPIOs bidirectional; NRSTC1MS open collector (note 3:
# open drain, external pull-up); OSC_OUT bidirectional per the table (the
# boot ROM senses it for HSE bypass); V08CAP is the output of the
# internal 0.8 V backup-domain regulator (power_out); REXT, TXRTUNE, ZQ
# and DDR_VREF passive. I/O supply domains (Table 9): PE0-5 VDDIO1
# (SDMMC1), PE6-15 VDDIO2 (SDMMC2), PD0-11 VDDIO3 (OCTOSPI port 1),
# PB0-11 VDDIO4 (OCTOSPI port 2); PC13, PI8, PZ0-6 and OSC32 on VSW
# (VBAT backed); OSC_IN/OUT and PDR_ON on VDDA18AON; the rest on VDD.
# Eight units: supplies, ground, DDR, system and high-speed PHYs, display
# and camera, and GPIO ports in three units.
NAME = "STM32MP255FAI3"

PROPS = {
    "Footprint": "Package_BGA:ST_TFBGA-436_18x18mm_Layout22x22_P0.8mm",
    "Datasheet": "https://www.st.com/resource/en/datasheet/stm32mp255c.pdf",
    "Description": "Arm dual Cortex-A35 1.5 GHz + Cortex-M33 400 MHz MPU, 3D GPU, NPU, H264/VP8 codec, DSI, dual LVDS, 2x Gigabit Ethernet, USB 3.0, PCIe, secure boot, crypto, DDR3L/DDR4/LPDDR4 32-bit, 172 GPIOs, TFBGA436 18x18 mm P0.8 mm",
    "Manufacturer": "ST",
    "Part Number": "STM32MP255FAI3",
    "ki_fp_filters": "ST*TFBGA*436*18x18mm*",
}

# DS14284 Rev 5 Table 11, TFBGA436 column, in table order: ball and name.
TABLE = """
    V5 ANA0  V6 ANA1  R4 BOOT0  R3 BOOT1  T2 BOOT2  T1 BOOT3  T15 UCPD1_CC1
    T17 UCPD1_CC2  D6 CSI_CKN  C6 CSI_CKP  B5 CSI_D0N  C5 CSI_D0P  E7 CSI_D1N
    D7 CSI_D1P  E6 CSI_REXT  M16 DDR_A0  U18 DDR_A1  N16 DDR_A2  M17 DDR_A3
    N19 DDR_A4  M19 DDR_A5  T18 DDR_A6  U19 DDR_A7  P19 DDR_A8  P18 DDR_A9
    N18 DDR_A10  N17 DDR_A11  K19 DDR_A12  K18 DDR_A13  L18 DDR_A14
    L17 DDR_A15  J18 DDR_A16  H18 DDR_A17  H19 DDR_A18  K17 DDR_A19
    G18 DDR_A20  J19 DDR_A21  H17 DDR_A22  J17 DDR_A23  R17 DDR_A25
    R19 DDR_A26  R18 DDR_A27  M18 DDR_A28  T19 DDR_A29  P17 DDR_A30
    P16 DDR_A31  W21 DDR_DQM0  P20 DDR_DQM1  E21 DDR_DQM2  H20 DDR_DQM3
    W20 DDR_DQS0N  N21 DDR_DQS1N  D22 DDR_DQS2N  H21 DDR_DQS3N  V20 DDR_DQS0P
    N20 DDR_DQS1P  D21 DDR_DQS2P  H22 DDR_DQS3P  Y22 DDR_DQ2  AA22 DDR_DQ3
    Y21 DDR_DQ1  W22 DDR_DQ0  U20 DDR_DQ7  U21 DDR_DQ6  T21 DDR_DQ4
    T20 DDR_DQ5  T22 DDR_DQ12  R22 DDR_DQ15  R21 DDR_DQ14  R20 DDR_DQ13
    M22 DDR_DQ9  M21 DDR_DQ8  L22 DDR_DQ11  L21 DDR_DQ10  F20 DDR_DQ20
    F19 DDR_DQ21  E20 DDR_DQ23  E19 DDR_DQ22  B22 DDR_DQ19  D20 DDR_DQ16
    C21 DDR_DQ18  C22 DDR_DQ17  L19 DDR_DQ31  K20 DDR_DQ30  J21 DDR_DQ28
    J20 DDR_DQ29  G22 DDR_DQ25  G21 DDR_DQ26  G20 DDR_DQ27  G19 DDR_DQ24
    L20 DDR_VREF  F18 DDR_RESETN  K16 DDR_ZQ  B8 DSI_CKN  A8 DSI_CKP
    B9 DSI_D0N  C9 DSI_D0P  E9 DSI_D1N  D9 DSI_D1P  D8 DSI_D2N  C8 DSI_D2P
    B7 DSI_D3N  A7 DSI_D3P  E8 DSI_REXT  AA1 JTCK-SWCLK  AB2 JTDI
    W1 JTDO-TRACESWO  Y1 JTMS-SWDIO  D3 LVDS1_D0N  D4 LVDS1_D0P  D1 LVDS1_D1N
    D2 LVDS1_D1P  E4 LVDS1_D2N  E3 LVDS1_D2P  F3 LVDS1_D3N  F2 LVDS1_D3P
    F5 LVDS1_D4N  F4 LVDS1_D4P  B4 LVDS2_D0N  A4 LVDS2_D0P  A3 LVDS2_D1N
    A2 LVDS2_D1P  B3 LVDS2_D2N  C3 LVDS2_D2P  C2 LVDS2_D3N  C1 LVDS2_D3P
    B2 LVDS2_D4N  B1 LVDS2_D4P  AA2 NJTRST  U3 NRST  T3 NRSTC1MS  Y2 PA0
    V15 PA1  W13 PA2  T14 PA3  Y15 PA4  Y13 PA5  V14 PA6  Y14 PA7  W15 PA8
    T12 PA9  U13 PA10  W12 PA11  U12 PA12  Y12 PA13  U10 PA14  T10 PA15
    C11 PB0  D11 PB1  C10 PB2  E10 PB3  D10 PB4  B11 PB5  C12 PB6  D12 PB7
    G11 PB8  A12 PB9  A11 PB10  B12 PB11  B20 PB12  D19 PB13  C20 PB14
    AB4 PB15  AA18 PCIE_CLKINN  Y18 PCIE_CLKINP  AB21 PCIE_CLKOUTN
    AA21 PCIE_CLKOUTP  AA12 PC0  V11 PC1  Y11 PC2  W9 PC3  V9 PC4  U9 PC5
    AA10 PC6  Y8 PC7  V8 PC8  U8 PC9  T8 PC10  AB7 PC11  Y7 PC12  P6 PC13
    R1 OSC32_IN  R2 OSC32_OUT  T7 PDR_ON  D14 PD0  E15 PD1  E14 PD2  C15 PD3
    C14 PD4  B15 PD5  A15 PD6  D15 PD7  C13 PD8  B13 PD9  D13 PD10  E13 PD11
    A21 PD12  B21 PD13  G15 PD14  F16 PD15  A16 PE0  B16 PE1  C16 PE2
    D16 PE3  B17 PE4  C17 PE5  E16 PE6  D17 PE7  C18 PE8  D18 PE9  A19 PE10
    E17 PE11  C19 PE12  B19 PE13  A20 PE14  F17 PE15  V12 PF0  W11 PF1
    V10 PF2  W10 PF3  Y10 PF4  Y9 PF5  AB8 PF6  T9 PF7  AA8 PF8  AA7 PF9
    AA6 PF10  Y6 PF11  K3 PF12  L4 PF13  H1 PF14  L7 PF15  W7 PG0  W6 PG1
    Y4 PG2  W4 PG3  AA4 PG4  L1 PG5  H2 PG6  K4 PG7  L5 PG8  G3 PG9  H3 PG10
    J4 PG11  J3 PG12  K5 PG13  G4 PG14  H4 PG15  V3 OSC_IN  V2 OSC_OUT
    V13 PH2  W14 PH3  AB15 PH4  AA15 PH5  AA14 PH6  T13 PH7  U14 PH8
    AB12 PH9  U11 PH10  T11 PH11  AA11 PH12  AB11 PH13  G5 PI0  H6 PI1
    J5 PI2  J6 PI3  K6 PI4  H5 PI5  J7 PI6  L6 PI7  M6 PI8  K7 PI9  G16 PI10
    E18 PI11  G1 PI12  G2 PI13  G13 PI14  E11 PI15  U15 PJ0  Y3 PJ1  AB3 PJ2
    AA3 PJ3  W3 PJ4  V4 PJ5  U5 PJ6  W2 PJ7  M2 PJ8  M1 PJ9  M3 PJ10  M5 PJ11
    L2 PJ12  M4 PJ13  L3 PJ14  K2 PJ15  F12 PK0  E12 PK1  F13 PK2  F15 PK3
    F11 PK4  F14 PK5  G12 PK6  G14 PK7  T6 PWR_CPU_ON  U4 PWR_LP  T5 PWR_ON
    N5 PZ0  N6 PZ1  P4 PZ2  N4 PZ3  R5 PZ4  P5 PZ5  R6 PZ6  P2 PZ7  P3 PZ8
    N3 PZ9  AB16 USBH_HS_DM  Y17 USB3DR_DM  AA16 USBH_HS_DP  W17 USB3DR_DP
    V16 USBH_HS_TXRTUNE  V17 USB3DR_TXRTUNE  U16 DNU  Y20 COMBOPHY_REXT
    AB20 COMBOPHY_RX1N  AA20 COMBOPHY_RX1P  AB19 COMBOPHY_TX1N
    AA19 COMBOPHY_TX1P  W5 VREF-  Y5 VREF+  P7 VBAT  M9 VDD  N8 VDD  P9 VDD
    P11 VDD  R8 VDD  R10 VDD  V7 VDDA18ADC  F6 VDDA18CSI  J16 VDDA18DDR
    C7 VDDA18DSI  C4 VDDA18LVDS  G17 VDDA18PLL1  L8 VDDA18PLL3  K8 VDDA18PLL2
    W18 VDDA18COMBOPHY  U17 VDDA18USB  H7 VDDCORE  H9 VDDCORE  J8 VDDCORE
    J10 VDDCORE  K9 VDDCORE  K11 VDDCORE  L10 VDDCORE  H11 VDDCPU  H13 VDDCPU
    H15 VDDCPU  J12 VDDCPU  J14 VDDCPU  K13 VDDCPU  L12 VDDCPU  K15 VDDQDDR
    L14 VDDQDDR  L16 VDDQDDR  M15 VDDQDDR  N14 VDDQDDR  P15 VDDQDDR
    R14 VDDQDDR  R16 VDDQDDR  F10 VDDIO2  M11 VDDGPU  M13 VDDGPU  N10 VDDGPU
    N12 VDDGPU  P13 VDDGPU  R12 VDDGPU  F8 VDDIO3  F9 VDDIO3  G8 VDDIO4
    G9 VDDIO4  G10 VDDIO1  T16 VDD33UCPD  D5 VDDCSI  F7 VDDDSI  G7 VDDLVDS
    V18 VDDPCIECLK  V19 VDDCOMBOPHY  Y19 VDDCOMBOPHYTX  R7 VDDA18AON
    Y16 VDD33USB  AB1 VSS  AB22 VSS  A1 VSS  A22 VSS  E5 VSS  G6 VSS  H8 VSS
    H10 VSS  H12 VSS  H14 VSS  H16 VSS  J9 VSS  J11 VSS  J13 VSS  J15 VSS
    K10 VSS  K12 VSS  K14 VSS  L9 VSS  L11 VSS  L13 VSS  L15 VSS  M10 VSS
    M12 VSS  M14 VSS  M20 VSS  N7 VSS  N9 VSS  N11 VSS  N13 VSS  N15 VSS
    P8 VSS  P10 VSS  P12 VSS  P14 VSS  R9 VSS  R11 VSS  R13 VSS  R15 VSS
    T4 VSS  U6 VSS  W8 VSS  W16 VSS  W19 VSS  U7 VSSA  M7 VSSAON  M8 V08CAP
"""
_pairs = TABLE.split()
_balls, _names = _pairs[0::2], _pairs[1::2]
BALLS = _balls
assert len(BALLS) == 436 and len(set(BALLS)) == 436

_by = {}
for _b, _n in zip(_balls, _names):
    _by.setdefault(_n, []).append(_b)


def p(names, typ):
    """One pin per name; the name must be on exactly one ball."""
    out = []
    for n in names:
        assert len(_by[n]) == 1, n
        out.append((_by[n][0], n, typ))
    return out


def rail(name, typ="power_in"):
    """Every ball of a repeated supply or ground name."""
    return [(b, name, typ) for b in _by[name]]


pw, io, i, o, pa = "power_in", "bidirectional", "input", "output", "passive"


def port(letter, nums):
    return (f"Port {letter}", p([f"P{letter}{k}" for k in nums], io))


# Supplies
sup_left = [
    ("Core / CPU / GPU", rail("VDDCORE") + [None] + rail("VDDCPU") + [None] + rail("VDDGPU")),
    ("DDR", rail("VDDQDDR") + p(["VDDA18DDR"], pw)),
    ("Analog / PLL", p(["VDDA18PLL1", "VDDA18PLL2", "VDDA18PLL3", "VDDA18ADC", "VREF+"], pw)),
]
sup_right = [
    ("I/O", rail("VDD") + [None] + p(["VDDIO1", "VDDIO2"], pw) + rail("VDDIO3") + rail("VDDIO4")),
    ("Backup / Always-on", p(["VBAT", "VDDA18AON"], pw) + p(["V08CAP"], "power_out")),
    ("Display / Camera PHY", p(["VDDA18CSI", "VDDCSI", "VDDA18DSI", "VDDDSI", "VDDA18LVDS", "VDDLVDS"], pw)),
    ("USB / PCIe PHY", p(["VDDA18USB", "VDD33USB", "VDD33UCPD", "VDDA18COMBOPHY",
                          "VDDCOMBOPHY", "VDDCOMBOPHYTX", "VDDPCIECLK"], pw)),
]

# Ground
_vss = rail("VSS")
assert len(_vss) == 44
gnd_left = [("Ground", _vss[:25])]
gnd_right = [
    ("Ground", _vss[25:]),
    ("Analog Ground", p(["VSSA", "VSSAON", "VREF-"], pw)),
    ("Do Not Use", p(["DNU"], "no_connect")),
]

# DDR
_addr = [f"DDR_A{k}" for k in range(32) if k != 24]


def byte(n):
    return (f"Byte {n}", p([f"DDR_DQ{8 * n + k}" for k in range(8)], io)
            + p([f"DDR_DQM{n}"], o) + p([f"DDR_DQS{n}P", f"DDR_DQS{n}N"], io))


ddr_left = [("Address / Command", p(_addr, o)), byte(0)]
ddr_right = [
    ("Control", p(["DDR_RESETN"], o) + p(["DDR_ZQ", "DDR_VREF"], pa)),
    byte(1), byte(2), byte(3),
]

# System and high-speed PHYs
sys_left = [
    ("Reset / Boot", p(["NRST"], io) + p(["NRSTC1MS"], "open_collector")
     + p(["BOOT0", "BOOT1", "BOOT2", "BOOT3"], i)),
    ("Power Control", p(["PDR_ON"], i) + p(["PWR_ON", "PWR_LP", "PWR_CPU_ON"], o)),
    ("Clocks", p(["OSC_IN"], i) + p(["OSC_OUT"], io) + p(["OSC32_IN"], i) + p(["OSC32_OUT"], o)),
    ("Debug", p(["NJTRST", "JTCK-SWCLK"], i) + p(["JTMS-SWDIO"], io) + p(["JTDI"], i)
     + p(["JTDO-TRACESWO"], o)),
]
sys_right = [
    ("ADC", p(["ANA0", "ANA1"], i)),
    ("USB 2.0 Host", p(["USBH_HS_DP", "USBH_HS_DM"], io) + p(["USBH_HS_TXRTUNE"], pa)),
    ("USB DRD", p(["USB3DR_DP", "USB3DR_DM"], io) + p(["USB3DR_TXRTUNE"], pa)),
    ("USB-C PD", p(["UCPD1_CC1", "UCPD1_CC2"], io)),
    ("USB 3.0 / PCIe PHY", p(["COMBOPHY_TX1P", "COMBOPHY_TX1N"], o)
     + p(["COMBOPHY_RX1P", "COMBOPHY_RX1N"], i) + p(["COMBOPHY_REXT"], pa)),
    ("PCIe Clock", p(["PCIE_CLKINP", "PCIE_CLKINN"], i) + p(["PCIE_CLKOUTP", "PCIE_CLKOUTN"], o)),
]

# Display and camera
disp_left = [
    ("CSI-2 Camera", p(["CSI_CKP", "CSI_CKN", "CSI_D0P", "CSI_D0N", "CSI_D1P", "CSI_D1N"], i)
     + p(["CSI_REXT"], pa)),
    ("DSI", p(["DSI_CKP", "DSI_CKN"], o) + p(["DSI_D0P", "DSI_D0N"], io)
     + p(["DSI_D1P", "DSI_D1N", "DSI_D2P", "DSI_D2N", "DSI_D3P", "DSI_D3N"], o) + p(["DSI_REXT"], pa)),
]


def lvds(n):
    return (f"LVDS {n}", p([f"LVDS{n}_D{k}{s}" for k in range(5) for s in "PN"], o))


disp_right = [lvds(1), lvds(2)]

UNITS = [
    ("STM32MP255 Supplies", sup_left, sup_right),
    ("STM32MP255 Ground", gnd_left, gnd_right),
    ("STM32MP255 DDR", ddr_left, ddr_right),
    ("STM32MP255 System", sys_left, sys_right),
    ("STM32MP255 Display", disp_left, disp_right),
    ("STM32MP255 GPIO A-D", [port("A", range(16)), port("B", range(16))],
                            [port("C", range(14)), port("D", range(16))]),
    ("STM32MP255 GPIO E-H", [port("E", range(16)), port("F", range(16))],
                            [port("G", range(16)), port("H", range(2, 14))]),
    ("STM32MP255 GPIO I-Z", [port("I", range(16)), port("J", range(16))],
                            [port("K", range(8)), port("Z", range(10))]),
]
