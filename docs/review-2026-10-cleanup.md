# Repo cleanup review — 2026-10-12

Audit of `kicadlib` on branch `rework_2026` (at `82a09c4`). Nothing has been
changed yet; this file is the action list for follow-up fix sessions.

How the audit was done: every `(property "Footprint" ...)` in
`library/*.kicad_sym` and every footprint column in `library/*.db` was
cross-referenced against `footprints/Jonas.pretty` and
`modules/footprints.pretty`, and every `(model ...)` path in those footprints
was cross-referenced against the `.3dshapes`/`packages3d` folders.

**Working with this file:** tick the boxes (`- [x]`) as actions land, and
add a short note with the commit hash. Action IDs (`A1.3` etc.) are stable;
refer to them in commit messages. If you find something new during a fix
session, add it here instead of fixing it silently.

## Summary

- `modules/` is 237 MB, of which 233 MB is 3D models nothing references.
  It can't simply be deleted: ~85 symbols still resolve (or try to resolve)
  footprints that only exist there.
- `.git` is ~410 MB, mostly `modules/packages3d` history. Deleting files
  only shrinks it if history is rewritten (A6).
- The DB libraries are in decent shape; issues are naming inconsistencies and
  three libraries without a matching importer.
- Symbol-library footprint links are the worst problem: only ~110 of 234
  symbols point at a footprint that resolves correctly.

Suggested order: A1 → A2 + A3 → A4 → A5 → (optional) A6.

---

## A1. Safe deletions (nothing references these)

A1.1–A1.5 landed together in `c1fcbcf` ("Remove unreferenced files
(A1.1–A1.5)"). Everything removed is recoverable from history (e.g.
`git show ebab8c3:<path>`).

- [x] **A1.1** Delete unreferenced 3D models in `modules/packages3d/`:
      ~~427 of 461 files, ~233 MB~~. Done: **371 of 461 files, 176 MB**
      removed (old KiCad-stock package copies, displays, switches, unrelated
      vendor parts). 90 kept:
  - 62 referenced by a footprint in `modules/footprints.pretty` or
    `Jonas.pretty` (matched by file stem, so a `.step` next to a referenced
    `.wrl` stays). The original "34" undercounted: it missed paths
    containing spaces (`User Library-*`, `Download_STP_* (rev1).stp`).
  - 28 not referenced but useful to the footprint plan
    (`review-2026-10-footprints.md` M/N/D/S+sym rows, F4.5, F5.5): vendor
    STEPs `781715006`, `348260200`, `fakra_green_734035114`,
    `M-RJE72-188-1X01-REVT1`, `M-RJHSE-X38X-02-REVT1` (+ `.FCStd`),
    `TFM-110-02-S-D-WT`, `User Library-LFCSP_VQ88(CP-88-5)`,
    `User Library-torx-ph-iso7045`, `c-1-1825027-1-g1-3d`, `keystone_pn54`,
    `K3D-MM60-52B1-G1-V1_JAE_Proprietary.igs`, `MPCI`/`mpci_modem.fcstd`,
    `Maxim_WLP-12`, `DSBGA-12_3x4_1.36x1.86mm_Pitch0.5mm`, `R-PWSON-N12`,
    `SW_Tactile_SPST_Angled_PTS645Vx31-2LFS`; FreeCAD sources
    `217LFBGA`, `9YZF`, `YJE`, `lara_r2`,
    `LTE_antenna_molex_146200-001` (`.FCStd` + `.FCStd1`).
  - The rest of `modules/` goes in A2.6.
- [x] **A1.2** `git rm -r footprints/Jonas.pretty/tmp/` — 40 KiCad-4-era
      copies (`C_0402`, `CP_Elec_8x5.4`, `LFBGA289`, ...). Not a registered
      library. The stock matches that used `tmp/DHC16` and
      `tmp/DFN-10-1EP_3x3mm_Pitch0.5mm` as their geometry are already
      recorded in `review-2026-10-footprints.md`.
- [x] **A1.3** `git rm -r scripting/old_stuff/` — 24 files (old `.lib`
      importer, DRC script, pinout generators). Recoverable from history.
- [ ] **A1.4** `git rm library/LEDs.bak` (tracked despite `*.bak` in
      `.gitignore`) and delete the 13 other local `library/*.bak` files.
      `LEDs.bak` removed from git. The 12 other `.bak` files are untracked
      and ignored, and were left on disk for Jonas to delete
      (`rm library/*.bak`). Checked first: each is KiCad's "one save ago"
      copy and holds no symbol that the current library lacks.
      (`LEDs.bak`'s 20 Rohm SML-P1 LEDs are in `82a09c4`.)
- [x] **A1.5** Delete unreferenced models in `footprints/Jonas.3dshapes/`:
      the 14 `C_Panasonic_ECHU_*.wrl` files and `C_Murata_GA3_5.7x2.8.wrl`
      (footprints reference the `.step` versions, which are all present).
- [ ] **A1.8** (new) `scripting/gen_ndk_footprints.py` copies its NX2520SA
      model from `modules/packages3d/"User Library-Crystal NDK NX2520SA
      series.step"`, so A2.6 breaks it. Before A2.6, point `SRC_MODEL` at
      `footprints/Jonas.3dshapes/NX2520SA.step` (or drop the copy step).
      Also, both `gen_ndk_footprints.py` and `gen_ihlp_footprints.py`
      hard-code the Cowork path `~/mnt/kicadlib/`. Make them repo-relative.
- [ ] **A1.6** `data/cap_film_wima_pps.csv` has no importer/library.
      Delete, or keep if a WIMA library is planned (then note it here).
- [ ] **A1.7** Decide on `simulation/` (35 MB, 427 AccuP `.s2p` files) and
      `datasheets/` (27 MB PDFs). Neither is referenced by any importer or
      library. Options: keep as reference, or drop and rely on Datasheet
      URLs in the DBs. If kept, fix the `kyrocera` typo in
      `datasheets/cap/cap_rfmw_kyrocera_Accu-P.pdf`.

## A2. Retire `modules/footprints.pretty` (152 footprints)

About 75 of them are still in use. For each footprint, decide: **remap the
symbol to a stock KiCad footprint**, or **move it into `Jonas.pretty`**
(with its 3D model into `Jonas.3dshapes`, path rewritten to
`${JONAS_KICADLIB}/footprints/Jonas.3dshapes/...`). Draft the mapping as a
table for Jonas to approve before editing symbols.

Rough guide: stock KiCad covers `C0402`/`R0603`/`L_0805`-style passives,
`CP_Elec_*`, `SOT-23*`, `TSOT-23-*`, `SC-70`, generic `DFN-*`/`QFN-*`,
`D_SMB`, `TO-277A`, `PowerPAK*`, `TSSOP-8`, `TSOP-I-48`, `USB_Micro-B`,
`MH_2.5mm`; `NX*` and `IHLP*` are now covered by
`scripting/gen_ndk_footprints.py` / `gen_ihlp_footprints.py`. Genuinely
custom (move): connectors, antennas, module LGAs, CPU/memory BGAs.

Existing model paths in `modules/footprints.pretty` are mostly dead
absolute paths (`/Users/jons/...`, `C:/Users/jonas.persson/Desktop`,
`../../../../../Users/...`) or KiCad 4 `${KISYS3DMOD}` names — rewrite all
of them on migration.

- [ ] **A2.1** Symbols with **no library nickname** in the Footprint field
      (87). "In modules" = a footprint of that name exists in
      `modules/footprints.pretty`.

  | Library | Symbol | Footprint field | In modules |
  |---|---|---|---|
  | `Audio Amp` | `TAS2770` | `RJQ0026A` | yes |
  | `LEDs` | `SK6812RGBW` | `SK6812RGBW` | yes |
  | `adcdac` | `AFE7225` | `QFN-64-1EP_9x9mm_P0.5mm_EP4.7x4.7mm` | yes |
  | `comm` | `1575AT43A0040` | `1575AT43A0040` | **no** |
  | `comm` | `2450AT18B100` | `2450AT18B100` | yes |
  | `comm` | `ALM-GA001` | `uDFN6_EP` | yes |
  | `comm` | `ANT016008LCD1575MA1` | `ANT016008LCD1575MA1` | yes |
  | `comm` | `CC2520` | `QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm.kicad_mod` | **no** |
  | `comm` | `DPX162500DT-8014A1` | `DPX1625` | yes |
  | `comm` | `DS2482S-100+` | `SOIC-8_3.9x4.9mm_Pitch1.27mm` | **no** |
  | `comm` | `HHM22106C1` | `HHM22106C1` | yes |
  | `comm` | `LARA-R2` | `LARA_LGA` | **no** |
  | `comm` | `LTC2802` | `DFN-12-1EP_3x4mm_P0.5mm_EP1.7x3.3mm` | yes |
  | `comm` | `LTC2803IDHC#PBF` | `DFN-16-1EP_3x5mm_P0.5mm_EP1.66x4.4mm` | yes |
  | `comm` | `LTC2850` | `DFN-8-1EP_3x3mm_P0.5mm_EP1.66x2.38mm` | yes |
  | `comm` | `MAX-7` | `MAX7` | yes |
  | `comm` | `SF14-1575F5UUC1` | `SF14` | yes |
  | `comm` | `SKY13587-378LF` | `MLPD6` | yes |
  | `comm` | `TJA1042TK_3` | `DFN-8-1EP_3x3mm_P0.5mm_EP1.66x2.38mm` | yes |
  | `comm` | `WLA.01` | `WLA.01` | yes |
  | `comm` | `mPCIe_modem` | `mPCIe` | yes |
  | `connectors` | `0430450818` | `Molex_0430450818` | yes |
  | `connectors` | `0781710003` | `0781710003` | yes |
  | `connectors` | `0781715006` | `78171-5006` | yes |
  | `connectors` | `34826-8200` | `34826-8200` | yes |
  | `connectors` | `430450427` | `Molex_430450427` | yes |
  | `connectors` | `430450629` | `Molex_430450629` | yes |
  | `connectors` | `5-104074-8` | `5-104074-8` | yes |
  | `connectors` | `BatClip_54` | `KS54` | yes |
  | `connectors` | `DX4R005JJ2R1800` | `USB_Micro-B` | yes |
  | `connectors` | `M-RJHSE-5385-02` | `M-RJHSE-X38X-02` | yes |
  | `connectors` | `MHNP_2.5mm` | `MH_2.5mm` | yes |
  | `connectors` | `MX34R36HF4T` | `34826-8200` | yes |
  | `connectors` | `RPi_GPIO` | `40p_header_2.54` | **no** |
  | `connectors` | `TE_5103310-1` | `TE_5103310_1` | yes |
  | `connectors` | `TFM-105-02-S-D-WT` | `TFM-105-02-S-D-WT` | yes |
  | `connectors` | `USB_A_292303-1` | `USB_A_TH` | yes |
  | `connectors` | `fakra_blue_0734035112` | `fakra_th` | yes |
  | `connectors` | `fakra_bordeaux_0734035113` | `fakra_th` | yes |
  | `connectors` | `fakra_green_734035114` | `fakra_th` | yes |
  | `connectors` | `fakra_violet_0734035117` | `fakra_th` | yes |
  | `cpu` | `ADAU1467` | `CP-88-10` | yes |
  | `cpu` | `AT91SAM9G25` | `217LFBGA` | yes |
  | `cpu` | `MCIMX6G2AVM07AA` | `LFBGA289` | yes |
  | `cpu` | `MIMX8MM6DVTLZAA` | `BGA-486_27x27_P0.5mm_14.0x14.0mm` | yes |
  | `cpu` | `MIMX8MN5DVTJZAA` | `BGA-486_27x27_P0.5mm_14.0x14.0mm` | yes |
  | `cpu` | `STM32F302K8U6` | `QFN-32-1EP_5x5mm_Pitch0.5mm` | yes |
  | `cpu` | `STM32F446ZE` | `UFBGA144` | yes |
  | `cpu` | `STM32L486Zx` | `144LQFP` | **no** |
  | `dcdc` | `FAN48623` | `WLCSP16` | yes |
  | `dcdc` | `FAN48623UC50X` | `WLCSP16` | yes |
  | `dcdc` | `LM536355QRNLRQ1` | `VQFN_HR_22` | yes |
  | `dcdc` | `LMZ10501SILR` | `TI_LMX_SIL` | yes |
  | `dcdc` | `LT8640` | `Linear_UDCF` | **no** |
  | `dcdc` | `LTC3528` | `8DFN_EP` | yes |
  | `dcdc` | `LTC3612` | `QFN_20_0.5mm_3x4mm_EP` | **no** |
  | `dcdc` | `LTC4065-4.4` | `uDFN6_EP` | yes |
  | `dcdc` | `LTC4267IDHC` | `DHC16` | **no** |
  | `dcdc` | `MIC23150-55YMT` | `DFN-8_2x2mm_Pitch0.5mm` | yes |
  | `dcdc` | `MIC23150-SYMT` | `DFN-8_2x2mm_Pitch0.5mm` | yes |
  | `dcdc` | `MIC23254` | `MLF-10` | yes |
  | `dcdc` | `MIC28511` | `FQFN34-24` | yes |
  | `dcdc` | `TPS62742` | `R-PWSON-N12` | yes |
  | `dcdc` | `XCL226A0K1H2` | `Torex_XCL22_QFN` | yes |
  | `diode_misc` | `PESD0402-140` | `D0402` | **no** |
  | `diode_misc` | `PESD1CAN` | `SOT-23` | yes |
  | `interface` | `LAN8710` | `QFN-32-1EP_5x5mm_Pitch0.5mm` | yes |
  | `interface` | `PLR135_T10` | `PLR135_T10` | yes |
  | `interface` | `PLT133_T10W` | `PLT133_T10W` | yes |
  | `interface` | `TORX1355(V,F)` | `TOSLINK_VERTICAL` | yes |
  | `interface` | `TOTX1350(V,F)` | `TOSLINK_VERTICAL` | yes |
  | `logic` | `74AHC1G125SE-7` | `SOT-353_SC-70-5` | yes |
  | `logic` | `74LVCH1T45GW` | `SOT-363_SC-70-6` | yes |
  | `logic` | `SN74AHC1G00DCKR` | `SOT-353_SC-70-5` | yes |
  | `logic` | `SN74AUP1G74DCU` | `VSSOP-8_2.3x2mm_P0.5mm` | yes |
  | `logic` | `SN74AVC4T774` | `Texas_S-PVQFN-N16_EP2.7x2.7mm` | yes |
  | `logic` | `SN74LV1T126` | `SOT-353_SC-70-5` | yes |
  | `memory` | `IS46DR16640B` | `BGA-90-0.8mm` | yes |
  | `memory` | `IS62WV102416DBLL` | `TSOP-I-48_18.4x12mm_P0.5mm` | yes |
  | `memory` | `MT53B256M32D1NP` | `BGA-200_12x22_10.0x14.5mm` | yes |
  | `memory` | `MX25L12835F` | `DFN-8-1EP_6x5mm_P1.27mm_EP4x4mm` | yes |
  | `memory` | `MX30LF1G08AA` | `VFBGA63` | yes |
  | `memory` | `SIM-ST-MFF2` | `DFN-8-1EP_6x5mm_P1.27mm_EP4x4mm` | yes |
  | `misc_inductors` | `2450BM15B0002` | `2450BM15B0002` | yes |
  | `misc_inductors` | `IHLP1212_1u2_4b` | `IHLP1212` | yes |
  | `misc_inductors` | `LQH2MCN100K02L` | `L0806` | **no** |
  | `power` | `bq27742-G1` | `DSBGA15` | yes |

  Accurate as of `82a09c4`; re-run the audit (see end of file) before
  fixing in case symbols changed since.

- [ ] **A2.2** Symbols using the `footprints:` nickname
      (= `modules/footprints.pretty`):
  - `comm/USB2512B` → `footprints:QFN-36-1EP_6x6mm_Pitch0.5mm`
  - `connectors/Header_2.54mm_10p` → `footprints:61201021621`
  - `cpu/AT91SAMA5D27` → `footprints:LFBGA289`
  - `cpu/ATSAMD21E15B` → `footprints:QFN-32-1EP_5x5mm_Pitch0.5mm`
  - `dcdc/LTC3113IDHD` → `footprints:DFN-16-1EP_4x5mm_P0.5mm_EP2.44x4.34mm`
  - `diode_misc/DS9503P+` → `footprints:TSOC6`
  - `memory/25AA1024` → `footprints:DFN-8-1EP_6x5mm_P1.27mm_EP4x4mm`
  - `power/1206SFS200F_63-2` → `footprints:Fuse_1206_3216Metric`
- [ ] **A2.3** Symbols pointing at `Jonas:X` where X only exists in
      `modules` (or nowhere):
  - `LEDs/LTST-C19HE1WT` → `Jonas:liteon_rgb_0603`
  - `comm/146200` → `Jonas:molex_lte_ant_146200`
  - `connectors/1051330011` → `Jonas:1051330011` (only in `Jonas.pretty/tmp`, see A1.2)
  - `connectors/FTSH-105-01-F-DV-K` → `Jonas:FTSH-105-01-F-DV-K`
  - `connectors/RJE72-188-1401` → `Jonas:RJE72-188-1401`
  - `connectors/TFM-110-02-S-D-WT` → `Jonas:TFM-110-02-S-D-WT`
  - `dcdc/FAN53541` → `Jonas:WLCSP20`
  - `dcdc/FAN5355UC00` → `Jonas:WLCSP12`
  - `misc_inductors/PT61018PEL` → `Jonas:Ethernet_trafo_so16w`
  - `power/1-1825027-1` → `Jonas:1-1825027-1`
  - `power/LP5562` → `Jonas:DSBGA12`
- [ ] **A2.4** Move the ~34 3D models still referenced from
      `modules/packages3d` into `Jonas.3dshapes` for footprints that move.
- [ ] **A2.5** Re-run the audit: zero symbols may reference `footprints:`,
      a bare name, or a missing `Jonas:` footprint.
- [ ] **A2.6** `git rm -r modules/` (after A1.8).

## A3. Other broken footprint/model links

- [ ] **A3.1** KiCad 4 library nicknames that no longer exist; remap:
  - `comm/SN65C3232EPWR` → `Housings_SSOP:SSOP-16_4.4x5.2mm_Pitch0.65mm` → `Package_SO:`
  - `dcdc/LTC3447` → `Housings_DFN_QFN:DFN-10-1EP_3x3mm_Pitch0.5mm` → `Package_DFN_QFN:`
  - `interface/TCA9535RGER` → `Housings_DFN_QFN:QFN-24-1EP_4x4mm_Pitch0.5mm` → `Package_DFN_QFN:`
  - `logic/SN74AHC1G08` → `TO_SOT_Packages_SMD:SOT-23-5` → `Package_TO_SOT_SMD:`
  - `logic/SN74AUP1G97DCKR` → `TO_SOT_Packages_SMD:SC-70-6` → `Package_TO_SOT_SMD:`
  - `logic/SN74AUP2G04DCKR` → `TO_SOT_Packages_SMD:SC-70-6` → `Package_TO_SOT_SMD:`
- [ ] **A3.2** `connectors/Wurth_7499210123` uses `jonas:` (lowercase);
      nicknames are case-sensitive → `Jonas:`.
- [ ] **A3.3** Empty Footprint field — check these (power flags like
      `GND`, `PWR_FLAG`, `PxVx`, `NxVx`, `BOM_Entry` are fine):
      `comm/WYSBCVGXA`, `connectors/0428202222`, `connectors/Conn_01x30`,
      `connectors/DuraClick_560020`, `connectors/GBC08SGSN-M89`,
      `connectors/SF7W008S1AE900`, `cpu/Zynq_7010`, `dcdc/TLV62084DSG`,
      `diode_misc/D_TVS_Uni`, `logic/NLSV4T3144-D`, `power/PT65503`.
- [ ] **A3.4** Unused footprints in `Jonas.pretty`: `NX5032GA`,
      `T_Wurth_WE-RJ45LAN_7499210001A`, `Wurth_7499210123` (the last is
      explained by A3.2). Wire them to a symbol or delete.
- [ ] **A3.5** Footprints referencing missing models:
      `T_Wurth_WE-RJ45LAN_7499210001A.step`,
      `tssop-38_4.4x9.7mm_p0.5mm.step`.
- [ ] **A3.6** Untracked `footprints/Jonas.3dshapes/614105150721 (rev1).stp`:
      rename without spaces/parens and reference it from its footprint.
- [ ] **A3.7** Two footprints use `${WE_3DMODEL_DIR}` (external Würth model
      library). Copy the models into `Jonas.3dshapes` so the repo is
      self-contained.

## A4. Database libraries

- [ ] **A4.1** Libraries without a reproducing importer (breaks the
      "importer is the source of truth" rule in `CLAUDE.md`):
  - `cap_mlcc_murata_GRM`: generated by the generic, argparse-driven
    `scripting/import_murata_cap.py`; the arguments used aren't recorded.
    Create `import_cap_mlcc_murata_grm.py` with them baked in.
  - `cap_rfmw_murata_gqm`: no importer at all; source CSV is named
    `data/cap_mlcc_murata_gqm.csv` (mlcc vs rfmw mismatch).
  - `cap_rfmw_kyocera_accu_p`: importer is `import_cap_rfmw_kyocera_accup.py`,
    `simulation/` uses `accup`. Pick `accup` and rename the library.
- [ ] **A4.2** Naming fixes:
  - `cap_mlcc_murata_GRM` → `cap_mlcc_murata_grm` (lowercase).
  - `diode_tvs_littlefuse` → `diode_tvs_littelfuse` (vendor spelling).
  - `data/ind_choke_murata_LQW_*.csv`, `data/ind_rfmw_murata_LQW_*.csv` →
    lowercase `lqw`.
  - `import_ind_rfmw_murata_lqg.py` still mentions the old
    `ind_rf_murata_lqg15hn.kicad_dbl`.
- [ ] **A4.3** LQW is split across `ind_choke_murata_lqw` and
      `ind_rfmw_murata_lqw`, both showing as "LQW" in the chooser. Merge
      them, or give distinct chooser names (e.g. `LQW (choke)`).
- [ ] **A4.4** Make chooser names (`libraries[].name`) consistently the
      series name. Currently `AlEl`, `TVS`, `Epson`, `NDK` are type/vendor
      names while the rest are series names.
- [ ] **A4.5** Re-run every importer and confirm `.db`/`.kicad_dbl` come out
      byte-identical (or explain the diff).

Renames of `.kicad_dbl` files change the library nickname in
`sym-lib-table`; do them in one batch with A5.

## A5. Symbol library naming and docs

Proposed renames (aligned with the DB type codes):

| Now | Proposed | Why |
|---|---|---|
| `misc_capacitors` / `misc_inductors` / `misc_resistors` | `cap_misc` / `ind_misc` / `res_misc` | Sort next to DB siblings; already proposed in `NAMING.md` §6 |
| `diode_misc` | keep | Already follows the pattern |
| `LEDs` | `led` | Lowercase, singular |
| `transistors`, `connectors` | `transistor`, `conn` | Singular, consistent |
| `Audio Amp` (1 symbol), `adcdac` (1), `sensors` (2) | merge into `analog` (keep `sensor` if it grows) | Space in name is a hazard; 1–2-symbol libs aren't worth an entry |
| `cpu` | `mcu` (or keep) | Mostly MCUs/SoCs |
| `dcdc`, `power` | keep `dcdc`; split `power` → `pwr` (GND/PWR_FLAG/PxVx flags) + `protection` (fuses, eFuses, ideal diodes) | `power` is a grab bag |
| `comm`, `interface`, `logic`, `memory` | keep | |

Crystals: `xtal_epson`/`xtal_ndk` skip the subtype. Acceptable; if
oscillators get added, use `xtal_smd_*` / `osc_tcxo_*`.

Caveat: schematics embed symbol copies, so they still open after a rename,
but "Update from library" breaks until each project's `sym-lib-table` is
remapped. Do all renames in one batch.

- [ ] **A5.1** Rename symbol libraries per the table (decide on `cpu`/`mcu`
      and the `power` split first).
- [ ] **A5.2** Update `NAMING.md`. It's stale: it still talks about `.lib`
      files, `cap_mlcc_murata` and `footprints.pretty`, and disagrees with
      current practice:
  - inductor type code `rf` → `rfmw` (matches caps and existing libraries);
  - add codes in use but undefined: `choke`, `pulse`, `tvs`, `pptc`, `xtal`;
  - make **one `.kicad_dbl` per series** (one importer each) the official
    rule, replacing the "one per vendor+type, multiple `libraries[]`" advice.
  - Consider moving it to `docs/naming.md`.
- [ ] **A5.3** Update `CLAUDE.md`: it describes `footprints/<Vendor_Series>.pretty`
      but the repo uses a single `Jonas.pretty`. Recommendation: keep one
      library (fewer `fp-lib-table` entries) and fix the doc. Also unify
      footprint names inside it (`T_Wurth_*` vs `Wurth_*`, bare part
      numbers, IPC names like `SOIC254P680X230-4N`) on a `Vendor_Part`
      scheme.

## A6. (Optional) Shrink history

- [ ] **A6.1** After A1/A2, rewrite history with `git filter-repo` to drop
      `modules/packages3d` (and other deleted bulk), bringing `.git` from
      ~410 MB to tens of MB. This rewrites `master` too and needs a
      force-push; only worth it if nobody else has clones. Requires explicit
      go-ahead from Jonas.

---

## Re-running the audit

The audit was an ad-hoc Python script (not committed). It:
1. collects every `(property "Footprint" "...")` per top-level symbol in
   `library/*.kicad_sym`, and every distinct value in DB columns whose
   name contains `ootprint`;
2. classifies each reference: empty / no `:` nickname / known stock KiCad
   nickname / `Jonas:` found or missing / anything else;
3. collects every `(model ...)` path in `footprints/Jonas.pretty` and
   `modules/footprints.pretty` and compares basenames against the files in
   `Jonas.3dshapes` and `modules/packages3d`.

If this gets re-run often, commit it as `scripting/audit_refs.py`.
