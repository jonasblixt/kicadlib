# Footprint & 3D-model migration plan — 2026-10-13

**Status: DRAFT for discussion. Nothing in the library has been changed.**

Audit of branch `rework_2026` **working tree** (including the uncommitted
symbol edits), done locally on archimedes against the real KiCad 10.0.6
stock libraries. It expands A2/A3 of `review-2026-10-cleanup.md` into a
per-symbol mapping and adds a consistency review of `Jonas.pretty` and
`Jonas.3dshapes`. Action IDs here are `F*`; corrections to the older doc
are at the end.

**Working with this file:** same rules as the cleanup review — tick boxes
as actions land, note the commit hash, add new findings here instead of
fixing them silently.

## How this was produced

- Every `Footprint` field in `library/*.kicad_sym` and every footprint
  column in `library/*.db` was resolved against the lib tables KiCad
  actually has (global `fp-lib-table` = stock table + `Jonas` only, so
  `footprints:` and bare names resolve to nothing today).
- Every old footprint a symbol still needs was compared pad-by-pad
  against all 15,450 stock footprints (rotation-invariant; pad position,
  size and numbering), then cross-checked against the part's MPN and the
  vendor package code (LTC DD/DDB/DC6/UDC, NXP SOT782, Microchip MF, TI
  RGE/RGY/DSG/DSS, ...).
- Symbol pin numbers were checked against footprint pad numbers for every
  symbol and every DB symbol/footprint pair.
- Footprints were checked KLC-style (courtyard, fab, silk, fields, attr,
  3D model); STEP files were checked for B-Rep vs CSG.
- `kicad-cli pcb render` works headless here, so footprint + 3D model
  alignment can be checked visually from a session (first render of
  `C_Murata_GA3_5.7x2.8`, `IHLP2020BZ`, `NX3225SA` today: all load and sit
  on their pads).

## Summary

| | |
|---|---|
| Symbols | 234 (231 non-power) |
| Footprint link resolves today | 105 |
| Broken link | 113 — 87 bare name, 11 `Jonas:` name that doesn't exist, 8 `footprints:`, 6 KiCad-4 nicknames, 1 lowercase `jonas:` |
| Empty Footprint field | 13 non-power (4 intentional: generic symbols and flags) |
| DB libraries | every symbol/footprint pair is pin-compatible; 68 crystal rows have no footprint (documented in the importers) |

Proposed outcome for the symbols that need a footprint:

| Outcome | Symbols | Distinct footprints |
|---|---|---|
| Stock KiCad footprint (classes S, S\*, FIX, S+sym) | 71 | 63 |
| Your call (D) | 3 | 3 |
| Already in `Jonas.pretty`, only the link is wrong (J) | 2 | 2 |
| Migrate old footprint into `Jonas.pretty` (M) | 37 | 31 |
| New footprint from datasheet (N) | 9 | 9 |

So of the 152 footprints in `modules/footprints.pretty` (+40 in
`Jonas.pretty/tmp/`, since removed by A1.2), **31 move** into
`Jonas.pretty`; the rest are either replaced by stock or unused.

## F1. Bugs that exist today (independent of the migration)

These are wrong in the current library and affect any board made from it.
Smallest, highest-value batch — do first. Batch 1 (2026-10-13) landed one
commit per action; the hash is on each ticked line.

- [x] **F1.1** `logic/SN74AHC1G00DCKR`: the GND pin is numbered **2**,
      same as input B. GND gets netlisted onto B and pad 3 floats.
      → renumber GND to 3. — `4912daf`
- [x] **F1.2** `comm/mPCIe_modem`: `PERST#` is pin **21**, which is also a
      GND pin (mini-PCIe has PERST# on 22). → renumber to 22. — `98e3305`
- [x] **F1.3** `comm/TJA1042TK_3`: footprint is a 0.5 mm-pitch DFN-8; the
      HVSON8 package (SOT782-1) is 0.65 mm pitch. → stock
      `Package_SON:HVSON-8-1EP_3x3mm_P0.65mm_EP1.6x2.4mm` (made from the
      TJA1051 datasheet, same package). — `c8e2330`
- [x] **F1.4** `dcdc/LTC4065-4.4`: `uDFN6_EP` is a 0.4 mm-pitch ~1.5 mm
      package; LTC4065EDC is LTC's DC6 (2×2 mm, 0.5 mm). → stock
      `Package_DFN_QFN:DFN-6-1EP_2x2mm_P0.5mm_EP0.61x1.42mm` (KiCad's DC6).
      — `340f9ee`
- [x] **F1.5** `logic/SN74AHC1G08`: MPN is `…DCK` (SC-70-5), footprint is
      SOT-23-5 (and `ki_fp_filters` already says SC70). → `SOT-353_SC-70-5`.
      — `ff5e918`
- [x] **F1.6** `logic/SN74AVC4T774`: three different packages — MPN
      `…RGYR` (VQFN 3.5×4, 0.5 mm), `ki_fp_filters` `RSV`, footprint RSA
      (4×4, 0.65 mm). Jonas: the part is RGYR. The symbol was numbered for
      **RSV** (A1 = 1 … DIR2 = 16); per TI SCES693I Table 4-1, RGY = PW
      numbering (DIR1 = 1, DIR2 = 2, A1 = 3 … VCCA = 16), so every pin moved
      by +2. Footprint `Texas_RGY_R-PVQFN-N16_EP2.05x2.55mm`, filter
      `Texas*RGY*PVQFN*`. TI only requires the thermal pad to be soldered,
      so pad 17 gets no pin. — `94fe08f`
- [ ] **F1.7** `connectors/MX34R36HF4T`: 36-pin symbol borrows the 20-pad
      `34826-8200` footprint (pins 21–36 have no pads). → new footprint.
- [x] **F1.8** `connectors/Header_2.54mm_10p` (Würth 61201021621): old
      footprint numbers pads DIP-style (1–5 down one row, 6–10 back up the
      other). Würth and the symbol use odd/even, so the pinout is scrambled
      against an IDC cable. → `Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical`
      (pad positions identical). — `4b20c3a`
- [x] **F1.9** `connectors/430450427`: old `Molex_430450427` numbering is
      rotated 180° relative to the latch pegs; the sibling
      `Molex_430450629` and KiCad stock agree with each other. → stock
      `Molex_Micro-Fit_3.0_43045-0412_2x02_P3.00mm_Vertical` (positions
      within 0.09 mm). Worth checking any board that used this connector.
      — `80f3675`
- [x] **F1.10** `dcdc/MIC23150-55YMT`, `MIC23150-SYMT`: ~~old footprint
      is stock `Micrel_MLF-8-1EP…` minus the ePad~~. **Corrected:** the
      MIC23150 TDFN-8 (MM) has **no** exposed pad (Micrel datasheet rev
      2.1: pin table p. 2, land pattern p. 17). The old footprint was an
      exact twin of stock `Package_DFN_QFN:DFN-8_2x2mm_P0.5mm` (no EP), so
      this was only a broken link. → that footprint, no symbol change.
      — `4408e37`
- [x] **F1.11** Exposed pads with no symbol pin (pad gets no net). Checked
      each datasheet; a pin is added only where the pad must be connected.
      — `2d6eb5a`
  - `power/MAX16058ATA31+` (9): "Connect exposed pad to GND" → pin 9
    added, hidden passive, stacked on GND (pin 2).
  - `power/LTC2941IDCB#TRMPBF` (7): "Exposed Pad (Pin 7): Do not connect"
    → no change; the symbol was already right.
  - `memory/MX25L12835F` (9): Macronix: "leave the metal pad floating or
    connect it to the same ground as the GND pin … Do not connect the
    metal pad to any other voltage or signal line" → no change (floating
    allowed). But see F1.16.
  - `memory/25AA1024` (9): DS20001836J says nothing about the pad's
    connection → no change. Its EP is 4.0×2.3 mm (not the 4×4 of the old
    footprint); check against the S\* target `DFN-S-8-1EP_6x5mm_P1.27mm`
    in F7.2.
  - `memory/SIM-ST-MFF2` (9): Hologram's MFF2 pinout lists 8 pins and no
    pad → no change.
  - `logic/SN74AVC4T774` (17): with F1.6.
- [x] **F1.12** `connectors/TFM-110-02-S-D-WT`: symbol pins 21/22 have no
      pads (old footprint numbers its weld tabs `0`). → fix during migration. — holes renumbered 21/22, `8b59022`
- [ ] **F1.13** `power/PT65503`: pin 2 is defined twice, named `2` and `C`.
- [ ] **F1.14** `cpu/MIMX8MM6DVTLZAA`, `MIMX8MN5DVTJZAA`: old BGA-486
      footprint has 487 distinct pad numbers. → check against the NXP ball
      map during migration.
- [ ] **F1.15** `memory/IS46DR16640B`: fp filter says `BGA84`, footprint is
      a 90-site BGA, so pads sit at depopulated sites. → check the ball map.
- [x] **F1.16** (new, found in batch 1) `memory/MX25L12835F`: MPN
      `MX25L12835FZ2I-10G` is the **8-WSON 8×6 mm** package (Macronix
      ordering code `Z2`; `ZN` is 6×5 mm), but the footprint was 6×5 mm.
      Jonas confirmed Z2I. → `Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm`
      (pad rows at ±3.75 mm match the outline; the 3.4×4.3 EP land is
      inside the package's 4.7×4.6 pad). — `8cb4f26`
- [ ] **F1.17** (new) `connectors/Wurth_7499210123`: footprint pads 7 and
      8 (through-hole) have no symbol pin. Check the Würth datasheet
      whether they are NC; add NC pins or wire them.

## F2. Migration method

### Decision rule per symbol

1. **Stock twin** — a stock footprint with identical pads (≤0.1 mm): remap.
   The board comes out the same as today.
2. **Stock for the real package** — chosen from MPN / package code; land
   pattern checked against the datasheet; remap.
3. **Stock + symbol tweak** — positions identical, but stock names
   mounting/shield pads `MP`/`SH`: renumber those symbol pins.
4. **Migrate** — no stock equivalent and a usable old footprint exists:
   rebuild it into `Jonas.pretty` to the standard below.
5. **New** — nothing usable: draw from the datasheet.

After every remap the pin↔pad check must pass: every symbol pin has a pad,
and pads without a pin are only datasheet NC/mechanical pads.

### Standard for `Jonas.pretty` (migrated and existing footprints)

- Name `<Vendor>_<part or package>[_<dims>]` (KLC style); file name =
  footprint name = Value.
- KiCad 10 format (`kicad-cli fp upgrade`, then edit).
- `F.CrtYd` closed, 0.05 mm lines, clearance 0.25 mm around pads + body
  (KLC's larger/smaller exceptions for connectors, BGAs and tiny passives).
- `F.Fab` body outline + `${REFERENCE}`; `F.SilkS` outline (0.12 mm) with a
  pin-1 mark and not over pads; Reference on `F.SilkS`, Value on `F.Fab`.
- `descr` (what it is, datasheet URL, where the land pattern came from),
  `tags`, `Datasheet` property.
- `attr` matches the pads (`smd` / `through_hole`).
- Pad numbers follow the vendor; EP = N+1; mounting/shield pads `MP`/`SH`;
  NPTH unnumbered.
- 3D model `${JONAS_KICADLIB}/footprints/Jonas.3dshapes/<footprint>.step`,
  B-Rep only, scale 1, offset in mm.

### Per-footprint process (M)

`kicad-cli fp upgrade` → rename → add courtyard/fab/fields/attr → fix pad
numbering → copy/rename/realign 3D model → automated checks → render top +
iso PNG with `kicad-cli pcb render` → you review a contact sheet per batch.

Proposed tooling to commit (the audit scripts used for this doc):
`scripting/audit_refs.py` (link + pin↔pad audit; A2.5 asked for it),
`scripting/audit_footprints.py` (section F4 checks),
`scripting/render_footprints.py` (render contact sheets).

## F3. Proposed mapping

Every symbol with a broken or empty Footprint field (power flags left
out). "Twin" = pads identical within 0.1 mm.

#### FIX - Current footprint is wrong for the part - stock fixes it (7) — done, see F1

| Symbol | MPN | Now | Proposed | Note |
|---|---|---|---|---|
| `comm/TJA1042TK_3` | TJA1042TK/3,118 | `DFN-8-1EP_3x3mm_P0.5mm_EP1.66x2.38mm` | `Package_SON:HVSON-8-1EP_3x3mm_P0.65mm_EP1.6x2.4mm` | current DFN-8 is 0.5 mm pitch; HVSON8 (SOT782-1) is 0.65 mm |
| `connectors/430450427` | 430450427 | `Molex_430450427` | `Connector_Molex:Molex_Micro-Fit_3.0_43045-0412_2x02_P3.00mm_Vertical` | old numbering rotated 180 deg vs pegs |
| `connectors/Header_2.54mm_10p` | 61201021621 | `footprints:61201021621` | `Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical` | old pads numbered DIP-style |
| `dcdc/LTC4065-4.4` | LTC4065EDC-4.4#TRMPBF | `uDFN6_EP` | `Package_DFN_QFN:DFN-6-1EP_2x2mm_P0.5mm_EP0.61x1.42mm` | LTC DC6; current is 0.4 mm pitch |
| `dcdc/MIC23150-55YMT` | MIC23150-55YMT | `DFN-8_2x2mm_Pitch0.5mm` | `Package_DFN_QFN:DFN-8_2x2mm_P0.5mm` | twin; part has no ePad (F1.10, corrected) |
| `dcdc/MIC23150-SYMT` | MIC23150-SYMT | `DFN-8_2x2mm_Pitch0.5mm` | `Package_DFN_QFN:DFN-8_2x2mm_P0.5mm` | twin; part has no ePad (F1.10, corrected) |
| `logic/SN74AHC1G08` | SN74AHC1G08DCK | `TO_SOT_Packages_SMD:SOT-23-5` | `Package_TO_SOT_SMD:SOT-353_SC-70-5` | DCK part on SOT-23-5 |

#### S - Stock twin - pads identical to the old footprint within 0.1 mm (no change vs. today) (29) — done, see F7.2

| Symbol | MPN | Now | Proposed | Note |
|---|---|---|---|---|
| `adcdac/AFE7225` | AFE7225IRGCT | `QFN-64-1EP_9x9mm_P0.5mm_EP4.7x4.7mm` | `Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP4.7x4.7mm` | twin; EP vs TI RGC drawing worth a glance |
| `comm/CC2520` | CC2520RHDR | `QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm.kicad_mod` | `Package_DFN_QFN:QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm` | twin; field has stray .kicad_mod |
| `comm/LTC2802` | LTC2802IDE#TRPBF | `DFN-12-1EP_3x4mm_P0.5mm_EP1.7x3.3mm` | `Package_DFN_QFN:DFN-12-1EP_3x4mm_P0.5mm_EP1.7x3.3mm` | twin (LTC DE12) |
| `comm/LTC2803IDHC#PBF` | LTC2803IDHC#PBF | `DFN-16-1EP_3x5mm_P0.5mm_EP1.66x4.4mm` | `Package_DFN_QFN:DFN-16-1EP_3x5mm_P0.5mm_EP1.66x4.4mm` | twin (LTC DHC) |
| `comm/LTC2850` | LTC2850IDD#PBF | `DFN-8-1EP_3x3mm_P0.5mm_EP1.66x2.38mm` | `Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.5mm_EP1.66x2.38mm` | twin (LTC DD8) |
| `comm/MAX-7` | MAX-7W-0-000 | `MAX7` | `RF_GPS:ublox_MAX` | twin |
| `comm/SF14-1575F5UUC1` | SF14-1575F5UUC1 | `SF14` | `Filter:Filter_1411-5_1.4x1.1mm` | twin |
| `connectors/0781710003` | 0781710003 | `0781710003` | `Connector_Molex:Molex_Pico-EZmate_78171-0003_1x03-1MP_P1.20mm_Vertical` | twin |
| `connectors/430450629` | 430450629 | `Molex_430450629` | `Connector_Molex:Molex_Micro-Fit_3.0_43045-0612_2x03_P3.00mm_Vertical` | twin |
| `connectors/FTSH-105-01-F-DV-K` | FTSH-105-01-F-DV-K.stp | `Jonas:FTSH-105-01-F-DV-K` | `Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD` | twin; MPN field has .stp |
| `connectors/MHNP_2.5mm` | N/A | `MH_2.5mm` | `MountingHole:MountingHole_2.5mm` | twin |
| `connectors/TE_5103310-1` | 5103310-1 | `TE_5103310_1` | `Connector_IDC:IDC-Header_2x05_P2.54mm_Vertical` | twin positions + numbering |
| `cpu/AT91SAMA5D27` | ATSAMA5D27C | `footprints:LFBGA289` | `Package_BGA:LFBGA-289_14x14mm_Layout17x17_P0.8mm` | twin |
| `cpu/MCIMX6G2AVM07AA` | MCIMX6G2AVM07AA | `LFBGA289` | `Package_BGA:MAPBGA-289_14x14mm_Layout17x17_P0.8mm` | twin |
| `cpu/STM32F446ZE` | STM32F446ZE | `UFBGA144` | `Package_BGA:UFBGA-144_10x10mm_Layout12x12_P0.8mm` | twin; MPN lacks suffix |
| `dcdc/FAN53541` | FAN53541 | `Jonas:WLCSP20` | `Package_CSP:WLCSP-20_1.934x2.434mm_Layout4x5_P0.4mm` | twin |
| `dcdc/FAN5355UC00` | FAN5355UC00 | `Jonas:WLCSP12` | `Package_BGA:Texas_DSBGA-12_1.36x1.86mm_Layout3x4_P0.5mm` | twin (TI-named) |
| `dcdc/LTC3113IDHD` | LTC3113IDHD#PBF | `footprints:DFN-16-1EP_4x5mm_P0.5mm_EP2.44x4.34mm` | `Package_DFN_QFN:DFN-16-1EP_4x5mm_P0.5mm_EP2.44x4.34mm` | twin (LTC DHD) |
| `dcdc/LTC3528` | LTC3528BEDDB#TRMPBF | `8DFN_EP` | `Package_DFN_QFN:DFN-8-1EP_2x3mm_P0.5mm_EP0.61x2.2mm` | twin + 2 vias |
| `dcdc/LTC4267IDHC` | LTC4267IDHC | `DHC16` | `Package_DFN_QFN:DFN-16-1EP_3x5mm_P0.5mm_EP1.66x4.4mm` | twin (LTC DHC) |
| `diode_misc/DS9503P+` | DS9503P+ | `footprints:TSOC6` | `Package_SO_J-Lead:TSOC-6_3.76x3.94mm_P1.27mm` | twin |
| `LEDs/LTST-C19HE1WT` | LTST-C19HE1WT | `Jonas:liteon_rgb_0603` | `LED_SMD:LED_LiteOn_LTST-C19HE1WT` | same part |
| `memory/IS46DR16640B` | IS46DR16640B-25EBLA1 | `BGA-90-0.8mm` | `Package_BGA:BGA-90_8.0x13.0mm_Layout2x3x15_P0.8mm` | twin, but part is 84-ball |
| `memory/MT53B256M32D1NP` | MT53B256M32D1NP-062 AIT:C | `BGA-200_12x22_10.0x14.5mm` | `Package_BGA:BGA-200_10x14.5mm_Layout12x22_P0.8x0.65mm` | twin |
| `memory/MX30LF1G08AA` | MX30LF1G08AA-XKI | `VFBGA63` | `Package_BGA:BGA-63_9x11mm_Layout10x12_P0.8mm` | twin |
| `memory/SIM-ST-MFF2` | SIM-ST-MFF2 | `DFN-8-1EP_6x5mm_P1.27mm_EP4x4mm` | `Package_DFN_QFN:DFN-8-1EP_6x5mm_P1.27mm_EP4x4mm` | twin |
| `misc_inductors/2450BM15B0002` | 2450BM15B0002 | `2450BM15B0002` | `RF_Converter:Balun_Johanson_0896BM15A0001` | twin geometry, sibling part name |
| `power/1206SFS200F_63-2` | 1206SFS200F/63-2 | `footprints:Fuse_1206_3216Metric` | `Fuse:Fuse_1206_3216Metric` | twin |
| `power/LP5562` | LP5562 | `Jonas:DSBGA12` | `Package_BGA:Maxim_WLP-12_2.008x1.608mm_Layout4x3_P0.4mm` | twin geometry, Maxim-named |

#### S* - Stock, chosen from the MPN/package - differs from the old one or old one missing (datasheet check during execution) (31) — done, see F7.2 (two targets changed, one moved to M)

| Symbol | MPN | Now | Proposed | Note |
|---|---|---|---|---|
| `comm/2450AT18B100` | 2450AT18B100 | `2450AT18B100` | `RF_Antenna:Johanson_2450AT18x100` | stock pads 1.2x1.8 @ +-1.45 vs old 0.8x1.6 @ +-1.7 |
| `comm/DS2482S-100+` | DS2482S-100+ | `SOIC-8_3.9x4.9mm_Pitch1.27mm` | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | KiCad-4 name; fp filter says WLP |
| `comm/SN65C3232EPWR` | SN65C3232EPWR | `Housings_SSOP:SSOP-16_4.4x5.2mm_Pitch0.65mm` | `Package_SO:TSSOP-16_4.4x5mm_P0.65mm` | PW = TSSOP-16 |
| `comm/USB2512B` | USB2512Bi-AEZG | `footprints:QFN-36-1EP_6x6mm_Pitch0.5mm` | `Package_DFN_QFN:QFN-36-1EP_6x6mm_P0.5mm_EP3.7x3.7mm` | EP size per SQFN-36 drawing (3.7 vs 4.1) |
| `connectors/0428202222` | 0428202222 | `(empty)` | `Connector_Molex:Molex_Mini-Fit_Sr_42820-22XX_1x02_P10.00mm_Horizontal` | field empty |
| `connectors/GBC08SGSN-M89` | GBC08SGSN-M89 | `(empty)` | `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` | field empty; confirm 1x08 |
| `cpu/ATSAMD21E15B` | ATSAMD21E15B-MUT | `footprints:QFN-32-1EP_5x5mm_Pitch0.5mm` | `Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm` | leads twin; EP per datasheet |
| `cpu/STM32F302K8U6` | STM32F302K8U6 | `QFN-32-1EP_5x5mm_Pitch0.5mm` | `Package_DFN_QFN:UFQFPN-32-1EP_5x5mm_P0.5mm_EP3.5x3.5mm` | leads twin; ST EP |
| `cpu/STM32L486Zx` | STM32L486ZGT6 | `144LQFP` | `Package_QFP:LQFP-144_20x20mm_P0.5mm` | ZGT6 = LQFP144 |
| `cpu/Zynq_7010` | Zynq 7010 | `(empty)` | `Package_BGA:Xilinx_CLG225` | field empty; filter clg225 |
| `dcdc/LTC3447` | LTC3447 | `Housings_DFN_QFN:DFN-10-1EP_3x3mm_Pitch0.5mm` | `Package_DFN_QFN:DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm` | LTC DD10 EP |
| `dcdc/LTC3612` | LTC3612EUDC#PBF | `QFN_20_0.5mm_3x4mm_EP` | `Package_DFN_QFN:QFN-20-1EP_3x4mm_P0.5mm_EP1.65x2.65mm` | LTC UDC20 |
| `dcdc/TLV62084DSG` | TLV62084DSG | `(empty)` | `Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm` | field empty |
| `dcdc/TPS62742` | TPS62742DSSR | `R-PWSON-N12` | `Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65` | TI DSS; old had EP tabs + vias |
| `diode_misc/PESD0402-140` | PESD0402-140 | `D0402` | `Diode_SMD:D_0402_1005Metric` | old D0402 missing |
| `diode_misc/PESD1CAN` | PESD1CAN | `SOT-23` | `Package_TO_SOT_SMD:SOT-23` | KiCad-4 land pattern |
| `interface/LAN8710` | LAN8710AI-EZK-ABC | `QFN-32-1EP_5x5mm_Pitch0.5mm` | `Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.3x3.3mm` | leads twin; EP per datasheet |
| `interface/TCA9535RGER` | TCA9535RGER | `Housings_DFN_QFN:QFN-24-1EP_4x4mm_Pitch0.5mm` | `Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm` | RGE0024C vs H |
| `LEDs/SK6812RGBW` | SK6812RGBW | `SK6812RGBW` | `LED_SMD:LED_SK6812_PLCC4_5.0x5.0mm_P3.2mm` | old pads 0.25 mm off |
| `logic/74AHC1G125SE-7` | 74AHC1G125SE-7 | `SOT-353_SC-70-5` | `Package_TO_SOT_SMD:SOT-353_SC-70-5` |  |
| `logic/74LVCH1T45GW` | 74LVCH1T45GW | `SOT-363_SC-70-6` | `Package_TO_SOT_SMD:SOT-363_SC-70-6` | mfr says TI, GW is Nexperia |
| `logic/SN74AHC1G00DCKR` | SN74AHC1G00DCKR | `SOT-353_SC-70-5` | `Package_TO_SOT_SMD:SOT-353_SC-70-5` | + symbol bug GND=pin 2 |
| `logic/SN74AUP1G74DCU` | SN74AUP1G74DCU | `VSSOP-8_2.3x2mm_P0.5mm` | `Package_SO:VSSOP-8_2.3x2mm_P0.5mm` |  |
| `logic/SN74AUP1G97DCKR` | SN74AUP1G97DCKR | `TO_SOT_Packages_SMD:SC-70-6` | `Package_TO_SOT_SMD:SOT-363_SC-70-6` | KiCad-4 name |
| `logic/SN74AUP2G04DCKR` | SN74AUP2G04DCKR | `TO_SOT_Packages_SMD:SC-70-6` | `Package_TO_SOT_SMD:SOT-363_SC-70-6` | KiCad-4 name |
| `logic/SN74LV1T126` | SN74LV1T126DCKR | `SOT-353_SC-70-5` | `Package_TO_SOT_SMD:SOT-353_SC-70-5` |  |
| `memory/25AA1024` | 25AA1024-I/MF | `footprints:DFN-8-1EP_6x5mm_P1.27mm_EP4x4mm` | `Package_DFN_QFN:DFN-S-8-1EP_6x5mm_P1.27mm` | Microchip MF |
| `memory/IS62WV102416DBLL` | IS62WV102416DBLL-45TLI | `TSOP-I-48_18.4x12mm_P0.5mm` | `Package_SO:TSOP-I-48_18.4x12mm_P0.5mm` |  |
| `memory/MX25L12835F` | MX25L12835FZ2I-10G | `DFN-8-1EP_6x5mm_P1.27mm_EP4x4mm` | `Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm` if Z2I (8x6) is right, see F1.16 | 8-WSON; EP |
| `misc_inductors/LQH2MCN100K02L` | LQH2MCN100K02L | `L0806` | `Inductor_SMD:L_Murata_LQH2MCNxxxx02_2.0x1.6mm` | old L0806 missing |
| `misc_inductors/PT61018PEL` | PT61018PEL | `Jonas:Ethernet_trafo_so16w` | `Transformer_SMD:Transformer_Ethernet_Bourns_PT61017PEL` | sibling Bourns part |

#### S+sym - Stock, plus symbol pin renumbering (mounting/shield pads are MP/SH in stock) (4) — done, see F7.2

| Symbol | MPN | Now | Proposed | Note |
|---|---|---|---|---|
| `connectors/0430450818` | 0430450818 | `Molex_0430450818` | `Connector_Molex:Molex_Micro-Fit_3.0_43045-0818_2x04-1MP_P3.00mm_Vertical` | twin; pins 9/10 -> MP |
| `connectors/1051330011` | 1051330011 | `Jonas:1051330011` | `Connector_USB:USB_Micro-B_Molex-105133-0001` | same positions; pins 6/7/8 -> SH; confirm -0011 |
| `connectors/BatClip_54` | 54 | `KS54` | `Battery:BatteryClip_Keystone_54_D16-19mm` | stock numbers all legs 1 |
| `connectors/M-RJHSE-5385-02` | RJHSE-5385-02 | `M-RJHSE-X38X-02` | `Connector_RJ:RJ45_Amphenol_RJHSE538X-02` | same positions; pins 25/26 -> SH |

#### D - Needs your decision (3)

| Symbol | MPN | Now | Proposed | Note |
|---|---|---|---|---|
| `connectors/RPi_GPIO` | N/A | `40p_header_2.54` | `Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical` | socket (HAT) or PinHeader_2x20 (Pi side) - **Jonas: HAT, socket** - `8952e3d` |
| `logic/SN74AVC4T774` | SN74AVC4T774RGYR | `Texas_S-PVQFN-N16_EP2.7x2.7mm` | `Package_DFN_QFN:Texas_RGY_R-PVQFN-N16_EP2.05x2.55mm` | MPN RGY / filter RSV / fp RSA |
| `power/1-1825027-1` | 1-1825027-1 | `Jonas:1-1825027-1` | `Button_Switch_THT:SW_Tactile_SPST_Angled_PTS645Vx31-2LFS` | geometry within 0.04 mm - **Jonas: stock** - `7d14550` |

#### J - Already in Jonas.pretty - fix the link only (2)

| Symbol | MPN | Now | Proposed | Note |
|---|---|---|---|---|
| `connectors/Wurth_7499210123` | 7499210123 | `jonas:Wurth_7499210123` | `Jonas:Wurth_7499210123` | lowercase nickname |
| `misc_inductors/IHLP1212_1u2_4b` | IHLP1212BZER1R2M11 | `IHLP1212` | `Jonas:IHLP1212BZ` | same fp the IHLP DB uses |

#### M - No stock equivalent - migrate old footprint into Jonas.pretty (KLC rebuild) (37)

| Symbol | MPN | Now | Proposed | Note |
|---|---|---|---|---|
| `Audio Amp/TAS2770` | TAS2770RJQT | `RJQ0026A` | `Jonas:Texas_RJQ0026A_VQFN-26` | no stock RJQ0026A; no model |
| `comm/146200` | 146200 | `Jonas:molex_lte_ant_146200` | `Jonas:Molex_146200` | antenna; no model |
| `comm/ALM-GA001` | ALM-GA001 | `uDFN6_EP` | `Jonas:Avago_ALM-GA001` | uDFN6_EP, shared with LTC4065 - confirm it is the ALM-GA001 package |
| `comm/ANT016008LCD1575MA1` | ANT016008LCD1575MA1 | `ANT016008LCD1575MA1` | `Jonas:TDK_ANT016008LCD1575MA1` | no model |
| `comm/DPX162500DT-8014A1` | DPX162500DT-8014A1 | `DPX1625` | `Jonas:TDK_DPX162500DT` | no model |
| `comm/HHM22106C1` | HHM22106C1 | `HHM22106C1` | `Jonas:TDK_HHM22106C1` | no model |
| `comm/mPCIe_modem` |  | `mPCIe` | `Jonas:JAE_MM60-52B1_Mini-PCIe` | + symbol bug PERST# on pin 21 |
| `comm/SKY13587-378LF` | SKY13587-378LF | `MLPD6` | `Jonas:Skyworks_SKY13587-378LF` | MLPD6, split EP; no model |
| `comm/WLA.01` | WLA.01 | `WLA.01` | `Jonas:Taoglas_WLA.01` | no model |
| `connectors/0781715006` | 78171-5006 | `78171-5006` | `Jonas:Molex_78171-5006` | model available |
| `connectors/34826-8200` | 34826-8200 | `34826-8200` | `Jonas:Molex_34826-8200` | no model |
| `connectors/5-104074-8` | 5-104074-8 | `5-104074-8` | `Jonas:TE_5-104074-8` | model path dead |
| `connectors/DX4R005JJ2R1800` | DX4R005JJ2R1800 | `USB_Micro-B` | `Jonas:JAE_DX4R005JJ2R1800` | model available |
| `connectors/fakra_blue_0734035112` | 0734035112 | `fakra_th` | `Jonas:Molex_FAKRA_73403-51xx` | one fp for 4 codings |
| `connectors/fakra_bordeaux_0734035113` | 0734035113 | `fakra_th` | `Jonas:Molex_FAKRA_73403-51xx` |  |
| `connectors/fakra_green_734035114` | 734035114 | `fakra_th` | `Jonas:Molex_FAKRA_73403-51xx` |  |
| `connectors/fakra_violet_0734035117` | 0734035117 | `fakra_th` | `Jonas:Molex_FAKRA_73403-51xx` |  |
| `connectors/RJE72-188-1401` | RJE72-188-1401 | `Jonas:RJE72-188-1401` | `Jonas:Amphenol_RJE72-188-1401` | model available |
| `connectors/TFM-105-02-S-D-WT` | TFM-105-02-S-D-WT | `TFM-105-02-S-D-WT` | `Jonas:Samtec_TFM-105-02-S-D-WT` | model available |
| `connectors/TFM-110-02-S-D-WT` | TFM-110-02-S-D-WT | `Jonas:TFM-110-02-S-D-WT` | `Jonas:Samtec_TFM-110-02-S-D-WT` | tabs numbered 0 vs pins 21/22 (renumbered 21/22, `8b59022`) |
| `connectors/USB_A_292303-1` | 292303-1 | `USB_A_TH` | `Jonas:TE_292303-1` | stock 292303-7 is SMD; -1 is THT |
| `cpu/ADAU1467` | ADAU1467WBCPZ300 | `CP-88-10` | `Jonas:ADI_CP-88-10_LFCSP-88` | model available |
| `cpu/AT91SAM9G25` | AT91SAM9G25 | `217LFBGA` | `Jonas:Microchip_LFBGA-217_15x15mm_P0.8mm` | no model |
| `cpu/MIMX8MM6DVTLZAA` | MIMX8MM6DVTLZAA | `BGA-486_27x27_P0.5mm_14.0x14.0mm` | `Jonas:NXP_FCBGA-486_14x14mm_P0.5mm` | 487 pads for 486 balls |
| `cpu/MIMX8MN5DVTJZAA` | MIMX8MN5DVTJZAA | `BGA-486_27x27_P0.5mm_14.0x14.0mm` | `Jonas:NXP_FCBGA-486_14x14mm_P0.5mm` |  |
| `dcdc/FAN48623` | FAN48623 | `WLCSP16` | `Jonas:WLCSP-16_1.6x1.6mm_Layout4x4_P0.4mm` | no stock 0.4 mm 4x4 |
| `dcdc/FAN48623UC50X` | FAN48623UC50X | `WLCSP16` | `Jonas:WLCSP-16_1.6x1.6mm_Layout4x4_P0.4mm` |  |
| `dcdc/LM536355QRNLRQ1` | LM536355QRNLRQ1 | `VQFN_HR_22` | `Jonas:Texas_RNL0022A_VQFN-HR-22` | no model |
| `dcdc/LMZ10501SILR` | LMZ10501SILR | `TI_LMX_SIL` | `Jonas:Texas_SIL0008A_MicroSiP-8` | stock SIL0008C/D differ |
| `dcdc/MIC23254` | MIC23254-GCYMT-TR | `MLF-10` | `Jonas:Microchip_MLF-10_P0.4mm` | no stock match |
| `dcdc/MIC28511` | MIC28511-1YFL-T5 | `FQFN34-24` | `Jonas:Microchip_FTQFN-24_3x4mm` | multi-EP; no model |
| `dcdc/XCL226A0K1H2` | XCL226A0K1H2 | `Torex_XCL22_QFN` | `Jonas:Torex_XCL226` | no model |
| `interface/PLR135_T10` | PLR135_T10 | `PLR135_T10` | `Jonas:Everlight_PLR135_PLT133` | model available |
| `interface/PLT133_T10W` | PLT133/T10W | `PLT133_T10W` | `Jonas:Everlight_PLR135_PLT133` | uses PLR135 model |
| `interface/TORX1355(V,F)` | TORX1355(V,F) | `TOSLINK_VERTICAL` | `Jonas:Toshiba_TORX1355_TOTX1350` | stock TORX170 family differs |
| `interface/TOTX1350(V,F)` | TOTX1350(V,F) | `TOSLINK_VERTICAL` | `Jonas:Toshiba_TORX1355_TOTX1350` |  |
| `power/bq27742-G1` | BQ27742YZFT-G1 | `DSBGA15` | `Jonas:Texas_YZF_DSBGA-15` | no stock DSBGA-15 |

#### N - No usable footprint anywhere - build new from datasheet (9)

| Symbol | MPN | Now | Proposed | Note |
|---|---|---|---|---|
| `comm/1575AT43A0040` | 1575AT43A0040 | `1575AT43A0040` | `Jonas:Johanson_1575AT43A0040` | no footprint anywhere |
| `comm/LARA-R2` | LARA-R211-02B | `LARA_LGA` | `Jonas:ublox_LARA-R2` | no footprint anywhere |
| `comm/WYSBCVGXA` | WYSBCVGXA | `(empty)` | `Jonas:TaiyoYuden_WYSBCVGXA` | field empty |
| `connectors/DuraClick_560020` | 5600200220 | `(empty)` | `Jonas:Molex_DuraClick_560020-0220` | field empty |
| `connectors/MX34R36HF4T` | MX34R36HF4T | `34826-8200` | `Jonas:JAE_MX34R36HF4T` | uses a 20-pad footprint for 36 pins |
| `connectors/SF7W008S1AE900` | SF7W008S1AE900 | `(empty)` | `Jonas:JAE_SF7W008S1AE900` | field empty |
| `dcdc/LT8640` | LT8640EUDC-1#TRPBF | `Linear_UDCF` | `Jonas:Linear_UDC-18_3x4mm` | old Linear_UDCF missing |
| `logic/NLSV4T3144-D` | NLSV4T3144MUTAG | `(empty)` | `Jonas:OnSemi_UDFN-12` | field empty |
| `power/PT65503` | PT65503 | `(empty)` | `Jonas:APEM_PT65503` | field empty; pin 2 named 2 and C |

#### G - Generic symbol - empty Footprint field is intentional (4)

| Symbol | MPN | Now | Proposed | Note |
|---|---|---|---|---|
| `connectors/Conn_01x30` |  | `(empty)` | `-` | generic |
| `diode_misc/D_TVS_Uni` |  | `(empty)` | `-` | generic (DB provides fp) |
| `power/BOM_Entry` |  | `(empty)` | `-` |  |
| `power/PWR_FLAG` | N/A | `(empty)` | `-` |  |

## F4. Footprint review: `Jonas.pretty` (51 footprints)

**Poetato first (2026-10-13).** Poetato (released for layout) places 14 of
these footprints (18 parts). Checked against its PCB: T2 `Coilcraft_FA2672`
was missing from SMD position files and T3 `T_Wurth_WE-RJ45LAN_7499511440`
was in them; T3's first 3D model path was dead. Fixed in `117ea13` and
`b04fc79`; poetato picks them up with *Update Footprints from Library* on
T2 and T3 (a board change, so re-check before re-release). C9's
`Eaton_KW_13.5x8.8mm` Value fix (`59b754b`) doesn't affect the board (the
footprint Value is replaced by the symbol's). The other poetato
footprints only have the cosmetic issues below.

- [x] **F4.1** `attr` wrong (affects BOM and position files). All fixed,
      one commit each, verified with `kicad-cli pcb export pos --smd-only`
      on a scratch board:
      SMD-only but marked `through_hole`: `Coilcraft_FA2672` (`117ea13`),
      `Coilcraft_FA2925-AL` (`5689b1e`), `Coilcraft_POE60F` (`8a8ebfa`),
      `Texas_YJE` (`85de11d`).
      THT pads but marked `smd`: `T_Wurth_WE-RJ45LAN_7499210001A`
      (`3aea93c`), `T_Wurth_WE-RJ45LAN_7499411122A` (`cf84e0f`),
      `T_Wurth_WE-RJ45LAN_7499511440` (`b04fc79`).
- [x] **F4.2** Courtyard. Fixed: `Wurth_7499210123` shield pads 15/16
      stuck out 0.54 mm → courtyard widened to ±9.30 mm (`18eee39`); 0.1 mm
      courtyard lines → 0.05 mm on `Wurth_7499210123`, `Texas_YJE`
      (`3449c63`) and `Coilcraft_POE60F` (`d8e528b`). KiCad DRC on a
      scratch board: no courtyard violations.
      **Corrected 2026-10-13:** the earlier "fab body outside courtyard" on
      `DLW5B_5050`, `NX3215SA`, `QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm`,
      `SAMTEC_FTSH-105-01-L-DV-007-K`, `SOIC254P680X230-4N` and `Texas_YJE`
      was a pin-1 dot/triangle drawn beside the body on F.Fab, not the body;
      all bodies are inside their courtyards with ≥ 0.25 mm clearance (F4.9).
- [x] **F4.3** Missing layers. Done 2026-10-13: every `Jonas.pretty`
      footprint now has silk, a fab body outline and `${REFERENCE}` on
      F.Fab.
  - Generated footprints, fixed in the generators (which are now
    repo-relative, A1.8): `8e1fdf3` IHLP (×11: fab reference; silk ticks
    moved 0.15 mm off the pads, which also clears 44 DRC "silk clipped by
    solder mask" hits; the hand-calibrated 2525 model offset is now in the
    script), `aea30fd` NX1255GB/NX2520SA/NX3225SA (fab reference; pin-1
    L-shaped silk outside the pads, like stock Crystal_SMD_3225-4Pin, which
    also clears 8 DRC hits on NX2520SA; NX3225SA's hand-added 3D model is
    now in the script). Regenerated output equals the committed files
    apart from these changes.
  - Hand-made, one commit each: silk on `Coilcraft_FA2672` (`21f90aa`),
    `Coilcraft_FA2925-AL` (`3ccb0c1`), `Eaton_KW_13.5x8.8mm` (`f777e2f`),
    `Eaton_KW_21.5x9.5mm` (`f92962f`); fab body from the existing silk
    body outline on `Coilcraft_POE60F` (`6cc50d7`),
    `Vishay_SOIC254P1016X440-4N` (`0fe7096`, had only a pin-1 dot),
    `Wurth_7499210123` (`473b7df`); `${REFERENCE}` on F.Fab on those and on
    `DLW5B_5050` (`569a370`), `FUSC3216X85N` (`d8e3616`), `NX3215SA`
    (`4d20fd6`), `NX5032GA` (`543d948`), `QFN-20_5x5mm…` (`909a5e3`),
    `SAMTEC_FTSH…` (`53bec8c`), `SOIC254P680X230-4N` (`0b57e10`).
    KiCad DRC on the 15: no new violations (5 before, 5 after, all F4.10).
- [x] **F4.4** Fields. `descr`/`tags` added on all 14 that lacked them
      (same commits as F4.3, plus `163890e` Texas_YJE); Value = footprint
      name on `Coilcraft_POE60F`, `DLW5B_5050`, `NX3215SA`, `NX5032GA` (and
      Eaton, `59b754b`). Descriptions name the parts each footprint serves;
      no datasheet URLs were added (none were on hand to check). The empty
      `Datasheet` property is left as is: KiCad's stock footprints keep it
      empty too and put the link in `descr`.
- [x] **F4.5** No 3D model: `NX1255GB`, `QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm`,
      `Texas_YJE`. Done in `1acc16e`: envelope B-Rep models from the new
      `scripting/gen_package_models.py` (data sheet dimensions cited in its
      header), checked in KiCad renders. The first QFN-20 model put 5
      terminals per side; the Si3402 has 4 on the left/right and 6 on the
      top/bottom, as the footprint already had. Fixed before committing.
- [x] **F4.6** Pads: `SAMTEC_FTSH-105-01-L-DV-007-K` numbers pads
      `01`…`10` (its symbol matches, but nothing else in the repo uses
      leading zeros; stock Samtec/pin-header footprints use `1`…`10`).
      Done in `81de170`: pads and the symbol's pin numbers/names renumbered
      together. Poetato J3 must update symbol and footprint together.
- [x] **F4.7** Unused: `NX5032GA` (NDK 5032 rows use stock
      `Crystal_SMD_5032-*`), `T_Wurth_WE-RJ45LAN_7499210001A` (also A3.4).
      Both deleted (`c8d3ce9` with `NX5032GA.step`, `aafe5a6`); neither is
      on poetato's board.
- [ ] **F4.8** (optional) Names are mixed — `T_Wurth_*` vs `Wurth_*`,
      `SAMTEC_*`, `TI_*` vs `Texas_*`, IPC-style (`FUSC3216X85N`,
      `SOIC254P680X230-4N`, `Vishay_SOIC254P1016X440-4N`), bare series
      (`IHLP1212AB`, `NX3225SA`, `DLW5B_5050`), generic
      (`QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm`). Renaming means updating symbols
      and importers (all in this repo); existing boards keep their embedded
      copies.
- [x] **F4.9** Pin-1 marks on F.Fab replaced by KLC body chamfers at the
      pad-1 corner (min(1 mm, 25 % of the short side), capped where an edge
      is short): `DLW5B_5050` (`eae9348`), `QFN-20_5x5mm…` (`0764f90`),
      `SAMTEC_FTSH…` (`06f26bd`, 0.66 mm, outer corner, not the notch at
      the side ear), `SOIC254P680X230-4N` (`e638ac4`), `Texas_YJE`
      (`ecf4189`, also centred its fab reference, which sat outside the
      body), `Vishay_SOIC254P1016X440-4N` (`6387ded`); `NX3215SA`
      (`8003f1e`) only loses its dot (2-pad crystal, not polarized). The
      Coilcraft FA2672/FA2925 vendor drawings keep their pin-1 circle on
      the body. DRC on these: 0 before, 0 after.
- [x] **F4.10** (from the F4.2 DRC run) 0.5 mm silk references on
      `Wurth_7499210123` and `Coilcraft_POE60F` → 1.0 mm, moved off the
      body to just above it; `Wurth_7499210123` silk re-cut 0.2 mm clear of
      every pad (`51d8d36`, `619530e`). DRC on the two: 4 before, 0 after.
- Note: `T_Wurth_WE-RJ45LAN_7498210003` has a rounded `Edge.Cuts` cutout —
  looks intentional (sink-mount), but it does cut the board.
- Note: 15 footprints (`C_Murata_GA3`, 14× ECHU) are still KiCad 7 format —
  harmless; they get resaved whenever their generator runs again.

## F5. 3D models

`Jonas.3dshapes` itself is healthy: all 45 STEP files are B-Rep, none CSG.

- [ ] **F5.1** Orphans: ~~the 15 `.wrl` files~~ (removed, A1.5) and the
      untracked `614105150721 (rev1).stp`. The stock footprint
      `USB_Micro-B_Wuerth_614105150721_Vertical` references a model that is
      not shipped by KiCad at all (see F5.4), which is probably why it was
      downloaded.
- [ ] **F5.2** Missing / dead: `T_Wurth_WE-RJ45LAN_7499210001A.step`
      (`${WE_3DMODEL_DIR}` isn't defined); ~~`T_Wurth_WE-RJ45LAN_7499511440`
      has a second, dead `${WE_3DMODEL_DIR}` model entry next to the good one~~
      (removed, `b04fc79`; render confirms the remaining model loads).
- [ ] **F5.3** Model names don't follow their footprint (`FA2925-AL.STEP`,
      `Coilcraft_POE60F-XXL.STEP`, `KW-5R5C*.STEP`, `AQY212GS.step`,
      `VO618A-3X017T.step`, `0ZCJ0005FF2E.step`, …) and extensions mix
      `.STEP`/`.step`/`.stp`. Proposal: `<footprint>.step`, shared only where
      the body really is identical (`IHLP1212.step` for the three 1212s).
- [ ] **F5.4** ~~KiCad install is only half populated~~. **Corrected
      2026-10-13:** the install is complete (re-run of the installer
      changed nothing: 7,251 STEP files, 3.2 GB). Of the 13,881 distinct
      model paths stock footprints reference, 6,748 simply do not exist
      upstream either (`kicad-packages3D` master: 20 of 20 sampled missing
      ones return 404; a present one returns 200). So stock footprints
      without a body are a KiCad library gap, not an install problem.
      Affected here: 22 stock footprints already in use (e.g. HVSON-8,
      QFN-32 5x5 EP3.1, LQFP-100-1EP, D_PowerDI-5, Micro-Fit 43045-0412,
      USB_Micro-B_Wuerth_614105150721) and 26 stock targets in F3 (most
      BGAs/CSPs, several DFN/QFN, the Molex/RJ45/USB connectors,
      `ublox_MAX`, PT61017PEL). Options, to decide with Jonas: (a) accept
      no body; (b) per board, add a vendor STEP in the PCB editor where
      enclosure fit matters; (c) a separate overlay of generated/vendor
      models for these exact paths. Do not copy stock footprints into
      `Jonas.pretty` just to get a body.
- [ ] **F5.5** Migrated footprints (M): 11 of 31 have a usable STEP in
      `modules/packages3d` (Molex 78171-5006, ADAU1467 LFCSP-88, FAKRA,
      Everlight PLR135 (also used by PLT133), Amphenol RJE72, Samtec
      TFM-105/-110, TE 292303-1, JAE DX4R005JJ2, Toshiba TOSLINK) — copy,
      rename, re-align (old offsets are KiCad-4 inches, WRLs scaled 0.3937;
      use STEP at scale 1). All 11 survived the A1.1 cleanup, as did a few
      other models that may help (JAE MM60 mPCIe socket `.igs`, the `MPCI`
      card STEP, FreeCAD sources for 217LFBGA/YZF/YJE/LARA-R2/146200, and
      `348260200.stp` for Molex 34826); A1.1 lists them. The other 20 have
      no model. Proposal: ICs, BGAs
      and QFNs get a generated body + pads via `scripting/step_brep_box.py`;
      connectors, antennas and modules get vendor STEPs (you download).
- [ ] **F5.6** After F4/F5: render every `Jonas.pretty` footprint once and
      look at the contact sheet — none of the custom models has ever been
      checked visually.

## F6. Other inconsistencies found

Symbols:

- Datasheet empty on 206 of 231 non-power symbols, Description on 114.
- `Description_1` duplicates Description on 9 LED symbols (KiCad 8 upgrade
  leftover) — merge.
- Manufacturer spelling: `Diodes Inc`/`Diodes Inc.`, `Wurth`/
  `Wurth Elektronik`, `ON Semi`/`ONSemi`/`On Semi`, `ublox`/`U-Blox`,
  `Skyworks`/`Skyworks Solutions Inc.`, `Littlefuse` (also in the DB library
  name, A4.2); legacy owners `Linear` (12), `Fairchild` (5), `Freescale` (1).
  Wrong: `Adafruit` on SK6812RGBW (maker is Opsco), `TI` on 74LVCH1T45GW
  (Nexperia part).
- MPN field: `FTSH-105-01-F-DV-K.stp`, `Zynq 7010`, `STM32F446ZE` (no
  package suffix), trailing space in `KW-5R5C105-R `, `N/A` on three.
- Reference prefixes vs KiCad convention: antennas `Z` (KiCad `AE`),
  push button `PB` (`SW`), SAW filter `X` (`FL`), mounting hole `M` (`H`),
  SK6812 `U` (`D`).
- `logic/SN74AUP1G74DCU` names both pin 3 and pin 5 `Q`; pin 3 is Q̄
  (the graphic has the inversion bubble, so it's cosmetic). Same for
  `CLR`/`PRE` without `~{}`.
- `ki_fp_filters` are stale in places (DS2482S `WLP`; SN74AVC4T774 fixed in F1.6)
  and only 94 symbols have them. After remapping, set them to match the
  chosen footprint or clear them.

Config and docs:

- `fp-lib-table` registers `Jonas` with an absolute path while
  `sym-lib-table` uses `${JONAS_KICADLIB}` — use the variable for both.
- `CLAUDE.md` points to
  `.claude/skills/kicad-db-library-import/references/step_brep_authoring.md`,
  which doesn't exist (only `field_styles.md` does).
- `CLAUDE.md` says no CAD viewer is available in-session — true for the
  Cowork sandbox, but a local Claude Code session on archimedes has KiCad
  10 and can render. Worth stating both.
- `scripting/step_brep_box.py`'s header still refers to
  `footprints/Murata_GA3.3dshapes/` (pre-`Jonas.3dshapes` layout).
- Nothing on this machine depends on `modules/` through a lib table: the
  only project-level tables (`Projects/B1`, `Snigel2`, `Snappy`, 2016–2018)
  point at long-dead paths, and `.kicad_pcb` files embed their footprints.

## F7. Proposed order

- [ ] **F7.1** F1 bug fixes (symbols only, plus the FIX remaps). Batch 1
      done 2026-10-13 (`4912daf`..`248baee`): F1.1–F1.5, F1.8–F1.11 and
      the two J link fixes; broken footprint links 113 → 104. F1.16 and
      F1.6 followed (`8cb4f26`, `94fe08f`). Left: F1.7 (new footprint),
      F1.12–F1.15 (during migration), F1.17.
- [ ] **F7.2** Stock remaps: S, then S+sym, then S\* (datasheet check per
      row) — one commit per symbol library.
  - [x] S (29 symbols), 2026-10-13: `610e64f` LEDs, `a01f7bb` adcdac,
    `9f9fd69` comm, `ecfa484` connectors, `71f40a7` cpu, `f0b4b4b` dcdc,
    `8c76f07` diode_misc, `c29f513` memory, `1e05f0f` misc_inductors,
    `cd1c28f` power. Re-verified before applying: pads within 0.1 mm of
    the old footprint and no symbol pin without a pad. Three needed a
    closer look: LTC3528 is a twin once the EP is compared as one pad,
    but loses the old footprint's two thermal vias; 78171-0003's tabs are
    `MP` instead of `0` (no pin uses them); LTC4267's DHC16 was compared
    from history. Broken links 104 → 73.
  - [x] S+sym (4), 2026-10-13 (Jonas OK'd question 6): `f51827a` 43045-0818,
    `9a63bf3` 105133, `e3507a6` BatClip_54, `64e2808` RJHSE. One pin per
    pad number: the first mounting/shield pin is renumbered `MP`/`SH`
    (RJHSE's is also renamed `SH`) and its duplicates are deleted, since
    duplicate pin numbers can leave a pad netless if one copy is unwired.
    Boards updated from the library must move wires from deleted pins.
    105133: the old footprint (from history) had round shell holes; Molex
    SD-105133-001 rev E specifies 0.50 mm slots, as stock has.
    BatClip_54: stock numbers all three legs `1` (one metal clip), so the
    symbol keeps pin 1 only.
  - [x] S\* (29 of 31), 2026-10-13: `ce31f3b` LEDs, `8e5b088` comm,
    `d5875ae` connectors, `641b48b` cpu, `5fb1db0` dcdc, `9006199`
    diode_misc, `4bb1083` interface, `0e1d564` logic, `faffbb0` memory,
    `654efdc` misc_inductors. Each commit message lists the evidence per
    row. Pin numbering was checked against the datasheet's column for the
    ordered package, or against KiCad's stock symbol of the same part
    (STM32F302K8, STM32L486ZG, SAMD21E15B, LAN8710, TCA9535, 1T45), or
    the vendor package file (Zynq: all 225 balls). Changes from the F3
    table:
    - `interface/TCA9535RGER`: TI uses RGE0024**B** (EP 2.45 ± 0.1), not
      RGE0024H (2.7) → `VQFN-24-1EP_4x4mm_P0.5mm_EP2.45x2.45mm`.
    - `cpu/ATSAMD21E15B`: MU = VQFN-32 with **3.60** mm EP (Microchip
      land 3.70), not 3.45 → `QFN-32-1EP_5x5mm_P0.5mm_EP3.6x3.6mm`.
    - `comm/2450AT18B100`: **moved to M.** Johanson's B100 spec gives a
      0.8×1.6 mm pad land, 4.2 mm overall, which is exactly the old
      footprint; the stock `Johanson_2450AT18x100` is the A100 land
      (1.2×1.8 mm).
    - `memory/MX25L12835F`: done earlier as F1.16.
  - [ ] F7.2 follow-ups (new):
    - `dcdc/LTC3612`: footprint is certain (LTC UDC20), but the symbol's
      pin order could not be checked (analog.com and its mirrors refuse
      connections from this machine). Check against the datasheet.
    - `memory/IS62WV102416DBLL` and `connectors/GBC08SGSN-M89`: vendor
      datasheets not reachable/checked; the IS62 footprint is a twin of
      the old one, the GBC08 is a plain 1x08 2.54 mm header.
    - `misc_inductors/PT61018PEL`: symbol labels RX/TX from the other side
      than Bourns' schematic (TD/RD); pairing and polarity are right.
- [ ] **F7.3** `Jonas.pretty` QA fixes (F4) and 3D cleanup (F5.1–F5.3).
- [x] **F7.4** Migrations (M), in batches by symbol library, each with a
      render contact sheet. **Inventory 2026-10-13** (Jonas: Q7 = Vendor_Part
      names; Q8 = reuse models from the repo, its history and the old
      projects first, generate the rest; every generated footprint/model
      goes on the F8 review list). Sources searched: `modules/`, git
      history (3,072 model files ever committed), and the old projects
      Snigel2, Sting2/Schematic, Vektor, Blixten Gateway and Blixten LED
      Device on Y: (129 model files, 4 boards). "Built" = the footprint is on that project's
      board; in every case but the ones noted in the text below, the
      board's embedded copy is pad-for-pad identical to `modules/`.

  | Symbol(s) | Footprint source | Built on | 3D model |
  |---|---|---|---|
  | TAS2770 | `RJQ0026A` | - | **generate** |
  | 146200 | `molex_lte_ant_146200` | Sting2 | git history `LTE_antenna_molex_146200-001.wrl` |
  | 2450AT18B100 | `2450AT18B100` | - | **generate** |
  | ALM-GA001 | `uDFN6_EP` | Sting2 | **generate** |
  | ANT016008LCD1575MA1 | `ANT016008LCD1575MA1` | Sting2 | **generate** |
  | DPX162500DT-8014A1 | `DPX1625` | Sting2 | **generate** |
  | HHM22106C1 | `HHM22106C1` | Sting2 | **generate** |
  | SKY13587-378LF | `MLPD6` | Sting2 | **generate** |
  | WLA.01 | `WLA.01` | Gateway, LED Device | git history `wla.01.wrl` |
  | mPCIe_modem | `mPCIe` | - | git history `MPCI.STEP` |
  | 0781715006 | `78171-5006` | - | git history `781715006.stp` |
  | 34826-8200 | `34826-8200` | Sting2 | git history `348260200.stp` |
  | 5-104074-8 | `5-104074-8` | Snigel2 | old project `ampmodu_5-104074-8.wrl` |
  | DX4R005JJ2R1800 | `USB_Micro-B` | Gateway, LED Device | git history `K3D-DX4R005JJ2-V3_JAE_Proprietary.STEP` |
  | RJE72-188-1401 | `RJE72-188-1401` | Gateway | git history `M-RJE72-188-1X01-REVT1.STEP` |
  | TFM-105-02-S-D-WT | `TFM-105-02-S-D-WT` | Snigel2, LED Device | git history `TFM-105-02-S-D-WT.stp` |
  | TFM-110-02-S-D-WT | `TFM-110-02-S-D-WT` | Gateway, Sting2 | git history `TFM-110-02-S-D-WT.stp` |
  | USB_A_292303-1 | `USB_A_TH` | Snigel2 | repo `c-292303-1-e4-3d.stp` |
  | fakra x4 | `fakra_th` | Sting2 | git history `fakra_green_734035114.stp` |
  | ADAU1467 | `CP-88-10` | - | repo `User Library-LFCSP_VQ88(CP-88-5).step` |
  | AT91SAM9G25 | `217LFBGA` | Gateway | git history `217LFBGA.wrl` |
  | MIMX8MM6/MN5 | `BGA-486_27x27_P0.5mm_14.0x14.0mm` | - | **generate** |
  | FAN48623 x2 | `WLCSP16` | Sting2 | **generate** |
  | LM536355QRNLRQ1 | `VQFN_HR_22` | Sting2 | **generate** |
  | LMZ10501SILR | `TI_LMX_SIL` | - | **generate** |
  | MIC23254 | `MLF-10` | Gateway | old project `2x2mm.wrl` |
  | MIC28511 | `FQFN34-24` | Snigel2 | **generate** |
  | XCL226A0K1H2 | `Torex_XCL22_QFN` | - | **generate** |
  | PLR135_T10, PLT133_T10W | `PLR135_T10`, `PLT133_T10W` (identical) | - | repo `PLR135.STEP` |
  | TORX1355, TOTX1350 | `TOSLINK_VERTICAL` | - | repo `toslink.step` (the footprint's own model) |
  | bq27742-G1 | `DSBGA15` | Sting2 | git history `15dsbga.wrl` |
  | LARA-R2 (N->M) | `LARA_R2_LGA` | Sting2 | git history `lara_r2.wrl` |
  | 1575AT43A0040 (N) | **new from data sheet** | - | **generate** |
  | WYSBCVGXA (N) | **new from data sheet** | - | **generate** |
  | DuraClick_560020 (N) | **new from data sheet** | - | **generate** |
  | MX34R36HF4T (N) | **new from data sheet** | - | **generate** |
  | SF7W008S1AE900 (N) | **new from data sheet** | - | **generate** |
  | LT8640 (N) | **new from data sheet** | - | **generate** |
  | NLSV4T3144-D (N) | **new from data sheet** | - | **generate** |
  | PT65503 (N) | **new from data sheet** | - | **generate** |

  Board copies vs `modules/`: an earlier note here listed `FQFN34-24`,
  `VQFN_HR_22`, `TFM-110-02-S-D-WT`, `WLA.01` and `5-104074-8` as
  differing. That was an extraction bug (KiCad 4/5 boards store pad
  angles including the footprint rotation); with it fixed, every board
  copy is pad-for-pad identical to `modules/` except `USB_Micro-B`
  (JAE DX4R005, Gateway and LED Device), which numbers all four shield
  pads 6 where `modules/` and the symbol have 6/7. The migration keeps
  6/7 (`24a6d48`). LARA-R2 moves from N to M: `modules/LARA_R2_LGA` exists (the
  symbol linked a wrong name) and is on the Sting2 board.
  Stock candidates from the 2026-10-13 recheck (LMZ10501 → TI SIL0008D,
  MIC23254 → DFN-10 2x2 P0.4, MIC28511 → QFN-24 3x4 P0.4, USB-A → TE
  292303-7, HHM22106C1 → Johanson 1.6x0.8 balun, ALM-GA001, NLSV4T3144 →
  UQFN-12, TORX/TOTX → Toshiba 170 series): where the old footprint is
  on a built board it is the proven land and is migrated instead; the
  rest get a data sheet check first.
  - [x] dcdc (7 symbols, 6 footprints): `ae9638e`..`4dfdfcd`. Pads verified identical to `modules/`; KiCad DRC shows only the original copper findings (EP via annular/drill, WLCSP pitch), silk findings went 68 -> 0.
  - [x] cpu (4 symbols, 3 footprints): `55ac534`..`8574f99`. Pads identical to `modules/`; DRC 0.
  - [x] Audio Amp + power (TAS2770, bq27742-G1): `02b16d4`..`d449ba1`. Pads identical to `modules/`.
  - [x] interface (4 symbols, 2 footprints): `99f417b`, `32ef941`. Vendor models from modules/packages3d. Pads identical to `modules/`; DRC 0.
  - [x] comm (10 symbols, 10 footprints): `130c9c1`..`a15f9e3`. Pads identical to `modules/`; per-footprint DRC 0 (old versions had 19 silk-over-pad hits).
  - [x] connectors (12 symbols, 9 footprints): `1bc0fa2`..`8b59022`. Vendor models (modules/packages3d, Snigel2 WRL). Pads identical to `modules/` except two fixes to match the symbols (DX4R005 shield 6/7, TFM-110 holes 21/22); per-footprint DRC 0 (old versions had 14 silk hits). MX34R36HF4T still linked 34826-8200 and stays in F7.5.
- [ ] **F7.5** New footprints (N), one at a time from datasheets.
  - [x] 1575AT43A0040: `8b81c83` (data sheet land, generated body)
- [ ] **F7.6** Re-run the audit: zero `footprints:`, bare, or missing
      `Jonas:` references; fix `gen_ndk_footprints.py` (A1.8); then
      `git rm -r modules/` (A2.6) and optionally A6. (`Jonas.pretty/tmp/`
      is already gone, A1.2.)
- [ ] **F7.7** (optional) F6 field hygiene and F4.8 renames.

## F8. Manual review: everything Claude generated (Jonas)

Per Jonas (2026-10-13), everything Claude makes or touches is listed here
for a manual check in KiCad: every footprint it creates or migrates
(Footprints), every 3D model it generates or downloads (3D models), and
every footprint where it places or adjusts a 3D model, including copying
an old transform (3D model placements). Tick when reviewed.

### Footprints

- [ ] `onsemi_WLCSP-16_1.6x1.6mm_Layout4x4_P0.4mm` (FAN48623) - migrated, pads unchanged; outline/courtyard/fab rebuilt, body 1.6x1.6 from old silk - `75b538c`
- [ ] `Texas_RNL0022B_VQFN-HR-22_4x5mm_P0.5mm` (LM536355) - migrated, pads unchanged; body per TI 4226904/A - `ba1b30b`
- [ ] `Texas_SIL0008G_MicroSiP-8_3x2.6mm` (LMZ10501) - migrated, pads unchanged; body per data sheet - `d5f014d`
- [ ] `Microchip_MLF-10_2x2mm_P0.4mm` (MIC23254) - migrated, pads unchanged; body per data sheet - `cd2634e`
- [ ] `Microchip_FTQFN-24_3x4mm` (MIC28511) - migrated, pads unchanged; body 4x3 from old silk - `438756d`
- [ ] `Torex_XCL226` (XCL226A0K1H2) - migrated, pads unchanged; body from old silk (XCL226 may really be 2.5x2.0, check) - `4dfdfcd`
- [ ] `Analog_CP-88-10_LFCSP-88-1EP_12x12mm_P0.5mm` (ADAU1467) - migrated, pads unchanged; body 12x12; vendor model re-rotated (-90,0,90) so the dimple is at pad 1 - `ed0d092`
- [ ] `Microchip_LFBGA-217_15x15mm_Layout17x17_P0.8mm` (AT91SAM9G25) - migrated, pads unchanged - `9778593`
- [ ] `NXP_FCBGA-486_14x14mm_Layout27x27_P0.5mm` (i.MX 8M Mini/Nano) - migrated, pads unchanged incl. pads E23/J18 without a pin (F1.14) - `8574f99`
- [ ] `Texas_RJQ0026A_VQFN-HR-26_4x3.5mm` (TAS2770) - migrated, pads unchanged; body per TI 4223791/C. Note: original pads 2 and 26 are 0.19 mm apart (KiCad default clearance 0.2) - compare with TI's land pattern - `d1afb13`
- [ ] `Texas_YZF0015_DSBGA-15_1.96x2.78mm_Layout3x5_P0.5mm` (bq27742-G1) - migrated, pads unchanged; body per TI 4219381/A - `d449ba1`
- [ ] `Everlight_PLR135_PLT133` (PLR135_T10, PLT133_T10W) - migrated, pads unchanged (the two old footprints were identical); body from old silk; vendor model with the old transform, eyeballed top/side - `99f417b`
- [ ] `Toshiba_TORX1355_TOTX1350` (TORX1355, TOTX1350) - migrated, pads unchanged; body from old silk; vendor model (toslink.step) with the old transform, eyeballed top/side - `32ef941`
- [ ] `Molex_146200` - migrated, pads unchanged; body from old silk; WRL model, old transform - `1cb696c`
- [ ] `Johanson_2450AT18B100` - migrated, pads unchanged (= Johanson B100 land); body 3.2x1.6 - `462565d`
- [ ] `Avago_ALM-GA001` - migrated from uDFN6_EP, pads unchanged; body from old silk - `375d3e6`
- [ ] `TDK_ANT016008LCD1575MA1` - migrated, pads unchanged; body 1.6x0.8 - `b61a185`
- [ ] `TDK_DPX162500DT` - migrated from DPX1625, pads unchanged; body 1.6x0.8 - `9e462f4`
- [ ] `TDK_HHM22106C1` - migrated, pads unchanged; body 2.2x2.0 from old silk (may be larger than the real part, check) - `c0611a7`
- [ ] `Skyworks_SKY13587-378LF` - migrated from MLPD6, pads unchanged; body from old silk - `40804f5`
- [ ] `Taoglas_WLA.01` - migrated, pads unchanged (= Gateway/LED Device boards); WRL model, old transform - `9f56273`
- [ ] `JAE_MM60-52B1_Mini-PCIe` (mPCIe_modem) - migrated, pads unchanged; three WRL models (socket, holder, card), old transforms - `eb7f7ed`
- [ ] `ublox_LARA-R2` - migrated from LARA_R2_LGA (symbol linked a non-existent name), pads unchanged; WRL model, old transform - `a15f9e3`
- [ ] `Molex_78171-5006` - migrated, pads unchanged; vendor STEP, old transform, eyeballed - `1bc0fa2`
- [ ] `Molex_34826-8200` - migrated, pads unchanged; vendor STEP, old transform, eyeballed - `07702d5`
- [ ] `TE_5-104074-8` - migrated, pads unchanged; WRL from Snigel2 project, old transform, eyeballed - `bb03aa6`
- [ ] `JAE_DX4R005JJ2R1800` - migrated from USB_Micro-B, shield pads 6/7 as modules/ (boards had all 6); vendor STEP - `0321d55`, `24a6d48`
- [ ] `Amphenol_RJE72-188-1401` - migrated, pads unchanged; vendor STEP, old transform, eyeballed - `4584b70`
- [ ] `Samtec_TFM-105-02-S-D-WT` - migrated, pads unchanged; vendor STEP - `2f8629d`
- [ ] `Samtec_TFM-110-02-S-D-WT` - migrated; plated holes renumbered 0 -> 21/22 to match the symbol; vendor STEP - `b31d1fc`, `8b59022`
- [ ] `TE_292303-1` - migrated from USB_A_TH, pads unchanged; vendor STEP - `2cf4d80`
- [ ] `Molex_FAKRA_73403-51xx` - migrated from fakra_th, pads unchanged; one footprint for 4 codings, green vendor STEP - `6769a2a`
- [ ] `Johanson_1575AT43A0040` - **new from data sheet** (1575AT43A0040001E rev 4.0, mounting config 1 land 1.0x1.8 @ +-3.5) - `8b81c83`

### 3D models

- [ ] `QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm.step` (Si3402, poetato U4) -
      `scripting/gen_package_models.py`, `1acc16e`
- [ ] `NX1255GB.step` - `scripting/gen_package_models.py`, `1acc16e`
- [ ] `Texas_YJE.step` (CSD83325L) - `scripting/gen_package_models.py`,
      `1acc16e`
- [ ] `onsemi_WLCSP-16_1.6x1.6mm_Layout4x4_P0.4mm.step` - plain body, height 0.6 ASSUMED - `ae9638e`
- [ ] `Texas_RNL0022B_VQFN-HR-22_4x5mm_P0.5mm.step` - plain body, 0.9 per TI drawing - `ae9638e`
- [ ] `Texas_SIL0008G_MicroSiP-8_3x2.6mm.step` - plain body, height 1.0 ASSUMED - `ae9638e`
- [ ] `Microchip_MLF-10_2x2mm_P0.4mm.step` - plain body, 0.55 per data sheet - `ae9638e`
- [ ] `Microchip_FTQFN-24_3x4mm.step` - plain body, height 0.75 ASSUMED - `ae9638e`
- [ ] `Torex_XCL226.step` - plain body, height 1.0 ASSUMED - `ae9638e`
- [ ] `Microchip_LFBGA-217_15x15mm_Layout17x17_P0.8mm.step` - plain body, height 1.4 ASSUMED - `55ac534`
- [ ] `NXP_FCBGA-486_14x14mm_Layout27x27_P0.5mm.step` - plain body, height 1.2 ASSUMED - `55ac534`
- [ ] `Texas_RJQ0026A_VQFN-HR-26_4x3.5mm.step` - plain body, 1.0 per TI drawing - `02b16d4`
- [ ] `Texas_YZF0015_DSBGA-15_1.96x2.78mm_Layout3x5_P0.5mm.step` - plain body, 0.625 per TI drawing - `02b16d4`
- [ ] `Johanson_2450AT18B100.step` - plain body, 1.3 per Johanson spec - `130c9c1`
- [ ] `Avago_ALM-GA001.step` - plain body, height 0.75 ASSUMED - `130c9c1`
- [ ] `TDK_ANT016008LCD1575MA1.step` - plain body, height 0.5 ASSUMED - `130c9c1`
- [ ] `TDK_DPX162500DT.step` - plain body, height 0.6 ASSUMED - `130c9c1`
- [ ] `TDK_HHM22106C1.step` - plain body, height 0.6 ASSUMED - `130c9c1`
- [ ] `Skyworks_SKY13587-378LF.step` - plain body, height 0.45 ASSUMED - `130c9c1`
- [ ] `Johanson_1575AT43A0040.step` - plain body 7.0x2.0x0.8 per data sheet; no vendor STEP (Johanson: on request) - `8b81c83`

### 3D model placements

Every footprint where Claude placed or adjusted a 3D model (model file, offset, rotation, scale), including models copied with their old transform. Check in the KiCad 3D viewer that the body sits on the board, pin 1 and the pins line up with the pads, and connector openings face the right way.
- [ ] `QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm`: `QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm.step` identity transform (generated, built in footprint coordinates) - `1acc16e`
- [ ] `NX1255GB`: `NX1255GB.step` identity transform (generated, built in footprint coordinates) - `1acc16e`
- [ ] `Texas_YJE`: `Texas_YJE.step` identity transform (generated, built in footprint coordinates) - `1acc16e`
- [ ] `onsemi_WLCSP-16_1.6x1.6mm_Layout4x4_P0.4mm`: `onsemi_WLCSP-16_1.6x1.6mm_Layout4x4_P0.4mm.step` identity transform (generated, built in footprint coordinates) - `75b538c`
- [ ] `Texas_RNL0022B_VQFN-HR-22_4x5mm_P0.5mm`: `Texas_RNL0022B_VQFN-HR-22_4x5mm_P0.5mm.step` identity transform (generated, built in footprint coordinates) - `ba1b30b`
- [ ] `Texas_SIL0008G_MicroSiP-8_3x2.6mm`: `Texas_SIL0008G_MicroSiP-8_3x2.6mm.step` identity transform (generated, built in footprint coordinates) - `d5f014d`
- [ ] `Microchip_MLF-10_2x2mm_P0.4mm`: `Microchip_MLF-10_2x2mm_P0.4mm.step` identity transform (generated, built in footprint coordinates) - `cd2634e`
- [ ] `Microchip_FTQFN-24_3x4mm`: `Microchip_FTQFN-24_3x4mm.step` identity transform (generated, built in footprint coordinates) - `438756d`
- [ ] `Torex_XCL226`: `Torex_XCL226.step` identity transform (generated, built in footprint coordinates) - `4dfdfcd`
- [ ] `Analog_CP-88-10_LFCSP-88-1EP_12x12mm_P0.5mm`: `Analog_CP-88-10_LFCSP-88-1EP_12x12mm_P0.5mm.step` rotate (-90, 0, 90) (vendor STEP from modules/packages3d; rotation worked out by Claude, the old transform was wrong) - `ed0d092`
- [ ] `Microchip_LFBGA-217_15x15mm_Layout17x17_P0.8mm`: `Microchip_LFBGA-217_15x15mm_Layout17x17_P0.8mm.step` identity transform (generated, built in footprint coordinates) - `9778593`
- [ ] `NXP_FCBGA-486_14x14mm_Layout27x27_P0.5mm`: `NXP_FCBGA-486_14x14mm_Layout27x27_P0.5mm.step` identity transform (generated, built in footprint coordinates) - `8574f99`
- [ ] `Texas_RJQ0026A_VQFN-HR-26_4x3.5mm`: `Texas_RJQ0026A_VQFN-HR-26_4x3.5mm.step` identity transform (generated, built in footprint coordinates) - `d1afb13`
- [ ] `Texas_YZF0015_DSBGA-15_1.96x2.78mm_Layout3x5_P0.5mm`: `Texas_YZF0015_DSBGA-15_1.96x2.78mm_Layout3x5_P0.5mm.step` identity transform (generated, built in footprint coordinates) - `d449ba1`
- [ ] `Everlight_PLR135_PLT133`: `Everlight_PLR135_PLT133.step` offset (0, -4.4, 0), rotate (-90, 0, -90) (vendor STEP, old transform) - `99f417b`
- [ ] `Toshiba_TORX1355_TOTX1350`: `Toshiba_TORX1355_TOTX1350.step` identity transform (vendor STEP, old transform) - `32ef941`
- [ ] `Molex_146200`: `Molex_146200.wrl` scale 0.3937 (WRL from git history, old transform) - `1cb696c`
- [ ] `Johanson_2450AT18B100`: `Johanson_2450AT18B100.step` identity transform (generated, built in footprint coordinates) - `462565d`
- [ ] `Avago_ALM-GA001`: `Avago_ALM-GA001.step` identity transform (generated, built in footprint coordinates) - `375d3e6`
- [ ] `TDK_ANT016008LCD1575MA1`: `TDK_ANT016008LCD1575MA1.step` identity transform (generated, built in footprint coordinates) - `b61a185`
- [ ] `TDK_DPX162500DT`: `TDK_DPX162500DT.step` identity transform (generated, built in footprint coordinates) - `9e462f4`
- [ ] `TDK_HHM22106C1`: `TDK_HHM22106C1.step` identity transform (generated, built in footprint coordinates) - `c0611a7`
- [ ] `Skyworks_SKY13587-378LF`: `Skyworks_SKY13587-378LF.step` identity transform (generated, built in footprint coordinates) - `40804f5`
- [ ] `Taoglas_WLA.01`: `Taoglas_WLA.01.wrl` offset (-0.254, 0, 0), scale 0.3937 (WRL from git history, old transform) - `9f56273`
- [ ] `JAE_MM60-52B1_Mini-PCIe`: `JAE_MM60-52B1_Mini-PCIe.wrl` offset (11.811, 0, 0), rotate (270, 0, 180), scale 0.3937; `JAE_MM60-52B1_Mini-PCIe_Holder.wrl` offset (11.811, 53.34, 0), scale 0.3937; `JAE_MM60-52B1_Mini-PCIe_Card.wrl` offset (11.811, 25.4, 1.27), rotate (90, 180, 180), scale 0.3937 (WRLs from git history, old transforms; three models: socket, holder, card) - `eb7f7ed`
- [ ] `ublox_LARA-R2`: `ublox_LARA-R2.wrl` offset (0, 0, 1.651), rotate (180, 0, 0), scale 0.3937 (WRL from git history, old transform) - `a15f9e3`
- [ ] `Molex_78171-5006`: `Molex_78171-5006.step` offset (0, -1.905, 1.27), rotate (-90, 0, 0) (vendor STEP, old transform) - `1bc0fa2`
- [ ] `Molex_34826-8200`: `Molex_34826-8200.step` offset (17.018, -5.334, 7.366), rotate (90, 0, 0) (vendor STEP, old transform) - `07702d5`
- [ ] `TE_5-104074-8`: `TE_5-104074-8.wrl` offset (0, -10.541, 2.413), rotate (-90, 0, 0), scale 0.3937 (WRL from the Snigel2 project, old transform) - `bb03aa6`
- [ ] `JAE_DX4R005JJ2R1800`: `JAE_DX4R005JJ2R1800.step` offset (0, 0.381, 1.27), rotate (-90, 0, 0) (vendor STEP, old transform) - `0321d55`
- [ ] `Amphenol_RJE72-188-1401`: `Amphenol_RJE72-188-1401.step` offset (-3.175, 4.191, 2.286), rotate (0, 90, 180) (vendor STEP, old transform) - `4584b70`
- [ ] `Samtec_TFM-105-02-S-D-WT`: `Samtec_TFM-105-02-S-D-WT.step` rotate (-90, 0, 0) (vendor STEP, old transform) - `2f8629d`
- [ ] `Samtec_TFM-110-02-S-D-WT`: `Samtec_TFM-110-02-S-D-WT.step` rotate (-90, 0, 0) (vendor STEP; old transform was for a WRL) - `b31d1fc`
- [ ] `TE_292303-1`: `TE_292303-1.step` offset (0, -13, 3.5), rotate (-90, 0, 0) (vendor STEP, old transform) - `2cf4d80`
- [ ] `Molex_FAKRA_73403-51xx`: `Molex_FAKRA_73403-51xx.step` offset (0, -18.415, 3.81) (vendor STEP (green variant), old transform) - `6769a2a`
- [ ] `Johanson_1575AT43A0040`: `Johanson_1575AT43A0040.step` identity transform (generated, built in footprint coordinates) - `8b81c83`

## Open questions

1. Prune first? "Only the ones we need" — are there symbols for parts you
   will never use again (e.g. 2016-era AT91SAM9G25, LARA-R2, FAKRA, mPCIe
   modem)? Deleting them shrinks M and N.
2. F1.6 — which SN74AVC4T774 package do you actually use?
3. `connectors/RPi_GPIO` — socket (HAT side) or header (Pi side)?
   **Answered: Pi HAT, so the socket (`8952e3d`).**
4. `power/1-1825027-1` — stock `SW_Tactile_SPST_Angled_PTS645Vx31-2LFS`
   (pads identical within 0.04 mm, C&K 3D model) or keep a TE-named copy?
   **Answered: stock (`7d14550`).**
5. Stock twins with another vendor's name (`LP5562` → `Maxim_WLP-12…`,
   `FAN5355UC00` → `Texas_DSBGA-12…`, `2450BM15B0002` →
   `Balun_Johanson_0896BM15A0001`): fine to use as-is, or would you rather
   have renamed copies in `Jonas.pretty`?
6. S+sym — OK to renumber symbol pins to `MP`/`SH` so the stock Molex, RJ45,
   USB and battery-clip footprints fit?
7. Footprint naming (F4.8): rename the existing `Jonas.pretty` footprints
   now, or only apply the convention to new/migrated ones?
8. Missing 3D models (F5.5): OK to generate simple bodies for ICs, with you
   downloading vendor STEPs for connectors/antennas/modules?
9. S\* rows need datasheet checks — OK for me to fetch datasheets from the
   web (TI, ADI, NXP, Microchip, ...) during the work?

## Corrections to `review-2026-10-cleanup.md`

- A3.5: `tssop-38_4.4x9.7mm_p0.5mm.step` is not missing — `TI_DFB0038A`
  uses the stock `${KICAD10_3DMODEL_DIR}/Package_SO.3dshapes/TSSOP-38_4.4x9.7mm_P0.5mm.step`.
  Only `T_Wurth_WE-RJ45LAN_7499210001A.step` is missing.
- A2.1 lists `LTC4267IDHC` (`DHC16`) as "not in modules": it exists in
  `Jonas.pretty/tmp/` (as does `DFN-10-1EP_3x3mm_Pitch0.5mm` for
  `LTC3447`, A3.1), which is also what the stock matches above were made
  from. (`tmp/` was later removed by A1.2; the files are in `ebab8c3`.)
- A2.4: under this plan only 11 models from `modules/packages3d` are
  needed (F5.5), not ~34.
