# Renders every footprint in footprints/Jonas.pretty with its 3D model and
# writes an HTML contact sheet (footprints review F5.6), so the custom
# models can be checked visually: body on the board, pin 1 and pins over
# the pads, connector openings facing the right way.
#
# Needs KiCad 10's Python (for pcbnew) and kicad-cli:
#   "C:\Program Files\KiCad\10.0\bin\python.exe" scripting/render_footprints.py --out <dir>
# Each footprint is placed alone on a scratch board whose Edge.Cuts outline
# is its bounding box plus a margin, then rendered from the top and
# isometrically (kicad-cli pcb render). ${JONAS_KICADLIB} is set to this
# repo for the model paths. Output: <dir>/index.html plus the PNGs and
# boards; nothing is written into the repo.
import argparse
import html
import os
import subprocess
import sys
from pathlib import Path

import pcbnew

REPO = Path(__file__).resolve().parent.parent
LIB = REPO / "footprints" / "Jonas.pretty"
KICAD_CLI = Path(sys.executable).parent / "kicad-cli.exe"
MARGIN_MM = 1.0
VIEWS = {"top": [], "iso": ["--rotate", "-55,0,45", "--zoom", "0.6"]}


def make_board(name, path):
    board = pcbnew.BOARD()
    fp = pcbnew.FootprintLoad(str(LIB), name)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(100), pcbnew.FromMM(100)))
    board.Add(fp)
    box = fp.GetBoundingBox(False)
    box.Inflate(pcbnew.FromMM(MARGIN_MM))
    rect = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECT)
    rect.SetStart(box.GetOrigin())
    rect.SetEnd(box.GetEnd())
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(pcbnew.FromMM(0.05))
    board.Add(rect)
    board.Save(str(path))
    models = [m.m_Filename for m in fp.Models()]
    return models


def render(board, png, extra, env):
    cmd = [str(KICAD_CLI), "pcb", "render", "-o", str(png), "--width", "480",
           "--height", "360", "--background", "opaque", "--quality", "high",
           *extra, str(board)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return r.returncode == 0 and png.exists()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="output directory (outside the repo)")
    ap.add_argument("names", nargs="*", help="only these footprints (default: all)")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, JONAS_KICADLIB=str(REPO))

    names = args.names or sorted(p.stem for p in LIB.glob("*.kicad_mod"))
    rows = []
    for i, name in enumerate(names, 1):
        board = out / f"{name}.kicad_pcb"
        models = make_board(name, board)
        ok = {v: render(board, out / f"{name}_{v}.png", extra, env)
              for v, extra in VIEWS.items()}
        print(f"{i}/{len(names)} {name}: {'ok' if all(ok.values()) else 'FAILED'}", flush=True)
        rows.append((name, models, ok))

    cells = []
    for name, models, ok in rows:
        imgs = "".join(
            f'<img src="{html.escape(name)}_{v}.png" alt="{v}">' if ok[v]
            else f'<div class="fail">{v} render failed</div>' for v in VIEWS)
        model_txt = "<br>".join(html.escape(os.path.basename(m)) for m in models) or "<em>no 3D model</em>"
        cells.append(f'<figure>{imgs}<figcaption><b>{html.escape(name)}</b><br>{model_txt}</figcaption></figure>')
    (out / "index.html").write_text(
        "<!doctype html><meta charset=utf-8><title>Jonas.pretty renders</title>"
        "<style>body{font:13px sans-serif;margin:16px;background:#fafafa}"
        "figure{display:inline-block;margin:6px;padding:6px;background:#fff;border:1px solid #ddd;vertical-align:top}"
        "img{width:240px;height:180px;margin:1px}figcaption{max-width:484px;word-break:break-all}"
        ".fail{display:inline-block;width:240px;height:180px;background:#fdd;text-align:center;line-height:180px}</style>"
        f"<h1>Jonas.pretty: {len(rows)} footprints (top / iso)</h1>" + "".join(cells),
        encoding="utf-8")
    print(f"Wrote {out / 'index.html'}")


if __name__ == "__main__":
    main()
