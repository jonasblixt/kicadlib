# ISM330BX, LGA-14L 2.5 x 3.0 x 0.74 mm.
# Pinout: ST DS14588 Rev 2 (June 2024), Figure 5 and Table 2. Package:
# Figure 32; the same land layout as KiCad's
# LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y (used by the stock ISM330DHCX
# symbol), but not the same pinout as the ISM330DHCX: INT2 is pin 10 here
# and pin 9 there. SCL/SDA carry their SPI names as on LSM9DS1.
# Unused pins (Table 2): TDMout and BCLK to GND or VDDIO, WCLK to VDDIO or
# open, AH1/QVAR1 and AH2/QVAR2 to VDD or GND. 100 nF on VDD and on VDDIO.
NAME = "ISM330BX"
TITLE = "6-Axis IMU"
PINCOUNT = 14
PROPS = {
    "Footprint": "Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
    "Datasheet": "https://www.st.com/resource/en/datasheet/ism330bx.pdf",
    "Description": "6-axis IMU, 3D accelerometer and 3D gyroscope with SPI, I2C/I3C and TDM, analog hub/Qvar, industrial 10-year longevity, LGA-14L 2.5x3x0.74 mm",
    "Manufacturer": "ST",
    "Part Number": "ISM330BXTR",
    "ki_fp_filters": "LGA*3x2.5mm*P0.5mm*",
}
LEFT = [
    ("SPI / I2C", [
        ("12", "CS", "input"), ("13", "SCL/SPC", "input"),
        ("14", "SDA/SDI/SDO", "bidirectional"), ("1", "SDO/TA0", "bidirectional"),
    ]),
    ("Interrupts", [("4", "INT1", "output"), ("10", "INT2", "output")]),
    ("TDM", [("2", "TDMout", "output"), ("3", "BCLK", "input"), ("11", "WCLK", "input")]),
]
RIGHT = [
    ("Power", [("8", "VDD", "power_in"), ("5", "VDDIO", "power_in"), None, ("7", "GND", "power_in")]),
    ("Analog Hub", [("6", "AH1/QVAR1", "passive"), ("9", "AH2/QVAR2", "passive")]),
]
