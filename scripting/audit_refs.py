# Audits the library's cross-references (cleanup review A2.5 / F7.6):
#   1. every symbol's Footprint field names an existing footprint, with a
#      library nickname (Jonas:... or a stock KiCad library);
#   2. every footprint used by a database library exists;
#   3. every 3D model path in footprints/Jonas.pretty resolves, and every
#      file in Jonas.3dshapes is referenced (or listed in PER_BOARD_MODELS);
#   4. symbol pins vs footprint pads: no pin without a pad, no duplicate
#      pin numbers; pads without a pin are listed for information;
#   5. nothing outside docs/ still depends on modules/.
# Exits 1 if any of 1-3, the pin checks of 4, or 5 fail.
#
#   python scripting/audit_refs.py [--kicad-share "C:\Program Files\KiCad\10.0\share\kicad"] [-v]
import argparse
import glob
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JONAS_PRETTY = REPO / "footprints" / "Jonas.pretty"
JONAS_3D = REPO / "footprints" / "Jonas.3dshapes"
# Footprint fields intentionally left empty (generic symbols; the DB or the
# user supplies the footprint).
GENERIC = {"connectors/Conn_01x30", "diode_misc/D_TVS_Uni", "power/BOM_Entry", "power/PWR_FLAG"}
# Models in Jonas.3dshapes that no Jonas footprint references because a
# board uses them on a stock footprint (F5.4: stock footprints without a
# KiCad model get one per board).
PER_BOARD_MODELS = {"614105150721 (rev1).stp"}  # poetato: USB_Micro-B_Wuerth_614105150721_Vertical


def symbols(path):
    """Yield (name, body) for each top-level symbol; derived symbols get their parent's pins."""
    text = path.read_text(encoding="utf-8")
    bodies = {m.group(1): m.group(2) for m in
              re.finditer(r'^\t\(symbol "([^"]+)"(.*?)^\t\)', text, re.S | re.M)}
    for name, body in bodies.items():
        parent = re.search(r'\(extends "([^"]+)"\)', body)
        pins_from = bodies.get(parent.group(1), body) if parent else body
        yield name, body, pins_from


def pins_of(body):
    pins = {}
    for m in re.finditer(r'\(pin \w+ \w+.*?\(name "([^"]*)".*?\(number "([^"]*)"', body, re.S):
        pins.setdefault(m.group(2), []).append(m.group(1))
    return pins


def footprint_file(ref, stock_dir):
    if ":" not in ref:
        return None
    lib, name = ref.split(":", 1)
    if lib == "Jonas":
        return JONAS_PRETTY / f"{name}.kicad_mod"
    return stock_dir / f"{lib}.pretty" / f"{name}.kicad_mod"


def resolve_model(path, kicad_share):
    p = path.replace("${JONAS_KICADLIB}", str(REPO))
    p = p.replace("${KICAD10_3DMODEL_DIR}", str(kicad_share / "3dmodels"))
    return Path(p)


def main():
    ap = argparse.ArgumentParser(description="Audit footprint, model and pin references.")
    ap.add_argument("--kicad-share", default=r"C:\Program Files\KiCad\10.0\share\kicad")
    ap.add_argument("-v", "--verbose", action="store_true", help="also list pads without a pin")
    args = ap.parse_args()
    share = Path(args.kicad_share)
    stock = share / "footprints"
    failures = 0

    # 1 + 4: symbols
    broken, empty, pin_problems, unpinned = [], [], [], []
    n = 0
    for lib in sorted((REPO / "library").glob("*.kicad_sym")):
        for name, body, pins_body in symbols(lib):
            key = f"{lib.stem}/{name}"
            if re.search(r"\(power[ )]", body.split("(property", 1)[0]):
                continue
            n += 1
            m = re.search(r'\(property "Footprint" "([^"]*)"', body)
            ref = m.group(1) if m else ""
            if not ref:
                if key not in GENERIC:
                    empty.append(key)
                continue
            fpath = footprint_file(ref, stock)
            if fpath is None or not fpath.exists():
                broken.append(f"{key} -> {ref}")
                continue
            pads = set(re.findall(r'\(pad "([^"]+)"', fpath.read_text(encoding="utf-8")))
            pins = pins_of(pins_body)
            no_pad = sorted(set(pins) - pads)
            dup = sorted(k for k, v in pins.items() if len(v) > 1)
            if no_pad or dup:
                pin_problems.append(f"{key} ({ref}): pins without pad {no_pad}, duplicate pins {dup}")
            extra = sorted(pads - set(pins))
            if extra:
                unpinned.append(f"{key}: {extra}")
    print(f"Symbols checked: {n}")
    for title, items in (("Broken footprint links", broken), ("Empty footprint fields", empty),
                         ("Pin/pad problems", pin_problems)):
        print(f"{title}: {len(items)}")
        for i in items:
            print(f"  {i}")
        failures += len(items)
    print(f"Symbols with pads that have no pin (NC, mounting, depopulated): {len(unpinned)}")
    if args.verbose:
        for i in unpinned:
            print(f"  {i}")

    # 2: database libraries
    db_broken = []
    for db in sorted((REPO / "library").glob("*.db")):
        dbl = json.loads(db.with_suffix(".kicad_dbl").read_text(encoding="utf-8"))
        for l in dbl["libraries"]:
            con = sqlite3.connect(db)
            for (ref,) in con.execute(f'SELECT DISTINCT "{l["footprints"]}" FROM "{l["table"]}"'):
                if not ref:
                    continue
                for one in ref.split(";"):
                    f = footprint_file(one.strip(), stock)
                    if f is None or not f.exists():
                        db_broken.append(f"{db.stem}: {one}")
            con.close()
    print(f"Broken database footprints: {len(db_broken)}")
    for i in db_broken:
        print(f"  {i}")
    failures += len(db_broken)

    # 3: models
    missing, used = [], set()
    for f in sorted(JONAS_PRETTY.glob("*.kicad_mod")):
        for p in re.findall(r'\(model "([^"]+)"', f.read_text(encoding="utf-8")):
            if "Jonas.3dshapes/" in p:
                used.add(p.rsplit("/", 1)[1])
            if not resolve_model(p, share).exists():
                missing.append(f"{f.stem}: {p}")
    orphans = sorted(set(os.listdir(JONAS_3D)) - used - PER_BOARD_MODELS)
    print(f"Missing 3D models: {len(missing)}")
    for i in missing:
        print(f"  {i}")
    print(f"Unreferenced files in Jonas.3dshapes: {len(orphans)}")
    for i in orphans:
        print(f"  {i}")
    failures += len(missing) + len(orphans)

    # 5: modules/ - real dependencies only (Footprint fields with the old
    # "footprints:" nickname, model paths, code), not provenance notes in
    # descr fields and comments ("Migrated from modules/...").
    legacy = []
    uses = {
        ".kicad_sym": r'\(property "Footprint" "footprints:',
        ".kicad_mod": r'\(model "[^"]*modules/',
        ".kicad_dbl": r'modules/',
        ".py": r'^[^#\n]*["\']([^"\'\n]*/)?modules["\'/]',
    }
    for f in glob.glob(str(REPO / "**" / "*"), recursive=True):
        rel = Path(f).relative_to(REPO).as_posix()
        pattern = uses.get(Path(f).suffix)
        if not pattern or rel.startswith(("modules/", "docs/")) or rel == "scripting/audit_refs.py":
            continue
        text = Path(f).read_text(encoding="utf-8", errors="ignore")
        if re.search(pattern, text, re.M):
            legacy.append(rel)
    print(f"Files still using modules/: {len(legacy)}")
    for i in legacy:
        print(f"  {i}")
    failures += len(legacy)

    print("OK" if not failures else f"{failures} problem(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
