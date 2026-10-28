"""Evidence comparison; structural checks are not source authentication."""
from collections import defaultdict
from copy import deepcopy

SOURCE_CLASSES = {'PRIVATE_GEDCOM', 'FAMILY_MANUSCRIPT', 'HISTORICAL_PUBLICATION',
                  'PRIMARY_RECORD', 'HUMAN_ATTESTATION'}

def reconcile(observations):
    """Keep distinct underlying works and all values; never auto-select a winner."""
    if not isinstance(observations, list) or not observations:
        raise ValueError('Nonempty evidence observations required')
    groups = defaultdict(list)
    for row in observations:
        if not isinstance(row, dict):
            raise ValueError('Evidence rows must be objects')
        for k in ('claim_id', 'value', 'source_id', 'source_class'):
            if not isinstance(row.get(k), str) or not row[k].strip():
                raise ValueError('Evidence missing ' + k)
        if row['source_class'] not in SOURCE_CLASSES:
            raise ValueError('Unknown source class')
        groups[row['claim_id']].append(deepcopy(row))
    output = []
    for claim, rows in sorted(groups.items()):
        by_source = {}
        for row in rows:
            source, value = row['source_id'], row['value'].strip()
            if source in by_source and by_source[source] != value:
                raise ValueError('One source has inconsistent values; separate its editions')
            by_source[source] = value
        values = sorted(set(by_source.values()))
        output.append({
            'claim_id': claim,
            'state': 'CONTRADICTED' if len(values) > 1 else 'SUPPORTED_BY_SUPPLIED_SOURCES',
            'values_observed': values, 'source_count': len(by_source),
            'observations': rows, 'selected_value': None,
            'historical_fact_verified': False, 'authority_effect': 'NONE',
            'next_action': 'INDEPENDENT_PRIMARY_RECORD_REVIEW' if len(values) > 1 else 'AUTHENTICATE_SOURCE_LOCATOR',
        })
    return {'schema_version': '0.1', 'claims': output, 'authority_effect': 'NONE',
            'source_authentication_performed': False, 'human_review_required': True}
