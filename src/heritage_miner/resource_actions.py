"""No-PII, non-authorizing envelope for HumanAIOS Resource Miner."""
import re
OPAQUE_REF = re.compile(r'^hm-[0-9a-f]{16,64}$')

def propose_research(subject_ref: str, claim_state: str, target: str) -> dict:
    if not isinstance(subject_ref, str) or not OPAQUE_REF.fullmatch(subject_ref):
        raise ValueError('Only local opaque references are allowed')
    if claim_state not in {'CONTRADICTED', 'UNKNOWN', 'PARTIAL'}:
        raise ValueError('No research action needed for this state')
    if target not in {'CENSUS', 'MILITARY_ROLL', 'VITAL_RECORD', 'HISTORICAL_ARCHIVE'}:
        raise ValueError('Unsupported target')
    return {
        'schema_version': '0.1', 'kind': 'genealogy_research_actions',
        'project': 'heritage-miner', 'authority_effect': 'NONE',
        'external_search_authorized': False,
        'actions': [{'action': 'VERIFY_SOURCE', 'subject_ref': subject_ref,
                     'evidence_state': claim_state, 'target': target,
                     'status': 'PROPOSED'}]
    }
