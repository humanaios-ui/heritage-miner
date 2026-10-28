# Data contract (synthetic prototype)

All content in this repo is SYNTHETIC. No real family data, scans, GEDCOM or living-person details.
Static site, vanilla HTML/CSS/JS (ES modules), no build deps, no network calls, no analytics, no login.
Served from repo root: `python3 -m http.server` then open `/reader/`.

## Layout (each area owned by one builder; do not edit others' files)
- `reader/`        index.html, reader.css, reader.js  (READ mode, facsimile + transcript, chapters nav, toggles)
- `data/`          manuscript.json, research.json, contributions/*.json, pages/page-NNN.svg  (synthetic)
- `tools/`         audit_pdf.py, pagination_audit.py, review_queue.py, build_public.py, privacy_check.py
- `tests/`         python unittest + a node-free JS-free check where possible
- `docs/`          DATA_CONTRACT.md (this), DESIGN.md, APPROVAL_GATES.md, ACCEPTANCE.md

## data/manuscript.json
{ "edition": "1992", "synthetic": true, "version": "sha-label string",
  "title", "dedication", "foreword",
  "chapters": [ {"id":"ch1","title":"...","pages":["p001","p003"]} ],
  "pages": [ { "id":"p001", "printed_number": 1 | null, "scan": "data/pages/page-001.svg",
               "alt": "description of scan for screen readers",
               "orientation_corrected": false,
               "transcription": "verbatim text, manually checked" | null,
               "transcription_status": "verified" | "unchecked" | "none",
               "interpretation_note": "separate note, never merged into transcription" | null,
               "kind": "text" | "photo" | "diagram" | "cover" } ],
  "completeness": { "status": "OPEN", "note": "printed numbers 1,3,5...; even pages unaccounted" } }
Printed numbers deliberately odd-only (1,3,5) to model the OPEN COMPLETENESS QUESTION; never claim complete.

## data/contributions/*.json
{ "id","submitted":"ISO date","contributor_label":"synthetic name","kind":"memory|audio|letter|photo|correction",
  "title","body","audience":"family|private-review|public","license":"...","involves_minor":false,
  "status":"pending|approved|rejected","reviewed_by":null|"label","reviewed_at":null|"ISO","attaches_to":"p003"|null,
  "base_edition_version":"..." }
`data/contributions/index.json` = JSON array of contribution filenames (e.g. `["c001.json","c002.json"]`), sorted, excluding itself.
The reader fetches only these (no directory-listing scrape). Dev: `review_queue.py` regenerates it on every decision and
`validate_data.py` checks it lists exactly the contribution files. Public bundle: `build_public.py` writes it with approved files only.
The reader still filters on status=="approved". A normal empty pending queue is valid.
Rule: only status=="approved" is copied to the public bundle. Contributions NEVER modify manuscript.json.
Approved ones render as clearly dated "Added <date> by <label> — not part of the 1992 edition".
Review decisions append to `data/review_log.jsonl` (append-only, one JSON per line, each with prev_hash and hash = sha256 of prev_hash+record).

## data/research.json  (opt-in overlay; default OFF)
{ "claims":[ {"id","text","label":"OBSERVED|SUPPORTED|UNVERIFIED|CONTRADICTED",
   "sources":[{"kind":"manuscript|gedcom|external","ref":"p003"|"synthetic-gedcom-example"|"...","note"}],
   "discrepancy": null | {"between":["manuscript","gedcom"],"detail"} } ],
  "leads":[ {"id","opaque":true,"executable":false,"claim_id","requires_human_approval":true} ] }
No claim auto-selects an ancestor or fact. Leads are inert data only.

## Privacy rules
`.gitignore` blocks *.pdf, *.gedcom/*.ged, private/, scans/, raw/. `tools/privacy_check.py` fails on any
tracked pdf/ged/jpg/png/tiff outside allowlisted synthetic SVGs, or on obvious PII patterns (emails, phone numbers).
