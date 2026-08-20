# kicadlib naming scheme

This document defines the naming convention for library files, internal database
tables, and part identifiers across `kicadlib`. It covers the four component
families large enough to warrant KiCad **database libraries** (`.kicad_dbl` +
`.db`, following the pattern established by `cap_mlcc_murata`): capacitors,
resistors, inductors, and ferrite beads.

Small, mixed, hand-maintained libraries (`diodes`, `transistors`, `logic`,
`connectors`, `power`, etc.) are function-based, not vendor/part-family based,
and are out of scope for this scheme — they keep their existing simple names.
The line for "does this deserve a database library" is roughly: does one
vendor's part family have enough SKUs (tens to thousands) that hand-authoring
one symbol per part stops being practical? `capacitors_murata_GRM.lib` (5,586
symbols) and `vishay_resistors.lib` (3,156 symbols) are the two existing
libraries that crossed that line, which is what motivated this scheme.

## 1. Library file naming

```
<component>_<type>_<vendor>[_<series>].kicad_dbl / .db
```

| Component | Prefix |
|---|---|
| Capacitor | `cap` |
| Resistor | `res` |
| Inductor | `ind` |
| Ferrite bead | `bead` |

`<vendor>` is a short lowercase vendor slug (`murata`, `vishay`, `kemet`,
`panasonic`, `coilcraft`, `koa`, ...). `<series>` is optional — include it
when a vendor has multiple distinct product lines within the same type that
you're maintaining as separate imports (e.g. `ihlp` vs `dcm` power inductor
series from the same vendor); omit it when there's only one series, or fold
multiple series into one file as multiple `libraries[]` entries in the same
`.kicad_dbl` (see §3).

Everything lowercase, underscore-separated — matches the convention
recommended for the rest of the library in the earlier review (the current
mix of `Audio Amp.lib` / `Mech.lib` / `beads_BLM.lib` casing should converge
on this same style over time).

The companion import script takes the same stem: `import_<library>.py`, e.g.
`import_cap_mlcc_murata.py` for `cap_mlcc_murata.kicad_dbl` — established by
the `cap_mlcc_murata` conversion and worth keeping for every library added
after it.

## 2. Type codes

### Capacitors (`cap_`)

| Code | Meaning | Leading vendors |
|---|---|---|
| `mlcc` | General ceramic MLCC (X7R/X5R/C0G) | Murata, Samsung Electro-Mechanics, TDK, Yageo |
| `rfmw` | High-Q RF/microwave ceramic | Kyocera AVX (Accu-P/ATC), Johanson, Presidio |
| `alel` | Aluminum electrolytic | Nichicon, Panasonic, Vishay, Chemi-Con |
| `alpoly` | Aluminum polymer | Panasonic (SP-Cap), Nichicon, Rubycon |
| `ta` | Tantalum (solid) | KEMET, Kyocera AVX, Vishay |
| `tapoly` | Tantalum polymer | Panasonic (POSCAP), KEMET (KO-CAP), Kyocera AVX |
| `film` | Film (PP/PET) | WIMA, KEMET, Vishay, Panasonic |
| `xy` | X/Y safety-rated | KEMET, Vishay |
| `edlc` | Supercapacitor | Panasonic, Eaton, Kyocera AVX, CAP-XX |
| `nbo` | Niobium oxide | Kyocera AVX (OxiCap) |

Example: `cap_alel_nichicon.kicad_dbl`, `cap_ta_kemet.kicad_dbl`.
`cap_murata` has been renamed to `cap_mlcc_murata` to match this scheme —
it's now the reference example the rest of this document points to.

### Resistors (`res_`)

| Code | Meaning | Leading vendors |
|---|---|---|
| `chip` | General-purpose thick-film chip resistor | Vishay (Dale), Yageo, Panasonic, KOA Speer |
| `thin` | Thin-film precision (low TCR, tight tolerance) | Susumu, Vishay Foil Resistors |
| `sense` | Current-sense / shunt (low-ohm, 4-terminal Kelvin) | Vishay (WSL), Susumu (KRL), Bourns |
| `power` | Power / wirewound | Vishay, Ohmite |
| `array` | Resistor networks / arrays | Bourns, Vishay, Panasonic |

Example: `res_chip_vishay.kicad_dbl` (the natural next step for converting
`vishay_resistors.lib`), `res_sense_vishay.kicad_dbl`.

### Inductors (`ind_`)

| Code | Meaning | Leading vendors |
|---|---|---|
| `power` | Shielded/unshielded power inductor (DC-DC) | Vishay (IHLP), Coilcraft, Murata, TDK, Würth Elektronik |
| `rf` | Wirewound/multilayer high-Q RF inductor | Coilcraft, Murata (LQG/LQW), Johanson |
| `cmc` | Common-mode choke | Würth Elektronik, TDK, Murata |
| `coupled` | Coupled inductor (SEPIC, multi-output) | Coilcraft, Würth Elektronik |

Example: `ind_power_vishay_ihlp.kicad_dbl` (replaces
`vishay_IHLP_inductors.lib`), `ind_rf_murata_lqg15hn.kicad_dbl` (replaces
`Murata_LQG15HN_inductors.lib`).

### Ferrite beads (`bead_`)

| Code | Meaning | Leading vendors |
|---|---|---|
| `emi` | Signal-line EMI suppression bead | Murata (BLM), TDK, Würth Elektronik (WE-CBF) |
| `power` | Power-line bead (higher current, DC bias) | Murata, TDK, Würth Elektronik |

Example: `bead_emi_murata_blm.kicad_dbl` (replaces `beads_BLM.lib`).

## 3. Internal database structure

Inside a `.kicad_dbl`, follow the pattern already used in
`cap_mlcc_murata.kicad_dbl`:

- **`libraries[].table`** — the SQLite table name, matching the file's full
  stem exactly: e.g. `cap_mlcc_murata`, `res_chip_vishay`,
  `ind_power_vishay_ihlp`.
- **`libraries[].name`** — the label shown in the KiCad symbol chooser: a
  short series or type name, e.g. `"MLCC"`, `"IHLP"`, `"BLM"`. When a file
  covers more than one series (multiple `libraries[]` entries), suffix the
  table name per series (`res_chip_vishay_wsl`, `res_chip_vishay_wcr`) so
  each stays unique, and use the series name for `name` in that case.

One `.kicad_dbl`/`.db` pair per vendor+type combination, with one
`libraries[]` entry per series within it. This keeps the file count bounded
(one file per `res_chip_vishay`, not one per Vishay chip-resistor sub-series)
while still letting KiCad show each series as a distinct chooser entry.

## 4. Part ID convention

The existing `import_cap_mlcc_murata.py` already establishes a good pattern
for capacitor IDs — case size, value using a letter-as-decimal-point notation
(`2u2` = 2.2 µF, avoiding a literal `.` in identifiers), then the
distinguishing electrical parameters. Extending that same idea to the other
three families:

| Component | Pattern | Example |
|---|---|---|
| Capacitor | `C<case>_<value>_<voltage>V_<dielectric>_<tolerance>` | `C0603_100n_25V_X7R_10` |
| Resistor | `R<case>_<value>_<tolerance>_<power>` | `R0402_4k7_1_63mW` |
| Inductor | `L<case>_<value>_<tolerance>_<current>` | `L0603_2u2_20_1A2` |
| Ferrite bead | `FB<case>_<impedance>_<current>` | `FB0603_600R_3A` |

Notes:

- Resistor/inductor values use the same IEC-60062-style unit-as-decimal-point
  notation as capacitors: `4k7` (4.7 kΩ), `10R0` (10.0 Ω), `1M2` (1.2 MΩ),
  `2u2` (2.2 µH), `10n0` (10.0 nH).
- Avoid `%`, `±`, and spaces in the ID itself — strip them the same way
  `import_cap_mlcc_murata.py` already strips `±` from tolerance. Tolerance appears as a
  bare number (`1`, `5`, `20`) since context makes the unit obvious; put the
  fully-formatted value (with `%`, `V`, units) in the `Description` field
  instead, same as the existing capacitor import does.
- Ferrite bead impedance is conventionally specified at 100 MHz unless noted
  otherwise — if a part's rated impedance uses a different reference
  frequency, say so in `Description` rather than encoding it in the ID.
- Fields that don't need to be part of the identifier (Q factor, SRF, DCR,
  saturation vs. rms current, etc.) belong as additional database columns
  with `visible_in_chooser` set as appropriate, the same way `cap_mlcc_murata`
  surfaces Voltage/Dielectric/Manufacturer/Part Number without cramming them
  all into the ID.

## 5. Footprints

Where a KiCad official footprint of the right size already exists
(`Resistor_SMD:R_0402_1005Metric`, `Inductor_SMD:L_0603_1608Metric`, etc.),
point new database-library entries at it directly rather than duplicating it
into `footprints.pretty` — this is already how `import_cap_mlcc_murata.py`
links capacitors to `Capacitor_SMD:C_0603_1608Metric`. Reserve `footprints.pretty`
for footprints that don't have an official KiCad equivalent (vendor-specific
packages, connectors, mechanical parts). This also sidesteps the
`L0402`/`L_0402`-style duplicate-footprint issue found in the earlier
library review — new parts shouldn't need a custom footprint for a standard
EIA case size at all.

## 6. Migration map (existing legacy libraries → new scheme)

| Current file | New name (when converted to a database library) |
|---|---|
| `capacitors_murata_GRM.lib` | superseded by `cap_mlcc_murata.kicad_dbl` (done) |
| `nichicon_polymer_cap.lib` | `cap_alpoly_nichicon` |
| `vishay_resistors.lib` | `res_chip_vishay` |
| `resistors_misc.lib` (6 symbols) | stays hand-maintained; rename to `res_misc.lib` for casing consistency only |
| `Murata_LQG15HN_inductors.lib` | `ind_rf_murata_lqg15hn` |
| `vishay_IHLP_inductors.lib` | `ind_power_vishay_ihlp` |
| `misc_inductors.lib` (5 symbols) | stays hand-maintained; rename to `ind_misc.lib` for casing consistency only |
| `beads_BLM.lib` | `bead_emi_murata_blm` |

Small hand-maintained libraries aren't worth converting to database libraries
— the point of a `.kicad_dbl` is amortizing the cost of thousands of
near-identical parts, which doesn't apply at 5-6 symbols. Renaming those for
casing consistency is optional cleanup, not a functional requirement.
