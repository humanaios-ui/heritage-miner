#!/usr/bin/env python3
"""Compare printed page numbers vs chapter TOC in data/manuscript.json.
Lists missing / blank / duplicate / unlisted. Never reports 'complete'; always states OPEN."""
import argparse, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def audit(m):
    pages = m.get("pages", [])
    by_id = {p["id"]: p for p in pages}
    toc = [pid for c in m.get("chapters", []) for pid in c.get("pages", [])]
    nums = [p["printed_number"] for p in pages if p.get("printed_number") is not None]
    seen, dups = set(), set()
    for n in nums:
        (dups if n in seen else seen).add(n)
    gaps = []
    if nums:
        have = set(nums)
        gaps = [n for n in range(min(nums), max(nums) + 1) if n not in have]
    tocseen, tocdup = set(), set()
    for pid in toc:
        (tocdup if pid in tocseen else tocseen).add(pid)
    return {
        "page_records": len(pages),
        "printed_numbers": sorted(seen),
        "duplicate_printed_numbers": sorted(dups),
        "unaccounted_numbers_in_range": gaps,
        "unnumbered_pages": [p["id"] for p in pages if p.get("printed_number") is None],
        "blank_pages": [p["id"] for p in pages if p.get("transcription_status") == "none" and p.get("kind") == "text"],
        "pages_without_transcription": [p["id"] for p in pages if p.get("transcription_status") == "none"],
        "toc_unknown_page_ids": sorted(pid for pid in toc if pid not in by_id),
        "toc_duplicate_page_ids": sorted(tocdup),
        "pages_not_in_toc": [p["id"] for p in pages if p["id"] not in tocseen],
        "completeness": "OPEN",
        "statement": "Completeness is NOT established. Gaps are unaccounted, not proven missing.",
    }

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manuscript", default=os.path.join(ROOT, "data", "manuscript.json"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    with open(a.manuscript, encoding="utf-8") as f:
        r = audit(json.load(f))
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        for k, v in r.items():
            print(f"{k}: {v}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
