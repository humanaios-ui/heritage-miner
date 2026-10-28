/* The Anderson Story: browser-only family edition preview. No remote calls. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  // Public-safe thematic guide only; the original named TOC is in the private PDF.
  const chapters = [
    ['The family beginnings','ROOTS'], ['Across the early generations','HISTORY'],
    ['Families and journeys west','JOURNEYS'], ['Shared photographs and recollections','MEMORIES'],
    ['The chapters still being written','TODAY']
  ];
  const knownPdfPages = 217; // From the 2026 private source scan. Not printed book pages.
  const dbName = 'anderson-living-edition-local-drafts';
  let db = null, memoryDrafts = [], pdfUrl = null, scannedPage = 1, rotated = false;
  let previewUrl = null;
  const allowed = new Set(['image/jpeg','image/png','image/webp','image/gif','audio/mpeg','audio/mp4','audio/wav','audio/webm','application/pdf']);
  const MAX = 12 * 1024 * 1024;

  function showStatus(message, error = false) {
    $('formMessage').textContent = message;
    $('formMessage').classList.toggle('error', error);
  }
  function cleanPlain(s, max=6000) { return String(s || '').trim().slice(0, max); }
  function validateFile(file) {
    if (!file) return;
    if (!allowed.has(file.type)) throw new Error('Please choose a supported image, audio, or PDF file.');
    if (file.size > MAX) throw new Error('File is over 12 MB. Please choose a smaller file.');
  }
  function safeName(s) { return (s || 'memory').replace(/[^a-z0-9-_]+/gi,'-').replace(/-+/g,'-').slice(0,48) || 'memory'; }
  function newId() { return (self.crypto && self.crypto.randomUUID) ? self.crypto.randomUUID() : 'memory-' + Date.now() + '-' + Math.random().toString(36).slice(2); }
  function make(tag, text, className) {const e=document.createElement(tag); if (text!==undefined) e.textContent=text; if(className)e.className=className; return e; }
  function download(blob, name) {
    const url=URL.createObjectURL(blob), a=make('a'); a.href=url;a.download=name;
    document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2500);
  }
  const readerPlaceholder = $('readerPlaceholder');
  const toc = $('chapters');
  for (const [title,p] of chapters) { const li=make('li');li.append(make('span',title), make('span',p));toc.append(li); }

  /* File stays in memory; every new visit requires selection. */
  $('pdfInput').addEventListener('change', (ev)=> {
    const file=ev.target.files[0];if(!file)return;
    if(file.type!=='application/pdf' && !/\.pdf$/i.test(file.name))return;
    if(pdfUrl)URL.revokeObjectURL(pdfUrl);
    pdfUrl=URL.createObjectURL(file);scannedPage=1;rotated=false;
    readerPlaceholder.hidden=true;$('readerActive').hidden=false;$('pdfStatus').textContent='OPEN ON THIS DEVICE';
    $('totalPages').textContent='/ '+knownPdfPages;updatePdf();
  });
  function updatePdf(){
    if(!pdfUrl)return;
    scannedPage=Math.min(knownPdfPages,Math.max(1,Number(scannedPage)||1));
    $('scanPage').value=String(scannedPage);
    $('pdfFrame').src=pdfUrl+'#page='+scannedPage+'&view=FitH';
    $('pdfFrame').style.transform=rotated?'rotate(180deg)':'none';
    $('externalPdf').href=pdfUrl+'#page='+scannedPage;
    $('prevPage').disabled=scannedPage===1;$('nextPage').disabled=scannedPage===knownPdfPages;
  }
  $('prevPage').addEventListener('click',()=>{scannedPage--;updatePdf();});
  $('nextPage').addEventListener('click',()=>{scannedPage++;updatePdf();});
  $('scanPage').addEventListener('change',e=>{scannedPage=Number(e.target.value);updatePdf();});
  $('rotatePage').addEventListener('click',()=>{rotated=!rotated;updatePdf();});

  $('menuButton').addEventListener('click',()=>{
    const on=$('navlinks').classList.toggle('open');$('menuButton').setAttribute('aria-expanded',String(on));
  });
  document.querySelectorAll('#navlinks a').forEach(a=>a.addEventListener('click',()=>{
    $('navlinks').classList.remove('open');$('menuButton').setAttribute('aria-expanded','false');
  }));

  /* IndexedDB stores local drafts only. If unavailable, session-only mode. */
  function openDb(){return new Promise((resolve,reject)=>{
    if(!('indexedDB' in self)){reject(new Error('no indexedDB'));return;}
    const r=indexedDB.open(dbName,1);
    r.onupgradeneeded=()=>r.result.createObjectStore('drafts',{keyPath:'id'});
    r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);
  });}
  function transaction(mode, operation){return new Promise((resolve,reject)=>{
    if(!db){resolve(null);return;}
    const tx=db.transaction('drafts',mode),store=tx.objectStore('drafts');
    let req;
    try{req=operation(store);}catch(e){reject(e);return;}
    if(req){req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);}
    else {tx.oncomplete=()=>resolve(true);tx.onerror=()=>reject(tx.error);}
  });}
  async function allDrafts(){ return db ? await transaction('readonly',s=>s.getAll()) : memoryDrafts.slice(); }
  async function addDraft(d){ if(db){await transaction('readwrite',s=>s.put(d));}else{memoryDrafts=memoryDrafts.filter(x=>x.id!==d.id);memoryDrafts.push(d);} }
  async function dropDraft(id){if(db){await transaction('readwrite',s=>s.delete(id));}else memoryDrafts=memoryDrafts.filter(x=>x.id!==id);}
  async function renderAlbum(){
    const drafts=(await allDrafts()).sort((a,b)=>(b.savedAt||'').localeCompare(a.savedAt||''));
    $('albumEmpty').hidden=drafts.length>0;$('albumList').hidden=drafts.length===0;
    $('albumList').replaceChildren();
    for(const draft of drafts){
      const card=make('article',undefined,'memoryCard');const box=make('div',undefined,'memoryVisual');
      if(draft.file && draft.file.type.startsWith('image/')){
        const img=document.createElement('img');img.alt=draft.title;img.src=URL.createObjectURL(draft.file);img.addEventListener('load',()=>URL.revokeObjectURL(img.src),{once:true});box.append(img);
      }else box.textContent=draft.type==='audio'?'♫':draft.type==='document'?'▤':'✳';
      const info=make('div',undefined,'memoryInfo');
      info.append(make('span',draft.audience==='family-review'?'PROPOSED FOR FAMILY REVIEW · NOT SUBMITTED':'PRIVATE DRAFT','memoryMeta'));
      info.append(make('h3',draft.title));
      const summary=[draft.date,draft.place].filter(Boolean).join(' · ');
      if(summary)info.append(make('p',summary));
      if(draft.story)info.append(make('p',draft.story.length>280?draft.story.slice(0,280)+'…':draft.story));
      info.append(make('p','Contributed by '+draft.by));
      const actions=make('div',undefined,'cardActions');
      const exportButton=make('button','Export contribution ↗');exportButton.type='button';exportButton.addEventListener('click',()=>exportDraft(draft));
      const deleteButton=make('button','Delete draft');deleteButton.type='button';deleteButton.addEventListener('click',async()=>{
        if(!confirm('Delete this local draft? Export a copy first if you want to keep it.'))return;
        await dropDraft(draft.id);await renderAlbum();
      });actions.append(exportButton,deleteButton);info.append(actions);card.append(box,info);$('albumList').append(card);
    }
  }
  function readAsDataUrl(file){return new Promise((resolve,reject)=>{let r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=()=>reject(r.error);r.readAsDataURL(file);});}
  async function exportDraft(d){
    const {file,...data}=d; const payload={format:'anderson-family-contribution-v1',draft:data,file:file?{
      name:file.name,type:file.type,size:file.size,dataUrl:await readAsDataUrl(file)
    }:null};
    download(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),safeName(d.title)+'-family-contribution.json');
  }
  function dataUrlToFile(f){
    if(!f)return null;
    if(typeof f.dataUrl!=='string'||typeof f.type!=='string'||!allowed.has(f.type))throw new Error('Unsupported imported attachment');
    const prefix='data:'+f.type+';base64,';
    if(!f.dataUrl.startsWith(prefix))throw new Error('Invalid attachment data');
    if(f.dataUrl.length>MAX*1.4+100)throw new Error('Attachment too large');
    const binary=atob(f.dataUrl.slice(prefix.length));
    const arr=new Uint8Array(binary.length);for(let i=0;i<binary.length;i++)arr[i]=binary.charCodeAt(i);
    const file=new File([arr],cleanPlain(f.name,130)||'attachment',{type:f.type});validateFile(file);return file;
  }
  $('importContribution').addEventListener('change',async(e)=>{
    try{
      const file=e.target.files[0];if(!file)return;
      if(file.size>17*1024*1024)throw Error('Contribution package is too large');
      const raw=JSON.parse(await file.text());
      if(raw.format!=='anderson-family-contribution-v1'||!raw.draft||typeof raw.draft.title!=='string'||typeof raw.draft.by!=='string')throw Error('Not a supported contribution file');
      const d=raw.draft;const safe={id:newId(),title:cleanPlain(d.title,110),type:cleanPlain(d.type,20),date:cleanPlain(d.date,70),place:cleanPlain(d.place,160),people:cleanPlain(d.people,160),story:cleanPlain(d.story),by:cleanPlain(d.by,100),audience:d.audience==='family-review'?'family-review':'private',savedAt:new Date().toISOString(),file:dataUrlToFile(raw.file)};
      if(!safe.title||!safe.by)throw Error('Missing required fields');
      await addDraft(safe);await renderAlbum();$('album').scrollIntoView({behavior:'smooth'});showStatus('Contribution imported on this device. It has not been submitted.');
    }catch(err){showStatus('Could not import: '+err.message,true);}finally{e.target.value='';}
  });
  $('memoryFile').addEventListener('change',e=>{
    const file=e.target.files[0];
    if(previewUrl)URL.revokeObjectURL(previewUrl);
    $('filePreview').hidden=true;$('filePreview').replaceChildren();
    if(!file){$('uploadLabel').textContent='Choose a photo, audio clip, or document';return;}
    try{validateFile(file);$('uploadLabel').textContent=file.name;previewUrl=URL.createObjectURL(file);
      if(file.type.startsWith('image/')){const img=document.createElement('img');img.src=previewUrl;img.alt='Selected contribution preview';$('filePreview').append(img);}
      else if(file.type.startsWith('audio/')){const audio=document.createElement('audio');audio.controls=true;audio.src=previewUrl;$('filePreview').append(audio);}
      else $('filePreview').append(make('p','PDF selected: '+file.name));
      $('filePreview').hidden=false;showStatus('File selected. Save your draft when ready.');
    }catch(err){showStatus(err.message,true);e.target.value='';}
  });
  $('resetForm').addEventListener('click',()=>{$('contributionForm').reset();$('filePreview').hidden=true;$('filePreview').replaceChildren();$('uploadLabel').textContent='Choose a photo, audio clip, or document';showStatus('Form cleared. Existing drafts remain saved.');});
  $('contributionForm').addEventListener('submit',async e=>{
    e.preventDefault();
    try{
      const title=cleanPlain($('memoryTitle').value,110),by=cleanPlain($('memoryBy').value,100),file=$('memoryFile').files[0]||null;
      if(!title||!by)throw Error('Please provide a title and your name.');
      if(!$('memoryConfirm').checked)throw Error('Please confirm you have permission to share this contribution with a family editor.');
      validateFile(file);
      const d={id:newId(),title,by,type:$('memoryType').value,date:cleanPlain($('memoryDate').value,70),story:cleanPlain($('memoryStory').value),people:cleanPlain($('memoryPeople').value,160),place:cleanPlain($('memoryPlace').value,160),audience:$('memoryAudience').value,file,savedAt:new Date().toISOString()};
      await addDraft(d);await renderAlbum();
      $('contributionForm').reset();$('filePreview').hidden=true;$('filePreview').replaceChildren();$('uploadLabel').textContent='Choose a photo, audio clip, or document';
      showStatus(db?'Draft saved on this device. Open Family album to export or delete it.':'Draft saved for this browser session only. Export it from Family album before leaving.');
      $('album').scrollIntoView({behavior:'smooth'});
    }catch(err){showStatus(err.message,true);}
  });
  openDb().then(async x=>{db=x;await renderAlbum();}).catch(async()=>{db=null;$('albumPrivate').textContent='Local saving is unavailable in this browser. Drafts last only until this page closes. Export your contribution before leaving.';await renderAlbum();});
})();