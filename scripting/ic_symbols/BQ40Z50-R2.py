# BQ40Z50-R2, VQFN-32 4 x 4 mm (RSM0032A), 1- to 4-series Li-ion pack manager.
# Pinout: TI SLUSCS4C (April 2021), section 6 pin diagram and Table 6-1.
# The BQ4050 (SLUSBX7) has the same pinout and package, so one symbol and
# footprint serve both; only the Value and Part Number change.
# Pin types: BAT and VCC are supplies (power_in). PBI only takes the
# 2.2 uF backup capacitor (passive). VC1-VC4, SRP/SRN and PACK are analog
# inputs (input). TS1-TS4 drive and sense the thermistors (passive). CHG,
# DSG and PCHG are FET gate drivers (output). FUSE (chemical-fuse FET
# drive) and BTP_INT are outputs in Table 6-1, but the table ties both to
# VSS when unused, so they are passive here: an output pin on the ground
# net is an ERC error otherwise. SMBC/SMBD are open-drain I/O
# (bidirectional). PRES/SHUTDN and DISP are inputs. LEDCNTLA-C are LED current sinks
# (output; Table 6-1 allows them floating). NC pins 7, 14, 29 are not
# connected inside (no_connect; Table 6-1: floating or VSS). The thermal
# pad (33) is device ground: tie it to VSS.
NAME = "BQ40Z50-R2"
TITLE = "BQ40Z50 Battery Pack Manager"
PINCOUNT = 33
PROPS = {
    "Footprint": "Jonas:Texas_RSM0032A_VQFN-32-1EP_4x4mm_P0.4mm_EP1.4x1.4mm",
    "Datasheet": "https://www.ti.com/lit/ds/symlink/bq40z50-r2.pdf",
    "Description": "1- to 4-series Li-ion battery pack manager: protection, high-side N-FET drive, cell balancing, Impedance Track gas gauge, SMBus; VQFN-32 4x4 mm (BQ4050RSM is pin and footprint compatible)",
    "Manufacturer": "TI",
    "Part Number": "BQ40Z50RSMR-R2",
    "ki_fp_filters": "*RSM0032A*",
}
LEFT = [
    ("Power", [
        ("32", "BAT", "power_in"), ("26", "VCC", "power_in"), ("1", "PBI", "passive"),
        None,
        ("9", "VSS", "power_in"), ("33", "PAD", "power_in"),
    ]),
    ("Cell Inputs", [
        ("2", "VC4", "input"), ("3", "VC3", "input"),
        ("4", "VC2", "input"), ("5", "VC1", "input"),
    ]),
    ("Current Sense", [("8", "SRP", "input"), ("6", "SRN", "input")]),
    ("Thermistors", [
        ("10", "TS1", "passive"), ("11", "TS2", "passive"),
        ("12", "TS3", "passive"), ("13", "TS4", "passive"),
    ]),
]
RIGHT = [
    ("FET Drive", [
        ("31", "CHG", "output"), ("28", "DSG", "output"), ("30", "PCHG", "output"),
        ("27", "PACK", "input"),
    ]),
    ("Fuse / PTC", [("25", "FUSE", "passive"), ("23", "PTC", "input"), ("24", "PTCEN", "input")]),
    ("SMBus", [("19", "SMBC", "bidirectional"), ("18", "SMBD", "bidirectional")]),
    ("System", [
        ("16", "PRES/SHUTDN", "input"), ("15", "BTP_INT", "passive"), ("17", "DISP", "input"),
    ]),
    ("LED", [("20", "LEDCNTLA", "output"), ("21", "LEDCNTLB", "output"), ("22", "LEDCNTLC", "output")]),
    ("NC", [("7", "NC", "no_connect"), ("14", "NC", "no_connect"), ("29", "NC", "no_connect")]),
]
