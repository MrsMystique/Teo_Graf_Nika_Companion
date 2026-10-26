#!/usr/bin/env python3
"""Make the PDF a usable prompt product, then verify text, download link and attachment."""
from pathlib import Path
import sys,re,hashlib,json,shutil
from pypdf import PdfReader,PdfWriter
from pypdf.generic import NameObject,DictionaryObject,ArrayObject
ROOT=Path(__file__).resolve().parents[1]

def normalized(text):return re.sub(r'\s+','',text)
def check(subject):
    file=ROOT/f'books/{subject}-companion.pdf';r=PdfReader(file)
    source=(ROOT/f'products/{subject}/PROMPT.txt').read_text()
    texts=[p.extract_text() or '' for p in r.pages]
    starts=[i for i,t in enumerate(texts) if 'COMPANION INSTRUCTIONS v' in t]
    ends=[i for i,t in enumerate(texts) if 'End of companion instructions.' in t]
    assert len(starts)==len(ends)==1,(starts,ends)
    assert r.get_destination_page_number(r.named_destinations['/full-prompt'])==starts[0],'Prompt button targets the wrong page'
    joined=''.join(re.sub(r'На одном листе\s*·\s*\d+\s*/\s*\d+','',t) for t in texts)
    start=joined.index('COMPANION INSTRUCTIONS v');end=joined.index('End of companion instructions.')+len('End of companion instructions.')
    assert normalized(source)==normalized(joined[start:end]),'PDF prompt differs from current TXT'
    name='THEO_GRAF_PROMPT.txt' if subject=='math' else 'NIKA_PROMPT.txt'
    assert r.attachments[name][0]==source.encode(),'Embedded file differs'
    uris=[str(a.get_object().get('/A',{}).get('/URI','')) for p in r.pages for a in p.get('/Annots',[])]
    urls=[u for u in uris if 'raw.githubusercontent.com/MrsMystique/Teo_Graf_Nika_Companion/' in u and u.endswith('/PROMPT.txt')]
    assert urls,'No public TXT link in PDF'
    assert any('Полный промпт для вставки' in str(o) for o in r.outline),'No prompt bookmark'
    return {'product':subject,'pages':len(r.pages),'promptStartPage':starts[0]+1,'promptEndPage':ends[0]+1,'fullPromptMatchesTXT':True,'comparison':'All characters match after removing page-number footers and normalising whitespace; attached TXT matches exact bytes.','attachment':name,'attachmentSha256':hashlib.sha256(source.encode()).hexdigest(),'publicTXTLinks':urls,'bookmark':'Полный промпт для вставки','internalPromptButtonVerified':True}

def finalize(subject):
    file=ROOT/f'books/{subject}-companion.pdf';r=PdfReader(file)
    texts=[p.extract_text() or '' for p in r.pages]
    prompt_page=next(i for i,t in enumerate(texts) if 'COMPANION INSTRUCTIONS v' in t)
    name='THEO_GRAF_PROMPT.txt' if subject=='math' else 'NIKA_PROMPT.txt'
    if name in r.attachments:
        result=check(subject)
        (ROOT/f'books/{subject}-PDF_CHECK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        shutil.copyfile(file,ROOT/f'books/{subject}-companion-2026-10-26.pdf')
        print(subject,'already finalized; full prompt and attachment verified')
        return
    w=PdfWriter(clone_from=r)
    w.add_attachment('THEO_GRAF_PROMPT.txt' if subject=='math' else 'NIKA_PROMPT.txt',(ROOT/f'products/{subject}/PROMPT.txt').read_bytes())
    w.add_outline_item('Начало',0)
    w.add_outline_item('Скачать TXT или перейти к промпту',1)
    w.add_outline_item('Полный промпт для вставки',prompt_page)
    for page in w.pages:
        for ref in page.get('/Annots',[]):
            a=ref.get_object();action=a.get('/A',{});uri=str(action.get('/URI',''))
            if uri.endswith('#full-prompt'):
                a.pop(NameObject('/Dest'),None)
                a[NameObject('/A')]=DictionaryObject({NameObject('/S'):NameObject('/GoTo'),NameObject('/D'):ArrayObject([w.pages[prompt_page].indirect_reference,NameObject('/Fit')])})
    temp=file.with_suffix('.tmp.pdf')
    with temp.open('wb') as f:w.write(f)
    temp.replace(file)
    result=check(subject)
    (ROOT/f'books/{subject}-PDF_CHECK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    shutil.copyfile(file,ROOT/f'books/{subject}-companion-2026-10-26.pdf')
    print(subject, 'complete prompt:',result['promptStartPage'],'–',result['promptEndPage'],'; exact TXT attached; public download and bookmark verified')
if __name__=='__main__':
    for subject in sys.argv[1:] or ['english','math']:finalize(subject)
