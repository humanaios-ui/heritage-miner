#!/usr/bin/env python3
"""Review queue for data/contributions/*.json.
  review_queue.py list [--status pending]
  review_queue.py approve|reject <id> --reviewer NAME [--note TEXT]
Decisions append a hash-chained entry to data/review_log.jsonl:
  hash = sha256(prev_hash + canonical_json(record minus prev_hash,hash)), canonical = sorted keys, compact.
Pending items are never copied anywhere. Contributions never modify manuscript.json."""
import argparse, datetime, glob, hashlib, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZERO = "0" * 64

def canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def paths(root):
    return os.path.join(root, "data", "contributions"), os.path.join(root, "data", "review_log.jsonl")

def load_all(root):
    d, _ = paths(root)
    out = []
    for p in sorted(glob.glob(os.path.join(d, "*.json"))):
        if os.path.basename(p) == "index.json": continue
        with open(p, encoding="utf-8") as f: out.append((p, json.load(f)))
    return out

def write_index(root):
    """data/contributions/index.json = sorted list of contribution filenames (static hosts cannot list dirs)."""
    d, _ = paths(root)
    names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(d, "*.json")) if os.path.basename(p) != "index.json")
    with open(os.path.join(d, "index.json"), "w", encoding="utf-8") as f: json.dump(names, f)
    return names

def read_log(root):
    _, lp = paths(root)
    if not os.path.isfile(lp): return []
    with open(lp, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

def verify_log(entries):
    prev = ZERO
    for e in entries:
        body = {k: v for k, v in e.items() if k not in ("prev_hash", "hash")}
        if e.get("prev_hash") != prev or e.get("hash") != hashlib.sha256((prev + canon(body)).encode()).hexdigest():
            return False
        prev = e["hash"]
    return True

def decide(root, cid, decision, reviewer, note="", today=None):
    if not reviewer or not reviewer.strip(): raise SystemExit("--reviewer is required")
    items = {c["id"]: (p, c) for p, c in load_all(root)}
    if cid not in items: raise SystemExit(f"unknown contribution {cid}")
    path, c = items[cid]
    if c["status"] != "pending": raise SystemExit(f"{cid} is {c['status']}, not pending")
    log = read_log(root)
    if not verify_log(log): raise SystemExit("review_log.jsonl hash chain is broken; refusing to append")
    at = today or datetime.date.today().isoformat()
    body = {"seq": len(log) + 1, "at": at, "contribution_id": cid, "decision": decision,
            "reviewer": reviewer.strip(), "note": note}
    prev = log[-1]["hash"] if log else ZERO
    rec = dict(body, prev_hash=prev, hash=hashlib.sha256((prev + canon(body)).encode()).hexdigest())
    c.update(status=decision, reviewed_by=reviewer.strip(), reviewed_at=at)
    with open(paths(root)[1], "a", encoding="utf-8") as f: f.write(canon(rec) + "\n")
    with open(path, "w", encoding="utf-8") as f: json.dump(c, f, indent=2, ensure_ascii=False)
    write_index(root)
    return rec

def main(argv=None, root=ROOT):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("list"); l.add_argument("--status", choices=["pending", "approved", "rejected"])
    for n in ("approve", "reject"):
        s = sub.add_parser(n); s.add_argument("id"); s.add_argument("--reviewer", required=True); s.add_argument("--note", default="")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for _, c in load_all(root):
            if a.status is None or c["status"] == a.status:
                print(f"{c['id']}\t{c['status']}\t{c['audience']}\t{c['kind']}\t{c['title']}")
        return 0
    rec = decide(root, a.id, "approved" if a.cmd == "approve" else "rejected", a.reviewer, a.note)
    print(f"{rec['decision']} {a.id} (seq {rec['seq']}, hash {rec['hash'][:12]})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
