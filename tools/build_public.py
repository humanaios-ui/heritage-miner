#!/usr/bin/env python3
"""Build dist/ public bundle: reader, manuscript, research, pages, and ONLY approved contributions.
Fails (exit 1, dist removed) if any pending/rejected contribution content leaks into the output."""
import argparse, glob, json, os, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Leak(Exception): pass

def build(root, out):
    contribs = []
    for p in sorted(glob.glob(os.path.join(root, "data", "contributions", "*.json"))):
        if os.path.basename(p) == "index.json": continue
        with open(p, encoding="utf-8") as f: contribs.append(json.load(f))
    approved = [c for c in contribs if c.get("status") == "approved"]
    blocked = [c for c in contribs if c.get("status") != "approved"]
    if os.path.isdir(out): shutil.rmtree(out)
    os.makedirs(os.path.join(out, "data", "contributions"))
    for d in ("reader",):
        if os.path.isdir(os.path.join(root, d)): shutil.copytree(os.path.join(root, d), os.path.join(out, d))
    for f in ("manuscript.json", "research.json"):
        if os.path.isfile(os.path.join(root, "data", f)): shutil.copy(os.path.join(root, "data", f), os.path.join(out, "data", f))
    if os.path.isdir(os.path.join(root, "data", "pages")):
        shutil.copytree(os.path.join(root, "data", "pages"), os.path.join(out, "data", "pages"))
    for c in approved:
        with open(os.path.join(out, "data", "contributions", c["id"] + ".json"), "w", encoding="utf-8") as f:
            json.dump(c, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out, "data", "contributions", "index.json"), "w") as f:
        json.dump([c["id"] + ".json" for c in approved], f)
    # leak check: no blocked id file, no blocked title/body text anywhere in dist
    for c in blocked:
        if os.path.exists(os.path.join(out, "data", "contributions", c["id"] + ".json")):
            raise Leak(f"{c['id']} ({c.get('status')}) copied")
    for dp, _, fs in os.walk(out):
        for fn in fs:
            try: text = open(os.path.join(dp, fn), encoding="utf-8").read()
            except (UnicodeDecodeError, OSError): continue
            for c in blocked:
                for k in ("body", "title"):
                    if c.get(k) and c[k] in text:
                        raise Leak(f"{c['id']} ({c.get('status')}) {k} found in {os.path.relpath(os.path.join(dp, fn), out)}")
    return [c["id"] for c in approved]

def main(argv=None, root=ROOT):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(root, "dist"))
    a = ap.parse_args(argv)
    try:
        ids = build(root, a.out)
    except Leak as e:
        shutil.rmtree(a.out, ignore_errors=True)
        print(f"LEAK: {e}", file=sys.stderr); return 1
    print(f"built {a.out}: approved contributions = {ids}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
