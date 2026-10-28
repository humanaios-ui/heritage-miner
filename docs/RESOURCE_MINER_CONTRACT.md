# Resource Miner boundary — non-executable prototype

## Inputs
Read-only local GEDCOM extracts and claim-source conflicts. Keep identities, private tree, and source files on the user's machine.

## Allowed proposal
```json
{
  "schema_version": "0.1",
  "kind": "genealogy_research_actions",
  "project": "heritage-miner",
  "authority_effect": "NONE",
  "external_search_authorized": false,
  "actions": [{
    "action": "VERIFY_SOURCE",
    "subject_ref": "hm-aaaaaaaaaaaaaaaaaaaa",
    "evidence_state": "CONTRADICTED",
    "target": "VITAL_RECORD",
    "status": "PROPOSED"
  }]
}
```

`subject_ref` is an opaque local token. No name, date, family relationship, health detail, scan or attachment passes to a shared/public broker.

## Existing HumanAIOS interfaces
- Resource Miner: candidate source searches, HUMAN_REVIEW_REQUIRED.
- Evidence Graph: separate claim/revision/source/locator links.
- Witness: read-only challenge; do not replace original observations.
- INTENT-OS: consent and objective selection.
- Coordinator: no automatic admission, contact, entitlement or authority.

The adapter produces a Python dictionary only; **it does not connect to a Resource Miner server**, perform searches, use a model, submit anything, or verify eligibility. No database or new external service is created. Align future schema changes with existing HumanAIOS data contracts through separate review.
