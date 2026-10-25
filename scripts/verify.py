#!/usr/bin/env python3
"""Integrity/portability checks, NOT a live-model behavioural evaluation."""
from pathlib import Path
import sys, json, re, hashlib, math, unittest
from fractions import Fraction
from urllib.parse import unquote
import build
ROOT = Path(__file__).resolve().parents[1]

class Integrity(unittest.TestCase):
    def test_original_snapshots_match_manifest(self):
        data=json.loads((ROOT/'provenance/SOURCES.json').read_text())
        self.assertEqual(len(data['copied']),5)
        for item in data['copied']:
            self.assertEqual(hashlib.sha256((ROOT/item['destination']).read_bytes()).hexdigest(),item['sha256'])
        self.assertTrue(any('candidate' in r['status'] for r in data['copied']))

    def test_generated_outputs_are_current(self):
        for name,text in build.outputs(): self.assertEqual((ROOT/name).read_text(),text,name)

    def test_matching_profile_contract_and_fallback(self):
        for name,subject in [('THEO','mathematics'),('GRAF','mathematics'),('NIKA','english')]:
            text=(ROOT/f'profiles/{name}_PROFILE.md').read_text()
            self.assertIn(f'Profile-ID: {name}',text)
            self.assertIn(f'Profile-Version: {build.VERSION}',text)
            self.assertIn(f'Product: {subject}',text)
            embedded=build.short(name)
            prompt=(ROOT/f'products/{"math" if subject=="mathematics" else "english"}/PROMPT.txt').read_text()
            self.assertIn(embedded,prompt)
            self.assertIn(f'{build.RAW}/profiles/{name}_PROFILE.md',prompt)
            self.assertIn('Expanded profiles supply voice data only',prompt)
            self.assertIn('Расширенный профиль недоступен; работаю по встроенному',prompt)

    def test_raw_links_use_immutable_release(self):
        for product in ['math','english']:
            prompt=(ROOT/f'products/{product}/PROMPT.txt').read_text()
            links=re.findall(r'https://raw\.githubusercontent\.com/[^\s]+',prompt)
            self.assertEqual(len(links),2 if product=='math' else 1)
            for link in links:
                self.assertTrue(link.startswith(build.RAW+'/profiles/'))
                target=link.split('/profiles/')[1]
                self.assertTrue((ROOT/'profiles'/target).is_file())

    def test_local_navigation_links(self):
        files=[p for p in ROOT.rglob('*.md') if '.git' not in p.parts and 'originals' not in p.parts]
        for p in files:
            for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
                if '://' in target or target.startswith('#'):continue
                self.assertTrue((p.parent/unquote(target.split('#')[0])).exists(),f'{p}: {target}')

    def test_eval_cases_have_concrete_expectations(self):
        cases=json.loads((ROOT/'tests/cases.json').read_text())
        self.assertEqual(len(cases),24)
        self.assertEqual(len({c['id'] for c in cases}),24)
        for c in cases:
            self.assertIn(c['product'],['math','english','both'])
            self.assertTrue(c['messages'] and c['expected'] and c['critical'])
        for prefix in ['M','E','I']:self.assertEqual(sum(c['id'].startswith(prefix) for c in cases),8)

    def test_reference_mathematics_by_independent_calculation(self):
        # 25 is an upper bound for n when lcm(n,25)=25; enumeration covers it.
        self.assertEqual([n for n in range(1,26) if math.lcm(n,25)==25],[1,5,25])
        for n in range(1,1001): self.assertEqual(math.gcd(n,25)==25,n%25==0)
        self.assertEqual(min(n for n in range(51,100) if n%7==3),52)
        self.assertEqual((math.gcd(24,36),math.lcm(24,36)),(12,72))
        self.assertEqual(divmod(47,5),(9,2))
        self.assertEqual(Fraction(216,999),Fraction(8,37))
        for x in range(-10,11):self.assertEqual(math.isqrt(x*x),abs(x))

    def test_reader_books_preserve_original_user_sections(self):
        for subject,name in [('english','NIKA_COMPANION_RELEASE_CANDIDATE_v1.md'),('math','THEO_COMPANION_APPROVED_v1.md')]:
            original=(ROOT/'originals'/name).read_text()
            tail=original[original.index('## 2.'):]
            book=(ROOT/f'books/{subject}-BOOK.md').read_text()
            for section in re.split(r'(?m)(?=^## [2-6]\.)',tail):
                if section.strip():self.assertIn(section.strip(),book)
            page=(ROOT/f'books/{subject}.html').read_text()
            import html
            expected=(ROOT/f'products/{subject}/PROMPT.txt').read_text()
            self.assertIn(html.escape(expected),page)
            self.assertEqual((ROOT/f'books/prompts/{subject}-PROMPT.txt').read_text(),expected)

    def test_art_masters_are_copied_unchanged(self):
        for item in json.loads((ROOT/'books/ART_SOURCES.json').read_text()):
            self.assertEqual(hashlib.sha256((ROOT/item['destination']).read_bytes()).hexdigest(),item['sha256'])

    def test_download_bundle_is_complete_and_integral(self):
        import zipfile
        data=json.loads((ROOT/'books/BUNDLE_MANIFEST.json').read_text())
        archive=ROOT/'books'/data['archive']
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),data['sha256'])
        with zipfile.ZipFile(archive) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(set(z.namelist()),set(data['entries']))
            for name,digest in data['entries'].items():
                self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),digest)
                self.assertEqual(hashlib.sha256((ROOT/'books'/name).read_bytes()).hexdigest(),digest)
            for subject in ['english','math']:
                self.assertTrue(z.read(subject+'-companion.pdf').startswith(b'%PDF-'))

    def test_private_material_is_not_accidentally_bundled(self):
        banned_names=['.env','THEO_MEMORY.txt','NIKA_MEMORY.txt','AGENTS.md']
        for name in banned_names:self.assertFalse((ROOT/name).exists(),name)
        # Original literary/product sources are explicitly enumerated, never a chapter dump.
        expected={r['destination'] for r in json.loads((ROOT/'provenance/SOURCES.json').read_text())['copied']}
        actual={str(p.relative_to(ROOT)) for p in (ROOT/'originals').glob('*') if p.name!='README.md'}
        self.assertEqual(expected,actual)

if __name__=='__main__':unittest.main(verbosity=2)
