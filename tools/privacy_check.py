#!/usr/bin/env python3
"""Scan git-tracked + untracked-not-ignored files for pdf/ged/gedcom/raster images, emails, phone numbers.
Synthetic SVG is allowed. Exit 1 on any finding. Falls back to a directory walk if not a git repo."""
import argparse, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAD_EXT = {".pdf", ".ged", ".gedcom", ".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".bmp", ".webp", ".heic"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"(?<![\w.])(?:\+\d[\d\s().-]{8,}\d|\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4})(?![\w])")
SAFE_EMAIL_DOMAINS = {"example.com", "example.org", "example.net", "invalid", "test"}

def files(root):
    try:
        out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             cwd=root, capture_output=True, check=True).stdout.decode().split("\0")
        return [f for f in out if f]
    except (OSError, subprocess.CalledProcessError):
        res = []
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in (".git", "dist", "__pycache__", "private", "scans", "raw")]
            res += [os.path.relpath(os.path.join(dp, f), root) for f in fn]
        return res

def scan(root):
    findings = []
    for rel in files(root):
        full = os.path.join(root, rel)
        if not os.path.isfile(full): continue
        ext = os.path.splitext(rel)[1].lower()
        if ext in BAD_EXT:
            findings.append(f"{rel}: forbidden file type {ext}"); continue
        try: text = open(full, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError): findings.append(f"{rel}: unreadable/binary"); continue
        for m in EMAIL.finditer(text):
            if m.group(0).rsplit("@", 1)[1].lower() not in SAFE_EMAIL_DOMAINS:
                findings.append(f"{rel}: email address")
                break
        if PHONE.search(text): findings.append(f"{rel}: phone-like number")
    return findings

def main(argv=None, root=ROOT):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    f = scan(root)
    for x in f: print("FAIL", x)
    print("privacy check:", "FAILED" if f else "ok")
    return 1 if f else 0

if __name__ == "__main__":
    sys.exit(main())
