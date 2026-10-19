# Re-runs every database-library importer and checks that it reproduces the
# committed library (cleanup review A4.5): the .kicad_dbl must be identical
# text (line endings aside) and the .db must hold the same schema and rows
# in the same order. Outputs go to a temporary directory; library/ is never
# touched (KiCad may have the .db files open).
#
#   python scripting/check_importers.py [library ...]
#
# Most importers take --csv/--db/--table/--kicad-dbl; the call used is the
# repo convention: data/<library>.csv or data/<library>_<n>.csv, table =
# library name (EXTRA_CSV lists the exceptions). The others
# (murata_lqw/murata_cap based, AccuP) default everything and only get
# --db/--kicad-dbl.
import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LIB = REPO / "library"
SCRIPT = {"cap_rfmw_kyocera_accu_p": "import_cap_rfmw_kyocera_accup.py"}  # until the A4.2 rename
EXTRA_CSV = {
    "ind_rfmw_murata_lqg": ["ind_rfmw_murata_lqg15h.csv", "ind_rfmw_murata_lqg18h.csv"],
    "xtal_epson": ["xtal_epson.csv", "xtal_epson_32k.csv"],
    "xtal_ndk": ["xtal_ndk_parts.csv"],
}


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True).stdout


def db_dump(path):
    con = sqlite3.connect(path)
    out = []
    for name, sql in con.execute("SELECT name, sql FROM sqlite_master ORDER BY name"):
        out.append((name, sql and " ".join(sql.split())))
        if sql and sql.startswith("CREATE TABLE"):
            out += con.execute(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall()
    con.close()
    return out


def command(lib, out_db, out_dbl):
    script = REPO / "scripting" / SCRIPT.get(lib, f"import_{lib}.py")
    if not script.exists():
        return None
    src = script.read_text(encoding="utf-8")
    cmd = [sys.executable, str(script)]
    if "required=True" in src:
        csvs = EXTRA_CSV.get(lib) or sorted(
            p.name for p in (REPO / "data").glob(f"{lib}*.csv")
            if p.stem == lib or p.stem[len(lib):].lstrip("_").isdigit())
        table = json.loads((LIB / f"{lib}.kicad_dbl").read_text(encoding="utf-8"))["libraries"][0]["table"]
        cmd += ["--csv", *[str(REPO / "data" / c) for c in csvs], "--table", table]
    return cmd + ["--db", str(out_db), "--kicad-dbl", str(out_dbl)]


def main():
    libs = sys.argv[1:] or sorted(p.stem for p in LIB.glob("*.kicad_dbl"))
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        for lib in libs:
            out_db, out_dbl = Path(tmp) / f"{lib}.db", Path(tmp) / f"{lib}.kicad_dbl"
            cmd = command(lib, out_db, out_dbl)
            if cmd is None:
                print(f"{lib}: NO IMPORTER")
                bad += 1
                continue
            head_db = Path(tmp) / f"{lib}.head.db"
            head_db.write_bytes(git("show", f"HEAD:library/{lib}.db"))
            r = subprocess.run(cmd, cwd=REPO / "scripting", capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            if r.returncode:
                print(f"{lib}: IMPORTER FAILED: {(r.stderr.strip().splitlines() or ['?'])[-1]}")
                bad += 1
                continue
            warnings = sum("WARNING" in line for line in r.stdout.splitlines())
            head_dbl = git("show", f"HEAD:library/{lib}.kicad_dbl").replace(b"\r\n", b"\n")
            new_dbl = out_dbl.read_bytes().replace(b"\r\n", b"\n")
            dbl_ok = head_dbl == new_dbl
            db_ok = db_dump(head_db) == db_dump(out_db)
            if not (dbl_ok and db_ok):
                bad += 1
            print(f"{lib}: {'ok' if dbl_ok and db_ok else 'DIFFERS'}"
                  f"{'' if dbl_ok else ' (.kicad_dbl)'}{'' if db_ok else ' (.db)'}"
                  f"{f', {warnings} duplicate warnings' if warnings else ''}")
    print("All importers reproduce their libraries." if not bad else f"{bad} library(s) differ.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
