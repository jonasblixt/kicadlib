# IC symbol style

Every IC symbol in the hand-maintained libraries (`library/*.kicad_sym`)
uses this style: a single-unit box with non-functional graphics (a title
band, a centre divider and labelled pin groups) that show what the part
is and how its pins are organised. Reference symbols: `cpu/MCXN247VKLT`
(the canonical one), `analog/TAS2770`, and the generated
`cpu/STM32U575RIT6` and `analog/ISM330BX`. Passives, connectors and other
simple parts keep their plain symbols.

Set down 2026-11-01 at Jonas's request.

## Rules

1. **Title band.** A full-width band across the top of the body, 5.08 mm
   high, separated by a horizontal line. It holds a short function title
   in 2.032 mm text, centred: the part family and what it is
   (`STM32U575 MCU`, `MCX N247 MCU`, `6-Axis IMU`,
   `Digital Input Class-D Audio Amp`), not the full part number, which is
   already the Value.
2. **Centre divider.** A vertical line at the middle of the body, from the
   title band to the bottom edge, splits it into a left and a right
   column. Pins on the left edge belong to the left column, and so on.
3. **Pin groups.** Each column is split into groups by horizontal lines
   that span that column only; the two columns' groups are independent.
   Each group has a heading in 1.27 mm text, centred in its column, one
   row below its separator line: `Power`, `Reset / Boot`, `Clocks`,
   `Port A`, `SPI / I2C`, `Interrupts`, `I/O 0`, `USB`, `Misc`. The last
   group of the shorter column runs to the bottom edge.
4. **Spacing.** Everything on the 2.54 mm grid: one empty row between a
   group's last pin and the next separator line, one between the line and
   the heading, then the pins; one empty row between the last pin and the
   bottom edge. Inside a group an empty row may split sub-groups (supplies
   from grounds).
5. **Lines** are 0.254 mm wide: the body rectangle, the band line, the
   divider and the group lines. No fill.
6. **Width.** Both columns are equally wide, a multiple of 2.54 mm, wide
   enough that the longest pin name or heading in either column clears
   the divider (about 1.2 mm per character at 1.27 mm text). Render the
   symbol and look before finishing.
7. **Group order.** Power at the top of a column (supplies, an empty row,
   then grounds), then reset/boot/clocks/debug, then the I/O ports or
   interfaces in datasheet order. Balance the two columns' heights.
8. **Pins.** 5.08 mm long, pin name offset 1.016, names as in the
   datasheet. Electrical types: supplies and grounds `power_in`, regulator
   outputs (VCAP, DREG) `power_out`, GPIO `bidirectional`, and the
   datasheet's direction for dedicated pins. Every package pin appears
   once; exposed pads get their own pin.
9. **Text fields.** Reference `U` at the top-left corner, left/bottom
   justified; Value (the symbol name) at the bottom-left corner,
   left/top justified. Hidden: Footprint (with library nickname),
   Datasheet (manufacturer URL), Description, Manufacturer, Part Number
   (orderable code, packing suffix included), `ki_fp_filters`.

## How to make one

`scripting/gen_ic_symbol.py` draws this style from a spec file in
`scripting/ic_symbols/<NAME>.py` (pin groups per column, title, fields,
and a header comment citing the datasheet revision and table the pinout
came from). It inserts the symbol into a library; then let KiCad write
the file:

```
python scripting/gen_ic_symbol.py scripting/ic_symbols/<NAME>.py library/<lib>.kicad_sym
kicad-cli sym upgrade --force library/<lib>.kicad_sym
kicad-cli sym export svg -s <NAME> -o <tmp> library/<lib>.kicad_sym   # look at it
python scripting/audit_refs.py
```

Check that the git diff of the library contains only the new symbol.
After that the library file is the source of truth: later edits are made
in KiCad's Symbol Editor, and the spec stays as the record of where the
pinout came from. Large BGA parts that need several units use the same
style in each unit, with the unit's function as its title.
