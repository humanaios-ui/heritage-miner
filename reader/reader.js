// Living Edition Reader. Vanilla ES module. Same-origin fetches only. Data is rendered with textContent.
const DATA = '../data/';
const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

let ms = null, pages = [], idx = 0;
let research = null, researchTried = false;
let contribs = null, contribTried = false;

async function getJSON(path) {
  const r = await fetch(path, { cache: 'no-cache' });
  if (!r.ok) throw new Error(path + ' ' + r.status);
  return r.json();
}

function showErr(msg) { const e = $('err'); e.textContent = msg; e.hidden = !msg; }

async function load() {
  for (let i = 0; i < 6; i++) { // data may still be arriving
    try { ms = await getJSON(DATA + 'manuscript.json'); break; }
    catch (e) { if (i === 5) { showErr('Could not load data/manuscript.json. Serve the repo root and open /reader/.'); return; } await new Promise(r => setTimeout(r, 800)); }
  }
  pages = ms.pages || [];
  $('book-title').textContent = ms.title || 'Untitled edition';
  document.title = (ms.title || 'Edition') + ' (' + (ms.edition || '') + ', synthetic)';
  renderNotice(); renderChapters();
  const h = location.hash.slice(1);
  const start = pages.findIndex(p => p.id === h);
  go(start >= 0 ? start : 0, false);
}

function renderNotice() {
  const c = ms.completeness || { status: 'OPEN', note: '' };
  const n = $('notice'); n.textContent = '';
  n.append(el('strong', null, 'Completeness: ' + (c.status || 'OPEN') + '. '),
    document.createTextNode((c.note || 'It is not established that every page is present.') +
      ' This edition is not claimed to be complete.'));
  n.hidden = false;
}

function chapterOf(i) {
  const id = pages[i] && pages[i].id;
  return (ms.chapters || []).findIndex(c => (c.pages || []).includes(id));
}

function renderChapters() {
  const sel = $('chapter-select'), list = $('chapter-list');
  sel.textContent = ''; list.textContent = '';
  const chs = ms.chapters || [];
  chs.forEach((c, i) => {
    sel.append(new Option(c.title, String(i)));
    const li = el('li'); const b = el('button', null, c.title); b.type = 'button';
    b.dataset.ch = i; b.addEventListener('click', () => gotoChapter(i));
    li.append(b); list.append(li);
  });
  sel.addEventListener('change', () => gotoChapter(+sel.value));
}

function gotoChapter(ci) {
  const first = (ms.chapters[ci].pages || [])[0];
  const i = pages.findIndex(p => p.id === first);
  if (i >= 0) go(i);
}

function go(i, focus = true) {
  if (!pages.length) return;
  idx = Math.max(0, Math.min(pages.length - 1, i));
  const p = pages[idx];
  history.replaceState(null, '', '#' + p.id);
  const img = $('scan');
  $('scan-fail').hidden = true;
  img.onerror = () => { $('scan-fail').hidden = false; };
  img.src = '../' + p.scan.replace(/^\.?\//, '');
  img.alt = p.alt || 'Scan of page ' + p.id;
  img.classList.remove('turn');
  if (!reduceMotion) { void img.offsetWidth; img.classList.add('turn'); }

  const label = p.printed_number != null ? 'printed page ' + p.printed_number : 'unnumbered page';
  const ci = chapterOf(idx);
  $('pos').textContent = 'Page ' + (idx + 1) + ' of ' + pages.length + ' (' + label + ')' +
    (ci >= 0 ? ' · ' + ms.chapters[ci].title : '');
  $('prev').disabled = idx === 0; $('next').disabled = idx === pages.length - 1;
  if (ci >= 0) {
    $('chapter-select').value = String(ci);
    document.querySelectorAll('#chapter-list button').forEach(b => {
      if (+b.dataset.ch === ci) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current');
    });
  }

  const st = p.transcription_status || 'none';
  const s = $('status'); s.textContent = 'Transcription status: ';
  s.append(el('span', 'badge ' + st, st));
  if (p.orientation_corrected) s.append(document.createTextNode(' · scan orientation corrected'));
  const t = $('transcription'); t.textContent = '';
  if (p.transcription) {
    p.transcription.split(/\n{2,}/).forEach(par => t.append(el('p', null, par)));
    if (st === 'unchecked') t.prepend(el('p', 'empty', 'Not yet checked against the scan.'));
  } else {
    t.append(el('p', 'empty', p.kind === 'text' ? 'No transcription yet.' : 'No text on this page (' + (p.kind || 'image') + ').'));
  }
  $('interp').hidden = !p.interpretation_note;
  $('interp-text').textContent = p.interpretation_note || '';
  renderResearch(); renderContribs();
  if (focus) $('main').focus({ preventScroll: true });
}

// ---- optional overlays (fetched only when toggled on) ----
async function renderResearch() {
  const box = $('research'), body = $('research-body');
  if (!$('t-research').checked) { box.hidden = true; return; }
  box.hidden = false;
  if (!research && !researchTried) {
    researchTried = true;
    try { research = await getJSON(DATA + 'research.json'); } catch (e) { research = null; }
  }
  body.textContent = '';
  if (!research) { body.append(el('p', 'muted', 'Research data is unavailable.')); return; }
  const pid = pages[idx].id;
  const claims = (research.claims || []).filter(c => (c.sources || []).some(s => s.ref === pid));
  body.append(el('p', 'muted', 'Claims are labelled, never confirmed facts. Nothing here selects an ancestor.'));
  if (!claims.length) body.append(el('p', null, 'No research claims cite this page.'));
  const ul = el('ul');
  claims.forEach(c => {
    const li = el('li');
    li.append(el('span', 'badge ' + c.label, c.label), document.createTextNode(' ' + c.text));
    (c.sources || []).forEach(s => li.append(el('div', 'muted', 'Source (' + s.kind + '): ' + s.ref + (s.note ? ' — ' + s.note : ''))));
    if (c.discrepancy) li.append(el('div', 'muted', 'Discrepancy between ' + (c.discrepancy.between || []).join(' and ') + ': ' + c.discrepancy.detail));
    ul.append(li);
  });
  body.append(ul);
  const n = (research.leads || []).length;
  if (n) body.append(el('p', 'muted', n + ' inert research lead(s) exist; they require human approval and are not shown or acted on here.'));
}

// index.json (DATA_CONTRACT.md): JSON array of contribution filenames, e.g. ["c002.json"]
function contribNames(m) {
  return (Array.isArray(m) ? m : []).filter(n => typeof n === 'string' && !/[\/]/.test(n) && n !== 'index.json')
    .map(n => /\.json$/.test(n) ? n : n + '.json');
}
async function loadContribs() {
  const found = [];
  let names = [];
  try { names = contribNames(await getJSON(DATA + 'contributions/index.json')); } catch (e) { /* no manifest */ }
  for (const n of names) { try { found.push(await getJSON(DATA + 'contributions/' + n)); } catch (e) { /* skip */ } }
  return found.filter(c => c && c.status === 'approved')
    .sort((a, b) => String(a.submitted).localeCompare(String(b.submitted)));
}

async function renderContribs() {
  const box = $('contrib'), body = $('contrib-body');
  if (!$('t-contrib').checked) { box.hidden = true; return; }
  box.hidden = false;
  if (!contribs && !contribTried) { contribTried = true; contribs = await loadContribs(); }
  body.textContent = '';
  const here = pages[idx].id;
  const list = (contribs || []).slice().sort((a, b) => (b.attaches_to === here) - (a.attaches_to === here));
  if (!list.length) { body.append(el('p', null, 'No approved additions yet.')); return; }
  list.forEach(c => {
    const d = el('article', 'addition');
    d.append(el('div', 'stamp', 'Added ' + String(c.submitted).slice(0, 10) + ' by ' + c.contributor_label + ' — not part of the 1992 edition'));
    d.append(el('h3', null, c.title));
    d.append(el('p', null, c.body));
    d.append(el('div', 'muted', c.kind + (c.attaches_to ? ' · relates to ' + (c.attaches_to === here ? 'this page' : c.attaches_to) : '') + (c.license ? ' · ' + c.license : '')));
    body.append(d);
  });
}

// ---- input ----
$('prev').addEventListener('click', () => go(idx - 1));
$('next').addEventListener('click', () => go(idx + 1));
$('t-research').addEventListener('change', renderResearch);
$('t-contrib').addEventListener('change', renderContribs);
addEventListener('hashchange', () => { const i = pages.findIndex(p => p.id === location.hash.slice(1)); if (i >= 0 && i !== idx) go(i, false); });
addEventListener('keydown', (e) => {
  if (e.altKey || e.ctrlKey || e.metaKey || /^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName)) return;
  if (e.key === 'ArrowRight') go(idx + 1);
  else if (e.key === 'ArrowLeft') go(idx - 1);
  else if (e.key === 'Home') go(0);
  else if (e.key === 'End') go(pages.length - 1);
});
let sx = null, sy = null;
$('spread').addEventListener('touchstart', (e) => { sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, { passive: true });
$('spread').addEventListener('touchend', (e) => {
  if (sx == null) return;
  const dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
  sx = null;
  if (Math.abs(dx) > 60 && Math.abs(dx) > 2 * Math.abs(dy)) go(idx + (dx < 0 ? 1 : -1));
}, { passive: true });

load();
