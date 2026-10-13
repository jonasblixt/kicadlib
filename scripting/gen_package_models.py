#!/usr/bin/env python3
# Generates simple B-Rep 3D models (stacks of boxes, via step_brep_box.py)
# for Jonas.pretty footprints that have no vendor STEP. Each model is
# written to footprints/Jonas.3dshapes/<footprint>.step and is referenced
# from its footprint with an identity transform (offset 0, scale 1,
# rotate 0): the models are built in footprint coordinates, origin at the
# footprint origin, Z up from the board surface.
#
# KiCad's 3D Y axis points the other way from the PCB editor's Y axis, so a
# footprint point (x, y) is model point (x, -y). Pin-1 marks below use that.
#
# These are envelope models (body, terminals, pin-1 mark) for clearance and
# BOM visuals, not detailed vendor geometry. Dimensions and their sources:
#
#   QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm (Skyworks Si3402-B-GM): Si3402-B data
#     sheet rev 1.1 (2021-08-06), section 5 / Table 9: D = E = 5.00,
#     A = 0.85 nom, b = 0.30, e = 0.80, L = 0.55, D2 = E2 = 2.70 (MO-220
#     VHHB-1). 4 terminals on the left/right sides (pins 1-4, 11-14) and 6
#     on the top/bottom (5-10, 15-20), Figures 6/7. Pin 1 is the top of the
#     left row (footprint pad 1 at x = -2.35, y = -1.2).
#   NX1255GB (NDK): NDK catalog sheet cu37_071108_NX1255GB_e1: body
#     11.8 x 5.5, H = 2.5 +-0.15; four wraparound terminals 2.0 wide x 1.5
#     deep on the long edges at 5.08 mm pitch.
#   Texas_YJE (TI CSD83325L, PicoStar YJE0006A): CSD83325L data sheet
#     SLPS494C, package outline 4221674/C: 1.07-1.15 x 2.12-2.20, 0.22 mm
#     max height, 6 lands 0.27-0.33 on a 0.65 mm grid (3 rows x 2), pin A1
#     top-left (footprint pad A1 at x = -0.325, y = -0.65).
#
# Run with no arguments to regenerate all three; --out writes elsewhere.
import argparse
import os

from step_brep_box import write_step_boxes

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BODY_BLACK = (0.15, 0.15, 0.15)
BODY_DARK = (0.25, 0.25, 0.27)
TIN = (0.80, 0.80, 0.82)
MARK = (0.90, 0.90, 0.90)


def box_c(cx, cy, z0, sx, sy, sz, rgb):
    """Centre-in-XY, bottom-at-z0 box -> step_brep_box's corner/size tuple."""
    return ((round(cx - sx / 2, 4), round(cy - sy / 2, 4), round(z0, 4)),
            (round(sx, 4), round(sy, 4), round(sz, 4)), rgb)


def qfn20_si3402():
    d, a, b, e, l, ep = 5.0, 0.85, 0.30, 0.80, 0.55, 2.70
    t = 0.2           # visible terminal height on the package side
    out = 0.02        # terminals stand 0.02 proud of the body so they show
    boxes = [box_c(0, 0, 0, d, d, a, BODY_BLACK)]
    # Not 5 per side: pins 1-4 and 11-14 are on the left/right sides,
    # pins 5-10 and 15-20 on the top/bottom (data sheet Figures 6 and 7).
    for sign in (-1, 1):
        for p in [(-1.5 + i) * e for i in range(4)]:
            # left/right rows (terminal length along X)
            boxes.append(box_c(sign * (d / 2 - l / 2 + out / 2), p, 0, l + out, b, t, TIN))
        for p in [(-2.5 + i) * e for i in range(6)]:
            # top/bottom rows (terminal length along Y)
            boxes.append(box_c(p, sign * (d / 2 - l / 2 + out / 2), 0, b, l + out, t, TIN))
    boxes.append(box_c(0, 0, 0, ep, ep, 0.02, TIN))
    # pin-1 mark on top, near footprint pad 1 (x -2.35, y -1.2) -> model (-, +)
    boxes.append(box_c(-1.7, 1.7, a, 0.5, 0.5, 0.01, MARK))
    return 'QFN-20_5x5mm_EP2.7x2.7mm_P0.8mm', boxes, 'QFN-20 5x5x0.85 mm, Si3402-B-GM'


def nx1255gb():
    lx, wy, h = 11.8, 5.5, 2.5
    tw, td, th, out = 2.0, 1.5, 0.5, 0.03
    boxes = [box_c(0, 0, 0, lx, wy, h, BODY_DARK)]
    for x in (-2.54, 2.54):
        for sign in (-1, 1):
            # wraparound terminal: 1.5 under the body + 0.5 up the long side
            boxes.append(box_c(x, sign * (wy / 2 - td / 2 + out / 2), 0, tw, td + out, th, TIN))
    return 'NX1255GB', boxes, 'NDK NX1255GB 11.8x5.5x2.5 mm'


def texas_yje():
    lx, wy, h, land, lh = 1.11, 2.16, 0.20, 0.30, 0.02
    boxes = [box_c(0, 0, lh, lx, wy, h, BODY_BLACK)]
    for x in (-0.325, 0.325):
        for y in (-0.65, 0.0, 0.65):
            boxes.append(box_c(x, y, 0, land, land, lh, TIN))
    # pin-A1 mark on top, footprint A1 (x -0.325, y -0.65) -> model (-, +)
    boxes.append(box_c(-0.33, 0.78, lh + h, 0.25, 0.25, 0.005, MARK))
    return 'Texas_YJE', boxes, 'TI PicoStar YJE0006A 1.11x2.16x0.22 mm, CSD83325L'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default=os.path.join(REPO, 'footprints', 'Jonas.3dshapes'))
    out = ap.parse_args().out
    os.makedirs(out, exist_ok=True)
    for fn in (qfn20_si3402, nx1255gb, texas_yje):
        name, boxes, descr = fn()
        path = os.path.join(out, name + '.step')
        write_step_boxes(path, name, boxes, descr)
        print('wrote %s (%d boxes)' % (path, len(boxes)))


if __name__ == '__main__':
    main()
