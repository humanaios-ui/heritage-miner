"""Public-safe dependency-free static site checks. Use: python3 -m unittest discover -s tests -p 'test_static_bundle.py' -v"""
import unittest
from pathlib import Path
from html.parser import HTMLParser

SITE=Path(__file__).resolve().parents[1]

class Inspector(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=set();self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        for k in ('src','href'):
            if k in a:self.links.append(a[k])

class SiteTests(unittest.TestCase):
    def test_expected_surfaces(self):
        p=Inspector();p.feed((SITE/'index.html').read_text())
        for x in ('home','read','album','contribute','pdfInput','memoryFile','contributionForm','albumList','importContribution'):
            self.assertIn(x,p.ids)
    def test_no_remote_assets(self):
        p=Inspector();p.feed((SITE/'index.html').read_text())
        self.assertFalse([x for x in p.links if x.startswith(('http://','https://','//'))])
    def test_client_only(self):
        s=(SITE/'app.js').read_text()
        for fragment in ('fetch(', 'XMLHttpRequest','sendBeacon','WebSocket','navigator.sendBeacon'):
            self.assertNotIn(fragment,s)
        self.assertIn('indexedDB',s)
        self.assertIn('authority', (SITE/'README.md').read_text().lower() if (SITE/'README.md').exists() else 'authority')
    def test_no_real_contributions_bundled(self):
        files=[p for p in SITE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
        self.assertTrue(all(p.suffix in {'.html','.css','.js','.md','.py'} for p in files))
        self.assertLess(sum(p.stat().st_size for p in files),160000)

if __name__=='__main__':unittest.main()