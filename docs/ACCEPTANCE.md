# Acceptance: 1 chapter, 1 photo, 1 contribution (synthetic)

Source: humanaios-ui/heritage-miner issue #2.

**This prototype is synthetic. No family content is published. No deployment is authorized. Completeness of the source work is OPEN.**

Status key: `pending` means only a human can complete it. Other statuses are "evidenced by command", to be re-run, not assumed. Run from the repo root.

| # | Step | Evidence (command / artifact) | Status |
|---|---|---|---|
| 1 | Compute PDF page count, orientation, rendered-page list, SHA-256 locally | `python3 tools/audit_pdf.py <path-to-pdf>` (run on a synthetic fixture to test the tool). Run on the real private PDF: human only, output stays private | pending (real PDF) |
| 2 | Audit pagination vs table of contents; list missing/blank/duplicated; no preservation claim until reconciled | `python3 tools/pagination_audit.py`; `python3 tools/validate_data.py` (checks `completeness.status` stays OPEN) | prototype checks only; reconciliation of the real work pending |
| 3 | Original scan + verbatim checked transcript; interpretation separate | Reader at `/reader/` (facsimile beside transcript, separate note); `python3 tools/validate_data.py` | evidenced on synthetic data |
| 4 | Pleasant mobile reading flow; works with research overlay OFF and no account | `python3 -m http.server`, open `/reader/` at phone width, overlay off by default; tests in `tests/` | evidenced on synthetic data (visual check by a human recommended) |
| 5 | Synthetic contribution enters review; not displayed until approved | `python3 tools/review_queue.py` ; `python3 tools/build_public.py` (only `status == "approved"` copied); `python3 -m unittest discover tests` | evidenced on synthetic data |
| 6 | Opt-in research view links an example discrepancy to both sources, originals retained | Reader EXPLORE toggle reading `data/research.json`; `python3 tools/validate_data.py` | evidenced on synthetic data |
| 7 | No original scan, private genealogy or user-specific record in Git history, payloads, logs, demo assets | `python3 tools/privacy_check.py`; `git log --all --stat` review; browser network panel shows no requests beyond local files | evidenced for current tree; history and network review by a human pending |
| 8 | After family review, decide distribution scope and contributor consent; no automatic public launch | `docs/APPROVAL_GATES.md` | pending (human) |

Overall: not accepted. Steps 1 (real PDF) and 8 are human-only and remain pending.
