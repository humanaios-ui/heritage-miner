# Design

Status: synthetic prototype. No family content is published and no deployment is authorized. Completeness of the source work is OPEN. See `DATA_CONTRACT.md` for data shapes.

## Reader modes

| Mode | Default | What it does | Never does |
|---|---|---|---|
| READ | on | Book in order: cover, dedication, foreword, chapters. Facsimile page beside verbatim transcript. Chapter nav. Works on mobile, no account, no AI. | Edit the 1992 text. |
| CONTRIBUTE | opt-in | Shows approved contributions as dated additions ("Added <date> by <label>, not part of the 1992 edition"). Submissions go to a review queue (`tools/review_queue.py`). | Display a pending or rejected item. Modify `manuscript.json`. |
| EXPLORE | opt-in, off | Research overlay from `data/research.json`: claims labelled OBSERVED / SUPPORTED / UNVERIFIED / CONTRADICTED, each linked to its sources and any discrepancy. | Select an ancestor or fact. Run a lead. |

Transcription is verbatim and manually checked. Interpretation lives in a separate `interpretation_note`, never merged. Pages with status `unchecked` or `none` say so on screen.

## Why static and offline

- Public repo: nothing server-side can hold private material, so there is nothing to leak.
- No database, login, analytics or network calls: a reader's behavior is not observable by design.
- It can be copied to a USB stick or a family member's laptop and still work.
- Few moving parts for a volunteer maintainer. Vanilla HTML/CSS/ES modules, no build step.
- The static bundle is built from approved items only (`tools/build_public.py`) and checked by `tools/privacy_check.py`.

## IIIF only on measured need

IIIF (deep zoom, image search) is not part of this slice. Introduce it only if native browser image handling is measured to fall short (for example, load time or zoom failure on a real scan on target devices), with the measurement recorded first. Until then, plain images/SVG.

## Completeness is OPEN

Printed numbers in the source run 1, 3, 5, ... The prototype models this with odd-only printed numbers. The reader and docs never claim the work is complete. `tools/pagination_audit.py` lists gaps, blanks and duplicates; nothing is called "fully preserved" until a human reconciles them.

## Research boundary

Any HumanAIOS behavioral study is separate from this reader and must be:

- explicitly opt-in, with its own clear consent, outside the reading flow;
- never inferred from reading, contributing or exploring;
- free of covert event collection (the reader collects none);
- never linked to candidate or job profiles;
- independently ethically reviewed before any human-subject results are published.

Research leads in `research.json` are opaque, non-executable and require human approval. External outreach and publication are human-gated (see `APPROVAL_GATES.md`).
