# Rename batch 2026-10: remap list for projects

Cleanup review A5.4 (`docs/review-2026-10-cleanup.md`), done 2026-10-19 in
one batch so projects remap once. Schematics store symbols as
`<nickname>:<symbol>` (database parts: `<nickname>:<chooser>/<id>`), boards
store `Jonas:<footprint>` and model paths, so each of the changes below
breaks *Update from Library* until the project is remapped.

## What changed

- **Symbol libraries** (A5.1): renamed, merged, `power` split. Global
  sym-lib-table updated on archimedes; project tables that list these
  libraries need the same change.
- **Database libraries** (A4.2/A4.1): `cap_mlcc_murata_GRM` ->
  `cap_mlcc_murata_grm`, `diode_tvs_littlefuse` -> `diode_tvs_littelfuse`,
  `cap_rfmw_kyocera_accu_p` -> `cap_rfmw_kyocera_accup`.
- **Chooser names** (A4.4): `cap_alel_chemicon` AlEl -> Chemi-Con,
  `diode_tvs_*` TVS -> SMAJ-SMCJ, `xtal_epson` Epson -> TSX-FA-FC,
  `xtal_ndk` NDK -> NX. Part ids are unchanged.
- **Footprints** (F4.8): 25 renamed in `Jonas.pretty`; **3D models** (F5.3):
  30 renamed in `Jonas.3dshapes`. Geometry and transforms are unchanged.
- **One symbol changed** (F1.19): `diode_misc:PDS1040-13` and
  `PDS5100Q-13D` lose their second `A` pin (both were number 2). If a wire
  ended on the removed pin (the one 2.54 mm off the K-A axis), reconnect
  it to the remaining A pin.

## How to remap a project

1. Project `sym-lib-table` / `fp-lib-table`: apply the nickname changes
   below (most projects use the global tables and need nothing).
2. Schematic: replace the `lib_id`s in the tables below (Symbol Editor:
   *Tools -> Edit Symbol Library References*, or a text replace of each old
   id everywhere in the `.kicad_sch` files while the project is closed,
   which also covers the embedded `lib_symbols` copies), then *Update
   Symbols from Library*. Also replace `Jonas:<old footprint>` in Footprint fields.
3. Board: *Change Footprints* (or replace `(footprint "Jonas:<old>"` while
   closed) per the footprint table, then *Update Footprints from Library*;
   that also brings the new model paths. For per-board models (the Würth
   USB connector), replace the model path.

## poetato (as of 2026-10-19, read-only scan)

### Symbols (`lib_id`)

| Old | New | Uses |
|---|---|---|
| `LEDs:LED0402_150040AS73240` | `led:LED0402_150040AS73240` | 1 |
| `LEDs:LED0402_150040SS73240` | `led:LED0402_150040SS73240` | 1 |
| `LEDs:LED0402_150040VS73240` | `led:LED0402_150040VS73240` | 5 |
| `cap_alel_chemicon:AlEl/C5x5.8_22u_50V_MZR_20` | `cap_alel_chemicon:Chemi-Con/C5x5.8_22u_50V_MZR_20` | 1 |
| `cap_alel_chemicon:AlEl/C8x10_22u_100V_MVE_20` | `cap_alel_chemicon:Chemi-Con/C8x10_22u_100V_MVE_20` | 1 |
| `cap_alel_chemicon:AlEl/C8x10_470u_25V_MZL_20` | `cap_alel_chemicon:Chemi-Con/C8x10_470u_25V_MZL_20` | 1 |
| `cap_mlcc_murata_GRM:GRM/C0402_100n_25V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C0402_100n_25V_X7R_10%` | 5 |
| `cap_mlcc_murata_GRM:GRM/C0402_10n_25V_C0G_5%` | `cap_mlcc_murata_grm:GRM/C0402_10n_25V_C0G_5%` | 2 |
| `cap_mlcc_murata_GRM:GRM/C0402_10p_50V_C0G_2%` | `cap_mlcc_murata_grm:GRM/C0402_10p_50V_C0G_2%` | 2 |
| `cap_mlcc_murata_GRM:GRM/C0402_12p_50V_C0G_2%` | `cap_mlcc_murata_grm:GRM/C0402_12p_50V_C0G_2%` | 2 |
| `cap_mlcc_murata_GRM:GRM/C0402_14n10_50V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C0402_14n10_50V_X7R_10%` | 1 |
| `cap_mlcc_murata_GRM:GRM/C0402_1u_10V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C0402_1u_10V_X7R_10%` | 23 |
| `cap_mlcc_murata_GRM:GRM/C0402_33p_50V_C0G_2%` | `cap_mlcc_murata_grm:GRM/C0402_33p_50V_C0G_2%` | 1 |
| `cap_mlcc_murata_GRM:GRM/C0402_68p_100V_C0G_5%` | `cap_mlcc_murata_grm:GRM/C0402_68p_100V_C0G_5%` | 1 |
| `cap_mlcc_murata_GRM:GRM/C0603_100n_100V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C0603_100n_100V_X7R_10%` | 7 |
| `cap_mlcc_murata_GRM:GRM/C0603_1n_100V_C0G_5%` | `cap_mlcc_murata_grm:GRM/C0603_1n_100V_C0G_5%` | 8 |
| `cap_mlcc_murata_GRM:GRM/C0603_22u_10V_X5R_20%` | `cap_mlcc_murata_grm:GRM/C0603_22u_10V_X5R_20%` | 1 |
| `cap_mlcc_murata_GRM:GRM/C0603_2u2_6.3V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C0603_2u2_6.3V_X7R_10%` | 2 |
| `cap_mlcc_murata_GRM:GRM/C0603_4u7_10V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C0603_4u7_10V_X7R_10%` | 1 |
| `cap_mlcc_murata_GRM:GRM/C0805_10n_100V_C0G_5%` | `cap_mlcc_murata_grm:GRM/C0805_10n_100V_C0G_5%` | 1 |
| `cap_mlcc_murata_GRM:GRM/C0805_10u_10V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C0805_10u_10V_X7R_10%` | 6 |
| `cap_mlcc_murata_GRM:GRM/C0805_10u_25V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C0805_10u_25V_X7R_10%` | 1 |
| `cap_mlcc_murata_GRM:GRM/C0805_1u_16V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C0805_1u_16V_X7R_10%` | 1 |
| `cap_mlcc_murata_GRM:GRM/C0805_1u_50V_X5R_20%` | `cap_mlcc_murata_grm:GRM/C0805_1u_50V_X5R_20%` | 1 |
| `cap_mlcc_murata_GRM:GRM/C0805_22u_16V_X5R_20%` | `cap_mlcc_murata_grm:GRM/C0805_22u_16V_X5R_20%` | 2 |
| `cap_mlcc_murata_GRM:GRM/C0805_22u_6.3V_X7R_20%` | `cap_mlcc_murata_grm:GRM/C0805_22u_6.3V_X7R_20%` | 1 |
| `cap_mlcc_murata_GRM:GRM/C0805_68p_250V_C0G_1%` | `cap_mlcc_murata_grm:GRM/C0805_68p_250V_C0G_1%` | 1 |
| `cap_mlcc_murata_GRM:GRM/C1206_1u_100V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C1206_1u_100V_X7R_10%` | 5 |
| `cap_mlcc_murata_GRM:GRM/C1206_4u7_50V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C1206_4u7_50V_X7R_10%` | 2 |
| `cap_mlcc_murata_GRM:GRM/C1210_22u_25V_X7R_10%` | `cap_mlcc_murata_grm:GRM/C1210_22u_25V_X7R_10%` | 2 |
| `connectors:7499511440` | `conn:7499511440` | 1 |
| `connectors:FTSH-105-01-L-DV-007-K` | `conn:FTSH-105-01-L-DV-007-K` | 1 |
| `connectors:Phoenix_1757268` | `conn:Phoenix_1757268` | 1 |
| `connectors:Phoenix_1757349` | `conn:Phoenix_1757349` | 1 |
| `connectors:Wurth_61300211121` | `conn:Wurth_61300211121` | 2 |
| `connectors:Wurth_61300611121` | `conn:Wurth_61300611121` | 1 |
| `connectors:Wurth_614105150721` | `conn:Wurth_614105150721` | 1 |
| `diode_tvs_littlefuse:TVS/SMAJ28CA` | `diode_tvs_littelfuse:SMAJ-SMCJ/SMAJ28CA` | 1 |
| `diode_tvs_littlefuse:TVS/SMAJ33CA` | `diode_tvs_littelfuse:SMAJ-SMCJ/SMAJ33CA` | 1 |
| `diode_tvs_littlefuse:TVS/SMAJ58A` | `diode_tvs_littelfuse:SMAJ-SMCJ/SMAJ58A` | 1 |
| `diode_tvs_littlefuse:TVS/SMAJ58CA` | `diode_tvs_littelfuse:SMAJ-SMCJ/SMAJ58CA` | 2 |
| `misc_capacitors:C1808_1n_3000V_X7R_10` | `cap_misc:C1808_1n_3000V_X7R_10` | 4 |
| `misc_capacitors:KW-5R5C334H-R` | `cap_misc:KW-5R5C334H-R` | 1 |
| `misc_inductors:1308_750319693` | `ind_misc:1308_750319693` | 1 |
| `misc_inductors:FA2672-ALD` | `ind_misc:FA2672-ALD` | 1 |
| `misc_resistors:R0204_1k_1_250mW_Vishay_SMM0204` | `res_misc:R0204_1k_1_250mW_Vishay_SMM0204` | 1 |
| `misc_resistors:R0402_0R_1_200mW_Vishay_CRCWHPe3` | `res_misc:R0402_0R_1_200mW_Vishay_CRCWHPe3` | 2 |
| `misc_resistors:R0805_0R_1_500mW_Vishay_CRCWHPe3` | `res_misc:R0805_0R_1_500mW_Vishay_CRCWHPe3` | 1 |
| `misc_resistors:R2512_10R_1_1.5W_Vishay_CRCWHPe3` | `res_misc:R2512_10R_1_1.5W_Vishay_CRCWHPe3` | 1 |
| `misc_resistors:R2512_12M_1_1W_Vishay_CRHV` | `res_misc:R2512_12M_1_1W_Vishay_CRHV` | 1 |
| `power:LP3470A293DBVR` | `power_mgmt:LP3470A293DBVR` | 1 |
| `power:TLVH431AQDBVR` | `power_mgmt:TLVH431AQDBVR` | 1 |
| `power:TPS26625DRCR` | `protection:TPS26625DRCR` | 1 |
| `transistors:AQY212GS` | `transistor:AQY212GS` | 1 |
| `transistors:FDV304P` | `transistor:FDV304P` | 2 |
| `transistors:NTK3134N` | `transistor:NTK3134N` | 5 |
| `transistors:VO618A-3X017T` | `transistor:VO618A-3X017T` | 1 |
| `xtal_epson:Epson/X1A0001410006` | `xtal_epson:TSX-FA-FC/X1A0001410006` | 1 |
| `xtal_epson:Epson/X1E0000210048` | `xtal_epson:TSX-FA-FC/X1E0000210048` | 1 |

### Footprints

| Old | New | Board | Schematic fields |
|---|---|---|---|
| `Jonas:FUSC3216X85N` | `Jonas:Fuse_Bel_0ZCJ_1206_3216Metric` | 2 | 2 |
| `Jonas:IHLP1212AE` | `Jonas:L_Vishay_IHLP-1212AE` | 2 | 4 |
| `Jonas:IHLP1212BZ` | `Jonas:L_Vishay_IHLP-1212BZ` | 2 | 6 |
| `Jonas:IHLP2020CZ` | `Jonas:L_Vishay_IHLP-2020CZ` | 1 | 3 |
| `Jonas:NX3215SA` | `Jonas:Crystal_SMD_NDK_NX3215SA-2Pin_3.2x1.5mm` | 1 | 2 |
| `Jonas:NX3225SA` | `Jonas:Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm` | 1 | 2 |
| `Jonas:QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm` | `Jonas:Skyworks_QFN-20-1EP_5x5mm_P0.8mm_EP2.7x2.7mm` | 1 | 2 |
| `Jonas:SAMTEC_FTSH-105-01-L-DV-007-K` | `Jonas:Samtec_FTSH-105-01-L-DV-007-K` | 1 | 2 |
| `Jonas:SOIC254P680X230-4N` | `Jonas:Panasonic_SOP-4_4.4x4.3mm_P2.54mm` | 2 | 2 |
| `Jonas:T_Wurth_WE-PPTI-1308` | `Jonas:Wurth_WE-PPTI-1308` | 1 | 3 |
| `Jonas:T_Wurth_WE-RJ45LAN_7499511440` | `Jonas:Wurth_WE-RJ45LAN_7499511440` | 1 | 2 |
| `Jonas:Vishay_SOIC254P1016X440-4N` | `Jonas:Vishay_SMD-4_W10.16mm_P2.54mm` | 1 | 2 |

### 3D model paths on the board

Footprints updated from the library bring these along. Only the USB model
sits on a stock footprint and must be replaced by hand.

| Old (`${JONAS_KICADLIB}/footprints/Jonas.3dshapes/...`) | New | Uses |
|---|---|---|
| `0ZCJ0005FF2E.step` | `Fuse_Bel_0ZCJ_1206_3216Metric.step` | 2 |
| `614105150721 (rev1).stp` | `USB_Micro-B_Wuerth_614105150721_Vertical.step` | 1 |
| `AQY212GS.step` | `Panasonic_SOP-4_4.4x4.3mm_P2.54mm.step` | 2 |
| `Coilcraft_FA2672-AL.STEP` | `Coilcraft_FA2672.step` | 1 |
| `FTSH-105-01-L-DV-007-K-TR.stp` | `Samtec_FTSH-105-01-L-DV-007-K.step` | 1 |
| `IHLP1212.step` | `L_Vishay_IHLP-1212.step` | 4 |
| `IHLP2020CZ.step` | `L_Vishay_IHLP-2020CZ.step` | 1 |
| `KW-5R5C104_224_334-R.STEP` | `Eaton_KW_13.5x8.8mm.step` | 1 |
| `NX3215SA.step` | `Crystal_SMD_NDK_NX3215SA-2Pin_3.2x1.5mm.step` | 1 |
| `NX3225SA.step` | `Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm.step` | 1 |
| `QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm.step` | `Skyworks_QFN-20-1EP_5x5mm_P0.8mm_EP2.7x2.7mm.step` | 1 |
| `T_Wurth_WE-PPTI-1308.step` | `Wurth_WE-PPTI-1308.step` | 1 |
| `T_Wurth_WE-RJ45LAN_7499511440.step` | `Wurth_WE-RJ45LAN_7499511440.step` | 1 |
| `VO618A-3X017T.step` | `Vishay_SMD-4_W10.16mm_P2.54mm.step` | 1 |

Also: `PDS5100Q-13D` (2x, `ethernet_poe`) is affected by F1.19.

## Full maps

### Symbol library nicknames

| Old | New |
|---|---|
| `misc_capacitors` | `cap_misc` |
| `misc_inductors` | `ind_misc` |
| `misc_resistors` | `res_misc` |
| `LEDs` | `led` |
| `transistors` | `transistor` |
| `connectors` | `conn` |
| `Audio Amp` | `analog` |
| `adcdac` | `analog` |
| `sensors` | `analog` |
| `power` | `power` (flags, BOM_Entry, TP), `protection`, `power_mgmt`, `driver`, `switch`, `dcdc`, `led` per symbol below |

### Symbols that left `power`

| Symbol | New library |
|---|---|
| `LTC3873IDDB-5` | `dcdc` |
| `L6470` | `driver` |
| `NCV7240` | `driver` |
| `LP5562` | `led` |
| `bq27742-G1` | `power_mgmt` |
| `INA226` | `power_mgmt` |
| `LP3470A293DBVR` | `power_mgmt` |
| `LP3470A308DBVR` | `power_mgmt` |
| `LTC2941IDCB#TRMPBF` | `power_mgmt` |
| `MAX16058ATA31+` | `power_mgmt` |
| `PAC1934` | `power_mgmt` |
| `TLVH431AQDBVR` | `power_mgmt` |
| `TPS3701` | `power_mgmt` |
| `TPS78318DDCR` | `power_mgmt` |
| `TPS7A1633DRBR` | `power_mgmt` |
| `1206SFS200F_63-2` | `protection` |
| `LM74610` | `protection` |
| `NCP360SNAET1G` | `protection` |
| `NCP380HSNAJAAT1G` | `protection` |
| `TPS25910` | `protection` |
| `TPS26625DRCR` | `protection` |
| `1-1825027-1` | `switch` |
| `PT65503` | `switch` |

### Footprints

| Old | New |
|---|---|
| `Coilcraft_FA2925-AL` | `Coilcraft_FA2925` |
| `DLW5B_5050` | `L_CommonModeChoke_Murata_DLW5B_5.0x5.0mm` |
| `FUSC3216X85N` | `Fuse_Bel_0ZCJ_1206_3216Metric` |
| `IHLP1212AB` | `L_Vishay_IHLP-1212AB` |
| `IHLP1212AE` | `L_Vishay_IHLP-1212AE` |
| `IHLP1212BZ` | `L_Vishay_IHLP-1212BZ` |
| `IHLP1616AB` | `L_Vishay_IHLP-1616AB` |
| `IHLP1616BZ` | `L_Vishay_IHLP-1616BZ` |
| `IHLP2020AB` | `L_Vishay_IHLP-2020AB` |
| `IHLP2020BZ` | `L_Vishay_IHLP-2020BZ` |
| `IHLP2020CZ` | `L_Vishay_IHLP-2020CZ` |
| `IHLP2525BD` | `L_Vishay_IHLP-2525BD` |
| `IHLP2525CZ` | `L_Vishay_IHLP-2525CZ` |
| `IHLP2525EZ` | `L_Vishay_IHLP-2525EZ` |
| `NX1255GB` | `Crystal_SMD_NDK_NX1255GB-4Pin_12.5x5.5mm` |
| `NX2520SA` | `Crystal_SMD_NDK_NX2520SA-4Pin_2.5x2.0mm` |
| `NX3215SA` | `Crystal_SMD_NDK_NX3215SA-2Pin_3.2x1.5mm` |
| `NX3225SA` | `Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm` |
| `QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm` | `Skyworks_QFN-20-1EP_5x5mm_P0.8mm_EP2.7x2.7mm` |
| `SAMTEC_FTSH-105-01-L-DV-007-K` | `Samtec_FTSH-105-01-L-DV-007-K` |
| `SOIC254P680X230-4N` | `Panasonic_SOP-4_4.4x4.3mm_P2.54mm` |
| `T_Wurth_WE-PPTI-1308` | `Wurth_WE-PPTI-1308` |
| `T_Wurth_WE-RJ45LAN_7498210002` | `Wurth_WE-RJ45LAN_7498210002` |
| `T_Wurth_WE-RJ45LAN_7498210003` | `Wurth_WE-RJ45LAN_7498210003` |
| `T_Wurth_WE-RJ45LAN_7499411122A` | `Wurth_WE-RJ45LAN_7499411122A` |
| `T_Wurth_WE-RJ45LAN_7499511440` | `Wurth_WE-RJ45LAN_7499511440` |
| `Texas_YJE` | `Texas_YJE0006A_PicoStar-6_1.15x2.2mm` |
| `TI_DFB0038A` | `Texas_DFB0038A_TSSOP-38_4.4x9.7mm_P0.5mm` |
| `Vishay_SOIC254P1016X440-4N` | `Vishay_SMD-4_W10.16mm_P2.54mm` |
| `Wurth_7499210123` | `Wurth_WE-RJ45LAN_7499210123` |

### 3D models

| Old | New |
|---|---|
| `0ZCJ0005FF2E.step` | `Fuse_Bel_0ZCJ_1206_3216Metric.step` |
| `614105150721 (rev1).stp` | `USB_Micro-B_Wuerth_614105150721_Vertical.step` |
| `AQY212GS.step` | `Panasonic_SOP-4_4.4x4.3mm_P2.54mm.step` |
| `Coilcraft_FA2672-AL.STEP` | `Coilcraft_FA2672.step` |
| `Coilcraft_FA2925-AL.step` | `Coilcraft_FA2925.step` |
| `DLW5B_5050.step` | `L_CommonModeChoke_Murata_DLW5B_5.0x5.0mm.step` |
| `FTSH-105-01-L-DV-007-K-TR.stp` | `Samtec_FTSH-105-01-L-DV-007-K.step` |
| `IHLP1212.step` | `L_Vishay_IHLP-1212.step` |
| `IHLP1616AB.step` | `L_Vishay_IHLP-1616AB.step` |
| `IHLP1616BZ.step` | `L_Vishay_IHLP-1616BZ.step` |
| `IHLP2020AB.step` | `L_Vishay_IHLP-2020AB.step` |
| `IHLP2020BZ.step` | `L_Vishay_IHLP-2020BZ.step` |
| `IHLP2020CZ.step` | `L_Vishay_IHLP-2020CZ.step` |
| `IHLP2525BD.step` | `L_Vishay_IHLP-2525BD.step` |
| `IHLP2525CZ.step` | `L_Vishay_IHLP-2525CZ.step` |
| `IHLP2525EZ.step` | `L_Vishay_IHLP-2525EZ.step` |
| `KW-5R5C104_224_334-R.STEP` | `Eaton_KW_13.5x8.8mm.step` |
| `NX1255GB.step` | `Crystal_SMD_NDK_NX1255GB-4Pin_12.5x5.5mm.step` |
| `NX2520SA.step` | `Crystal_SMD_NDK_NX2520SA-4Pin_2.5x2.0mm.step` |
| `NX3215SA.step` | `Crystal_SMD_NDK_NX3215SA-2Pin_3.2x1.5mm.step` |
| `NX3225SA.step` | `Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm.step` |
| `QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm.step` | `Skyworks_QFN-20-1EP_5x5mm_P0.8mm_EP2.7x2.7mm.step` |
| `T_Wurth_WE-PPTI-1308.step` | `Wurth_WE-PPTI-1308.step` |
| `T_Wurth_WE-RJ45LAN_7498210002.step` | `Wurth_WE-RJ45LAN_7498210002.step` |
| `T_Wurth_WE-RJ45LAN_7498210003.step` | `Wurth_WE-RJ45LAN_7498210003.step` |
| `T_Wurth_WE-RJ45LAN_7499411122A.step` | `Wurth_WE-RJ45LAN_7499411122A.step` |
| `T_Wurth_WE-RJ45LAN_7499511440.step` | `Wurth_WE-RJ45LAN_7499511440.step` |
| `Texas_YJE.step` | `Texas_YJE0006A_PicoStar-6_1.15x2.2mm.step` |
| `VO618A-3X017T.step` | `Vishay_SMD-4_W10.16mm_P2.54mm.step` |
| `Wurth_7499210123.step` | `Wurth_WE-RJ45LAN_7499210123.step` |

Machine-readable: `docs/rename-batch-2026-10.json` (symbol moves, database
nicknames, chooser names, footprints, models).
