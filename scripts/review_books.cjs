// Browser QA for the downloaded offline reader editions. Requires Playwright and Chromium.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const root = path.resolve(__dirname, '..');
(async () => {
 const baseDir=path.join(root,'books');
 const server=http.createServer((req,res)=>{
  const target=path.resolve(baseDir,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!target.startsWith(baseDir+path.sep)){res.writeHead(403);return res.end();}
  const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.png':'image/png','.webp':'image/webp','.woff':'font/woff','.ttf':'font/ttf','.txt':'text/plain; charset=utf-8'};
  fs.readFile(target,(error,data)=>{if(error){res.writeHead(404);return res.end();}res.writeHead(200,{'Content-Type':types[path.extname(target)]||'application/octet-stream'});res.end(data);});
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const base=`http://127.0.0.1:${server.address().port}`;
 const browser = await chromium.launch({ executablePath:'/usr/bin/chromium', args:['--no-sandbox'] });
 const context = await browser.newContext({acceptDownloads:true});
 await context.route('**/*',route=>route.request().url().startsWith(base+'/')?route.continue():route.abort());
 await context.grantPermissions(['clipboard-read','clipboard-write']);
 const results=[];
 for (const product of ['english','math']) {
  const page=await context.newPage();await page.emulateMedia({reducedMotion:"reduce"});
  const errors=[];page.on('pageerror', e=>errors.push(e.message));
  const file=`${base}/${product}.html`;
  for (const width of [1440,375]) {
   await page.setViewportSize({width,height:1000});await page.goto(file);await page.evaluate(()=>document.fonts.ready);
   assert(await page.evaluate(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0)),'offline images');
   assert(await page.evaluate(()=>document.fonts.check('20px Literata')&&document.fonts.check('24px Caveat')),'offline fonts');
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'horizontal overflow');
   assert.equal(await page.locator('#prompt-text').textContent(), fs.readFileSync(path.join(root,`products/${product}/PROMPT.txt`),'utf8'));
   await page.screenshot({path:path.join(root,`books/screenshots/${product}-full-${width}.jpg`),fullPage:true,type:'jpeg',quality:82});
   await page.screenshot({path:path.join(root,`books/screenshots/${product}-cover-${width}.png`)});
   await page.locator('#voice').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
   await page.screenshot({path:path.join(root,`books/screenshots/${product}-reading-${width}.png`)});
   if(product==='math'){
    const graf=page.getByRole('button',{name:'Граф',exact:true});await graf.focus();await page.keyboard.press('Enter');
    assert.equal(await graf.getAttribute('aria-pressed'),'true');
    assert((await page.locator('.voice-quote').textContent()).includes('В мою рукопись'));
   }
   const copy=page.locator('[data-copy-prompt]').first();await copy.click();
   await page.waitForFunction(()=>document.querySelector('.copy-status').textContent.includes('Готово'),null,{timeout:10000});
   assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),fs.readFileSync(path.join(root,`products/${product}/PROMPT.txt`),'utf8'));
   const downloadPromise=page.waitForEvent('download');await page.getByRole('link',{name:'Скачать TXT ↓',exact:true}).first().click();
   const download=await downloadPromise;const temp=await download.path();
   assert.equal(fs.readFileSync(temp,'utf8'),fs.readFileSync(path.join(root,`products/${product}/PROMPT.txt`),'utf8'));
   await page.locator('details').evaluate(el=>el.open=true);
   assert(await page.locator('#prompt-text').isVisible());
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'prompt overflow');
   assert.equal(errors.length,0,errors.join('\n'));
   results.push({product,width,offlineImages:true,offlineFonts:true,noOverflow:true,exactPrompt:true,clipboard:true,download:true,keyboardVoiceSwitch:product==='math',jsErrors:errors});
  }
  await page.goto(file);
  await page.evaluate(()=>{
   Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('permission denied')}}});
   document.execCommand=()=>false;
  });
  await page.locator('[data-copy-prompt]').first().click();
  await page.waitForFunction(()=>document.querySelector('.copy-status').textContent.includes('Браузер не разрешил'));
  await page.setViewportSize({width:1440,height:1000});await page.goto(file);await page.evaluate(()=>document.fonts.ready);
  await page.pdf({path:path.join(root,`books/${product}-companion.pdf`),format:'A4',printBackground:true,preferCSSPageSize:true,displayHeaderFooter:true,headerTemplate:'<span></span>',footerTemplate:'<div style="width:100%;text-align:center;font:9px Arial;color:#6e554f">На одном листе · <span class="pageNumber"></span> / <span class="totalPages"></span></div>' });
  await page.close();
 }
 const page=await context.newPage();await page.setViewportSize({width:375,height:900});await page.goto(`${base}/START.html`);await page.evaluate(()=>document.fonts.ready);
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.getByRole('link',{name:/Ника/}).click();assert(page.url().endsWith('english.html'));
 fs.writeFileSync(path.join(root,'books/BROWSER_QA.json'),JSON.stringify({mode:'Chromium, local HTTP static files only; external network blocked; file:// restricted by execution environment',date:'2026-10-25',checks:results,pdfExported:true,collectionNavigation:true,clipboardDeniedFallback:true},null,2)+'\n');
 await browser.close();await new Promise(resolve=>server.close(resolve));console.log('Self-contained books verified: 4 viewport/product combinations, clipboard, TXT download, keyboard, PDFs.');
})().catch(e=>{console.error(e);process.exit(1)});
