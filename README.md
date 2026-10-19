# kicadlib

Jonas Blixt's personal KiCad component library (KiCad 10). It holds the
schematic symbols, footprints and 3D models used across my projects. All of
it is built around one rule: **every part placed from this library comes
with a footprint that has been checked against the manufacturer's data
sheet.**

The library has two halves:

- **Hand-maintained symbol libraries** (`library/*.kicad_sym`), grouped by
  function: `dcdc`, `comm`, `conn`, and so on. About 230 symbols, one
  per real part.
- **Database libraries** (`library/*.kicad_dbl` + `*.db`), generated from
  vendor part tables. They cover whole passive families, from MLCCs to
  crystals: about 11,700 orderable parts in 28 libraries.

Footprints come from KiCad's stock libraries wherever one really fits. The
rest live in one custom library, `footprints/Jonas.pretty`, with a 3D model
for each in `footprints/Jonas.3dshapes`.

## Setup

1. Set the environment variable **`JONAS_KICADLIB`** to the repo root, either
   in KiCad's *Preferences → Configure Paths* or system-wide. Symbol library
   paths and every custom 3D model path go through it.
2. Install the **SQLite3 ODBC driver** (`SQLite3 ODBC Driver`, from
   ch-werner.de). The database libraries connect through it. Each
   `.kicad_dbl` finds its `.db` next to itself via `${CWD}`.
3. Add the symbol libraries to the global **sym-lib-table**, one entry per
   file, named after the file stem:
   - `.kicad_sym` files with type `KiCad`, e.g.
     `${JONAS_KICADLIB}/library/dcdc.kicad_sym`
   - `.kicad_dbl` files with type `Database`, e.g.
     `${JONAS_KICADLIB}/library/cap_mlcc_murata_grm.kicad_dbl`
4. Add the footprint library to the global **fp-lib-table** under the
   nickname **`Jonas`**: `${JONAS_KICADLIB}/footprints/Jonas.pretty`. Symbols
   refer to it as `Jonas:<footprint>`, so the nickname must be exactly that.

Stock footprints and models resolve through KiCad's own
`${KICAD10_3DMODEL_DIR}` and stock library tables. Nothing else needs
configuring.

## Layout

```
kicadlib/
  library/        symbol libraries: *.kicad_sym (hand-maintained) and
                  *.kicad_dbl + *.db (database libraries, generated)
  footprints/
    Jonas.pretty/     custom footprints (nickname "Jonas")
    Jonas.3dshapes/   one 3D model per custom footprint, same base name
  data/           source tables for the database libraries (vendor CSV exports)
  scripting/      importers and generators (see below)
  docs/           review docs: audits with numbered action lists
  NAMING.md       detailed naming reference for the database libraries
  CLAUDE.md       working notes for Claude sessions in this repo
```

### `scripting/`

| Script | What it does |
|---|---|
| `import_<library>.py` | Builds `library/<library>.db` and `.kicad_dbl` from `data/<library>*.csv`. One per database library; shared helpers in `murata_cap.py` and `murata_lqw.py`. |
| `check_importers.py` | Re-runs every importer into a temp directory and checks it reproduces the committed library. |
| `audit_refs.py` | Checks symbol footprint links, database footprints, 3D model paths and symbol pins vs footprint pads. |
| `render_footprints.py` | Renders every `Jonas.pretty` footprint with its 3D model into an HTML contact sheet (needs KiCad's Python). |
| `gen_ihlp_footprints.py` | Generates the Vishay IHLP power inductor footprints. |
| `gen_ndk_footprints.py` | Generates the NDK crystal footprints. |
| `gen_package_models.py` | Generates 3D models for custom footprints that have no vendor model. |
| `step_brep_box.py` | Writes STEP files as proper B-Rep solids (used by the generator above). |
| `digikey-export.py` | Pulls a manufacturer/series from the Digi-Key Product Information API (v4) into a CSV for `data/`. |

### `docs/`

`docs/review-*.md` are audits of the repo, each with a numbered action list
(`A2.3`, `F7.5`, ...) that gets ticked off with commit hashes as the work
lands. `review-2026-10-footprints.md` also holds **F8**, the manual-review
list. Every footprint and 3D model that was created rather than copied is
listed there, as is every 3D model placement. Each entry stays open until it
has been checked in KiCad.

## Symbol libraries

### Hand-maintained (`*.kicad_sym`)

Grouped by what the part does, not by who makes it:

| Library | Contents |
|---|---|
| `cpu` | Processors, MCUs, SoCs |
| `memory` | Flash, RAM, EEPROM |
| `dcdc` | Switching regulators, PMICs, power modules |
| `power` | Schematic helpers: power flags (`GND`, `PxVx`, `NxVx`, `PWR_FLAG`), `BOM_Entry`, `TP` |
| `power_mgmt` | Supervisors, power monitors, gas gauges, LDOs, references |
| `protection` | Fuses, eFuses, hot-swap, ideal-diode and overvoltage controllers |
| `comm` | Radios, modules, antennas, RF parts, transceivers |
| `interface` | PHYs, level shifters, optical links, bus interfaces |
| `logic` | Logic gates, buffers, translators |
| `analog` | Converters, audio amplifiers, sensors |
| `driver` | Motor and relay drivers |
| `transistor` | Discrete transistors, optocouplers, solid-state relays |
| `diode_misc` | Diodes not covered by a database library |
| `led` | LEDs and LED drivers |
| `conn` | Connectors, card sockets, headers |
| `switch` | Switches |
| `cap_misc`, `ind_misc`, `res_misc` | One-off passives outside the database libraries |

Every symbol's **Footprint** field names its footprint with a library
nickname: a stock library (`Package_DFN_QFN:...`) or `Jonas:...`, never a
bare name. Symbol pin numbers match the footprint's pad numbers one to one.
Purely mechanical pads (mounting tabs, hold-downs) have no symbol pin. New
footprints number them `MP`; some older ones use `0` or leave the number
empty.

### Database libraries (`*.kicad_dbl` + `*.db`)

One library per vendor series. Each row is one orderable part with its
electrical fields (value, voltage, tolerance, ...), MPN, data sheet link and
footprint. All rows share a generic symbol such as `Device:C`.

| Family | Libraries |
|---|---|
| Capacitors | `cap_mlcc_murata_grm`, `cap_rfmw_murata_gqm`, `cap_rfmw_kyocera_accup`, `cap_alel_chemicon`, `cap_alpoly_panasonic_oscon`, `cap_tapoly_panasonic_poscap`, `cap_film_panasonic_echux`, `cap_xy_murata_ga3` |
| Resistors | `res_chip_vishay_crcw`, `res_sense_koaspeer_sr73`, `res_sense_koaspeer_ur73`, `res_pulse_panasonic_erj14t` |
| Inductors | `ind_power_vishay_ihlp`, `ind_rfmw_murata_lqg`, `ind_rfmw_murata_lqw15an`, `ind_rfmw_murata_lqw15aw`, `ind_rfmw_murata_lqw18an`, `ind_rfmw_murata_lqw2bas`, `ind_rfmw_murata_lqw2uas`, `ind_choke_murata_lqw15cn`, `ind_choke_murata_lqw15dn`, `ind_choke_murata_lqw18cn`, `ind_cmc_murata_dlw5b` |
| Other | `bead_emi_murata_blm`, `diode_tvs_littelfuse`, `fuse_pptc_bel_0zcj`, `xtal_epson`, `xtal_ndk` |

**The importer is the source of truth.** Never edit a `.db` or `.kicad_dbl`
by hand. Change `scripting/import_<library>.py` (or the CSV in `data/`) and
re-run it; re-running must reproduce the committed files exactly
(`scripting/check_importers.py` checks all of them). Each
importer's header comment records the source data, the footprint mapping and
any judgement calls.

Two field layouts are in use, chosen by part type:

- **Ceramic style:** for non-polarized parts (MLCC, RF ceramic, X/Y,
  film chip).
- **Polarized-electrolytic style:** for aluminum electrolytic, aluminum
  polymer and tantalum polymer. It adds ESR, Leakage, Endurance and Ripple
  Current fields.

The exact field lists live in the `kicad-db-library-import` skill
(`.claude/skills/`).

## Footprints and 3D models

**Stock first.** If a footprint in KiCad's stock libraries matches the data
sheet's land pattern, the symbol uses it, even when it carries another
vendor's name. A custom footprint is only added to `Jonas.pretty` when no
stock footprint fits. Some of these are migrated from old, board-proven
footprints; others are drawn from the data sheet.

Custom footprints follow the KiCad Library Conventions (KLC):

- courtyard 0.25 mm around body and pads (0.5 mm for connectors, 1.0 mm for
  BGAs), on a 0.01 mm grid
- F.Fab body outline with a pin-1 chamfer, and `${REFERENCE}` on F.Fab
- silkscreen outside the body and clear of pads, plus a pin-1 marker
- Value = footprint name; `attr` matches the pad types

Each footprint's `descr` field records where its land pattern came from
(document, revision, page). For a footprint that was migrated, it also
records what changed.

**3D models** live in `footprints/Jonas.3dshapes/`, named exactly like their
footprint, and are referenced as
`${JONAS_KICADLIB}/footprints/Jonas.3dshapes/<footprint>.step`. The order
of preference is:

1. the vendor's STEP (or an existing model from this repo or an old project)
2. a model generated by `scripting/gen_package_models.py`

Generated models are boxes: body, terminals, a pin-1 mark, sized from the
data sheet. Assumed dimensions are marked as such in the script. They must
be real B-Rep solids written by `step_brep_box.py`. Hand-written CSG STEP
(`BLOCK`/`CSG_SOLID`) is valid STEP, but KiCad silently fails to load it.

## Naming

The rules are meant to answer one question: *can I find the part from what
it is, and tell from the name where it came from?*

**Symbol libraries.** Hand-maintained libraries take a short, lowercase
function name (`dcdc`, `comm`); the one-off passives are `cap_misc`,
`ind_misc`, `res_misc`.

**Database libraries** follow `<type>_<subtype>_<vendor>[_<series>]`,
lowercase and underscore-separated.

| Part | Type | Subtypes in use |
|---|---|---|
| Capacitors | `cap` | `mlcc` (general ceramic), `rfmw` (high-Q RF/microwave), `alel` (aluminum electrolytic), `alpoly` (aluminum polymer), `tapoly` (tantalum polymer), `film`, `xy` (X/Y safety) |
| Resistors | `res` | `chip`, `sense` (current sense), `pulse` (pulse-withstanding) |
| Inductors | `ind` | `power`, `rfmw` (RF), `choke` (filter/choke), `cmc` (common-mode choke) |
| Beads, diodes, fuses | `bead`, `diode`, `fuse` | `emi`, `tvs`, `pptc` |
| Crystals | `xtal` | no subtype: `xtal_<vendor>` |

The series part is added when one vendor has several product lines of the
same type that are imported separately, e.g. `ind_rfmw_murata_lqw15an` and
`ind_rfmw_murata_lqw18an`. Before inventing a new type code, check whether
an existing one fits. The importer is `scripting/import_<library>.py`, and
the data is `data/<library>.csv` (or `_1.csv`, `_2.csv`, ... when a series
comes in several files). See `NAMING.md` for the background and the
reserved codes not yet in use; parts of it predate the 2026 rework.

**Footprints in `Jonas.pretty`** are named after the vendor first:

- **Part-specific footprints** (connectors, modules, antennas, switches):
  `Vendor_Part`, e.g. `JAE_MX34R36HF4T`, `Molex_146200`, `ublox_LARA-R2`,
  `Johanson_1575AT43A0040`. A footprint shared by a part family uses the
  family, e.g. `Molex_FAKRA_73403-51xx`, `Everlight_PLR135_PLT133`.
- **IC packages:** vendor, then the vendor's package code, then KiCad-style
  package dimensions. For example `Texas_RNL0022B_VQFN-HR-22_4x5mm_P0.5mm`,
  `onsemi_UQFN-12_1.7x2mm_P0.4mm`,
  `Microchip_LFBGA-217_15x15mm_Layout17x17_P0.8mm`.
- **Generated passive families:** the KiCad stock pattern, e.g.
  `C_Panasonic_ECHU_D1_6041Metric_H1.90mm`.

The older footprints were renamed to these rules in 2026-10 (F4.8, e.g.
`IHLP1212AB` -> `L_Vishay_IHLP-1212AB`); `docs/rename-batch-2026-10.md`
lists every old and new name.

**3D models** take the footprint's name: `Jonas.3dshapes/<footprint>.step`
(or `.wrl` where only a WRL exists).
