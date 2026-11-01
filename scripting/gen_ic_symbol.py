# Generates an IC symbol in the house style (docs/symbol-style.md) from a
# spec file and adds it to a hand-maintained symbol library.
#
#   python scripting/gen_ic_symbol.py scripting/ic_symbols/<NAME>.py library/<lib>.kicad_sym
#   kicad-cli sym upgrade --force library/<lib>.kicad_sym   # let KiCad serialize it
#
# The script inserts the symbol text before the library's closing paren.
# KiCad then sorts it into place and writes its own formatting, so the
# git diff of the library is the new symbol only. It refuses to run if the
# library already has a symbol of that name; delete it in the Symbol Editor
# (or pass --replace) to regenerate.
#
# A spec is a Python file defining:
#   NAME   symbol name (the orderable part without packing suffix, or the
#          base part when the symbol covers several)
#   TITLE  short function text for the title band, e.g. "STM32U575 MCU"
#   PROPS  dict of extra fields, in order: Footprint, Datasheet,
#          Description, Manufacturer, Part Number, ki_fp_filters
#   LEFT, RIGHT  lists of (heading, pins), top to bottom, where pins is a
#          list of (number, name, electrical type) or None for an empty row
#   PINCOUNT     optional; asserts pins 1..PINCOUNT appear exactly once
# The library file stays the source of truth: later edits are made in
# KiCad, and the spec records where the pinout came from.
#
# Geometry (everything on the 2.54 mm grid):
#   rows at y = 2.54 * k, k = R..1, top to bottom. Each group takes a
#   separator row (its line drawn through the row), a heading row and one
#   row per pin entry; R is the taller column. The first group's separator
#   is the bottom of the title band.
#   Body (0, 0)-(W, 2.54 * (R + 2)); title band 5.08 high, title text
#   2.032 mm centred in it. Centre divider at W / 2 from the band down.
#   Group separators span only their own column. Lines 0.254 mm. Pins
#   5.08 mm long, outward. The last group of the shorter column runs to
#   the bottom edge.
import argparse
import math
import runpy
import sys

GRID = 2.54
LINE = 0.254
CHAR_W = 1.2          # stroke-font advance per char at 1.27 mm (measured
                      # 1.18-1.25 on uppercase pin names in KiCad 10)
TITLE_CHAR_W = 1.9    # the same at 2.032 mm


def fmt(v):
    return f"{round(v, 4):g}"


def font(size, justify=None):
    j = f"\n\t\t\t\t({justify})" if justify else ""
    return (f"(effects\n\t\t\t\t(font\n\t\t\t\t\t(size {fmt(size)} {fmt(size)})\n"
            f"\t\t\t\t){j}\n\t\t\t)")


def prop(key, val, x, y, hide=True, justify=None):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return (f'\t\t(property "{key}" "{val}"\n\t\t\t(at {fmt(x)} {fmt(y)} 0)\n'
            f"\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no){h}\n"
            f"\t\t\t{font(1.27, justify)}\n\t\t)\n")


def line(x1, y1, x2, y2):
    return (f"\t\t\t(polyline\n\t\t\t\t(pts\n\t\t\t\t\t(xy {fmt(x1)} {fmt(y1)}) (xy {fmt(x2)} {fmt(y2)})\n"
            f"\t\t\t\t)\n\t\t\t\t(stroke\n\t\t\t\t\t(width {LINE})\n\t\t\t\t\t(type solid)\n"
            f"\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type none)\n\t\t\t\t)\n\t\t\t)\n")


def text(s, x, y, size):
    return (f'\t\t\t(text "{s}"\n\t\t\t\t(at {fmt(x)} {fmt(y)} 0)\n'
            f"\t\t\t\t(effects\n\t\t\t\t\t(font\n\t\t\t\t\t\t(size {fmt(size)} {fmt(size)})\n"
            f"\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)\n")


def pin(num, name, typ, x, y, ang):
    eff = "(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)"
    return (f"\t\t\t(pin {typ} line\n\t\t\t\t(at {fmt(x)} {fmt(y)} {ang})\n\t\t\t\t(length 5.08)\n"
            f'\t\t\t\t(name "{name}"\n\t\t\t\t\t{eff}\n\t\t\t\t)\n'
            f'\t\t\t\t(number "{num}"\n\t\t\t\t\t{eff}\n\t\t\t\t)\n\t\t\t)\n')


def build(spec):
    name, title = spec["NAME"], spec["TITLE"]
    cols = (spec["LEFT"], spec["RIGHT"])
    rows = [sum(2 + len(pins) for _, pins in col) for col in cols]
    R = max(rows)
    band_y = GRID * R          # the first group's separator row
    H = GRID * (R + 2)

    need = 0.0
    for col in cols:
        for heading, pins in col:
            need = max(need, len(heading) * CHAR_W + GRID)
            for p in pins:
                if p:
                    need = max(need, 1.016 + len(p[1]) * CHAR_W + GRID / 2)
    col_w = math.ceil(need / GRID - 1e-9) * GRID
    W = max(2 * col_w, math.ceil((len(title) * TITLE_CHAR_W + 2 * GRID) / (2 * GRID)) * 2 * GRID)
    mid = W / 2

    body = [f"\t\t(symbol \"{name}_0_1\"\n",
            f"\t\t\t(rectangle\n\t\t\t\t(start 0 {fmt(H)})\n\t\t\t\t(end {fmt(W)} 0)\n"
            f"\t\t\t\t(stroke\n\t\t\t\t\t(width {LINE})\n\t\t\t\t\t(type solid)\n\t\t\t\t)\n"
            f"\t\t\t\t(fill\n\t\t\t\t\t(type none)\n\t\t\t\t)\n\t\t\t)\n",
            line(0, band_y, W, band_y),
            line(mid, band_y, mid, 0),
            text(title, mid, (band_y + H) / 2, 2.032)]
    pins_out, seen = [], []
    for side, col in enumerate(cols):
        x0, x1 = (0, mid) if side == 0 else (mid, W)
        px, ang = (-5.08, 0) if side == 0 else (W + 5.08, 180)
        k = R
        for gi, (heading, pins) in enumerate(col):
            if gi:
                body.append(line(x0, GRID * k, x1, GRID * k))
            k -= 1
            body.append(text(heading, (x0 + x1) / 2, GRID * k, 1.27))
            k -= 1
            for p in pins:
                if p:
                    num, pname, typ = p
                    seen.append(num)
                    pins_out.append(pin(num, pname, typ, px, GRID * k, ang))
                k -= 1
    body.append("\t\t)\n")

    if len(seen) != len(set(seen)):
        sys.exit(f"{name}: duplicate pin numbers")
    if "PINCOUNT" in spec and sorted(seen, key=int) != [str(i) for i in range(1, spec["PINCOUNT"] + 1)]:
        sys.exit(f"{name}: pins are not exactly 1..{spec['PINCOUNT']}")

    out = [f'\t(symbol "{name}"\n\t\t(pin_names\n\t\t\t(offset 1.016)\n\t\t)\n'
           "\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n"
           "\t\t(in_pos_files yes)\n\t\t(duplicate_pin_numbers_are_jumpers no)\n",
           prop("Reference", "U", 0, H + 0.254, hide=False, justify="justify left bottom"),
           prop("Value", name, 0.254, -1.524, hide=False, justify="justify left top")]
    y = -5.08
    for key, val in spec["PROPS"].items():
        out.append(prop(key, val, 0, y))
        y -= GRID
    out += body
    out.append(f'\t\t(symbol "{name}_1_1"\n' + "".join(pins_out) + "\t\t)\n")
    out.append("\t\t(embedded_fonts no)\n\t)\n")
    return "".join(out), len(seen), W, H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("library")
    ap.add_argument("--replace", action="store_true",
                    help="remove an existing symbol of the same name first")
    a = ap.parse_args()
    spec = runpy.run_path(a.spec)
    sym, npins, W, H = build(spec)

    raw = open(a.library, "rb").read().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    txt = raw.replace("\r\n", "\n")
    head = f'\t(symbol "{spec["NAME"]}"\n'
    if head in txt:
        if not a.replace:
            sys.exit(f'{spec["NAME"]} is already in {a.library}; use --replace')
        i = txt.index(head)
        txt = txt[:i] + txt[txt.index("\n\t)\n", i) + 4:]
    end = txt.rstrip().rindex(")")
    txt = txt[:end] + sym + txt[end:]
    open(a.library, "wb").write(txt.replace("\n", nl).encode("utf-8"))
    print(f'{spec["NAME"]}: {npins} pins, body {fmt(W)} x {fmt(H)} mm; '
          f"now run: kicad-cli sym upgrade --force {a.library}")


if __name__ == "__main__":
    main()
