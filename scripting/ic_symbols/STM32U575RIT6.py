# STM32U575RIT6, LQFP64 without SMPS (no Q suffix; the Q parts give PB9,
# PB12, PC4 and PC5 to the SMPS and have 47 I/Os instead of 51).
# Pinout: ST DS13737 Rev 10, Figure 12 "LQFP64 pinout" and the LQFP64
# column of the pin definitions table; cross-checked pin for pin against
# KiCad 10's MCU_ST_STM32U5:STM32U575RITx. NRST and PH3-BOOT0 are I/O per
# the table. VCAP is the LDO output (4.7 uF to VSS).
NAME = "STM32U575RIT6"
TITLE = "STM32U575 MCU"
PINCOUNT = 64
PROPS = {
    "Footprint": "Package_QFP:LQFP-64_10x10mm_P0.5mm",
    "Datasheet": "https://www.st.com/resource/en/datasheet/stm32u575ag.pdf",
    "Description": "Ultra-low-power Arm Cortex-M33 MCU with TrustZone and FPU, 160 MHz, 2 MB flash, 786 KB SRAM, USB OTG FS, 51 I/Os, LQFP64 (LDO pinout, no SMPS)",
    "Manufacturer": "ST",
    "Part Number": "STM32U575RIT6",
    "ki_fp_filters": "LQFP*10x10mm*P0.5mm*",
}
pw, io = "power_in", "bidirectional"
LEFT = [
    ("Power", [
        ("19", "VDD", pw), ("32", "VDD", pw), ("64", "VDD", pw),
        ("13", "VDDA", pw), ("48", "VDDUSB", pw), ("1", "VBAT", pw),
        ("30", "VCAP", "power_out"),
        None,
        ("18", "VSS", pw), ("31", "VSS", pw), ("47", "VSS", pw), ("63", "VSS", pw),
        ("12", "VSSA", pw),
    ]),
    ("Reset / Boot", [("7", "NRST", io), ("60", "PH3-BOOT0", io)]),
    ("Clocks", [
        ("5", "PH0-OSC_IN", io), ("6", "PH1-OSC_OUT", io),
        ("3", "PC14-OSC32_IN", io), ("4", "PC15-OSC32_OUT", io),
    ]),
    ("Port C", [
        ("8", "PC0", io), ("9", "PC1", io), ("10", "PC2", io), ("11", "PC3", io),
        ("24", "PC4", io), ("25", "PC5", io), ("37", "PC6", io), ("38", "PC7", io),
        ("39", "PC8", io), ("40", "PC9", io), ("51", "PC10", io), ("52", "PC11", io),
        ("53", "PC12", io), ("2", "PC13", io),
    ]),
]
RIGHT = [
    ("Port A", [
        ("14", "PA0", io), ("15", "PA1", io), ("16", "PA2", io), ("17", "PA3", io),
        ("20", "PA4", io), ("21", "PA5", io), ("22", "PA6", io), ("23", "PA7", io),
        ("41", "PA8", io), ("42", "PA9", io), ("43", "PA10", io), ("44", "PA11", io),
        ("45", "PA12", io), ("46", "PA13", io), ("49", "PA14", io), ("50", "PA15", io),
    ]),
    ("Port B", [
        ("26", "PB0", io), ("27", "PB1", io), ("28", "PB2", io), ("55", "PB3", io),
        ("56", "PB4", io), ("57", "PB5", io), ("58", "PB6", io), ("59", "PB7", io),
        ("61", "PB8", io), ("62", "PB9", io), ("29", "PB10", io), ("33", "PB12", io),
        ("34", "PB13", io), ("35", "PB14", io), ("36", "PB15", io),
    ]),
    ("Port D", [("54", "PD2", io)]),
]
