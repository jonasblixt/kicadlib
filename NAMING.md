# kicadlib naming reference

The detailed reference behind the README's *Naming* section: how database
libraries, their tables and part ids are named, and why. Rewritten
2026-10-19 (cleanup review A5.2); the earlier version described the
KiCad-5 `.lib` conversion, which is finished.

Hand-maintained symbol libraries (`library/*.kicad_sym`) are grouped by
function and take a short lowercase name (`dcdc`, `comm`, `memory`). They
are out of scope here; renames for the few that don't fit (`LEDs`,
`Audio Amp`, ...) are proposed in `docs/review-2026-10-cleanup.md` (A5.1).

## 1. Database library names

```
<type>_<subtype>_<vendor>[_<series>]   ->  library/<name>.kicad_dbl + library/<name>.db
```

- Lowercase, underscore-separated. `<vendor>` is a short slug: `murata`,
  `vishay`, `panasonic`, `koaspeer`, `chemicon`, `kyocera`, `bel`, ...
- **One `.kicad_dbl` per library, with exactly one `libraries[]` entry and
  one importer.** A library is normally one vendor series
  (`ind_rfmw_murata_lqw15an`). Closely related series that share fields and
  footprint style may share a library (`ind_rfmw_murata_lqg` = LQG15H +
  LQG18H, `ind_power_vishay_ihlp` = four case sizes, `xtal_epson`), but one
  file never carries several `libraries[]` entries: in KiCad's chooser they
  would show up as look-alike sub-libraries (the old merged LQW libraries,
  split by A4.3).
- Add `_<series>` when the vendor has more than one product line of that
  type in the repo, or is likely to; omit it for a vendor's only line.
- The importer is `scripting/import_<name>.py`; its source data is
  `data/<name>.csv`, or `data/<name>_1.csv`, `_2.csv`, ... when the vendor
  export comes in several files.

Names that don't follow this yet, renamed together with A5.1 so projects
remap once: `cap_mlcc_murata_GRM` (upper-case series),
`diode_tvs_littlefuse` (vendor spelling: Littelfuse) and
`cap_rfmw_kyocera_accu_p` (series slug `accup`, as its importer).

## 2. Type and subtype codes

`*` = in use in this repo.

| Type | Subtype | Meaning |
|---|---|---|
| `cap` | `mlcc`\* | general ceramic MLCC (X7R/X5R/C0G) |
| | `rfmw`\* | high-Q RF/microwave ceramic or thin film (GQM, Accu-P) |
| | `alel`\* | aluminum electrolytic |
| | `alpoly`\* | aluminum polymer (OS-CON, SP-Cap) |
| | `ta` | solid tantalum (MnO2) |
| | `tapoly`\* | tantalum polymer (POSCAP, KO-CAP) |
| | `film`\* | film, including film chip (ECHU) |
| | `xy`\* | X/Y safety-rated |
| | `edlc` | supercapacitor |
| `res` | `chip`\* | general thick-film chip |
| | `thin` | thin-film precision |
| | `sense`\* | current sense / shunt |
| | `pulse`\* | pulse- and surge-withstanding |
| | `power` | power / wirewound |
| | `array` | networks and arrays |
| `ind` | `power`\* | power inductor (DC-DC) |
| | `rfmw`\* | high-Q RF inductor, wire-wound or multilayer (not `rf`: the code is shared with `cap_rfmw`) |
| | `choke`\* | single-winding filter / power-line choke (ferrite LQW_C) |
| | `cmc`\* | common-mode choke |
| | `coupled` | coupled inductor |
| `bead` | `emi`\* | signal-line EMI bead |
| | `power` | power-line bead |
| `diode` | `tvs`\* | TVS protection diode |
| `fuse` | `pptc`\* | resettable PPTC fuse |
| `xtal` | (none)\* | quartz crystal: `xtal_<vendor>`. If oscillators or a second crystal style arrive, use `xtal_smd_<vendor>` / `osc_tcxo_<vendor>` |

Check this table (and `library/`) before inventing a new code.

## 3. Inside the `.kicad_dbl`

- `libraries[].table`: the SQLite table, equal to the library name.
- `libraries[].name`: the label in KiCad's symbol chooser, the series name
  (`GRM`, `LQW15AN`, `IHLP`). Older libraries still use type or vendor
  names (`AlEl`, `TVS`, `Epson`, `NDK`, A4.4).
- `key` is the `id` column; `symbols` / `footprints` name the `Symbol` and
  `Footprints` columns; `properties.description` points at `Description`.
- Field definitions follow one of two styles (ceramic or
  polarized-electrolytic); the lists live in the `kicad-db-library-import`
  skill.

**A schematic stores a database part as `<nickname>:<chooser name>/<id>`**
(e.g. `cap_mlcc_murata_GRM:GRM/C0402_1u_10V_X7R_10%`). Renaming a library,
its chooser name, or the id format therefore breaks *Update Symbols from
Library* in every project that uses it, until the project's symbols are
remapped. Do such renames in planned batches and list the affected
projects.

## 4. Part ids

The id is the part's identity in the library and in schematics. Build it
from every field that tells two electrically different parts apart, using
IEC-60062-style values where the unit letter is the decimal point (`2u2`,
`4k7`, `10n0`, `0R05`):

| Family | Pattern | Example |
|---|---|---|
| Capacitor | `C<case>_<value>_<voltage>V_<dielectric/series>_<tolerance>`, plus grade segments where the series needs them | `C0603_100p_16V_PPS_2`, `CB1S_150u_6.3V_TPS_30mOhm_20`, `C1808_100p_250VAC_X7R_10_X1+Y2` |
| Resistor | `R<case>_<value>_<tolerance>_<power>` | `R0402_100k0_1_63mW` |
| Inductor | `L<case>_<value>_<tolerance>_<current>` | `L0402_10n0_2_1A4` |
| Bead | `FB<case>_<impedance>_<current>` | `FB0603_1000R_1A2` |
| Fuse | `F<case>_<hold current>_<voltage>` | `F1206_100m_60V` |
| Crystal, TVS | the MPN (or its base) | `NX1255GB-10.000000MHZ`, `SMAJ100A` |

- `<case>` is the EIA code for chips, `<D>x<L>` for radial cans, or the
  vendor case code (`B1S`).
- Tolerance is a bare number (`1`, `5`, `20`) in new libraries. The older
  capacitor libraries (GRM, GQM, Accu-P) keep the tolerance text from the
  CSV, units and all (`10%`, `0.05pF`, `±0.01 pF`); since ids are part of
  every schematic reference, they are not rewritten after the fact.
- Grade fields the vendor varies independently belong in the id: ESR
  (POSCAP), safety class (`X1+Y2`), voltage class. A high duplicate rate
  usually means such a field is missing; diff a few colliding rows in full.
- Packaging and thickness variants of one electrical part may share an id;
  the importer keeps one row and prints a warning for each collision.
- Fields that don't identify the part (SRF, DCR, ESR where it isn't a
  grade, temperature range) are columns, not id segments.

## 5. Footprints and 3D models

- Stock KiCad footprints first, even when they carry another vendor's name,
  if the land pattern matches the data sheet.
- Custom footprints live in the single library `footprints/Jonas.pretty`
  (nickname `Jonas`). Part-specific ones are `Vendor_Part`
  (`JAE_MX34R36HF4T`); IC packages are vendor, vendor package code, then
  KiCad-style dimensions (`Texas_RNL0022B_VQFN-HR-22_4x5mm_P0.5mm`);
  generated passive families follow the stock pattern
  (`C_Panasonic_ECHU_D1_6041Metric_H1.90mm`).
- The 3D model is `footprints/Jonas.3dshapes/<footprint>.step` (`.wrl` only
  where no STEP exists), referenced through `${JONAS_KICADLIB}`. A model is
  shared only when bodies are identical (`IHLP1212.step`).
- Database rows reference footprints with their nickname
  (`Inductor_SMD:L_0402_1005Metric`, `Jonas:DLW5B_5050`), never a bare name.
