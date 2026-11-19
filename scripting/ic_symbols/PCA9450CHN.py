# PCA9450CHN: NXP PMIC for the i.MX 8M Plus (the EVK's PMIC, SPF-46368 A3
# sheet 11), HVQFN56 7 x 7 mm, 0.4 mm pitch, 4.7 mm exposed pad (SOT949-6).
# Six bucks (PCA9450C: BUCK1 + BUCK3 one 6 A dual-phase regulator, BUCK2
# 3 A with DVS and remote sense, BUCK4-6), five LDOs, 400 mA SD-card load
# switch, 2-bit I2C level translator, 32.768 kHz crystal driver.
# Pinout: NXP PCA9450 data sheet Rev. 2.3 (8 July 2024), Figure 2 (pin
# map, top view) and Table 3 (pin description); EP is pin 57 here.
# PCA9450AAHN (i.MX 8M Mini) and PCA9450BHN (i.MX 8M Nano) have the same
# pinout and package, but R_SNSP3_CFG means something else on each
# (BUCK3 remote sense on AA, tie to VSYS on B, tie to GND on C).
# Pin types: VSYS, INL1, INB13/INB26/INB45 and SWIN supplies (power_in),
# AGND, BUCK_AGND and EP grounds (power_in). LDO1-5, VINT (internal supply,
# 1 uF) and SWOUT (load switch output) regulator outputs (power_out). LXn
# switch nodes (output). BUCK4FB/5FB/6FB and R_SNSP1/2 sense the buck
# outputs on their rails, which nothing else drives: power_out, as on
# STPMIC25 (else every buck rail needs a PWR_FLAG). R_SNSP3_CFG is a logic
# input on the C (tied to GND). POR_B and IRQ_B are open drain;
# RTC_RESET_B goes high-Z with an internal pull-up to LDO1: open_collector.
# The level translator (SDAH/SCLH/SDAL/SCLL) senses direction
# automatically: bidirectional.
NAME = "PCA9450CHN"
TITLE = "PCA9450C PMIC"
PINCOUNT = 57
PROPS = {
    "Footprint": "Jonas:NXP_SOT949-6_HVQFN-56-1EP_7x7mm_P0.4mm_EP4.7x4.7mm",
    "Datasheet": "https://www.nxp.com/docs/en/data-sheet/PCA9450.pdf",
    "Description": "PMIC for i.MX 8M Plus: 6 A dual-phase buck (BUCK1/3) + 5 bucks with DVS and remote sense, 5 LDOs, 400 mA SD load switch, I2C level translator, 32.768 kHz oscillator, I2C; 2.7-5.5 V input; HVQFN-56 7x7 mm P0.4 mm (SOT949-6)",
    "Manufacturer": "NXP",
    "Part Number": "PCA9450CHNY",
    "ki_fp_filters": "*SOT949*HVQFN*56*7x7mm*P0.4mm*",
}
pw, po, o, i, io, oc = "power_in", "power_out", "output", "input", "bidirectional", "open_collector"
LEFT = [
    ("Power", [
        ("53", "VSYS", pw), ("56", "INL1", pw),
        None,
        ("5", "AGND", pw), ("43", "BUCK_AGND", pw), ("57", "EP", pw),
    ]),
    ("Buck Inputs", [
        ("33", "INB13", pw), ("34", "INB13", pw), ("35", "INB13", pw),
        None,
        ("47", "INB26", pw), ("48", "INB26", pw), ("49", "INB26", pw),
        None,
        ("16", "INB45", pw), ("17", "INB45", pw), ("18", "INB45", pw),
    ]),
    ("Load Switch", [("22", "SWIN", pw), ("12", "SW_EN", i), ("23", "SWOUT", po)]),
    ("Control", [
        ("39", "PMIC_ON_REQ", i), ("40", "PMIC_STBY_REQ", i), ("8", "PMIC_RST_B", i),
        ("28", "WDOG_B", i), ("29", "SD_VSEL", i), ("30", "R_SNSP3_CFG", i),
    ]),
    ("I2C", [("41", "SCL", i), ("42", "SDA", io)]),
    ("32 kHz Crystal", [("10", "XTAL_IN", i), ("11", "XTAL_OUT", o)]),
]
RIGHT = [
    ("Bucks", [
        ("36", "LX1", o), ("37", "LX1", o), ("38", "R_SNSP1", po),
        None,
        ("31", "LX3", o), ("32", "LX3", o),
        None,
        ("45", "LX2", o), ("46", "LX2", o), ("44", "R_SNSP2", po),
        None,
        ("19", "LX4", o), ("20", "LX4", o), ("21", "BUCK4FB", po),
        None,
        ("15", "LX5", o), ("14", "BUCK5FB", po),
        None,
        ("50", "LX6", o), ("51", "LX6", o), ("52", "BUCK6FB", po),
    ]),
    ("LDOs", [
        ("3", "LDO1", po), ("2", "LDO2", po), ("54", "LDO3", po),
        ("1", "LDO4", po), ("55", "LDO5", po), ("4", "VINT", po),
    ]),
    ("Status", [
        ("9", "POR_B", oc), ("13", "IRQ_B", oc), ("6", "RTC_RESET_B", oc), ("7", "CLK_32K_OUT", o),
    ]),
    ("Level Translator", [("24", "SDAH", io), ("25", "SCLH", io), ("26", "SDAL", io), ("27", "SCLL", io)]),
]
