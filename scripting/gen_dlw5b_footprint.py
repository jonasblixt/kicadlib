#!/usr/bin/env python3
# Generates the custom footprint for Murata's DLW5B-series chip common-
# mode choke (5.0mm x 5.0mm body, "5050" metric / "2020" imperial size
# code, 4-terminal wraparound-end package). No footprint in KiCad's
# official Inductor_SMD.pretty matches this part - the closest official
# common-mode-choke footprints (L_CommonModeChoke_Coilcraft_0805USB/
# 1812CAN, L_CommonMode_Wuerth_WE-SL2/WE-SL5) are all smaller EIA cases,
# and none is a 2020/5050-size 4-pad chip - so this is a from-scratch
# custom footprint, not a substitution.
#
# GEOMETRY SOURCE: Jonas supplied Murata's own recommended-land-pattern
# drawing for the DLW5A/5B 5050 size directly (the "flow soldering"
# variant - larger pads than the reflow variant, per Murata's DLx_Series
# land-pattern guide, which gives reflow a=0.9/d=1.3/b=2.9/c=3.9 vs this
# flow-solder drawing's 0.9/2.9/5.5 (X) and 1.3/3.3/4.7 (Y)). Web-fetched
# Murata/distributor PDFs for this part were unreliable for this level of
# detail (summary sheets with no mechanical drawing, or text-extracted
# tables that didn't resolve unambiguously) - per this repo's established
# preference (see import_ind_power_vishay_ihlp.py's IHLP 3232/4040/5050/
# 6767 deferral), a hand-supplied drawing was used instead of guessing.
#
# The drawing shows each of the 4 terminals as a stepped/notched shape
# (an interdigitated "tab" that reaches closer to the part's centerlines
# than the terminal's main block, to cut solder-bridge risk during wave
# soldering) - not a plain rectangle. This footprint SIMPLIFIES that to a
# plain rectangular pad per terminal, sized to each terminal's full
# bounding box (outer corner to the tip of its tab, in both X and Y):
#   pad width (X)  = 2.75mm - 0.45mm = 2.3mm  (2.75 = half of the 5.5mm
#                     overall X span; 0.45 = half of the 0.9mm tab-tip
#                     gap between the two terminals that face each other
#                     across the vertical centerline)
#   pad height (Y) = 2.35mm - 0.65mm = 1.7mm  (2.35 = half of the 4.7mm
#                     overall Y span; 0.65 = half of the 1.3mm tab-tip
#                     gap between the two terminals stacked in the same
#                     column)
# This bounding-box rectangle is a strict superset of Murata's actual
# notched copper shape, so it never reduces the pad-to-pad clearance
# below Murata's own numbers - checked against both neighbours: the
# vertical neighbour (same column, e.g. pin 1 vs pin 4) clears by
# 2*0.65=1.3mm, and the horizontal neighbour across the centerline
# (e.g. pin 3 vs pin 4) clears by 2*0.45=0.9mm, matching the drawing's
# tightest points exactly. The simplification only removes the "notch"
# itself - it doesn't touch either given clearance number. It does add a
# small amount of copper Murata's own pattern leaves bare (the inner
# corner each notch cuts away), which is a solderability plus, not a
# risk. If Jonas wants the exact interdigitated shape reproduced (custom
# polygon pads) rather than this rectangular simplification, that would
# need re-deriving as a follow-up.
#
# Body size (5.0mm x 5.0mm, all 20 rows in ind_cmc_murata_dlw5b_{1,2}.csv
# share this size code) is used for the F.Fab outline and courtyard, per
# the "Size code in mm(inch)" column ("5050/2020") and the Mouser summary
# datasheet's dimension line ("5.0mm +/-0.3mm" x2). Thickness differs by
# sub-series (DLW5BSM: 4.5mm Max.; DLW5BTM: 2.5mm) but that only affects
# the Z-height / a 3D model, not this 2D land pattern - both sub-series
# share this one footprint, same as NAMING.md section 5 recommends (reuse
# one footprint across parts with identical land geometry). No 3D model
# is bundled - none was sourced for this part.
import os

NAME = "DLW5B_5050"
OUT_DIR = os.path.expanduser("~/mnt/kicadlib/footprints/Murata_DLW5B.pretty")
os.makedirs(OUT_DIR, exist_ok=True)

# Pads: (pin number, x, y) - all four are plain axis-aligned rectangles,
# no rotation. Pin numbering (1=top-right, 2=top-left, 3=bottom-left,
# 4=bottom-right) matches the terminal numbering in Jonas's supplied
# drawing. KiCad Y+ is down, so "top" (drawing) = negative Y here.
PAD_SX, PAD_SY = 2.3, 1.7
PADS = [
    (1, 1.6, -1.5),
    (2, -1.6, -1.5),
    (3, -1.6, 1.5),
    (4, 1.6, 1.5),
]

# F.Fab / nominal body outline half-extents (5.0mm x 5.0mm body).
BOX_X, BOX_Y = 2.5, 2.5

# Courtyard: bounding box of (pads union body box), + 0.25mm clearance -
# same margin convention as gen_ihlp_footprints.py.
pad_x_max = max(abs(x) + PAD_SX / 2 for _, x, _ in PADS)
pad_y_max = max(abs(y) + PAD_SY / 2 for _, _, y in PADS)
CRTYD_X = round(max(pad_x_max, BOX_X) + 0.25, 2)
CRTYD_Y = round(max(pad_y_max, BOX_Y) + 0.25, 2)

REF_AT = (0, -3.3)
VAL_AT = (0, 3.3)


def gen_footprint():
    lines = []
    lines.append(f'(footprint "{NAME}"')
    lines.append('\t(version 20240108)')
    lines.append('\t(generator "kicadlib_dlw5b_import")')
    lines.append('\t(generator_version "10.0")')
    lines.append('\t(layer "F.Cu")')
    lines.append('\t(descr "Murata DLW5B-series chip common-mode choke, 5.0mm x 5.0mm '
                 '(5050/2020 size) 4-terminal wraparound package. Land pattern per Murata\'s '
                 'recommended flow-solder pattern, simplified to rectangular pads (no '
                 'anti-bridging notch) - see scripting/gen_dlw5b_footprint.py header.")')
    lines.append('\t(tags "inductor common mode choke CMC DLW5B 5050 2020")')
    lines.append('\t(attr smd)')
    lines.append('\t(property "Reference" "REF**"')
    lines.append(f'\t\t(at {REF_AT[0]} {REF_AT[1]} 0)')
    lines.append('\t\t(layer "F.SilkS")')
    lines.append('\t\t(uuid "00000000-0000-0000-0000-000000000001")')
    lines.append('\t\t(effects (font (size 1 1) (thickness 0.15)))')
    lines.append('\t)')
    lines.append(f'\t(property "Value" "{NAME}"')
    lines.append(f'\t\t(at {VAL_AT[0]} {VAL_AT[1]} 0)')
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

    # F.SilkS: top/bottom lines at the full body box width (safe - this Y
    # sits outside every pad's Y-extent), plus short corner ticks in the
    # Y-gap between each pad's outer edge and the body box edge (same
    # clip-clear-of-copper approach as gen_ihlp_footprints.py).
    silk_lines = [
        (-BOX_X, BOX_Y, BOX_X, BOX_Y),
        (-BOX_X, -BOX_Y, BOX_X, -BOX_Y),
    ]
    if pad_y_max < BOX_Y - 0.01:
        for x in (-BOX_X, BOX_X):
            silk_lines.append((x, pad_y_max, x, BOX_Y))
            silk_lines.append((x, -pad_y_max, x, -BOX_Y))

    for (x1, y1, x2, y2) in silk_lines:
        uid += 1
        lines.append(f'\t(fp_line (start {x1} {y1}) (end {x2} {y2})')
        lines.append('\t\t(stroke (width 0.12) (type solid))')
        lines.append('\t\t(layer "F.SilkS")')
        lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
        lines.append('\t)')

    # F.Fab body outline - full rectangle, documentation layer only, safe
    # to overlap pads.
    fab_corners = [(-BOX_X, -BOX_Y, BOX_X, -BOX_Y), (BOX_X, -BOX_Y, BOX_X, BOX_Y),
                   (BOX_X, BOX_Y, -BOX_X, BOX_Y), (-BOX_X, BOX_Y, -BOX_X, -BOX_Y)]
    for (x1, y1, x2, y2) in fab_corners:
        uid += 1
        lines.append(f'\t(fp_line (start {x1} {y1}) (end {x2} {y2})')
        lines.append('\t\t(stroke (width 0.1) (type solid))')
        lines.append('\t\t(layer "F.Fab")')
        lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
        lines.append('\t)')

    # F.CrtYd
    crtyd_corners = [(-CRTYD_X, -CRTYD_Y, CRTYD_X, -CRTYD_Y), (CRTYD_X, -CRTYD_Y, CRTYD_X, CRTYD_Y),
                      (CRTYD_X, CRTYD_Y, -CRTYD_X, CRTYD_Y), (-CRTYD_X, CRTYD_Y, -CRTYD_X, -CRTYD_Y)]
    for (x1, y1, x2, y2) in crtyd_corners:
        uid += 1
        lines.append(f'\t(fp_line (start {x1} {y1}) (end {x2} {y2})')
        lines.append('\t\t(stroke (width 0.05) (type solid))')
        lines.append('\t\t(layer "F.CrtYd")')
        lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
        lines.append('\t)')

    for (num, x, y) in PADS:
        uid += 1
        lines.append(f'\t(pad "{num}" smd rect (at {x} {y} 0) (size {PAD_SX} {PAD_SY})')
        lines.append('\t\t(layers "F.Cu" "F.Paste" "F.Mask")')
        lines.append(f'\t\t(uuid "00000000-0000-0000-0000-{uid:012d}")')
        lines.append('\t)')

    lines.append(')')
    lines.append('')
    return "\n".join(lines)


text = gen_footprint()
path = os.path.join(OUT_DIR, f"{NAME}.kicad_mod")
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("wrote", path)
print(f"courtyard: {CRTYD_X} x {CRTYD_Y} (half-extents)")
print(f"pad bounding box: {pad_x_max} x {pad_y_max} (half-extents)")
