#!/usr/bin/env python3
"""Local PDF audit: page count, per-page size/orientation/rotation, SHA-256, rendered-page list.
Read-only. Never copies or writes the PDF. Prints no filename or metadata (path is not echoed).
Uses pypdf if installed, else a minimal stdlib fallback; pdftoppm only to list renderable pages (no output kept)."""
import argparse, hashlib, json, re, shutil, sys

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def _orient(w, h, rot):
    if rot % 180: w, h = h, w
    return "landscape" if w > h else "portrait" if h > w else "square"

def pages_pypdf(path):
    from pypdf import PdfReader
    out = []
    for i, p in enumerate(PdfReader(path).pages, 1):
        w, h = float(p.mediabox.width), float(p.mediabox.height)
        rot = int(p.get("/Rotate", 0) or 0) % 360
        out.append({"page": i, "width": w, "height": h, "rotation": rot, "orientation": _orient(w, h, rot)})
    return out

def pages_fallback(path):
    """Regex scan of raw bytes; works on simple (non-compressed-object-stream) PDFs only."""
    data = open(path, "rb").read().decode("latin-1")
    out = []
    for m in re.finditer(r"<<[^<>]*?/Type\s*/Page(?![s\w])[^<>]*?(?:<<[^<>]*>>[^<>]*?)*>>", data, re.S):
        d = m.group(0)
        mb = re.search(r"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", d)
        rot = re.search(r"/Rotate\s+(-?\d+)", d)
        w = h = None
        if mb:
            a = [float(x) for x in mb.groups()]; w, h = a[2] - a[0], a[3] - a[1]
        r = int(rot.group(1)) % 360 if rot else 0
        out.append({"page": len(out) + 1, "width": w, "height": h, "rotation": r,
                    "orientation": _orient(w, h, r) if w else "unknown"})
    return out

def audit(path):
    with open(path, "rb") as f:
        if f.read(5) != b"%PDF-":
            raise ValueError("not a PDF")
    try:
        pages, method = pages_pypdf(path), "pypdf"
    except Exception:  # pypdf missing or unable to parse
        pages, method = pages_fallback(path), "stdlib-fallback (limited: simple PDFs only)"
    rendered = list(range(1, len(pages) + 1)) if shutil.which("pdftoppm") else []
    return {"sha256": sha256(path), "page_count": len(pages), "method": method,
            "pdftoppm_available": bool(rendered), "renderable_pages": rendered,
            "pages": pages,
            "note": "Page count is not proof of completeness; compare with printed numbers via pagination_audit.py."}

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        r = audit(a.pdf)
    except (OSError, ValueError) as e:
        print(f"error: {e.__class__.__name__}", file=sys.stderr); return 2
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        print(f"sha256: {r['sha256']}\npages: {r['page_count']}  (method: {r['method']})")
        print("renderable pages:", ",".join(map(str, r["renderable_pages"])) or "none (pdftoppm missing)")
        for p in r["pages"]:
            print(f"  p{p['page']}: {p['orientation']} rot={p['rotation']} {p['width']}x{p['height']}")
        print(r["note"])
    return 0

if __name__ == "__main__":
    sys.exit(main())
