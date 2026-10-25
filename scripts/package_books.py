#!/usr/bin/env python3
"""Package only the reader-facing standalone gift editions, never private notes."""
from pathlib import Path
import zipfile,hashlib,json
ROOT=Path(__file__).resolve().parents[1];BOOKS=ROOT/'books'
paths=[BOOKS/'START.html', BOOKS/'english.html', BOOKS/'math.html',BOOKS/'english-companion.pdf',BOOKS/'math-companion.pdf',BOOKS/'README.txt']
paths+=sorted((BOOKS/'assets').glob('*'))+sorted((BOOKS/'prompts').glob('*.txt'))
for p in paths:
 if not p.is_file(): raise SystemExit(f'Missing: {p}')
out=BOOKS/'companion-gift-editions.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as bundle:
 for p in paths:bundle.write(p,p.relative_to(BOOKS))
with zipfile.ZipFile(out) as bundle:
 assert bundle.testzip() is None
 names=set(bundle.namelist())
 assert 'START.html' in names and 'math-companion.pdf' in names and 'english-companion.pdf' in names
 manifest={str(p.relative_to(BOOKS)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 for name,digest in manifest.items():assert hashlib.sha256(bundle.read(name)).hexdigest()==digest
(BOOKS/'BUNDLE_MANIFEST.json').write_text(json.dumps({'archive':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'entries':manifest},ensure_ascii=False,indent=2)+'\n')
print(f'Bundle: {len(paths)} files; {out.stat().st_size/1048576:.1f} MiB; exact hashes verified.')
