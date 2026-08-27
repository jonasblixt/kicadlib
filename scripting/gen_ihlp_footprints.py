import re
import os

# Legacy footprint geometry (pads + silk box), taken verbatim from
# modules/footprints.pretty/IHLP<case>.kicad_mod. Pad positions/sizes/
# rotation and the silk box corner coordinates are preserved exactly -
# only the copper-overlapping vertical silk lines are corrected (clipped
# to the Y-gap outside the pads), and courtyard/fab/modern-format/3D
# links are added on top.
CASES = {
    "1212": {
        "pads": [
            {"num": 1, "x": -1.3, "y": 0, "rot": 270, "sx": 1.2, "sy": 1.5},
            {"num": 2, "x": 1.4, "y": 0, "rot": 90, "sx": 1.2, "sy": 1.5},
        ],
        "box": (1.5, 1.4),  # (x half-width, y half-height) of the silk box
        "ref_at": (0.5, 2.4),
        "val_at": (1.9, -2.2),
        "body_lw_mm": (3.65, 3.00),  # from Description, for courtyard sizing
        "series": {
            "AB": "IHLP1212.step",
            "AE": "IHLP1212.step",
            "BZ": "IHLP1212.step",
        },
        "model_xform": {"offset": (-1.75, 1.5, 0), "scale": (1, 1, 1), "rotate": (0, 0, 0)},
    },
    "1616": {
        "pads": [
            {"num": 1, "x": -1.8545, "y": 0, "rot": 0, "sx": 1.8545, "sy": 2.286},
            {"num": 2, "x": 1.8545, "y": 0, "rot": 0, "sx": 1.8545, "sy": 2.286},
        ],
        "box": (2.225, 2.03),
        "ref_at": (-0.3, 3.1),
        "val_at": (-0.06, -2.94),
        "body_lw_mm": (4.45, 4.06),
        "series": {
            "AB": "IHLP1616AB.step",
            "BZ": "IHLP1616BZ.step",
        },
        "model_xform": {"offset": (-0.2, 6.6, -2.5), "scale": (1, 1, 1), "rotate": (-90, 0, 0)},
    },
    "2020": {
        "pads": [
            {"num": 1, "x": -2.4278, "y": 0, "rot": 0, "sx": 1.9095, "sy": 2.79},
            {"num": 2, "x": 2.4278, "y": 0, "rot": 0, "sx": 1.9095, "sy": 2.79},
        ],
        "box": (2.75, 2.6),
        "ref_at": (-0.8, 3.55),
        "val_at": (0.7, -3.4),
        "body_lw_mm": (5.49, 5.18),
        "series": {
            "AB": "IHLP2020AB.step",
            "BZ": "IHLP2020BZ.step",
            "CZ": "IHLP2020CZ.step",
        },
        "model_xform": {"offset": (-0.65, 6.1, -2.5), "scale": (1, 1, 1), "rotate": (-90, 0, 0)},
    },
    "2525": {
        "pads": [
            {"num": 1, "x": -2.971, "y": 0, "rot": 0, "sx": 2.413, "sy": 3.429},
            {"num": 2, "x": 2.971, "y": 0, "rot": 0, "sx": 2.413, "sy": 3.429},
        ],
        "box": (3.25, 3.25),
        "ref_at": (-1.25, 4.25),
        "val_at": (0, -4),
        "body_lw_mm": (6.86, 6.47),
        "series": {
            # All 3 IHLP2525BD parts in this library's scope (3.3-10uH) fall
            # in the "(1.5-10uH)" step variant's range - the "(0.1-1.0uH)"
            # variant isn't needed for this dataset. Copied in as plain
            # "IHLP2525BD.step" (see footprints/Vishay_IHLP.3dshapes/).
            "BD": "IHLP2525BD.step",
            "CZ": "IHLP2525CZ.step",
            "EZ": "IHLP2525EZ.step",
        },
        # UNCALIBRATED: the legacy footprint referenced a hand-authored WRL
        # model (inch-based, scale 0.393701, offset/rotate tuned for that
        # specific file: "../../../../../Users/jons/Documents/Projects/
        # Snigel2/3D models/IHLP2525.wrl" - a broken absolute path pointing
        # at a former developer's machine, not usable regardless). Since
        # we're switching to the mm-native STEP models copied in from
        # modules/packages3d, that old inch-scale transform doesn't apply.
        # No calibration reference is available for these STEP files'
        # origin/orientation, so this reuses the same rotate/scale pattern
        # as the 2020 case (same footprint family, same pad orientation)
        # with an offset only large enough to roughly center a ~7mm part.
        # VERIFY IN KICAD'S 3D VIEWER before using - this is a best-effort
        # placement, not a calibrated one.
        "model_xform": {"offset": (0, 7.5, -3.2), "scale": (1, 1, 1), "rotate": (-90, 0, 0)},
    },
}

OUT_DIR = os.path.expanduser("~/mnt/kicadlib/footprints/Vishay_IHLP.pretty")
os.makedirs(OUT_DIR, exist_ok=True)


def pad_extents(pad):
    # Effective X/Y half-extents on the board, accounting for the 90/270
    # rotations used by the 1212 pads (which swap the pad's sx/sy).
    sx, sy = pad["sx"], pad["sy"]
    if pad["rot"] in (90, 270):
        sx, sy = sy, sx
    return pad["x"] - sx / 2, pad["x"] + sx / 2, pad["y"] - sy / 2, pad["y"] + sy / 2


def gen_footprint(case, series, step_file, geo):
    name = f"IHLP{case}{series}"
    pads = geo["pads"]
    box_x, box_y = geo["box"]
    ref_x, ref_y = geo["ref_at"]
    val_x, val_y = geo["val_at"]
    body_l, body_w = geo["body_lw_mm"]
    xf = geo["model_xform"]

    # Courtyard: bounding box of (pads union silk box), + 0.25mm clearance,
    # rounded outward to 0.01mm - standard IPC-derived courtyard margin.
    xs, ys = [], []
    for p in pads:
        x0, x1, y0, y1 = pad_extents(p)
        xs += [x0, x1]
        ys += [y0, y1]
    xs += [-box_x, box_x]
    ys += [-box_y, box_y]
    cx = round(max(abs(min(xs)), abs(max(xs))) + 0.25, 2)
    cy = round(max(abs(min(ys)), abs(max(ys))) + 0.25, 2)

    # Silk: keep the original top/bottom lines (they sit outside every
    # pad's Y-extent, so they never touch copper regardless of X span -
    # verified per case below). Replace the original FULL-HEIGHT vertical
    # side lines (which cross straight through the pads' Y-extent at an
    # X position inside the pad copper - a real DRC violation in the
    # legacy files) with short corner ticks that only occupy the safe
    # Y-gap between the pad edge and the box edge, on each side. If a
    # case has no such gap (pads reach all the way to the box's Y edge),
    # the tick for that side is simply omitted.
    pad_y_max = max(pad_extents(p)[3] for p in pads)
    silk_lines = [
        # top and bottom horizontal - unchanged from the legacy files
        (-box_x, box_y, box_x, box_y),
        (-box_x, -box_y, box_x, -box_y),
    ]
    if pad_y_max < box_y - 0.01:
        for x in (-box_x, box_x):
            silk_lines.append((x, pad_y_max, x, box_y))
            silk_lines.append((x, -pad_y_max, x, -box_y))

    lines = []
    lines.append(f'(footprint "{name}"')
    lines.append('\t(version 20240108)')
    lines.append('\t(generator "kicadlib_ihlp_import")')
    lines.append('\t(generator_version "10.0")')
    lines.append('\t(layer "F.Cu")')
    lines.append('\t(descr "Vishay IHLP-' + case + series +
                 f' shielded power inductor, {body_l}mm x {body_w}mm body")')
    lines.append(f'\t(tags "inductor IHLP{case} {series}")')
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
    for (x1, y1, x2, y2) in silk_lines:
        uid += 1
        lines.append(f'\t(fp_line (start {x1} {y1}) (end {x2} {y2})')
        lines.append('\t\t(stroke (width 0.12) (type solid))')
        lines.append('\t\t(layer "F.SilkS")')
        lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
        lines.append('\t)')

    # Fab-layer body outline (thin line, distinct from silkscreen) at the
    # box geometry - matches the repo's existing footprints, which use
    # this same box for their visual body outline.
    fab_corners = [(-box_x, -box_y, box_x, -box_y), (box_x, -box_y, box_x, box_y),
                   (box_x, box_y, -box_x, box_y), (-box_x, box_y, -box_x, -box_y)]
    for (x1, y1, x2, y2) in fab_corners:
        uid += 1
        lines.append(f'\t(fp_line (start {x1} {y1}) (end {x2} {y2})')
        lines.append('\t\t(stroke (width 0.1) (type solid))')
        lines.append('\t\t(layer "F.Fab")')
        lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
        lines.append('\t)')

    # Courtyard
    crtyd_corners = [(-cx, -cy, cx, -cy), (cx, -cy, cx, cy), (cx, cy, -cx, cy), (-cx, cy, -cx, -cy)]
    for (x1, y1, x2, y2) in crtyd_corners:
        uid += 1
        lines.append(f'\t(fp_line (start {x1} {y1}) (end {x2} {y2})')
        lines.append('\t\t(stroke (width 0.05) (type solid))')
        lines.append('\t\t(layer "F.CrtYd")')
        lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
        lines.append('\t)')

    for p in pads:
        uid += 1
        lines.append(f'\t(pad "{p["num"]}" smd rect (at {p["x"]} {p["y"]} {p["rot"]})'
                      f' (size {p["sx"]} {p["sy"]})')
        lines.append('\t\t(layers "F.Cu" "F.Paste" "F.Mask")')
        lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
        lines.append('\t)')

    ox, oy, oz = xf["offset"]
    sx_, sy_, sz_ = xf["scale"]
    rx, ry, rz = xf["rotate"]
    # Same ${JONAS_KICADLIB}/footprints/<Vendor_Series>.3dshapes/ path
    # convention used by the repo's other custom footprints (Murata_GA3,
    # Panasonic_ECHU) - keeps the 3D model bundled with the footprint
    # library instead of depending on modules/packages3d + ${KISYS3DMOD}.
    lines.append(f'\t(model "${{JONAS_KICADLIB}}/footprints/Vishay_IHLP.3dshapes/{step_file}"')
    lines.append(f'\t\t(offset (xyz {ox} {oy} {oz}))')
    lines.append(f'\t\t(scale (xyz {sx_} {sy_} {sz_}))')
    lines.append(f'\t\t(rotate (xyz {rx} {ry} {rz}))')
    lines.append('\t)')
    lines.append(')')
    lines.append('')

    return name, "\n".join(lines)


count = 0
for case, geo in CASES.items():
    for series, step_file in geo["series"].items():
        name, text = gen_footprint(case, series, step_file, geo)
        path = os.path.join(OUT_DIR, f"{name}.kicad_mod")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote", path)
        count += 1

print(f"\n{count} footprints written to {OUT_DIR}")
