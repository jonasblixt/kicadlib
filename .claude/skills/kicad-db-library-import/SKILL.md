---
name: kicad-db-library-import
description: Converts a vendor part-number CSV (Digikey export, manufacturer product-table export, or hand-built spreadsheet) into a KiCad database library for Jonas's kicadlib repo (C:\Users\jonas\work\kicadlib on the archimedes device). Produces a scripting/import_NAME.py script, a library/NAME.db SQLite file, and a library/NAME.kicad_dbl definition, following the repo's established conventions for field layout, duplicate-part handling, and footprint mapping. Use this whenever Jonas asks to "build a library," "import a CSV," "convert this into a dblibrary," "add this component library," or names a data/*.csv file in kicadlib and wants it turned into something KiCad can place parts from — even if he doesn't use the word "skill" or spell out the conventions, since the whole point of this skill is that the conventions are already known. Also use it when extending an existing library with more CSVs (e.g. more case sizes or a second vendor series) rather than starting fresh with the general-purpose CSV/database tools.
---

# KiCad Database Library Import

Jonas maintains a personal KiCad component library repo (`kicadlib`, at
`C:\Users\jonas\work\kicadlib`). Its database libraries all follow the same
shape, built up one vendor CSV at a time. This skill captures that shape so
each new library starts from the right conventions instead of reinventing
them. `NAMING.md` in the repo is the naming reference (type codes, id
patterns, chooser names); read it before naming anything.

## Repo layout

```
kicadlib/
  data/<library_name>.csv             source data (vendor export or hand-built; _1.csv, _2.csv, ... if several)
  scripting/import_<library_name>.py  the importer that produced the library
  library/<library_name>.db           SQLite database (generated, committed anyway)
  library/<library_name>.kicad_dbl    KiCad database-library definition (generated)
  footprints/Jonas.pretty/            custom footprints (nickname "Jonas"), only when no stock match exists
  footprints/Jonas.3dshapes/          their 3D models, <footprint>.step
```

Library names follow `<type>_<subtype>_<vendor>[_<series>]`, lowercase,
e.g. `cap_alel_chemicon` (aluminum electrolytic), `cap_alpoly_panasonic_oscon`
(aluminum polymer), `cap_tapoly_panasonic_poscap` (tantalum polymer),
`cap_xy_murata_ga3` (X/Y safety-rated MLCC), `cap_mlcc_murata_grm` (plain
MLCC), `cap_film_panasonic_echux` (film chip), `ind_rfmw_murata_lqw15an`
(RF inductor, one series). Check `NAMING.md` §2 and `library/` before
inventing a new type code; a close match probably already exists. One
`.kicad_dbl` per library, with exactly one `libraries[]` entry and one
importer.

The importer script is always the source of truth, kept alongside the CSV
it consumes and the outputs it produces — re-running it must exactly
reproduce the `.db`/`.kicad_dbl` files (`scripting/check_importers.py`
verifies every library). Never hand-edit the `.db` or `.kicad_dbl`.

## Workflow

1. **Locate and inspect the CSV.** It usually lives in `data/` already, or
   needs to be staged there first — check both, and name it after the
   library. Read the full header row and a handful of sample rows before
   writing any parsing code; vendor exports (Digikey, manufacturer product
   tables) are inconsistent about units, comma-thousands-separators in
   numbers, compound columns (e.g. `"4.5mm ±0.3mm"`), and which of several
   rated-voltage columns are actually populated for a given part family.
   Don't guess a column's format — print a few raw values and look. Also
   check the product class columns: a file named "choke" turned out to be
   RF inductors (LQW2UAS).

2. **Reuse before writing.** If the new series is a sibling of an existing
   library, extend the shared module instead of copying an importer:
   `scripting/murata_lqw.py` (Murata LQW inductors, one thin
   `import_<library>.py` per series), `scripting/murata_cap.py` (Murata
   MLCC product tables: GRM, GQM). A new series then costs a footprint-map
   entry and a five-line importer.

3. **Pick the field-convention style.** Two styles are in use, and which
   one applies is a question about the part family, not a free choice:

   - **Ceramic/MLCC style** (`cap_mlcc_murata_grm`, `cap_rfmw_murata_gqm`,
     `cap_rfmw_kyocera_accup`, `cap_xy_murata_ga3`): non-polarized ceramic
     capacitors. `Device:C` symbol. Value field is `"${Capacitance}"`.
     Dielectric shown but not on add. No ESR/Leakage/Endurance/Ripple
     Current columns — MLCC datasheets don't carry that data.
   - **Polarized-electrolytic style** (`cap_alel_chemicon`,
     `cap_alpoly_panasonic_oscon`, `cap_tapoly_panasonic_poscap`):
     aluminum electrolytic, aluminum polymer, tantalum polymer.
     `Device:C_Polarized_US` symbol. Value field shows only the resolved
     value (`show_name: false`). Series and Dielectric present but hidden.
     Adds ESR, Leakage Current, Endurance, Temp Range and Ripple Current
     from the vendor's own columns (leave a column blank across all rows if
     the datasheet doesn't have it — schema parity, not a bug).
   - Film chip (`cap_film_panasonic_echux`) is the hybrid: the
     electrolytic-style ESR/Endurance columns, but `Device:C` and no
     Series field. Other families have their own established layouts —
     inductors (`murata_lqw.py`, `import_ind_power_vishay_ihlp.py`),
     resistors (`import_res_chip_vishay_crcw.py`), beads, fuses, crystals,
     TVS — copy the closest sibling.

   If genuinely unclear — a part family that doesn't obviously fit — ask
   before building, since the field schema is baked into the whole library.
   Read `references/field_styles.md` for the exact field-definition lists.

4. **Design the duplicate-part id.** Vendor exports are usually one row
   per orderable SKU, not one row per distinct electrical part — many rows
   differ only by a packaging/taping suffix (or, for MLCCs, thickness).
   Build a semantic id from every field that could distinguish two
   electrically-different parts, following `NAMING.md` §4 (IEC-60062
   values like `2u2`, `4k7`, `0p15`), track a `seen_ids` dict, and skip +
   warn on collision.

   **The one thing that has bitten this before**: building the id from
   the "obvious" fields only. On the POSCAP import, that made 114 of 266
   parts look like duplicates when they were distinct ESR-grade variants.
   On Accu-P, formatting values to 0.1 pF silently merged the 0.05 pF
   steps and showed wrong values. Before trusting a collision rate above
   ~5-10%, diff a few colliding pairs' *entire* rows — and check every
   formatted value against the raw CSV value. A low, spot-checked rate
   (packaging/thickness only) is normal; print a warning per collision.

5. **Map case sizes to footprints.** Check KiCad's stock libraries first
   (`Capacitor_SMD`, `Capacitor_Tantalum_SMD`, `Inductor_SMD`, ...)
   against the **vendor's recommended land pattern**, not just the case
   code: Murata's LQW lands matched `L_Coilcraft_0805HQ/1008HQ` exactly,
   where the generic `L_0805`/`L_1008` were 0.33-0.35 mm off. A stock
   footprint with another vendor's name is fine. A deviation under ~0.3 mm
   may be substituted without asking — document it in the importer header.
   A larger deviation, an ambiguous case, or anything affecting a
   meaningful fraction of the dataset (>25%) is worth a check-in. A new
   custom footprint goes into `footprints/Jonas.pretty` (`Vendor_Part` or
   KiCad-stock-style name, `NAMING.md` §5) with a B-Rep model in
   `Jonas.3dshapes/<footprint>.step` (vendor STEP first, otherwise generated
   B-Rep, never hand-written CSG: `references/step_brep_authoring.md`), and
   it must be added
   to the F8 manual-review list in `docs/review-2026-10-footprints.md`.
   That is its own task: surface it to Jonas rather than folding it into
   the import.

6. **Write the importer script.** Start from `scripts/import_template.py`
   (table-name validation, `write_database`/`write_kicad_dbl`, the
   `seen_ids` dedup skeleton, and arguments that default to the repo
   paths, so `python scripting/import_<library>.py` regenerates the
   library with no arguments). Fill in the CSV parsing, the id format and
   `build_field_defs()`. Choose the chooser name (`libraries[].name`)
   carefully: it is the series name (`GRM`, `LQW15AN`), the family name for
   a multi-series library (`IHLP`, `NX`, `SMAJ-SMCJ`), or the vendor if
   there is none (`Chemi-Con`). Schematics store parts as
   `<library>:<chooser>/<id>`, so renaming the library, the chooser name or
   the id format later breaks every project that uses it. Give the script
   a header comment explaining the source data, the style choice and why,
   the footprint mapping and any substitutions, and any dedup subtlety —
   the reasoning isn't recoverable from the code alone.

7. **Run it, then validate before delivering.** Sanity-check row count
   against the source CSV, confirm `SELECT COUNT(DISTINCT id)` matches the
   row count, check each distinct footprint exists, spot-check a handful
   of rows, then run `python scripting/check_importers.py <library>` (on a
   new library it fails only because HEAD has no copy yet) and
   `python scripting/audit_refs.py`. If KiCad is open it holds the `.db`
   files: importers must drop tables, not delete the file, and never
   `git commit -a` (it sweeps in .db files a re-run touched).

8. **Register, deliver and commit.** Add the library to the global
   `sym-lib-table` (`%APPDATA%\kicad\10.0\sym-lib-table`, type `Database`,
   `${JONAS_KICADLIB}/library/<name>.kicad_dbl`) and to the README's
   database list. In a local Claude Code session, commit importer, CSV,
   `.db` and `.kicad_dbl` together (one commit per library, no Claude
   co-author line). In a Cowork session, send the files with
   `SendUserFile`, then write them into the matching paths with
   `device_commit_files`. Tell Jonas the part count, which footprints got
   used, and anything he should double check (a footprint substitution, a
   non-trivial dedup skip count, a field-style call that wasn't obvious).

## Reference

- `references/field_styles.md` — the exact field-definition arrays for
  both styles, copy-pasteable into `build_field_defs()`.
- `references/step_brep_authoring.md` — how to make and validate a 3D model
  for a custom footprint.
- `scripts/import_template.py` — the shared importer skeleton.
- Repo: `NAMING.md` (names, ids), `scripting/check_importers.py`,
  `scripting/audit_refs.py`, `docs/review-*.md` (open actions).
