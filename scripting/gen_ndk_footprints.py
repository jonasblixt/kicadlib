#!/usr/bin/env python3
# Modernizes the 3 usable legacy NDK crystal footprints found in
# modules/footprints.pretty/ into footprints/Jonas.pretty/, for use by
# scripting/import_xtal_ndk.py. See that script's header for the full
# footprint-mapping decision (which of the 21 package/series codes in
# library/xtal_NDK.kicad_sym get one of these 3, which get a stock KiCad
# Crystal footprint instead, and which get none at all).
#
# Pad geometry (position/size, all rectangular, no rotation) is taken
# verbatim from the legacy files - only the modern footprint wrapper
# (version/generator/uuid), F.Fab body outline, and F.CrtYd courtyard are
# added, following the same modernization pattern already used by
# gen_ihlp_footprints.py and gen_dlw5b_footprint.py.
#
# SILKSCREEN: the legacy files' silk "box" is the nominal ceramic body
# outline, but on 2 of these 3 footprints (NX1255GB, NX3225SA) the pads'
# wraparound end terminations extend PAST that body box in one axis, so
# the box's own top/bottom (NX1255GB) or all 4 edges (NX3225SA) actually
# cross pad copper - a real DRC violation, not something safe to carry
# forward as-is (same class of issue gen_ihlp_footprints.py fixed for
# IHLP). This script keeps the full silk box only where it verifiably
# clears every pad (NX2520SA - clears by ~0.05mm on all 4 sides). Where
# it doesn't (NX1255GB, NX3225SA), it draws an L outside all pads at the
# pin-1 corner instead (since 2026-10-13, F4.3; before that these two had
# no silk outline at all), the way KiCad's stock Crystal_SMD_3225-4Pin
# does. F.Fab gets the full nominal-body outline regardless (documentation
# only, safe to overlap copper) plus a ${REFERENCE} text sized to the body.
#
# 3D MODELS: NX2520SA uses the NDK STEP model copied once from
# modules/packages3d/"User Library-Crystal NDK NX2520SA series.step" to
# footprints/Jonas.3dshapes/NX2520SA.step (identity transform, as the
# legacy footprint had). NX3225SA uses Jonas.3dshapes/NX3225SA.step,
# added by hand after the first generation and carried back into this
# script (rotate -90 about X). NX1255GB uses the envelope model made by
# scripting/gen_package_models.py (F4.5); its legacy file had none. NX3225SA's legacy footprint referenced a generic
# stock box placeholder ("${KISYS3DMOD}/Crystal SMD 2.5x3.5mm.step") that
# doesn't match this package's real 3.2x2.5mm footprint - not carried
# forward.
#
# Footprint names changed 2026-10-19 (footprints review F4.8, KiCad-stock /
# Vendor_Part naming): NX1255GB -> Crystal_SMD_NDK_NX1255GB-4Pin_12.5x5.5mm;
# NX2520SA -> Crystal_SMD_NDK_NX2520SA-4Pin_2.5x2.0mm; NX3225SA ->
# Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm (models renamed to match).
# Older names in the comments above refer to the same files.
import argparse
import os

# Paths are relative to the repo (A1.8; this used to write to the Cowork
# mount ~/mnt/kicadlib). --out writes elsewhere, e.g. to diff a run
# against the committed footprints.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ap = argparse.ArgumentParser(description="Generate the NDK crystal footprints in Jonas.pretty.")
_ap.add_argument("--out", default=os.path.join(REPO, "footprints", "Jonas.pretty"))
OUT_DIR = _ap.parse_args().out
os.makedirs(OUT_DIR, exist_ok=True)

# NX2520SA.step was copied once from modules/packages3d/"User Library-
# Crystal NDK NX2520SA series.step"; footprints/Jonas.3dshapes/ is now its
# source of truth, so the generator no longer copies it.
DST_MODEL_NAME = "Crystal_SMD_NDK_NX2520SA-4Pin_2.5x2.0mm.step"

# Footprint names follow KiCad's stock crystal pattern (F4.8, 2026-10-19);
# the tags keep the NDK series.
FP_NAME = {
    "NX1255GB": "Crystal_SMD_NDK_NX1255GB-4Pin_12.5x5.5mm",
    "NX2520SA": "Crystal_SMD_NDK_NX2520SA-4Pin_2.5x2.0mm",
    "NX3225SA": "Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm",
}

FOOTPRINTS = {
    "NX1255GB": {
        "pads": [(1, -2.54, 2.2), (2, 2.54, 2.2), (3, 2.54, -2.2), (4, -2.54, -2.2)],
        "pad_size": (2.4, 2.2),
        "box": (5.9, 2.75),
        "ref_at": (-2.54, 4.4),
        "val_at": (-2.54, -4.4),
        "descr": "NDK NX1255GB-series crystal, 12.5mm x 5.5mm body, 4-pad wraparound package.",
        # Envelope model from scripting/gen_package_models.py (F4.5).
        "model": "Crystal_SMD_NDK_NX1255GB-4Pin_12.5x5.5mm.step",
        "keep_silk_box": False,
    },
    "NX2520SA": {
        "pads": [(1, -0.85, 0.65), (2, 0.85, 0.65), (3, 0.85, -0.65), (4, -0.85, -0.65)],
        "pad_size": (1.2, 1.0),
        "box": (1.5, 1.2),
        "ref_at": (0, -2.1),
        "val_at": (0, 2.1),
        "descr": "NDK NX2520SA-series crystal, 2.5mm x 2.0mm body, 4-pad wraparound package. "
                 "Also used for the NX2520SD/NX2520SG series (same 2.5x2.0mm land pattern, "
                 "differ only in body height, which the 2D footprint doesn't encode) - see "
                 "import_xtal_ndk.py's FOOTPRINT_MAP.",
        "model": DST_MODEL_NAME,
        # The body box clears the pads by only 0.05 mm, which the 0.12 mm
        # stroke eats (KiCad DRC: silk clipped by solder mask), so this one
        # gets the pin-1 L as well since 2026-10-13 (F4.3).
        "keep_silk_box": False,
    },
    "NX3225SA": {
        "pads": [(1, -1.1, 0.8), (2, 1.1, 0.8), (3, 1.1, -0.8), (4, -1.1, -0.8)],
        "pad_size": (1.4, 1.2),
        "box": (1.6, 1.25),
        "ref_at": (0, -2.4),
        "val_at": (0, 2.4),
        "descr": "NDK NX3225SA-series crystal, 3.2mm x 2.5mm body, 4-pad wraparound package. "
                 "Also used for the NX3225GA/NX3225GB/NX3225GD/NX3225SC series (same "
                 "3.2x2.5mm land pattern per NDK's own package-size figures across all 5 "
                 "series in this dataset) - see import_xtal_ndk.py's FOOTPRINT_MAP.",
        # NX3225SA.step was added to Jonas.3dshapes and wired into the
        # committed footprint by hand after generation (82a09c4); carried
        # back here 2026-10-13 so regenerating keeps it.
        "model": "Crystal_SMD_NDK_NX3225SA-4Pin_3.2x2.5mm.step",
        "model_rotate": (-90, 0, 0),
        "keep_silk_box": False,
    },
}

MARGIN = 0.25



def fab_ref_size(w, h):
    """${REFERENCE} text size on F.Fab: 1.0 mm (KLC), scaled down to ~1/3
    of the body's short side for small parts, never below 0.5 mm."""
    s = round(min(w, h) * 0.32 / 0.05) * 0.05
    return round(min(1.0, max(0.5, s)), 2)


def fab_ref_lines(w, h):
    fs = fab_ref_size(w, h)
    return ['\t(fp_text user "${REFERENCE}" (at 0 0 0) (layer "F.Fab")',
            '\t\t(uuid "00000000-0000-0000-0000-000000000006")',
            f'\t\t(effects (font (size {fs} {fs}) (thickness {round(fs * 0.15, 3)})))',
            '\t)']


def gen_footprint(series, geo):
    name = FP_NAME[series]
    pads = geo["pads"]
    psx, psy = geo["pad_size"]
    box_x, box_y = geo["box"]
    ref_x, ref_y = geo["ref_at"]
    val_x, val_y = geo["val_at"]

    pad_x_max = max(abs(x) + psx / 2 for _, x, _ in pads)
    pad_y_max = max(abs(y) + psy / 2 for _, _, y in pads)
    crtyd_x = round(max(pad_x_max, box_x) + MARGIN, 2)
    crtyd_y = round(max(pad_y_max, box_y) + MARGIN, 2)

    lines = []
    lines.append(f'(footprint "{name}"')
    lines.append('\t(version 20240108)')
    lines.append('\t(generator "kicadlib_ndk_import")')
    lines.append('\t(generator_version "10.0")')
    lines.append('\t(layer "F.Cu")')
    lines.append(f'\t(descr "{geo["descr"]}")')
    lines.append(f'\t(tags "crystal NDK {series}")')
    lines.append('\t(attr smd)')
    lines.append('\t(property "Reference" "REF**"')
    lines.append(f'\t\t(at {ref_x} {ref_y} 0)')
    lines.append('\t\t(layer "F.SilkS")')
    lines.append('\t\t(uuid "00000000-0000-0000-0000-000000000001")')
    lines.append('\t\t(effects (font (size 1 1) (thickness 0.15)))')
    lines.append('\t)')
    lines.append(f'\t(property "Value" "{name}"')
    lines.append(f'\t\t(at {val_x} {val_y} 0)')
    lines.append('\t\t(layer "F.Fab")')
    lines.append('\t\t(uuid "00000000-0000-0000-0000-000000000002")')
    lines.append('\t\t(effects (font (size 1 1) (thickness 0.15)))')
    lines.append('\t)')
    lines.append('\t(property "Footprint" ""')
    lines.append('\t\t(at 0 0 0) (layer "F.Fab") (hide yes)')
    lines.append('\t\t(uuid "00000000-0000-0000-0000-000000000003")')
    lines.append('\t\t(effects (font (size 1 1) (thickness 0.15)))')
    lines.append('\t)')
    lines.append('\t(property "Datasheet" ""')
    lines.append('\t\t(at 0 0 0) (layer "F.Fab") (hide yes)')
    lines.append('\t\t(uuid "00000000-0000-0000-0000-000000000004")')
    lines.append('\t\t(effects (font (size 1 1) (thickness 0.15)))')
    lines.append('\t)')
    lines.append('\t(property "Description" ""')
    lines.append('\t\t(at 0 0 0) (layer "F.Fab") (hide yes)')
    lines.append('\t\t(uuid "00000000-0000-0000-0000-000000000005")')
    lines.append('\t\t(effects (font (size 1 1) (thickness 0.15)))')
    lines.append('\t)')
    lines += fab_ref_lines(2 * box_x, 2 * box_y)

    uid = 100

    if geo["keep_silk_box"]:
        silk_corners = [(-box_x, -box_y, box_x, -box_y), (box_x, -box_y, box_x, box_y),
                         (box_x, box_y, -box_x, box_y), (-box_x, box_y, -box_x, -box_y)]
    else:
        # The body box would cross the pads, so mark pin 1 with an L
        # outside all pads instead (one full side + one full end at the
        # pin-1 corner), like KiCad's stock Crystal_SMD_3225-4Pin. Lines
        # sit 0.18 mm outside the pad/body extent: 0.12 mm clear of copper
        # with the 0.12 mm stroke, and still inside the 0.25 mm courtyard.
        _, x1p, y1p = next(p for p in pads if p[0] == 1)
        sx = -1 if x1p < 0 else 1
        sy = -1 if y1p < 0 else 1
        ex = round(max(pad_x_max, box_x) + 0.18, 2)
        ey = round(max(pad_y_max, box_y) + 0.18, 2)
        silk_corners = [(sx * ex, -ey, sx * ex, ey), (-ex, sy * ey, ex, sy * ey)]
    if silk_corners:
        for (x1, y1, x2, y2) in silk_corners:
            uid += 1
            lines.append(f'\t(fp_line (start {x1} {y1}) (end {x2} {y2})')
            lines.append('\t\t(stroke (width 0.12) (type solid))')
            lines.append('\t\t(layer "F.SilkS")')
            lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
            lines.append('\t)')

    # F.Fab body outline - always drawn at the nominal box size, safe to
    # overlap copper (documentation layer only).
    fab_corners = [(-box_x, -box_y, box_x, -box_y), (box_x, -box_y, box_x, box_y),
                   (box_x, box_y, -box_x, box_y), (-box_x, box_y, -box_x, -box_y)]
    for (x1, y1, x2, y2) in fab_corners:
        uid += 1
        lines.append(f'\t(fp_line (start {x1} {y1}) (end {x2} {y2})')
        lines.append('\t\t(stroke (width 0.1) (type solid))')
        lines.append('\t\t(layer "F.Fab")')
        lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
        lines.append('\t)')

    crtyd_corners = [(-crtyd_x, -crtyd_y, crtyd_x, -crtyd_y), (crtyd_x, -crtyd_y, crtyd_x, crtyd_y),
                      (crtyd_x, crtyd_y, -crtyd_x, crtyd_y), (-crtyd_x, crtyd_y, -crtyd_x, -crtyd_y)]
    for (x1, y1, x2, y2) in crtyd_corners:
        uid += 1
        lines.append(f'\t(fp_line (start {x1} {y1}) (end {x2} {y2})')
        lines.append('\t\t(stroke (width 0.05) (type solid))')
        lines.append('\t\t(layer "F.CrtYd")')
        lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
        lines.append('\t)')

    for (num, x, y) in pads:
        uid += 1
        lines.append(f'\t(pad "{num}" smd rect (at {x} {y} 0) (size {psx} {psy})')
        lines.append('\t\t(layers "F.Cu" "F.Paste" "F.Mask")')
        lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
        lines.append('\t)')

    if geo["model"]:
        lines.append(f'\t(model "${{JONAS_KICADLIB}}/footprints/Jonas.3dshapes/{geo["model"]}"')
        rx, ry, rz = geo.get("model_rotate", (0, 0, 0))
        lines.append('\t\t(offset (xyz 0 0 0))')
        lines.append('\t\t(scale (xyz 1 1 1))')
        lines.append(f'\t\t(rotate (xyz {rx} {ry} {rz}))')
        lines.append('\t)')

    lines.append(')')
    lines.append('')
    return "\n".join(lines), (crtyd_x, crtyd_y)


for series, geo in FOOTPRINTS.items():
    text, (cx, cy) = gen_footprint(series, geo)
    path = os.path.join(OUT_DIR, f"{FP_NAME[series]}.kicad_mod")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {path} (courtyard {cx} x {cy} half-extents)")
