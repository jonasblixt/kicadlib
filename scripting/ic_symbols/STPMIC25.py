# STPMIC25, VQFN 56L 6.5 x 6.5 x 0.9 mm, 0.4 mm pitch, exposed pad 4.5 x
# 4.5 mm: PMIC companion of the STM32MP2 MPUs, 7 buck SMPS (2 MHz COT),
# 8 LDOs (LDO3 DDR3L/DDR4 termination sink/source or bypass, LDO4 USB PHY
# supply with VBUS/VIN source detection), VREFDDR, NVM-programmed
# voltages and power-up sequence, I2C.
# Pinout: ST DS14278 Rev 7 (October 2026), Figure 2 (pin configuration,
# top view) and Table 3 (pin description), checked against each other pin
# for pin. The exposed pad EPGND is pin 57 here (to ground).
# One symbol for all three orderable codes (Table 110): STPMIC25APQR,
# STPMIC25BPQR and STPMIC25DPQR have the same die and pinout and differ
# only in the NVM defaults of Table 1 (B: VIO/BUCK4 1.8 V instead of
# 3.3 V; D: other LDO/BUCK defaults). Part Number is set to the A code;
# change it (and the Value) on the schematic for B or D.
# Pin types: VIN, VBUS, VIO and the LDO/buck power inputs are supplies
# (power_in), AGND, GNDLDO, PGND1-7 and EPGND grounds (power_in).
# LDOxOUT, VREFDDR and INTLDO (internal LDO, 4.7 uF to ground) are
# regulator outputs (power_out). VLXn are the switch nodes (output).
# VOUTn are the buck feedback inputs in Table 3 ("I"), but they sit on
# the buck's output rail, which nothing else on the board drives, so they
# are power_out: with input every rail fed by a buck would need a
# PWR_FLAG to pass ERC. PONKEYn (pull-up to VIN), WAKEUPn (pull-up to
# VINTLDO), PWRCTRL1-3 and SCL are inputs; SDA bidirectional. RSTn
# (input + open-drain output, section 5.4) and INTn (open drain) have an
# internal pull-up to VIO: open_collector.
NAME = "STPMIC25"
TITLE = "STPMIC25 PMIC"
PINCOUNT = 57
PROPS = {
    "Footprint": "Jonas:ST_VQFN-56-1EP_6.5x6.5mm_P0.4mm_EP4.5x4.5mm",
    "Datasheet": "https://www.st.com/resource/en/datasheet/stpmic25.pdf",
    "Description": "PMIC for STM32MP2 MPUs: 7 buck converters (2 MHz COT), 8 LDOs (DDR termination sink/source, USB PHY), VREFDDR, NVM-programmable voltages and sequencing, I2C, 2.8-5.5 V input; VQFN-56 6.5x6.5 mm P0.4 mm (STPMIC25BPQR/DPQR: same pinout, other NVM defaults)",
    "Manufacturer": "ST",
    "Part Number": "STPMIC25APQR",
    "ki_fp_filters": "*QFN*56*6.5x6.5mm*P0.4mm*",
}
LEFT = [
    ("Power", [
        ("11", "VIN", "power_in"), ("12", "VBUS", "power_in"), ("29", "VIO", "power_in"),
        None,
        ("10", "AGND", "power_in"), ("9", "GNDLDO", "power_in"),
        ("41", "PGND1", "power_in"), ("27", "PGND2", "power_in"), ("22", "PGND3", "power_in"),
        ("18", "PGND4", "power_in"), ("36", "PGND5", "power_in"), ("47", "PGND6", "power_in"),
        ("52", "PGND7", "power_in"), ("57", "EPGND", "power_in"),
    ]),
    ("Buck Inputs", [
        ("39", "BUCK1IN", "power_in"), ("25", "BUCK2IN", "power_in"), ("24", "BUCK3IN", "power_in"),
        ("20", "BUCK4IN", "power_in"), ("38", "BUCK5IN", "power_in"), ("49", "BUCK6IN", "power_in"),
        ("50", "BUCK7IN", "power_in"),
    ]),
    ("LDO Inputs", [
        ("15", "LDO12IN", "power_in"), ("43", "LDO3IN", "power_in"),
        ("6", "LDO56IN", "power_in"), ("3", "LDO78IN", "power_in"),
    ]),
    ("Control", [
        ("1", "PONKEYn", "input"), ("30", "WAKEUPn", "input"),
        ("31", "RSTn", "open_collector"), ("32", "INTn", "open_collector"),
        ("56", "PWRCTRL1", "input"), ("55", "PWRCTRL2", "input"), ("54", "PWRCTRL3", "input"),
    ]),
]
RIGHT = [
    ("Bucks", [
        ("40", "VLX1", "output"), ("42", "VOUT1", "power_out"),
        None,
        ("26", "VLX2", "output"), ("28", "VOUT2", "power_out"),
        None,
        ("23", "VLX3", "output"), ("21", "VOUT3", "power_out"),
        None,
        ("19", "VLX4", "output"), ("17", "VOUT4", "power_out"),
        None,
        ("37", "VLX5", "output"), ("35", "VOUT5", "power_out"),
        None,
        ("48", "VLX6", "output"), ("46", "VOUT6", "power_out"),
        None,
        ("51", "VLX7", "output"), ("53", "VOUT7", "power_out"),
    ]),
    ("LDOs", [
        ("14", "LDO1OUT", "power_out"), ("16", "LDO2OUT", "power_out"),
        ("44", "LDO3OUT", "power_out"), ("13", "LDO4OUT", "power_out"),
        ("7", "LDO5OUT", "power_out"), ("5", "LDO6OUT", "power_out"),
        ("4", "LDO7OUT", "power_out"), ("2", "LDO8OUT", "power_out"),
    ]),
    ("References", [("45", "VREFDDR", "power_out"), ("8", "INTLDO", "power_out")]),
    ("I2C", [("33", "SCL", "input"), ("34", "SDA", "bidirectional")]),
]
