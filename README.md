# HumanAIOS Heritage Miner

**State: Z1 research prototype. No admission, external execution, or production deployment.**

**PRIVACY ALERT:** The GitHub repository is currently PUBLIC. Do not upload real GEDCOM files, private family manuscripts, person-level research receipts, or living-person records. Even after it becomes private, such uploads require a separate privacy review. All real family source material remains outside GitHub.

A bounded, read-only, standard-library Python prototype for HumanAIOS Resource Miner. It traces explicit GEDCOM parent links, retains competing historical assertions, and proposes non-executable research actions.

## Test
Run `python3 -m unittest discover -s tests -v` (Python 3.10+).

## Local-only CLI
`PYTHONPATH=src python3 -m heritage_miner.cli --gedcom private/tree.ged --root-id PRIVATE_RECORD_ID --out private/trace.json`.

## Components
- `heritage_miner.gedcom`: explicit parent links; refuse ambiguous matches.
- `heritage_miner.evidence.reconcile`: compare claimed values; never select a winner.
- `heritage_miner.resource_actions.propose_research`: opaque, human-reviewable research leads only.
- `docs/RESOURCE_MINER_CONTRACT.md`: intended Resource Miner integration.

Two web transcriptions of one historical book count as **one** work. Agreement does not establish authenticity. A reproduced contradiction is not resolution of historical truth. Human authority remains primary.
