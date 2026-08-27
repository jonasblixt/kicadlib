---
name: kicad-db-library-import
description: Converts a vendor part-number CSV (Digikey export, manufacturer product-table export, or hand-built spreadsheet) into a KiCad database library for Jonas's kicadlib repo (C:\Users\jonas\work\kicadlib on the archimedes device). Produces a scripting/import_NAME.py script, a library/NAME.db SQLite file, and a library/NAME.kicad_dbl definition, following the repo's established conventions for field layout, duplicate-part handling, and footprint mapping. Use this whenever Jonas asks to "build a library," "import a CSV," "convert this into a dblibrary," "add this component library," or names a data/*.csv file in kicadlib and wants it turned into something KiCad can place parts from — even if he doesn't use the word "skill" or spell out the conventions, since the whole point of this skill is that the conventions are already known. Also use it when extending an existing library with more CSVs (e.g. more case sizes or a second vendor series) rather than starting fresh with the general-purpose CSV/database tools.
---

# KiCad Database Library Import

Jonas maintains a personal KiCad component library repo (`kicadlib`, reached
via the device folder `C:\Users\jonas\work\kicadlib`). Its database
libraries all follow the same shape, built up one vendor CSV at a time. This
skill captures that shape so each new library starts from the right
conventions instead of reinventing them.

## Repo layout

```
kicadlib/
  data/<library_name>.csv           source data (vendor export or hand-built)
  scripting/import_<library_name>.py  the importer that produced the library
  library/<library_name>.db           SQLite database (generated, committed anyway)
  library/<library_name>.kicad_dbl    KiCad database-library definition (generated)
  footprints/<Vendor_Series>.pretty/   custom footprints, only when no standard match exists
  footprints/<Vendor_Series>.3dshapes/ matching STEP/WRL 3D models
```

Library names follow `<type>_<subtype>_<vendor>[_<series>]`, e.g.
`cap_alel_chemicon` (aluminum electrolytic), `cap_alpoly_panasonic_oscon`
(aluminum polymer), `cap_tapoly_panasonic_poscap` (tantalum polymer),
`cap_xy_vishay_vj` (X/Y safety-rated MLCC), `cap_mlcc_murata_GRM` (plain
MLCC), `cap_film_wima_pps` (film). When building a new library, pick a name
that fits this pattern — check `data/` and `library/` for what's already
there before inventing a new type code, since a close match probably
already exists.

The importer script is always the source of truth, kept alongside the CSV
it consumes and the outputs it produces — re-running it should exactly
reproduce the `.db`/`.kicad_dbl` files. Never hand-edit the `.db` or
`.kicad_dbl` directly.

## Workflow

1. **Locate and inspect the CSV.** It usually lives in `data/` on the
   device already, or needs to be staged there first — check both. Read
   the full header row and a handful of sample rows before writing any
   parsing code; vendor exports (Digikey, manufacturer product tables) are
   inconsistent about units, comma-thousands-separators in numbers,
   compound columns (e.g. `"4.5mm ±0.3mm"`), and which of several rated-
   voltage columns are actually populated for a given part family. Don't
   guess a column's format — print a few raw values and look.

2. **Pick the field-convention style.** Two styles are in use across the
   repo, and which one applies is really a question about the part
   family, not a free choice:

   - **Ceramic/MLCC style** (`cap_mlcc_murata_GRM`, `cap_rfmw_kyocera_accu_p`,
     `cap_xy_vishay_vj`, `cap_xy_murata_ga3`): non-polarized ceramic
     capacitors. `Device:C` symbol. Value field shown normally with its
     label. Dielectric shown but not on add. No ESR/Leakage/Endurance/
     Ripple Current columns — MLCC datasheets don't carry that data.
   - **Polarized-electrolytic style** (`cap_alel_chemicon`,
     `cap_alpoly_panasonic_oscon`, `cap_tapoly_panasonic_poscap`): polarized/electrolytic-type parts
     (aluminum electrolytic, aluminum polymer, tantalum polymer). `Device:C_Polarized_US` symbol. Value field
     uses the `"${Capacitance}"` trick with `show_name:false` so only the
     resolved value shows, not the literal word "Value". Series and
     Dielectric present as real fields but hidden on the schematic. Adds
     ESR, Leakage Current, Endurance, Temp Range, and Ripple Current
     columns sourced from the vendor's own datasheet columns (leave a
     column blank across all rows if the datasheet just doesn't have it —
     that's fine, it's schema parity with sibling libraries, not a bug).

   Infer the style from the part type: if it's a polarized/electrolytic
   part (anything with a + terminal, ESR/ripple-current specs, or "polymer"
   /electrolytic" in its name), use the electrolytic style. If it's a
   non-polarized ceramic/film-chip/safety-rated MLCC, use the ceramic
   style. If genuinely unclear — a part family that doesn't obviously fit
   either bucket — ask before building rather than guessing, since the
   field schema is baked into the whole library and awkward to change
   later.

   Read `references/field_styles.md` for the exact field-definition
   lists to reuse.

3. **Design the duplicate-part id.** Vendor exports are usually one row
   per orderable SKU, not one row per distinct electrical part — many
   rows differ only by a packaging/taping suffix on the part number
   (`VJ2008A100JXUSTX1` vs `VJ2008A100JXUSTX1A`) and are otherwise
   identical. Build a semantic id string from every field that could
   actually distinguish two electrically-different parts (case size,
   capacitance, voltage, dielectric, tolerance, and — critically — any
   grade/spec field the datasheet varies independently, like ESR grade or
   safety rating), track a `seen_ids` dict, and skip + warn on collision.

   **The one thing that has bitten this before**: it's tempting to build
   the id from the "obvious" fields (case/cap/voltage/tolerance) and call
   it done. On the POSCAP import, that scheme caused 114 of 266 parts to
   look like duplicates when they were actually distinct ESR-grade
   variants — the id just didn't include ESR. Before trusting a high
   collision rate (say, more than ~5-10% of rows), pick a few colliding
   pairs and diff their *entire* row, not just the fields already in the
   id — if anything else differs, that field belongs in the id too. A
   genuinely low, spot-checked collision rate (packaging suffixes only)
   is normal and fine to skip silently with a warning.

4. **Map case sizes to footprints.** Check KiCad's own standard footprint
   libraries first (`Capacitor_SMD.pretty` for ceramic/electrolytic SMD,
   `Capacitor_Tantalum_SMD.pretty` for tantalum EIA cases) for an exact or
   near-exact dimensional match. A deviation under ~0.3mm is small enough
   to substitute without asking — just document the substitution and the
   reasoning in a code comment. A larger deviation, an ambiguous case, or
   anything affecting a meaningful fraction of the dataset (rule of thumb:
   >25%) is worth a quick check-in before building, since footprint
   choice is hard to silently correct later. Building an all-new custom
   footprint + 3D model from scratch is its own significant effort (land-
   pattern derivation, STEP/WRL authoring) and outside what this skill
   covers directly — if no standard footprint fits at all, surface that
   to Jonas and ask how he wants to handle it (accept a nearest-neighbor
   substitution, drop those rows, or take on building a custom footprint
   as a separate, explicit task).

5. **Write the importer script.** Start from
   `scripts/import_template.py`, which has the boilerplate every importer
   in this repo shares: `TABLE_NAME_RE` validation, the `write_database`/
   `write_kicad_dbl` pair, the `seen_ids` dedup skeleton, and the argparse
   interface (`--csv` (accepts multiple, for multi-file series),
   `--db`, `--table`, `--kicad-dbl`). Fill in the CSV-specific parsing:
   column names, unit/format normalization functions, the id string
   format, and `build_field_defs()` for whichever style applies. Give the
   script a comment block at the top explaining the source data, the
   style choice and why, the footprint mapping and any substitutions, and
   any dedup subtlety — future re-reads of this script (by Jonas or by a
   future instance of this skill extending the same library) rely on that
   context being there, since the reasoning isn't otherwise recoverable
   from the code alone.

6. **Run it, then validate before delivering.** Sanity-check row count
   against the source CSV (does the skip count make sense?), confirm
   `SELECT COUNT(DISTINCT id)` matches the row count, print the distinct
   footprints used and check each maps to a real, existing footprint
   library entry, and spot-check a handful of rows for plausible values.

7. **Deliver and commit.** Send the generated `scripting/import_<name>.py`,
   `library/<name>.db`, and `library/<name>.kicad_dbl` (plus any new
   footprint files) with `SendUserFile`, then write them into the
   matching paths under `C:\Users\jonas\work\kicadlib\` with
   `device_commit_files`. Tell Jonas the final part count, which
   footprints got used, and flag anything he should double check (a
   footprint substitution, a non-trivial dedup skip count, or a field-
   style call that wasn't obvious).

## Reference

- `references/field_styles.md` — the exact field-definition arrays for
  both styles (ceramic-MLCC and polarized-electrolytic), copy-pasteable
  into `build_field_defs()`.
- `scripts/import_template.py` — the shared importer skeleton described
  in step 5 above.
