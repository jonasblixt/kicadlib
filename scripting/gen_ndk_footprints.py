#!/usr/bin/env python3
# Modernizes the 3 usable legacy NDK crystal footprints found in
# modules/footprints.pretty/ into footprints/NDK.pretty/, for use by
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
# IHLP). Rather than hand-deriving safe corner-tick geometry per pad
# layout, this script keeps the full silk box only where it verifiably
# clears every pad (NX2520SA - clears by ~0.05mm on all 4 sides) and
# drops the silk body outline entirely where it doesn't (NX1255GB,
# NX3225SA), keeping only the reference/value silk text (which sits well
# outside the body already). This matches how several of KiCad's own
# official small-crystal footprints handle this same wraparound-vs-body
# conflict. F.Fab still gets the full nominal-body outline regardless -
# that layer is documentation-only and safe to overlap copper.
#
# 3D MODELS: only NX2520SA has a real NDK-specific STEP model available
# (modules/packages3d/"User Library-Crystal NDK NX2520SA series.step",
# copied in here as footprints/NDK.3dshapes/NX2520SA.step with no
# transform - the legacy footprint referenced it with an identity
# offset/scale/rotate, so none is needed here either). NX1255GB has no
# model in modules/packages3d at all. NX3225SA's legacy footprint
# referenced a generic stock box placeholder ("${KISYS3DMOD}/Crystal SMD
# 2.5x3.5mm.step") that doesn't even match this package's real 3.2x2.5mm
# footprint - not carried forward, since a wrong model is worse than none
# and no correctly-sized replacement was available in this session.
import os
import shutil

OUT_DIR = os.path.expanduser("~/mnt/kicadlib/footprints/NDK.pretty")
MODEL_OUT_DIR = os.path.expanduser("~/mnt/kicadlib/footprints/NDK.3dshapes")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(MODEL_OUT_DIR, exist_ok=True)

SRC_MODEL = os.path.expanduser(
    "~/mnt/kicadlib/modules/packages3d/User Library-Crystal NDK NX2520SA series.step")
DST_MODEL_NAME = "NX2520SA.step"

FOOTPRINTS = {
    "NX1255GB": {
        "pads": [(1, -2.54, 2.2), (2, 2.54, 2.2), (3, 2.54, -2.2), (4, -2.54, -2.2)],
        "pad_size": (2.4, 2.2),
        "box": (5.9, 2.75),
        "ref_at": (-2.54, 4.4),
        "val_at": (-2.54, -4.4),
        "descr": "NDK NX1255GB-series crystal, 12.5mm x 5.5mm body, 4-pad wraparound package.",
        "model": None,
        "keep_silk_box": False,
    },
    "NX2520SA": {
        "pads": [(1, -0.85, 0.65), (2, 0.85, 0.65), (3, 0.85, -0.65), (4, -0.85, -0.65)],
        "pad_size": (1.2, 1.0),
        "box": (1.5, 1.2),
        "ref_at": (0.4, 2),
        "val_at": (1.1, -1.9),
        "descr": "NDK NX2520SA-series crystal, 2.5mm x 2.0mm body, 4-pad wraparound package. "
                 "Also used for the NX2520SD/NX2520SG series (same 2.5x2.0mm land pattern, "
                 "differ only in body height, which the 2D footprint doesn't encode) - see "
                 "import_xtal_ndk.py's FOOTPRINT_MAP.",
        "model": DST_MODEL_NAME,
        "keep_silk_box": True,
    },
    "NX3225SA": {
        "pads": [(1, -1.1, 0.8), (2, 1.1, 0.8), (3, 1.1, -0.8), (4, -1.1, -0.8)],
        "pad_size": (1.4, 1.2),
        "box": (1.6, 1.25),
        "ref_at": (0.2, 2.2),
        "val_at": (1, -2.1),
        "descr": "NDK NX3225SA-series crystal, 3.2mm x 2.5mm body, 4-pad wraparound package. "
                 "Also used for the NX3225GA/NX3225GB/NX3225GD/NX3225SC series (same "
                 "3.2x2.5mm land pattern per NDK's own package-size figures across all 5 "
                 "series in this dataset) - see import_xtal_ndk.py's FOOTPRINT_MAP.",
        "model": None,
        "keep_silk_box": False,
    },
}

MARGIN = 0.25


def gen_footprint(name, geo):
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
    lines.append(f'\t(tags "crystal NDK {name}")')
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

    uid = 100

    if geo["keep_silk_box"]:
        silk_corners = [(-box_x, -box_y, box_x, -box_y), (box_x, -box_y, box_x, box_y),
                         (box_x, box_y, -box_x, box_y), (-box_x, box_y, -box_x, -box_y)]
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
        lines.append(f'\t(model "${{JONAS_KICADLIB}}/footprints/NDK.3dshapes/{geo["model"]}"')
        lines.append('\t\t(offset (xyz 0 0 0))')
        lines.append('\t\t(scale (xyz 1 1 1))')
        lines.append('\t\t(rotate (xyz 0 0 0))')
        lines.append('\t)')

    lines.append(')')
    lines.append('')
    return "\n".join(lines), (crtyd_x, crtyd_y)


if os.path.exists(SRC_MODEL):
    shutil.copyfile(SRC_MODEL, os.path.join(MODEL_OUT_DIR, DST_MODEL_NAME))
    print(f"copied 3D model -> {os.path.join(MODEL_OUT_DIR, DST_MODEL_NAME)}")
else:
    print(f"WARNING: source 3D model not found: {SRC_MODEL}")

for name, geo in FOOTPRINTS.items():
    text, (cx, cy) = gen_footprint(name, geo)
    path = os.path.join(OUT_DIR, f"{name}.kicad_mod")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {path} (courtyard {cx} x {cy} half-extents)")
