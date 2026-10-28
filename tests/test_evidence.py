import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from heritage_miner.evidence import reconcile
from heritage_miner.resource_actions import propose_research

class EvidenceTests(unittest.TestCase):
    def sample(self):
        return [
            {'claim_id':'synthetic.date', 'value':'YEAR_A', 'source_id':'research_tree_v1', 'source_class':'PRIVATE_GEDCOM'},
            {'claim_id':'synthetic.date', 'value':'YEAR_B', 'source_id':'historic_book_1900', 'source_class':'HISTORICAL_PUBLICATION'},
        ]
    def test_retains_disagreement_without_picking_year(self):
        original = self.sample()
        result = reconcile(original)
        claim = result['claims'][0]
        self.assertEqual(claim['state'], 'CONTRADICTED')
        self.assertEqual(claim['values_observed'], ['YEAR_A', 'YEAR_B'])
        self.assertIsNone(claim['selected_value'])
        self.assertFalse(claim['historical_fact_verified'])
        self.assertEqual(original, self.sample())
    def test_two_mirrors_of_same_book_not_independent(self):
        x = self.sample()[:1]
        x += [{'claim_id':'synthetic.date','value':'YEAR_A', 'source_id':'historic_book_1900', 'source_class':'HISTORICAL_PUBLICATION', 'url':'https://archive.example/a'},
              {'claim_id':'synthetic.date','value':'YEAR_A', 'source_id':'historic_book_1900', 'source_class':'HISTORICAL_PUBLICATION', 'url':'https://mirror.example/a'}]
        claim = reconcile(x)['claims'][0]
        self.assertEqual(claim['source_count'], 2)
        self.assertFalse(claim['historical_fact_verified'])
    def test_misleading_same_source_values_rejected(self):
        rows = self.sample()
        rows[1]['source_id'] = rows[0]['source_id']
        with self.assertRaises(ValueError): reconcile(rows)
    def test_unverified_single_source_cannot_be_promoted(self):
        claim = reconcile(self.sample()[:1])['claims'][0]
        self.assertIsNone(claim['selected_value'])
        self.assertFalse(claim['historical_fact_verified'])
    def test_broker_only_opaque_refs_and_no_execution(self):
        response = propose_research('hm-' + 'a'*20, 'CONTRADICTED', 'VITAL_RECORD')
        self.assertEqual(response['authority_effect'], 'NONE')
        self.assertFalse(response['external_search_authorized'])
        self.assertEqual(response['actions'][0]['status'], 'PROPOSED')
        with self.assertRaises(ValueError): propose_research('John /Example/ 1800-1870', 'CONTRADICTED', 'VITAL_RECORD')
        with self.assertRaises(ValueError): propose_research('hm-'+'b'*20, 'SUPPORTED', 'CENSUS')

if __name__ == '__main__': unittest.main()
