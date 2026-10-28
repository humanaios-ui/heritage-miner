import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from heritage_miner.gedcom import parse, paternal_line

FIXTURE = '''0 HEAD
1 SOUR SYNTHETIC
0 @CHILD@ INDI
1 NAME Example /Descendant/
1 BIRT
2 DATE ABT 2000
1 FAMC @F1@
0 @PARENT@ INDI
1 NAME Example /Parent/
1 BIRT
2 DATE 1960
0 @F1@ FAM
1 HUSB @PARENT@
1 CHIL @CHILD@
0 TRLR
'''

class GedcomTests(unittest.TestCase):
    def test_explicit_paternal_relationship(self):
        people, fams = parse(FIXTURE)
        r = paternal_line(people, fams, root_id='CHILD')
        self.assertEqual([p['record_id'] for p in r['line']], ['CHILD', 'PARENT'])
        self.assertEqual(r['alerts'], [])
        self.assertEqual(r['line'][1]['claim_state'], 'GEDCOM_REPORTED')
        self.assertFalse(r['independently_verified'])
    def test_ambiguous_birth_families_not_guessed(self):
        s=FIXTURE.replace('1 FAMC @F1@', '1 FAMC @F1@\n1 FAMC @F2@')
        people, fams = parse(s)
        r = paternal_line(people, fams, root_id='CHILD')
        self.assertEqual(len(r['line']), 1)
        self.assertEqual(r['alerts'][0]['code'], 'MULTIPLE_PARENT_FAMILIES')
    def test_missing_reciprocal_child_link_blocks(self):
        s=FIXTURE.replace('1 CHIL @CHILD@', '1 CHIL @SOMEONE_ELSE@')
        people, fams = parse(s)
        r = paternal_line(people, fams, root_id='CHILD')
        self.assertEqual(r['alerts'][0]['code'], 'INCONSISTENT_FAMILY_EDGE')
    def test_ambiguous_names_refused(self):
        s=FIXTURE.replace('0 @PARENT@ INDI', '0 @OTHER@ INDI\n1 NAME Example /Descendant/\n0 @PARENT@ INDI')
        people,fams=parse(s)
        with self.assertRaises(ValueError):paternal_line(people,fams,root_name='Example /Descendant/')
    def test_duplicate_individual_id_refused(self):
        with self.assertRaises(ValueError):parse(FIXTURE + '0 @CHILD@ INDI\n1 NAME Duplicate /Entry/\n')

if __name__ == '__main__': unittest.main()
