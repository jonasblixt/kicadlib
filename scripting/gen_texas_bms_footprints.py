#!/usr/bin/env python3
# Generates two TI footprints for the Snigel2 battery board (BMS) into
# footprints/Jonas.pretty. Neither has a stock KiCad match:
#
#   Texas_RSM0032A_VQFN-32-1EP_4x4mm_P0.4mm_EP1.4x1.4mm (BQ40Z50-R2, BQ4050)
#     BQ40Z50-R2 data sheet SLUSCS4C (April 2021), RSM0032A drawing
#     4219107/A: package outline p.52, example board layout p.53, stencil
#     p.54. Body 3.9-4.1 square, 1 mm max; 32 terminals 0.15-0.25 x
#     0.3-0.5 at 0.4 pitch; exposed pad 1.4 +-0.05 square. Land: 32 pads
#     0.6 x 0.2 (R0.05), pad rows 3.8 apart centre to centre; thermal pad
#     1.4 square; stencil 1.3 square on the thermal pad, 0.6 x 0.2 on the
#     pins. Non-solder-mask-defined (the board's 0 mask expansion is within
#     TI's 0.05 max). The stock VQFN-32-1EP_4x4mm_P0.4mm_EP2.8x2.8mm is
#     TI's TPS25750 RSM variant with a 2.8 mm pad: wrong for this part.
#
#   Texas_Q3A_SON-8_3.3x3.3mm_P0.65mm (CSD17579Q3A and other Q3A NexFETs)
#     CSD17579Q3A data sheet SLPS527A (January 2016), section 7.1 Q3A
#     package dimensions, 7.2 recommended PCB pattern, 7.3 stencil. Body
#     2.9-3.1 x 3.05-3.25, 0.9 max. Land: pins 1-4 0.6 x 0.3 at x -1.55,
#     0.65 pitch; drain pad (pins 5-8 and the thermal pad 9, all one pad
#     "5" as on the stock NexFET footprint and the transistor-library
#     symbols) 1.775 x 2.45 from x -0.56, with four 0.635 x 0.3 fingers
#     out to x +1.85. Stencil: four 0.705 x 1.125 apertures on the drain
#     pad (columns 0.905 apart, the left one centred 0.208 left of the
#     package centre, rows centred +-0.6625) and 0.6 x 0.3 on pins 1-8.
#     The stock VSON-8_3.3x3.3mm_P0.65mm_NexFET (from the CSD87334Q3D)
#     has 0.5 mm tall pins at x -1.44 and different drain fingers.
#
# Origin at the package centre. Run, then let KiCad serialize the files:
#   python scripting/gen_texas_bms_footprints.py
#   kicad-cli fp upgrade --force footprints/Jonas.pretty
# 3D models: scripting/gen_package_models.py (texas_rsm0032a, texas_q3a).
import os
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(REPO, 'footprints', 'Jonas.pretty')


def f(v):
    return f"{round(v, 4):g}"


def uid():
    return str(uuid.uuid4())


def text_prop(key, val, x, y, layer, hide=False):
    h = "\n\t\t(hide yes)" if hide else ""
    return (f'\t(property "{key}" "{val}"\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(layer "{layer}"){h}\n'
            f'\t\t(uuid "{uid()}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n'
            f'\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n')


def fp_line(x1, y1, x2, y2, layer, w):
    return (f'\t(fp_line\n\t\t(start {f(x1)} {f(y1)})\n\t\t(end {f(x2)} {f(y2)})\n'
            f'\t\t(stroke\n\t\t\t(width {w})\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "{layer}")\n'
            f'\t\t(uuid "{uid()}")\n\t)\n')


def fp_poly(pts, layer, w, fill):
    p = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
    return (f'\t(fp_poly\n\t\t(pts\n\t\t\t{p}\n\t\t)\n\t\t(stroke\n\t\t\t(width {w})\n'
            f'\t\t\t(type solid)\n\t\t)\n\t\t(fill {"yes" if fill else "no"})\n\t\t(layer "{layer}")\n'
            f'\t\t(uuid "{uid()}")\n\t)\n')


def rect_lines(x1, y1, x2, y2, layer, w):
    return (fp_line(x1, y1, x2, y1, layer, w) + fp_line(x2, y1, x2, y2, layer, w)
            + fp_line(x2, y2, x1, y2, layer, w) + fp_line(x1, y2, x1, y1, layer, w))


def fab_body(hx, hy, ch):
    """Body outline on F.Fab with the pin-1 corner (top left) chamfered."""
    pts = [(-hx + ch, -hy), (hx, -hy), (hx, hy), (-hx, hy), (-hx, -hy + ch)]
    return fp_poly(pts, "F.Fab", 0.1, False)


def fab_ref(size):
    th = round(size * 0.15, 3)
    return (f'\t(fp_text user "${{REFERENCE}}"\n\t\t(at 0 0 0)\n\t\t(layer "F.Fab")\n'
            f'\t\t(uuid "{uid()}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {f(size)} {f(size)})\n'
            f'\t\t\t\t(thickness {th})\n\t\t\t)\n\t\t)\n\t)\n')


def pad(num, x, y, sx, sy, layers, rratio=None, extra=""):
    shape = "roundrect" if rratio else "rect"
    rr = f"\n\t\t(roundrect_rratio {f(rratio)})" if rratio else ""
    lay = " ".join(f'"{l}"' for l in layers)
    return (f'\t(pad "{num}" smd {shape}\n\t\t(at {f(x)} {f(y)})\n\t\t(size {f(sx)} {f(sy)})\n'
            f'\t\t(layers {lay}){rr}{extra}\n\t\t(uuid "{uid()}")\n\t)\n')


def footprint(name, descr, tags, body, ref_y, val_y):
    model = (f'\t(model "${{JONAS_KICADLIB}}/footprints/Jonas.3dshapes/{name}.step"\n'
             '\t\t(offset\n\t\t\t(xyz 0 0 0)\n\t\t)\n\t\t(scale\n\t\t\t(xyz 1 1 1)\n\t\t)\n'
             '\t\t(rotate\n\t\t\t(xyz 0 0 0)\n\t\t)\n\t)\n')
    return (f'(footprint "{name}"\n\t(version 20260206)\n\t(generator "pcbnew")\n'
            f'\t(generator_version "10.0")\n\t(layer "F.Cu")\n\t(descr "{descr}")\n'
            f'\t(tags "{tags}")\n'
            + text_prop("Reference", "REF**", 0, ref_y, "F.SilkS")
            + text_prop("Value", name, 0, val_y, "F.Fab")
            + text_prop("Datasheet", "", 0, 0, "F.Fab", hide=True)
            + text_prop("Description", "", 0, 0, "F.Fab", hide=True)
            + '\t(attr smd)\n\t(duplicate_pad_numbers_are_jumpers no)\n'
            + body + '\t(embedded_fonts no)\n' + model + ')\n')


def rsm0032a():
    name = "Texas_RSM0032A_VQFN-32-1EP_4x4mm_P0.4mm_EP1.4x1.4mm"
    descr = ("TI RSM0032A VQFN-32, 4x4x1mm, 0.4mm pitch, 1.4x1.4mm thermal pad "
             "(BQ40Z50-R2 data sheet SLUSCS4C, drawing 4219107/A pp.52-54: TI land pattern "
             "and stencil). BQ40Z50-R2, BQ4050. Generated by scripting/gen_texas_bms_footprints.py")
    b = ""
    # silkscreen corner marks (body 4.0 + 0.11), clear of the pads by > 0.2
    s, e = 2.11, 1.76
    for sx in (-1, 1):
        for sy in (-1, 1):
            b += fp_line(sx * s, sy * s, sx * e, sy * s, "F.SilkS", 0.12)
            b += fp_line(sx * s, sy * s, sx * s, sy * e, "F.SilkS", 0.12)
    b += fp_poly([(-2.45, -1.4), (-2.75, -1.22), (-2.75, -1.58)], "F.SilkS", 0.12, True)
    b += rect_lines(-2.5, -2.5, 2.5, 2.5, "F.CrtYd", 0.05)
    b += fab_body(2.0, 2.0, 1.0)
    b += fab_ref(0.8)
    lay = ["F.Cu", "F.Mask", "F.Paste"]
    p, c = 0.4, 1.9
    for i in range(8):
        o = -1.4 + i * p
        b += pad(str(1 + i), -c, o, 0.6, 0.2, lay, 0.25)        # left, top to bottom
        b += pad(str(9 + i), o, c, 0.2, 0.6, lay, 0.25)         # bottom, left to right
        b += pad(str(17 + i), c, -o, 0.6, 0.2, lay, 0.25)       # right, bottom to top
        b += pad(str(25 + i), -o, -c, 0.2, 0.6, lay, 0.25)      # top, right to left
    b += pad("33", 0, 0, 1.4, 1.4, ["F.Cu", "F.Mask"], None,
             "\n\t\t(property pad_prop_heatsink)\n\t\t(zone_connect 2)")
    b += pad("", 0, 0, 1.3, 1.3, ["F.Paste"])
    return name, footprint(name, descr, "VQFN NoLead TI RSM0032A BQ40Z50", b, -3.4, 3.4)


def q3a():
    name = "Texas_Q3A_SON-8_3.3x3.3mm_P0.65mm"
    descr = ("TI Q3A SON-8 3.3x3.3mm NexFET, 0.65mm pitch, pins 5-8 and thermal pad as one drain pad 5 "
             "(CSD17579Q3A data sheet SLPS527A, sections 7.1-7.3: TI recommended PCB pattern and "
             "stencil). Generated by scripting/gen_texas_bms_footprints.py")
    b = ""
    hx, hy = 1.55, 1.625
    # silkscreen: top and bottom edges just outside the body, pin-1 tick on the top line
    ys = hy + 0.11
    b += fp_line(-2.1, -ys, hx, -ys, "F.SilkS", 0.12)
    b += fp_line(-hx, ys, hx, ys, "F.SilkS", 0.12)
    b += rect_lines(-2.35, -1.9, 2.35, 1.9, "F.CrtYd", 0.05)
    b += fab_body(hx, hy, 0.775)
    b += fab_ref(0.7)
    lay = ["F.Cu", "F.Mask", "F.Paste"]
    ys4 = (-0.975, -0.325, 0.325, 0.975)
    for i, y in enumerate(ys4):
        b += pad(str(1 + i), -1.55, y, 0.6, 0.3, lay, 0.1667)
    # drain pad: anchor = main rectangle, polygon = TI outline with the fingers
    ax = (-0.56 + 1.215) / 2
    outline = [(-0.56, -1.225), (1.215, -1.225)]
    for yc in ys4:
        outline += [(1.215, yc - 0.15), (1.85, yc - 0.15), (1.85, yc + 0.15), (1.215, yc + 0.15)]
    outline += [(1.215, 1.225), (-0.56, 1.225)]
    pts = " ".join(f"(xy {f(x - ax)} {f(y)})" for x, y in outline)
    b += (f'\t(pad "5" smd custom\n\t\t(at {f(ax)} 0)\n\t\t(size 1.775 2.45)\n'
          f'\t\t(layers "F.Cu" "F.Mask")\n\t\t(property pad_prop_heatsink)\n'
          f'\t\t(zone_connect 2)\n\t\t(options\n\t\t\t(clearance outline)\n\t\t\t(anchor rect)\n\t\t)\n'
          f'\t\t(primitives\n\t\t\t(gr_poly\n\t\t\t\t(pts\n\t\t\t\t\t{pts}\n\t\t\t\t)\n'
          f'\t\t\t\t(width 0)\n\t\t\t\t(fill yes)\n\t\t\t)\n\t\t)\n\t\t(uuid "{uid()}")\n\t)\n')
    for cx in (-0.208, -0.208 + 0.905):
        for cy in (-0.6625, 0.6625):
            b += pad("", cx, cy, 0.705, 1.125, ["F.Paste"])
    for y in ys4:
        b += pad("", 1.55, y, 0.6, 0.3, ["F.Paste"], 0.1667)
    return name, footprint(name, descr, "SON NexFET TI Q3A CSD17579Q3A", b, -2.7, 2.7)


def main():
    for fn in (rsm0032a, q3a):
        name, text = fn()
        path = os.path.join(LIB, name + ".kicad_mod")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("wrote", path)


if __name__ == "__main__":
    main()
