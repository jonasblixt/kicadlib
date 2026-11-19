# MIMX8ML8CVNKZAB: NXP i.MX 8M Plus Quad (4x Cortex-A53 at 1.6 GHz +
# Cortex-M7, NPU 2.3 TOPS, ISP, VPU, HiFi 4 DSP, CAN-FD), industrial
# qualification (Tj -40..105 C), FCBGA 548 15 x 15 mm, 0.5 mm pitch.
# Pinout: NXP IMX8MPIEC Rev. 2.2 (09/2024), Table 76 (supplies contact
# assignments) and Table 77 (functional contact assignments), extracted
# from the PDF by word position and cross-checked ball for ball against
# Table 78 (ball map): all 548 agree (the map's footnote digits on the
# three DNU balls aside). Package: Figure 52, drawing 98ASA01539D rev A.
# Also checked against NXP's IBIS model imx8mp_15x15_v2.ibs (2020-10, [Pin]
# lists all 548 balls: identical except the three DNU balls, which the
# older model still names USB1_ID, USB2_ID and MIPI_VREG2_CAP) and the BSDL
# IMX8MP_15X15_A1 v2.0 (2024; its 252 boundary-scan balls all agree).
# Both files are in Z:\Library\Datasheets\cpu\imx8mp\ (ibis/, bsdl/).
# Electrical types: pads of ball type GPIO are bidirectional (all are
# muxable through the IOMUX), except the dedicated pins: BOOT_MODE0-3,
# POR_B, ONOFF, JTAG_MOD/TCK/TMS/TDI, CLKIN1/2 inputs; JTAG_TDO, CLKOUT1/2,
# PMIC_ON_REQ, PMIC_STBY_REQ outputs. DRAM: address/command outputs, DQ,
# DM (LPDDR4 DMI) and DQS bidirectional, DRAM_RESET_N output, DRAM_ALERT_N
# input, DRAM_ZN and DRAM_VREF passive. PHY pins by direction; TXRTUNE,
# RESREF, REXT and MIPI_VREG1_CAP passive (resistor or capacitor only).
# VDD_SNVS_0P8_CAP and VDD_MIPI_1P2_CAP are outputs of internal regulators
# that only take a capacitor (the EVK's PMIC LDO2 0.8 V is marked "no need
# for 8M Plus", SPF-46368 A3 sheet 11; Table 6: "connect to outside cap"):
# power_out. USB1_DNU, USB2_DNU and MIPI_TEST_DNU are "do not use"
# (Table 78 notes 1-3; Tables 6/7: not connected): no_connect.
# Seven units: supplies, ground, DRAM, system/USB/PCIe, display/camera,
# GPIO/ENET/SD, NAND/audio/serial.
NAME = "MIMX8ML8CVNKZAB"

PROPS = {
    "Footprint": "Jonas:NXP_FCBGA-548_15x15mm_Layout29x29_P0.5mm",
    "Datasheet": "https://www.nxp.com/docs/en/data-sheet/IMX8MPIEC.pdf",
    "Description": "NXP i.MX 8M Plus Quad applications processor: 4x Arm Cortex-A53 1.6 GHz + Cortex-M7, NPU 2.3 TOPS, ISP, VPU, HiFi 4 DSP, 3D/2D GPU, LPDDR4/DDR4 32-bit, 2x GbE, 2x USB 3.0, PCIe, HDMI, MIPI DSI/CSI, LVDS, CAN-FD; industrial Tj -40..105 C; FCBGA-548 15x15 mm P0.5 mm",
    "Manufacturer": "NXP",
    "Part Number": "MIMX8ML8CVNKZAB",
    "ki_fp_filters": "*FCBGA*548*15x15mm*",
}

# IMX8MPIEC Rev. 2.2 Table 76 (supplies) then Table 77 (functional), in
# table order: ball and name.
TABLE = """
    R22 NVCC_CLK  J8 NVCC_DRAM  J10 NVCC_DRAM  L8 NVCC_DRAM  N8 NVCC_DRAM
    R8 NVCC_DRAM  U8 NVCC_DRAM  W8 NVCC_DRAM  AA8 NVCC_DRAM  AA10 NVCC_DRAM
    AA14 NVCC_ECSPI_HDMI  AA24 NVCC_ENET  J11 NVCC_GPIO  Y10 NVCC_I2C_UART
    K11 NVCC_JTAG  U22 NVCC_NAND  Y11 NVCC_SAI1_SAI5  AA11
    NVCC_SAI2_SAI3_SPDIF  U24 NVCC_SD1  W24 NVCC_SD2  R24 NVCC_SNVS_1P8  J16
    PVCC0_1P8  AA19 PVCC1_1P8  AA16 PVCC2_1P8  L22 VDD_24M_XTAL_1P8  J20
    VDD_ANA0_1P8  R21 VDD_ANA1_0P8  N22 VDD_ANA1_1P8  Y20 VDD_ANA2_1P8  T14
    VDD_ARM  V16 VDD_ARM  W12 VDD_ARM  W13 VDD_ARM  W17 VDD_ARM  Y14 VDD_ARM
    Y15 VDD_ARM  Y16 VDD_ARM  T16 VDD_ARM  U12 VDD_ARM  U13 VDD_ARM  U14
    VDD_ARM  U15 VDD_ARM  U16 VDD_ARM  U17 VDD_ARM  V14 VDD_ARM  W21
    VDD_ARM_PLL_0P8  Y19 VDD_ARM_PLL_1P8  W19 VDD_AVPLL_1P8  R9
    VDD_DRAM_PLL_0P8  R6 VDD_DRAM_PLL_1P8  AA20 VDD_EARC_1P8  W22
    VDD_HDMI_0P8  AA22 VDD_HDMI_1P8  J22 VDD_LVDS_1P8  K16 VDD_MIPI_0P8  F20
    VDD_MIPI_1P2_CAP  K20 VDD_MIPI_1P8  K15 VDD_PCI_0P8  K19 VDD_PCI_1P8
    U21 VDD_SAI_PLL_0P8  W18 VDD_SAI_PLL_1P8  N26 VDD_SNVS_0P8_CAP  K10
    VDD_SOC  L9 VDD_SOC  L10 VDD_SOC  L11 VDD_SOC  L12 VDD_SOC  L13 VDD_SOC
    L17 VDD_SOC  L18 VDD_SOC  L19 VDD_SOC  L20 VDD_SOC  L21 VDD_SOC  M14
    VDD_SOC  M16 VDD_SOC  N9 VDD_SOC  N10 VDD_SOC  N12 VDD_SOC  N13 VDD_SOC
    N14 VDD_SOC  N15 VDD_SOC  N16 VDD_SOC  N17 VDD_SOC  N18 VDD_SOC  N20
    VDD_SOC  N21 VDD_SOC  P14 VDD_SOC  P16 VDD_SOC  R10 VDD_SOC  R20 VDD_SOC
    U9 VDD_SOC  U10 VDD_SOC  U20 VDD_SOC  W9 VDD_SOC  W10 VDD_SOC  W11
    VDD_SOC  W20 VDD_SOC  K14 VDD_USB_0P8  J19 VDD_USB_1P8  J14 VDD_USB_3P3
    A1 VSS  A29 VSS  C4 VSS  C6 VSS  C8 VSS  C10 VSS  C12 VSS  C14 VSS  C16
    VSS  C18 VSS  C20 VSS  C22 VSS  C24 VSS  C26 VSS  E3 VSS  E27 VSS  G3
    VSS  G6 VSS  G24 VSS  G27 VSS  H8 VSS  H10 VSS  H12 VSS  H14 VSS  H16
    VSS  H18 VSS  H20 VSS  H22 VSS  J3 VSS  J7 VSS  J23 VSS  J27 VSS  L3 VSS
    L7 VSS  L14 VSS  L16 VSS  L23 VSS  L27 VSS  M11 VSS  M19 VSS  N3 VSS  N7
    VSS  N11 VSS  N19 VSS  N23 VSS  N27 VSS  P11 VSS  P19 VSS  R3 VSS  R7
    VSS  R11 VSS  R12 VSS  R13 VSS  R14 VSS  R16 VSS  R17 VSS  R18 VSS  R19
    VSS  R23 VSS  R27 VSS  T11 VSS  T19 VSS  U3 VSS  U7 VSS  U11 VSS  U18
    VSS  U19 VSS  U23 VSS  U27 VSS  V11 VSS  V19 VSS  W3 VSS  W7 VSS  W14
    VSS  W16 VSS  W23 VSS  W27 VSS  AA3 VSS  AA7 VSS  AA23 VSS  AA27 VSS
    AB8 VSS  AB10 VSS  AB12 VSS  AB14 VSS  AB16 VSS  AB18 VSS  AB20 VSS
    AB22 VSS  AC3 VSS  AC6 VSS  AC24 VSS  AC27 VSS  AE3 VSS  AE27 VSS  AG4
    VSS  AG6 VSS  AG8 VSS  AG10 VSS  AG12 VSS  AG14 VSS  AG16 VSS  AG18 VSS
    AG20 VSS  AG22 VSS  AG24 VSS  AG26 VSS  AJ1 VSS  AJ29 VSS  G10
    BOOT_MODE0  F8 BOOT_MODE1  G8 BOOT_MODE2  G12 BOOT_MODE3  K28 CLKIN1
    L28 CLKIN2  K29 CLKOUT1  L29 CLKOUT2  J6 DRAM_AC00  G5 DRAM_AC01  N6
    DRAM_AC02  J4 DRAM_AC03  M1 DRAM_AC04  M2 DRAM_AC05  G4 DRAM_AC06  J5
    DRAM_AC07  L6 DRAM_AC08  L4 DRAM_AC09  E4 DRAM_AC10  D4 DRAM_AC11  N4
    DRAM_AC12  N5 DRAM_AC13  L5 DRAM_AC14  R5 DRAM_AC15  N1 DRAM_AC16  N2
    DRAM_AC17  P2 DRAM_AC19  AA4 DRAM_AC20  AA5 DRAM_AC21  AA6 DRAM_AC22  U4
    DRAM_AC23  V2 DRAM_AC24  V1 DRAM_AC25  P1 DRAM_AC26  R4 DRAM_AC27  W4
    DRAM_AC28  W5 DRAM_AC29  AE4 DRAM_AC30  AF4 DRAM_AC31  U5 DRAM_AC32  U6
    DRAM_AC33  U1 DRAM_AC34  U2 DRAM_AC35  W6 DRAM_AC36  AC4 DRAM_AC37  AC5
    DRAM_AC38  T2 DRAM_ALERT_N  B2 DRAM_DM0  H2 DRAM_DM1  AB2 DRAM_DM2  AH2
    DRAM_DM3  B3 DRAM_DQ00  A2 DRAM_DQ01  E1 DRAM_DQ02  F2 DRAM_DQ03  E2
    DRAM_DQ04  C1 DRAM_DQ05  C2 DRAM_DQ06  B1 DRAM_DQ07  G1 DRAM_DQ08  H1
    DRAM_DQ09  K1 DRAM_DQ10  K2 DRAM_DQ11  L2 DRAM_DQ12  L1 DRAM_DQ13  G2
    DRAM_DQ14  F1 DRAM_DQ15  AC1 DRAM_DQ16  AB1 DRAM_DQ17  W2 DRAM_DQ18  Y2
    DRAM_DQ19  Y1 DRAM_DQ20  W1 DRAM_DQ21  AC2 DRAM_DQ22  AD1 DRAM_DQ23  AH3
    DRAM_DQ24  AJ2 DRAM_DQ25  AE1 DRAM_DQ26  AD2 DRAM_DQ27  AE2 DRAM_DQ28
    AG1 DRAM_DQ29  AG2 DRAM_DQ30  AH1 DRAM_DQ31  D1 DRAM_DQS0_N  D2
    DRAM_DQS0_P  J1 DRAM_DQS1_N  J2 DRAM_DQS1_P  AA1 DRAM_DQS2_N  AA2
    DRAM_DQS2_P  AF1 DRAM_DQS3_N  AF2 DRAM_DQS3_P  T1 DRAM_RESET_N  R2
    DRAM_VREF  R1 DRAM_ZN  AH23 EARC_AUX  AH22 EARC_N_HPD  AJ23 EARC_P_UTIL
    AD20 ECSPI1_MISO  AC20 ECSPI1_MOSI  AF20 ECSPI1_SCLK  AE20 ECSPI1_SS0
    AH20 ECSPI2_MISO  AJ21 ECSPI2_MOSI  AH21 ECSPI2_SCLK  AJ22 ECSPI2_SS0
    AH28 ENET_MDC  AH29 ENET_MDIO  AG29 ENET_RD0  AG28 ENET_RD1  AF29
    ENET_RD2  AF28 ENET_RD3  AE28 ENET_RX_CTL  AE29 ENET_RXC  AC25 ENET_TD0
    AE26 ENET_TD1  AF26 ENET_TD2  AD24 ENET_TD3  AF24 ENET_TX_CTL  AE24
    ENET_TXC  A7 GPIO1_IO00  E8 GPIO1_IO01  B6 GPIO1_IO02  D6 GPIO1_IO03  E6
    GPIO1_IO04  B4 GPIO1_IO05  A3 GPIO1_IO06  F6 GPIO1_IO07  A8 GPIO1_IO08
    B8 GPIO1_IO09  B7 GPIO1_IO10  D8 GPIO1_IO11  A5 GPIO1_IO12  A6
    GPIO1_IO13  A4 GPIO1_IO14  B5 GPIO1_IO15  AD22 HDMI_CEC  AC22
    HDMI_DDC_SCL  AF22 HDMI_DDC_SDA  AE22 HDMI_HPD  AJ28 HDMI_REXT  AJ25
    HDMI_TX0_N  AH25 HDMI_TX0_P  AJ26 HDMI_TX1_N  AH26 HDMI_TX1_P  AJ27
    HDMI_TX2_N  AH27 HDMI_TX2_P  AJ24 HDMI_TXC_N  AH24 HDMI_TXC_P  AC8
    I2C1_SCL  AH7 I2C1_SDA  AH6 I2C2_SCL  AE8 I2C2_SDA  AJ7 I2C3_SCL  AJ6
    I2C3_SDA  AF8 I2C4_SCL  AD8 I2C4_SDA  G20 JTAG_MOD  G18 JTAG_TCK  G16
    JTAG_TDI  F14 JTAG_TDO  G14 JTAG_TMS  G28 LVDS0_CLK_N  F29 LVDS0_CLK_P
    E28 LVDS0_D0_N  D29 LVDS0_D0_P  F28 LVDS0_D1_N  E29 LVDS0_D1_P  H28
    LVDS0_D2_N  G29 LVDS0_D2_P  J28 LVDS0_D3_N  H29 LVDS0_D3_P  B28
    LVDS1_CLK_N  A28 LVDS1_CLK_P  B26 LVDS1_D0_N  A26 LVDS1_D0_P  B27
    LVDS1_D1_N  A27 LVDS1_D1_P  C28 LVDS1_D2_N  B29 LVDS1_D2_P  D28
    LVDS1_D3_N  C29 LVDS1_D3_P  E22 MIPI_CSI1_CLK_N  D22 MIPI_CSI1_CLK_P
    E18 MIPI_CSI1_D0_N  D18 MIPI_CSI1_D0_P  E20 MIPI_CSI1_D1_N  D20
    MIPI_CSI1_D1_P  E24 MIPI_CSI1_D2_N  D24 MIPI_CSI1_D2_P  E26
    MIPI_CSI1_D3_N  D26 MIPI_CSI1_D3_P  B23 MIPI_CSI2_CLK_N  A23
    MIPI_CSI2_CLK_P  B25 MIPI_CSI2_D0_N  A25 MIPI_CSI2_D0_P  B24
    MIPI_CSI2_D1_N  A24 MIPI_CSI2_D1_P  B22 MIPI_CSI2_D2_N  A22
    MIPI_CSI2_D2_P  B21 MIPI_CSI2_D3_N  A21 MIPI_CSI2_D3_P  B18
    MIPI_DSI1_CLK_N  A18 MIPI_DSI1_CLK_P  B16 MIPI_DSI1_D0_N  A16
    MIPI_DSI1_D0_P  B17 MIPI_DSI1_D1_N  A17 MIPI_DSI1_D1_P  B19
    MIPI_DSI1_D2_N  A19 MIPI_DSI1_D2_P  B20 MIPI_DSI1_D3_N  A20
    MIPI_DSI1_D3_P  F18 MIPI_VREG1_CAP  F24 MIPI_TEST_DNU  N25 NAND_ALE  L26
    NAND_CE0_B  T29 NAND_CE1_B  P28 NAND_CE2_B  N28 NAND_CE3_B  M28 NAND_CLE
    R25 NAND_DATA00  L25 NAND_DATA01  L24 NAND_DATA02  N24 NAND_DATA03  P29
    NAND_DATA04  N29 NAND_DATA05  M29 NAND_DATA06  R29 NAND_DATA07  R26
    NAND_DQS  R28 NAND_RE_B  T28 NAND_READY_B  U28 NAND_WE_B  U29 NAND_WP_B
    G22 ONOFF  E16 PCIE_REF_PAD_CLK_N  D16 PCIE_REF_PAD_CLK_P  F16
    PCIE_RESREF  B14 PCIE_RXN_N  A14 PCIE_RXN_P  B15 PCIE_TXN_N  A15
    PCIE_TXN_P  F22 PMIC_ON_REQ  J24 PMIC_STBY_REQ  J29 POR_B  J25 RTC_XTALI
    J26 RTC_XTALO  AE12 SAI1_MCLK  AH8 SAI1_RXC  AC10 SAI1_RXD0  AF10
    SAI1_RXD1  AH9 SAI1_RXD2  AJ8 SAI1_RXD3  AD10 SAI1_RXD4  AE10 SAI1_RXD5
    AH10 SAI1_RXD6  AH12 SAI1_RXD7  AJ9 SAI1_RXFS  AJ12 SAI1_TXC  AJ11
    SAI1_TXD0  AJ10 SAI1_TXD1  AH11 SAI1_TXD2  AD12 SAI1_TXD3  AH13
    SAI1_TXD4  AH14 SAI1_TXD5  AC12 SAI1_TXD6  AJ13 SAI1_TXD7  AF12
    SAI1_TXFS  AJ15 SAI2_MCLK  AJ16 SAI2_RXC  AJ14 SAI2_RXD0  AH17 SAI2_RXFS
    AH15 SAI2_TXC  AH16 SAI2_TXD0  AJ17 SAI2_TXFS  AJ20 SAI3_MCLK  AJ18
    SAI3_RXC  AF18 SAI3_RXD  AJ19 SAI3_RXFS  AH19 SAI3_TXC  AH18 SAI3_TXD
    AC16 SAI3_TXFS  AF14 SAI5_MCLK  AD14 SAI5_RXC  AE16 SAI5_RXD0  AD16
    SAI5_RXD1  AF16 SAI5_RXD2  AE14 SAI5_RXD3  AC14 SAI5_RXFS  W28 SD1_CLK
    W29 SD1_CMD  Y29 SD1_DATA0  Y28 SD1_DATA1  V29 SD1_DATA2  V28 SD1_DATA3
    U26 SD1_DATA4  AA29 SD1_DATA5  AA28 SD1_DATA6  U25 SD1_DATA7  W25
    SD1_RESET_B  W26 SD1_STROBE  AD29 SD2_CD_B  AB29 SD2_CLK  AB28 SD2_CMD
    AC28 SD2_DATA0  AC29 SD2_DATA1  AA26 SD2_DATA2  AA25 SD2_DATA3  AD28
    SD2_RESET_B  AC26 SD2_WP  AC18 SPDIF_EXT_CLK  AD18 SPDIF_RX  AE18
    SPDIF_TX  AD6 UART1_RXD  AJ3 UART1_TXD  AF6 UART2_RXD  AH4 UART2_TXD
    AE6 UART3_RXD  AJ4 UART3_TXD  AJ5 UART4_RXD  AH5 UART4_TXD  E10 USB1_D_N
    D10 USB1_D_P  B11 USB1_DNU  B9 USB1_RX_N  A9 USB1_RX_P  B10 USB1_TX_N
    A10 USB1_TX_P  F10 USB1_TXRTUNE  A11 USB1_VBUS  E14 USB2_D_N  D14
    USB2_D_P  E12 USB2_DNU  B12 USB2_RX_N  A12 USB2_RX_P  B13 USB2_TX_N  A13
    USB2_TX_P  F12 USB2_TXRTUNE  D12 USB2_VBUS  G25 XTALI_24M  G26 XTALO_24M
"""
_pairs = TABLE.split()
_balls, _names = _pairs[0::2], _pairs[1::2]
BALLS = _balls
assert len(BALLS) == 548 and len(set(BALLS)) == 548

_by = {}
for _b, _n in zip(_balls, _names):
    _by.setdefault(_n, []).append(_b)
_used = set()


def p(names, typ):
    """One pin per name; the name must be on exactly one ball."""
    out = []
    for n in names:
        assert len(_by[n]) == 1, n
        _used.add(n)
        out.append((_by[n][0], n, typ))
    return out


def rail(name, typ="power_in"):
    """Every ball of a repeated supply or ground name."""
    _used.add(name)
    return [(b, name, typ) for b in _by[name]]


pw, io, i, o, pa, nc = "power_in", "bidirectional", "input", "output", "passive", "no_connect"


def pn(prefix, lanes):
    """Differential pairs, P before N: prefix + lane + _P/_N."""
    return [f"{prefix}{k}_{s}" for k in lanes for s in "PN"]


# Supplies
sup_left = [
    ("Arm Core", rail("VDD_ARM")),
    ("SoC", rail("VDD_SOC")),
]
sup_right = [
    ("DRAM", rail("NVCC_DRAM") + p(["VDD_DRAM_PLL_0P8", "VDD_DRAM_PLL_1P8"], pw)),
    ("I/O Banks", p(["NVCC_CLK", "NVCC_ECSPI_HDMI", "NVCC_ENET", "NVCC_GPIO", "NVCC_I2C_UART",
                     "NVCC_JTAG", "NVCC_NAND", "NVCC_SAI1_SAI5", "NVCC_SAI2_SAI3_SPDIF",
                     "NVCC_SD1", "NVCC_SD2"], pw)
     + [None] + p(["PVCC0_1P8", "PVCC1_1P8", "PVCC2_1P8"], pw)),
    ("Analog / PLL", p(["VDD_24M_XTAL_1P8", "VDD_ANA0_1P8", "VDD_ANA1_0P8", "VDD_ANA1_1P8",
                        "VDD_ANA2_1P8", "VDD_ARM_PLL_0P8", "VDD_ARM_PLL_1P8", "VDD_AVPLL_1P8",
                        "VDD_SAI_PLL_0P8", "VDD_SAI_PLL_1P8"], pw)),
    ("SNVS", p(["NVCC_SNVS_1P8"], pw) + p(["VDD_SNVS_0P8_CAP"], "power_out")),
    ("PHY", p(["VDD_EARC_1P8", "VDD_HDMI_0P8", "VDD_HDMI_1P8", "VDD_LVDS_1P8", "VDD_MIPI_0P8",
               "VDD_MIPI_1P8"], pw) + p(["VDD_MIPI_1P2_CAP"], "power_out")
     + p(["VDD_PCI_0P8", "VDD_PCI_1P8", "VDD_USB_0P8", "VDD_USB_1P8", "VDD_USB_3P3"], pw)),
]

# Ground
_vss = rail("VSS")
assert len(_vss) == 109
gnd_left = [("Ground", _vss[:55])]
gnd_right = [("Ground", _vss[55:])]

# DRAM
_ac = [f"DRAM_AC{k:02d}" for k in range(39) if k != 18]


def byte(n):
    return (f"Byte {n}", p([f"DRAM_DQ{8 * n + k:02d}" for k in range(8)] + [f"DRAM_DM{n}"]
                           + [f"DRAM_DQS{n}_P", f"DRAM_DQS{n}_N"], io))


ddr_left = [
    ("Address / Command", p(_ac, o)),
    ("Control", p(["DRAM_RESET_N"], o) + p(["DRAM_ALERT_N"], i) + p(["DRAM_ZN", "DRAM_VREF"], pa)),
]
ddr_right = [byte(0), byte(1), byte(2), byte(3)]

# System, USB, PCIe
sys_left = [
    ("Reset / Power", p(["POR_B", "ONOFF"], i) + p(["PMIC_ON_REQ", "PMIC_STBY_REQ"], o)),
    ("Boot", p([f"BOOT_MODE{k}" for k in range(4)], i)),
    ("Clocks", p(["XTALI_24M"], i) + p(["XTALO_24M"], o) + p(["RTC_XTALI"], i) + p(["RTC_XTALO"], o)
     + p(["CLKIN1", "CLKIN2"], i) + p(["CLKOUT1", "CLKOUT2"], o)),
    ("JTAG", p(["JTAG_MOD", "JTAG_TCK", "JTAG_TMS", "JTAG_TDI"], i) + p(["JTAG_TDO"], o)),
]


def usb(n):
    u = f"USB{n}_"
    return (f"USB {n}", p([u + "VBUS"], i) + p([u + "D_P", u + "D_N"], io) + p([u + "TX_P", u + "TX_N"], o)
            + p([u + "RX_P", u + "RX_N"], i) + p([u + "TXRTUNE"], pa) + p([u + "DNU"], nc))


sys_right = [
    usb(1), usb(2),
    ("PCIe", p(["PCIE_TXN_P", "PCIE_TXN_N"], o) + p(["PCIE_RXN_P", "PCIE_RXN_N"], i)
     + p(["PCIE_REF_PAD_CLK_P", "PCIE_REF_PAD_CLK_N"], io) + p(["PCIE_RESREF"], pa)),
]

# Display and camera


def csi(n):
    return (f"MIPI CSI {n}", p([f"MIPI_CSI{n}_CLK_P", f"MIPI_CSI{n}_CLK_N"]
                               + pn(f"MIPI_CSI{n}_D", range(4)), i))


def lvds(n):
    return (f"LVDS {n}", p([f"LVDS{n}_CLK_P", f"LVDS{n}_CLK_N"] + pn(f"LVDS{n}_D", range(4)), o))


disp_left = [
    csi(1), csi(2),
    ("MIPI DSI", p(["MIPI_DSI1_CLK_P", "MIPI_DSI1_CLK_N"], o) + p(pn("MIPI_DSI1_D", [0]), io)
     + p(pn("MIPI_DSI1_D", range(1, 4)), o) + p(["MIPI_VREG1_CAP"], pa) + p(["MIPI_TEST_DNU"], nc)),
]
disp_right = [
    lvds(0), lvds(1),
    ("HDMI", p(["HDMI_TXC_P", "HDMI_TXC_N"] + pn("HDMI_TX", range(3)), o) + p(["HDMI_HPD"], i)
     + p(["HDMI_CEC", "HDMI_DDC_SCL", "HDMI_DDC_SDA"], io) + p(["HDMI_REXT"], pa)),
    ("eARC", p(["EARC_P_UTIL", "EARC_N_HPD", "EARC_AUX"], io)),
]

# GPIO, Ethernet, SD
io1_left = [
    ("GPIO1", p([f"GPIO1_IO{k:02d}" for k in range(16)], io)),
    ("ENET (RGMII)", p(["ENET_MDC", "ENET_MDIO"] + [f"ENET_TD{k}" for k in range(4)] + ["ENET_TX_CTL", "ENET_TXC"]
                       + [f"ENET_RD{k}" for k in range(4)] + ["ENET_RX_CTL", "ENET_RXC"], io)),
]
io1_right = [
    ("SD1", p(["SD1_CLK", "SD1_CMD"] + [f"SD1_DATA{k}" for k in range(8)] + ["SD1_STROBE", "SD1_RESET_B"], io)),
    ("SD2", p(["SD2_CLK", "SD2_CMD"] + [f"SD2_DATA{k}" for k in range(4)] + ["SD2_CD_B", "SD2_WP", "SD2_RESET_B"], io)),
    ("I2C", p([f"I2C{n}_{s}" for n in range(1, 5) for s in ("SCL", "SDA")], io)),
]

# NAND, audio, serial
io2_left = [
    ("NAND", p(["NAND_ALE", "NAND_CLE"] + [f"NAND_CE{k}_B" for k in range(4)]
               + ["NAND_RE_B", "NAND_WE_B", "NAND_WP_B", "NAND_READY_B", "NAND_DQS"]
               + [f"NAND_DATA{k:02d}" for k in range(8)], io)),
    ("ECSPI1", p([f"ECSPI1_{s}" for s in ("SCLK", "MOSI", "MISO", "SS0")], io)),
    ("ECSPI2", p([f"ECSPI2_{s}" for s in ("SCLK", "MOSI", "MISO", "SS0")], io)),
    ("UART", p([f"UART{n}_{s}" for n in range(1, 5) for s in ("TXD", "RXD")], io)),
    ("SAI5", p(["SAI5_MCLK", "SAI5_RXC", "SAI5_RXFS"] + [f"SAI5_RXD{k}" for k in range(4)], io)),
]
io2_right = [
    ("SAI1", p(["SAI1_MCLK", "SAI1_TXC", "SAI1_TXFS"] + [f"SAI1_TXD{k}" for k in range(8)]
               + ["SAI1_RXC", "SAI1_RXFS"] + [f"SAI1_RXD{k}" for k in range(8)], io)),
    ("SAI2", p(["SAI2_MCLK", "SAI2_TXC", "SAI2_TXFS", "SAI2_TXD0", "SAI2_RXC", "SAI2_RXFS", "SAI2_RXD0"], io)),
    ("SAI3", p(["SAI3_MCLK", "SAI3_TXC", "SAI3_TXFS", "SAI3_TXD", "SAI3_RXC", "SAI3_RXFS", "SAI3_RXD"], io)),
    ("SPDIF", p(["SPDIF_TX", "SPDIF_RX", "SPDIF_EXT_CLK"], io)),
]

UNITS = [
    ("i.MX 8M Plus Supplies", sup_left, sup_right),
    ("i.MX 8M Plus Ground", gnd_left, gnd_right),
    ("i.MX 8M Plus DRAM", ddr_left, ddr_right),
    ("i.MX 8M Plus System / USB / PCIe", sys_left, sys_right),
    ("i.MX 8M Plus Display / Camera", disp_left, disp_right),
    ("i.MX 8M Plus GPIO / ENET / SD", io1_left, io1_right),
    ("i.MX 8M Plus NAND / Audio / Serial", io2_left, io2_right),
]
assert _used == set(_by), sorted(set(_by) - _used)
