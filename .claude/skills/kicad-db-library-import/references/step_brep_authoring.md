# Authoring STEP 3D models for Jonas.pretty

Read this before creating or changing any `footprints/Jonas.3dshapes/*.step`.

## Order of preference

1. **The vendor's STEP**, downloaded by Jonas or found in the repo's history
   (`git log --all -- '*.step' '*.stp'`) or his old projects. Copy it to
   `Jonas.3dshapes/<footprint>.step` and place it with offset/rotation in
   the footprint's `(model ...)` block.
2. **A generated envelope model** when no vendor model exists: body,
   terminals, pin-1 mark as boxes, sized from the data sheet. Add it to
   `scripting/gen_package_models.py` (one function or a `PLAIN_BODIES`
   entry) so it can be regenerated, and mark every dimension that is
   assumed rather than taken from a drawing.

Never hand-write STEP with CSG primitives (`BLOCK`, `CSG_SOLID`,
`BOOLEAN_RESULT`). It is valid STEP, but KiCad's OpenCASCADE importer
silently drops it (this broke `C_Murata_GA3_5.7x2.8.step` once). Models
must be B-Rep: `MANIFOLD_SOLID_BREP` inside an
`ADVANCED_BREP_SHAPE_REPRESENTATION`.

## The helper: `scripting/step_brep_box.py`

```python
from step_brep_box import write_step_boxes
write_step_boxes(path, product_name, boxes, description="")
```

- `boxes`: list of `(corner_xyz, size_xyz, rgb)`. Corner-anchored: the box
  spans `corner .. corner + size` along +X/+Y/+Z, in mm. `rgb` is 0..1
  floats (one colour per box).
- `product_name`: use the footprint name (it is embedded in the file).
- Output: one manifold B-Rep box per entry, millimetre units.

`gen_package_models.py` adds `box_c(cx, cy, z0, sx, sy, sz, rgb)` (centre in
XY, bottom at `z0`) and the colours `BODY_BLACK`, `BODY_DARK`, `TIN`,
`MARK`. Conventions there:

- Build in **footprint coordinates**: origin at the footprint origin, Z up
  from the board surface, so the footprint references the model with an
  identity transform (offset 0, scale 1, rotate 0).
- KiCad's 3D Y axis points opposite to the PCB editor's Y: footprint point
  `(x, y)` is model point `(x, -y)`. Pin-1 marks must account for this.
- Body bottom at z=0 for leadless parts; add stand-off where the drawing
  has one.

## Naming and referencing

- File: `footprints/Jonas.3dshapes/<footprint>.step` (share one file only
  when bodies are identical, e.g. `L_Vishay_IHLP-1212.step`).
- Footprint: `(model "${JONAS_KICADLIB}/footprints/Jonas.3dshapes/<file>"
  (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))`.

## Validation

1. `grep -c "CSG_SOLID\|BLOCK(" <file>` is 0 and the file contains
   `MANIFOLD_SOLID_BREP`.
2. `python scripting/audit_refs.py`: no missing model, no orphan file.
3. Render it (local Claude Code sessions on archimedes have KiCad 10):
   `"C:\Program Files\KiCad\10.0\bin\python.exe" scripting/render_footprints.py --out <scratch dir> <footprint>`
   and look at the top and iso PNGs: body on the board, pin-1 mark at pad 1,
   terminals over the pads, connector openings facing the right way. The
   Cowork sandbox has no KiCad; there, say the model is unrendered.
4. Re-running `gen_package_models.py` must reproduce every generated model
   byte for byte (compare into a scratch `--out`).
5. Add the model **and** its placement to the F8 manual-review list in
   `docs/review-2026-10-footprints.md`, and tell Jonas it has not been
   checked by him in a viewer.
