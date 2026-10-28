#!/usr/bin/env python3
"""Validate data/ against docs/DATA_CONTRACT.md (stdlib only). Exit 1 on any error."""
import glob, hashlib, json, os, re, sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errs = []
def err(m): errs.append(m)
def load(p):
    try:
        with open(os.path.join(ROOT, p), encoding="utf-8") as f: return json.load(f)
    except Exception as e:
        err(f"{p}: cannot load ({e})"); return None
def need(o, keys, where):
    for k in keys:
        if k not in o: err(f"{where}: missing '{k}'")

PII = [re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), re.compile(r"(?<!\d)(?:\+?\d[\s().-]?){10,}(?!\d)")]
def pii(text, where):
    for rx in PII:
        if rx.search(text): err(f"{where}: possible PII ({rx.pattern[:12]}...)")

# manuscript
m = load("data/manuscript.json") or {}
need(m, ["edition","synthetic","version","title","dedication","foreword","chapters","pages","completeness"], "manuscript")
if m.get("synthetic") is not True: err("manuscript: synthetic must be true")
ids = set(); page_ids = []
for p in m.get("pages", []):
    w = f"page {p.get('id')}"
    need(p, ["id","printed_number","scan","alt","orientation_corrected","transcription","transcription_status","interpretation_note","kind"], w)
    if p.get("id") in ids: err(f"{w}: duplicate id")
    ids.add(p.get("id")); page_ids.append(p.get("id"))
    if p.get("kind") not in ("text","photo","diagram","cover"): err(f"{w}: bad kind")
    st, tr = p.get("transcription_status"), p.get("transcription")
    if st not in ("verified","unchecked","none"): err(f"{w}: bad transcription_status")
    if st == "none" and tr is not None: err(f"{w}: status none but transcription present")
    if st in ("verified","unchecked") and not tr: err(f"{w}: status {st} but no transcription")
    note = p.get("interpretation_note")
    if note and tr and note in tr: err(f"{w}: interpretation_note merged into transcription")
    n = p.get("printed_number")
    if n is not None and (not isinstance(n, int) or n % 2 == 0): err(f"{w}: printed_number must be odd int or null")
    if not p.get("alt"): err(f"{w}: empty alt")
    if not isinstance(p.get("orientation_corrected"), bool): err(f"{w}: orientation_corrected must be bool")
    sp = os.path.join(ROOT, p.get("scan", ""))
    if not p.get("scan", "").startswith("data/pages/") or not p["scan"].endswith(".svg"): err(f"{w}: scan path")
    elif not os.path.isfile(sp): err(f"{w}: scan file missing")
    for k in ("transcription","interpretation_note","alt"): pii(str(p.get(k) or ""), f"{w}.{k}")
nums = [p["printed_number"] for p in m.get("pages", []) if p.get("printed_number") is not None]
if nums != sorted(nums) or len(nums) != len(set(nums)): err("printed numbers not strictly increasing")
if not any(p.get("orientation_corrected") for p in m.get("pages", [])): err("no orientation_corrected page (fixture requires one)")
if not any(p.get("transcription_status") == "unchecked" for p in m.get("pages", [])): err("no unchecked page (fixture requires one)")
for c in m.get("chapters", []):
    need(c, ["id","title","pages"], f"chapter {c.get('id')}")
    for pid in c.get("pages", []):
        if pid not in ids: err(f"chapter {c.get('id')}: unknown page {pid}")
comp = m.get("completeness", {})
if comp.get("status") != "OPEN": err("completeness.status must be OPEN")
if re.search(r"\bcomplete\b", comp.get("note", "").replace("not claimed complete", "").replace("Not claimed complete", ""), re.I):
    err("completeness note claims completeness")
for k in ("title","dedication","foreword"): pii(str(m.get(k, "")), f"manuscript.{k}")

# svgs
for f in glob.glob(os.path.join(ROOT, "data/pages/*.svg")):
    rel = os.path.relpath(f, ROOT)
    txt = open(f, encoding="utf-8").read()
    try: ET.fromstring(txt)
    except ET.ParseError as e: err(f"{rel}: invalid XML ({e})")
    if re.search(r"<script|https?://(?!www\.w3\.org)|href=|on\w+=", txt): err(f"{rel}: script/external reference")
    pii(re.sub(r"<[^>]+>", " ", txt), rel)
    if not any(p.get("scan") == rel for p in m.get("pages", [])): err(f"{rel}: orphan scan")

# contributions
contribs = {}
for f in sorted(glob.glob(os.path.join(ROOT, "data/contributions/*.json"))):
    if os.path.basename(f) == "index.json": continue
    rel = os.path.relpath(f, ROOT); c = load(rel)
    if not c: continue
    need(c, ["id","submitted","contributor_label","kind","title","body","audience","license","involves_minor","status","reviewed_by","reviewed_at","attaches_to","base_edition_version"], rel)
    contribs[c.get("id")] = c
    if c.get("kind") not in ("memory","audio","letter","photo","correction"): err(f"{rel}: bad kind")
    if c.get("audience") not in ("family","private-review","public"): err(f"{rel}: bad audience")
    if c.get("status") not in ("pending","approved","rejected"): err(f"{rel}: bad status")
    if c.get("status") == "pending" and (c.get("reviewed_by") or c.get("reviewed_at")): err(f"{rel}: pending but reviewed")
    if c.get("status") in ("approved","rejected") and not (c.get("reviewed_by") and c.get("reviewed_at")): err(f"{rel}: decided without reviewer/date")
    if c.get("involves_minor") and c.get("audience") == "public": err(f"{rel}: minor must not be public")
    if c.get("attaches_to") is not None and c["attaches_to"] not in ids: err(f"{rel}: attaches_to unknown page")
    if c.get("base_edition_version") != m.get("version"): err(f"{rel}: base_edition_version mismatch")
    if os.path.basename(f) != f"{c.get('id')}.json": err(f"{rel}: filename != id")
    pii(json.dumps(c), rel)
idx = load("data/contributions/index.json")
actual = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "data/contributions/*.json")) if os.path.basename(f) != "index.json")
if idx is not None and idx != actual: err(f"contributions/index.json must list exactly {actual}, got {idx}")

# review log hash chain: hash = sha256(prev_hash + canonical(record minus prev_hash,hash))
def canon(r): return json.dumps(r, sort_keys=True, separators=(",",":"), ensure_ascii=False)
prev = "0" * 64; logged = {}
lp = os.path.join(ROOT, "data/review_log.jsonl")
if not os.path.isfile(lp): err("review_log.jsonl missing")
else:
    for i, line in enumerate(open(lp, encoding="utf-8").read().splitlines(), 1):
        try: r = json.loads(line)
        except Exception: err(f"review_log:{i}: invalid JSON"); continue
        if r.get("prev_hash") != prev: err(f"review_log:{i}: prev_hash broken")
        body = {k: v for k, v in r.items() if k not in ("prev_hash","hash")}
        if r.get("hash") != hashlib.sha256((r.get("prev_hash","") + canon(body)).encode()).hexdigest(): err(f"review_log:{i}: hash mismatch")
        prev = r.get("hash", "")
        if r.get("contribution_id") not in contribs: err(f"review_log:{i}: unknown contribution")
        logged[r.get("contribution_id")] = r.get("decision")
        pii(canon(body), f"review_log:{i}")
for cid, c in contribs.items():
    if c.get("status") in ("approved","rejected") and logged.get(cid) != c["status"]: err(f"{cid}: status not backed by a review_log decision")

# research
r = load("data/research.json") or {}
cl_ids = set(); labels = set()
for c in r.get("claims", []):
    w = f"claim {c.get('id')}"
    need(c, ["id","text","label","sources","discrepancy"], w); cl_ids.add(c.get("id")); labels.add(c.get("label"))
    if c.get("label") not in ("OBSERVED","SUPPORTED","UNVERIFIED","CONTRADICTED"): err(f"{w}: bad label")
    if not c.get("sources"): err(f"{w}: no sources")
    for s in c.get("sources", []):
        need(s, ["kind","ref","note"], w)
        if s.get("kind") not in ("manuscript","gedcom","external"): err(f"{w}: bad source kind")
        if s.get("kind") == "manuscript" and s.get("ref") not in ids: err(f"{w}: unknown page {s.get('ref')}")
        if s.get("kind") == "gedcom" and s.get("ref") != "synthetic-gedcom-example": err(f"{w}: gedcom ref must be synthetic")
    d = c.get("discrepancy")
    if d is not None:
        need(d, ["between","detail"], w)
    if c.get("label") == "CONTRADICTED" and d is None: err(f"{w}: CONTRADICTED needs discrepancy")
    pii(json.dumps(c), w)
for lab in ("OBSERVED","SUPPORTED","UNVERIFIED","CONTRADICTED"):
    if lab not in labels: err(f"research: label {lab} unused")
if not any(c.get("discrepancy") for c in r.get("claims", [])): err("research: no discrepancy example")
for l in r.get("leads", []):
    w = f"lead {l.get('id')}"
    need(l, ["id","opaque","executable","claim_id","requires_human_approval"], w)
    if l.get("opaque") is not True or l.get("executable") is not False or l.get("requires_human_approval") is not True: err(f"{w}: must be inert")
    if l.get("claim_id") not in cl_ids: err(f"{w}: unknown claim")
    if set(l) - {"id","opaque","executable","claim_id","requires_human_approval"}: err(f"{w}: extra fields (leads are inert data)")

if errs:
    print("\n".join("FAIL " + e for e in errs)); sys.exit(1)
print(f"OK: {len(ids)} pages, {len(contribs)} contributions, {len(logged)} logged, {len(cl_ids)} claims")
