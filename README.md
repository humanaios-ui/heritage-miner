# heritage-miner

Prototype of a family-first "living edition" reader for a family-history manuscript (issue #2).

**Everything here is synthetic** (an invented family). No family content is published, no deployment is authorized, and completeness of the source work is OPEN.

## Run

```
python3 -m http.server
# open http://localhost:8000/reader/
```

Static site, vanilla JS, no dependencies, no network calls, no tracking, no login.

Checks:

```
python3 -m unittest discover tests
python3 tools/privacy_check.py
python3 tools/validate_data.py
```

## Privacy constraint

This repo is public. Never commit original scans, PDFs, GEDCOM files, photos, living-person data, relatives' drafts or research receipts. `.gitignore` blocks them and `tools/privacy_check.py` fails on them.

## Pointers

- `docs/DATA_CONTRACT.md` data shapes and rules
- `docs/DESIGN.md` modes, static/offline rationale, research boundary
- `docs/APPROVAL_GATES.md` human approvals required
- `docs/ACCEPTANCE.md` the 8 acceptance steps and their evidence
