# kicadlib

Jonas's personal KiCad component library repo. Lives on his machine
("archimedes") and is reached from Claude sessions via the device folder
`C:\Users\jonas\work\kicadlib`.

## Layout

```
kicadlib/
  data/<library_name>.csv             source data (vendor export or hand-built)
  scripting/import_<library_name>.py  importer that produced the library
  library/<library_name>.db           SQLite database (generated)
  library/<library_name>.kicad_dbl    KiCad database-library definition (generated)
  footprints/Jonas.pretty/            custom footprints (nickname "Jonas"), only when no stock KiCad match exists
  footprints/Jonas.3dshapes/          their 3D models, <footprint>.step
  .claude/skills/                     project skills - check here before improvising a workflow
  docs/                               review docs and action lists (see below)
```

## Review docs

`docs/review-*.md` hold repo audits with numbered action lists (e.g.
`docs/review-2026-10-cleanup.md`). Don't read them by default - only when
Jonas asks for a review/cleanup/fix session or refers to an action ID like
`A2.3`. When working from one, tick off actions with the commit hash and
add newly found issues to it rather than fixing them silently.

## Database libraries

Library names follow `<type>_<subtype>_<vendor>[_<series>]`, e.g.
`cap_alel_chemicon`, `cap_tapoly_panasonic_poscap`, `cap_xy_vishay_vj`.
Check `data/` and `library/` for an existing close match before inventing a
new type code.

Each library has an importer script that is the source of truth — the
`.db` and `.kicad_dbl` files are generated output and should never be
hand-edited directly. Re-running the importer should exactly reproduce
them.

For converting a CSV into a new database library, or extending an
existing one with more CSVs, use the `kicad-db-library-import` skill
(`.claude/skills/kicad-db-library-import/`) rather than improvising the
workflow from scratch — it captures the field-convention styles, the
duplicate-part id pitfalls, and the footprint-matching decision tree
already worked out across this repo's libraries.

Two field-convention styles are in use, chosen by part type (see the
skill for the full definitions): a plain ceramic/MLCC style for
non-polarized parts, and a polarized-electrolytic style (with
ESR/Endurance/Ripple Current fields) for aluminum electrolytic, aluminum
polymer, tantalum polymer, and film-chip parts.

## Footprints and symbols

Prefer KiCad's own standard footprint libraries (`Capacitor_SMD.pretty`,
`Capacitor_Tantalum_SMD.pretty`, etc.) over building something custom.
Only add a custom footprint when no standard footprint is an acceptable
match, and then to the single library `footprints/Jonas.pretty` (named
`Vendor_Part`, see `NAMING.md` §5) with its model in
`footprints/Jonas.3dshapes/<footprint>.step`. Note the reasoning
(dimensions, source or lack of source datasheet, any interpolation used)
in both the footprint's `descr` field and the importer or generator
script's header comment - a future session re-reading either file has no
other way to recover why a decision was made.

No CAD library (cadquery, FreeCAD, pythonocc) or network access to fetch
pre-built 3D models is available in a Claude session's sandbox, and PyPI
is blocked so none can be installed either.

Custom STEP files in this repo MUST use proper B-Rep geometry via
`scripting/step_brep_box.py`, never hand-written CSG primitives (`BLOCK`,
`CSG_SOLID`) - CSG is valid STEP syntax but KiCad's STEP importer
silently fails to load it (bit Murata_GA3's footprint this way). Full
guidance, the helper's API, and validation steps live in the
`kicad-db-library-import` skill's `references/step_brep_authoring.md` -
read that before authoring or changing any `.3dshapes/*.step` file.
Nothing in this repo's custom STEP files has been visually confirmed by
Jonas in a CAD viewer - always flag that to Jonas when delivering a new or
changed one, and add it to the F8 review list in
`docs/review-2026-10-footprints.md`. Sessions running locally on
archimedes (Claude Code, not Cowork) do have KiCad 10:
`scripting/render_footprints.py` renders footprints with their models for
a first look.

## Working in this environment

This repo is reached through the device bridge from a Claude Cowork
session, not edited in place. The normal flow: stage or inspect files
from `data/` on the device, do the actual work (running scripts, building
files) in the session's own workspace, then deliver finished files with
`SendUserFile` followed by `device_commit_files` into the matching path
under `C:\Users\jonas\work\kicadlib\`.

`device_commit_files` refuses to write inside `.claude/` - that's a
deliberate guardrail, not a bug, since it's the folder Claude Code loads
instructions from automatically. Don't try to route around it without
Jonas explicitly asking for something to be placed there; when he does,
`device_bash` (a full shell on his machine) can write there directly,
e.g. via a base64-encoded heredoc to avoid quoting issues with code or
markdown content.
