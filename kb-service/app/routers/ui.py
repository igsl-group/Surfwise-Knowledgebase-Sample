"""Minimal self-contained web GUI for document management (upload/download/delete)."""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.manual import MANUAL_MD
from app.markdown_utils import render_html
from app.security import require_ui_auth

router = APIRouter(tags=["ui"], include_in_schema=False)

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Knowledge Base - Documents</title>
<style>
  :root{--fg:#1f2937;--muted:#6b7280;--line:#e5e7eb;--brand:#2563eb;--bg:#f8fafc}
  *{box-sizing:border-box}
  body{margin:0;font:14px/1.5 system-ui,Segoe UI,Roboto,sans-serif;color:var(--fg);background:var(--bg)}
  header{background:#0f172a;color:#fff;padding:14px 20px}
  header h1{margin:0;font-size:18px}
  header small{color:#94a3b8}
  main{max-width:1000px;margin:20px auto;padding:0 16px}
  .card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:16px}
  .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
  label{font-weight:600;font-size:12px;color:var(--muted)}
  input,select,button{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:#fff}
  input[type=text],input[type=password]{min-width:280px}
  button{background:var(--brand);color:#fff;border:0;cursor:pointer}
  button.sec{background:#fff;color:var(--fg);border:1px solid var(--line)}
  button.danger{background:#dc2626}
  table{width:100%;border-collapse:collapse;margin-top:8px}
  th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line);font-size:13px;vertical-align:top}
  th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
  .tag{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:6px;padding:1px 7px;font-size:11px}
  #msg{min-height:20px;font-size:13px}
  .ok{color:#16a34a}.err{color:#dc2626}
  #viewer{white-space:normal}
  #viewer h1,#viewer h2,#viewer h3{margin:.4em 0}
  pre{background:#0f172a;color:#e2e8f0;padding:10px;border-radius:8px;overflow:auto}
  code{background:#f1f5f9;padding:1px 4px;border-radius:4px}
  a.dl{color:var(--brand);cursor:pointer;text-decoration:underline}
  .actions{display:flex;gap:6px;flex-wrap:wrap}
  .ic{width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
  .btn-sm{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:600;padding:5px 10px;border-radius:7px;border:1px solid var(--line);background:#fff;color:#374151;cursor:pointer;text-decoration:none;transition:all .15s ease;line-height:1;white-space:nowrap}
  .btn-sm:hover{box-shadow:0 1px 3px rgba(0,0,0,.12)}
  .btn-view:hover{border-color:#2563eb;color:#2563eb;background:#eff6ff}
  .btn-dl{border-color:#bfdbfe;color:#2563eb;background:#eff6ff}
  .btn-dl:hover{background:#2563eb;color:#fff;border-color:#2563eb}
  .btn-del{color:#dc2626;border-color:#fecaca;background:#fef2f2}
  .btn-del:hover{background:#dc2626;color:#fff;border-color:#dc2626}
  .nav{display:flex;gap:4px;background:#fff;border-bottom:1px solid var(--line);padding:0 18px}
  .navlink{padding:12px 16px;font-weight:600;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent;user-select:none}
  .navlink:hover{color:var(--fg)}
  .navlink.active{color:var(--brand);border-bottom-color:var(--brand)}
  button.sec[disabled]{opacity:.5;cursor:not-allowed}
  .modal-overlay{position:fixed;inset:0;background:rgba(15,23,42,.55);display:flex;align-items:center;justify-content:center;z-index:60;padding:20px}
  .modal{background:#fff;border-radius:12px;max-width:840px;width:100%;max-height:86vh;display:flex;flex-direction:column;box-shadow:0 12px 44px rgba(0,0,0,.32)}
  .modal-head{display:flex;justify-content:space-between;align-items:center;padding:14px 18px;border-bottom:1px solid var(--line)}
  .modal-body{padding:18px;overflow:auto}
</style>
</head>
<body>
<header>
  <h1>Knowledge Base &mdash; Document Management</h1>
  <small>Upload, download and delete documents. Content is indexable by SurfWise via the BookStack-compatible API.</small>
</header>
<nav class="nav">
  <a class="navlink" id="nav-docs" onclick="showView('docs')">Documents</a>
  <a class="navlink" id="nav-tokens" onclick="showView('tokens')">API Tokens</a>
  <a class="navlink" id="nav-links" onclick="showView('links')">Docs</a>
  <a class="navlink" id="nav-settings" onclick="showView('settings')">Settings</a>
</nav>
<main>
  <div class="card" id="card-settings">
    <div class="row">
      <div>
        <div><label>API token (id:secret)</label></div>
        <input id="token" type="password" placeholder="tokenid:tokensecret"/>
      </div>
      <button class="sec" onclick="saveToken()">Save token</button>
      <span id="whoami" style="color:var(--muted)"></span>
    </div>
  </div>

  <div class="card" id="card-upload">
    <div class="row">
      <div>
        <div><label>Book</label></div>
        <select id="book"></select>
      </div>
      <div>
        <div><label>New book</label></div>
        <input id="newbook" type="text" placeholder="e.g. Runbooks"/>
      </div>
      <button class="sec" onclick="createBook()">Create book</button>
    </div>
    <hr style="border:none;border-top:1px solid var(--line);margin:14px 0"/>
    <div class="row">
      <div>
        <div><label>Upload document</label></div>
        <input id="file" type="file"/>
      </div>
      <div>
        <div><label>Title (optional)</label></div>
        <input id="title" type="text" placeholder="defaults to filename"/>
      </div>
      <button onclick="upload()">Upload</button>
    </div>
    <p id="msg"></p>
  </div>

  <div class="card" id="card-docs">
    <div class="row" style="justify-content:space-between">
      <strong>Documents</strong>
      <button class="sec" onclick="loadDocs()">Refresh</button>
    </div>
    <table>
      <thead><tr><th>Name</th><th>Book</th><th>Type</th><th>Size</th><th>Updated</th><th>Actions</th></tr></thead>
      <tbody id="docs"></tbody>
    </table>
    <div id="docpager" style="margin-top:12px;display:flex;align-items:center"></div>
  </div>

  <div class="card" id="card-tokens">
    <div class="row" style="justify-content:space-between">
      <strong>API Tokens</strong>
      <button class="sec" onclick="loadTokens()">Refresh</button>
    </div>
    <div class="row" style="margin-top:8px">
      <div><div><label>New token name</label></div><input id="tokname" type="text" placeholder="e.g. surfwise-connector"/></div>
      <label style="align-self:end"><input id="tokadmin" type="checkbox"/> admin (write access)</label>
      <button onclick="createToken()">Create token</button>
    </div>
    <div style="font-size:12px;color:var(--muted);margin-top:4px">Tip: give SurfWise a <strong>read-only</strong> token (leave &ldquo;admin&rdquo; unchecked) &mdash; it can index but not modify content.</div>
    <div id="newtok" style="display:none;margin-top:10px;padding:10px;border:1px dashed #16a34a;border-radius:8px;background:#f0fdf4"></div>
    <table>
      <thead><tr><th>Name</th><th>Token ID</th><th>Created</th><th>Admin</th><th>Actions</th></tr></thead>
      <tbody id="toks"></tbody>
    </table>
  </div>

  <div class="card" id="card-links">
    <div class="row" style="justify-content:space-between"><strong>Documentation &amp; Links</strong></div>
    <ul style="line-height:2.1;margin:10px 0 0;padding-left:18px">
      <li><a href="/manual" target="_blank" style="color:var(--brand);font-weight:600">&#128214; How to connect this KB to SurfWise (Admin Guide)</a></li>
      <li><a href="/docs" target="_blank" style="color:var(--brand)">API docs (Swagger)</a></li>
      <li><a href="https://github.com/igsl-group/Surfwise-Knowledgebase-Sample" target="_blank" style="color:var(--brand)">GitHub repo</a></li>
    </ul>
  </div>

  <div id="modal" class="modal-overlay" style="display:none" onclick="if(event.target===this)closeModal()">
    <div class="modal">
      <div class="modal-head"><strong id="viewtitle">Preview</strong><button class="sec" onclick="closeModal()">Close</button></div>
      <div id="viewer" class="modal-body"></div>
    </div>
  </div>
</main>
<script>
const $ = (id) => document.getElementById(id);
const IC_VIEW='<svg class="ic" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
const IC_DL='<svg class="ic" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>';
const IC_DEL='<svg class="ic" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>';
function tok(){ return localStorage.getItem('kb_token') || ''; }
function hdr(){ return { 'Authorization': 'Token ' + tok() }; }
function saveToken(){ localStorage.setItem('kb_token', $('token').value.trim()); msg('Token saved.', true); init(); }
function msg(t, ok){ const m=$('msg'); m.textContent=t; m.className = ok? 'ok':'err'; }
function fmtSize(n){ if(n==null) return '-'; if(n<1024) return n+' B'; if(n<1048576) return (n/1024).toFixed(1)+' KB'; return (n/1048576).toFixed(1)+' MB'; }

async function api(path, opts){
  opts = opts || {}; opts.headers = Object.assign({}, hdr(), opts.headers||{});
  const r = await fetch(path, opts);
  if(r.status===401){ msg('Unauthorized - check your token.', false); throw new Error('401'); }
  return r;
}

async function loadBooks(){
  const r = await api('/api/books?count=200'); const d = await r.json();
  const sel = $('book'); sel.innerHTML='';
  (d.data||[]).forEach(b=>{ const o=document.createElement('option'); o.value=b.id; o.textContent=b.name; sel.appendChild(o); });
}
async function createBook(){
  const name = $('newbook').value.trim(); if(!name){ msg('Enter a book name.', false); return; }
  const r = await api('/api/books', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name, is_admin: $('tokadmin').checked})});
  if(r.ok){ $('newbook').value=''; await loadBooks(); msg('Book created.', true); } else { msg('Create failed: '+r.status, false); }
}
async function upload(){
  const f = $('file').files[0]; if(!f){ msg('Choose a file.', false); return; }
  const fd = new FormData(); fd.append('file', f); fd.append('book_id', $('book').value);
  if($('title').value.trim()) fd.append('name', $('title').value.trim());
  msg('Uploading...', true);
  const r = await api('/api/documents/upload', {method:'POST', body:fd});
  if(r.ok){ $('file').value=''; $('title').value=''; msg('Uploaded.', true); loadDocs(); }
  else { const e = await r.text(); msg('Upload failed: '+r.status+' '+e, false); }
}
let docPage = 0;
const DOC_PAGE_SIZE = 10;
async function loadDocs(){
  const r = await api('/api/documents?count='+DOC_PAGE_SIZE+'&offset='+(docPage*DOC_PAGE_SIZE));
  const d = await r.json();
  const rows = d.data || [];
  if(rows.length===0 && docPage>0){ docPage--; return loadDocs(); }
  const tb = $('docs'); tb.innerHTML='';
  rows.forEach(doc=>{
    const tr=document.createElement('tr');
    const type = doc.is_file ? (doc.content_type||'file') : 'markdown';
    tr.innerHTML = '<td>'+esc(doc.name)+'</td><td>'+esc(doc.book_name)+'</td>'+
      '<td><span class="tag">'+esc(type)+'</span></td><td>'+fmtSize(doc.size)+'</td>'+
      '<td>'+(doc.updated_at||'').slice(0,19).replace('T',' ')+'</td>'+
      '<td><div class="actions">'+
        '<a class="btn-sm btn-view" onclick="view('+doc.id+')">'+IC_VIEW+'View</a>'+
        '<a class="btn-sm btn-dl" onclick="downloadDoc('+doc.id+', this)">'+IC_DL+'Download</a>'+
        '<a class="btn-sm btn-del" onclick="del('+doc.id+')">'+IC_DEL+'Delete</a>'+
      '</div></td>';
    tb.appendChild(tr);
  });
  renderDocPager(d.total || 0);
}
function renderDocPager(total){
  const pg=$('docpager'); if(!pg) return;
  const pages = Math.max(1, Math.ceil(total/DOC_PAGE_SIZE));
  const start = total ? docPage*DOC_PAGE_SIZE+1 : 0;
  const end = Math.min(total, (docPage+1)*DOC_PAGE_SIZE);
  pg.innerHTML = '<button class="sec" '+(docPage<=0?'disabled':'')+' onclick="docPrev()">&lsaquo; Prev</button>'+
    '<span style="margin:0 12px;color:var(--muted);font-size:13px">'+start+'&ndash;'+end+' of '+total+' documents</span>'+
    '<button class="sec" '+(docPage>=pages-1?'disabled':'')+' onclick="docNext()">Next &rsaquo;</button>';
}
function docPrev(){ if(docPage>0){ docPage--; loadDocs(); } }
function docNext(){ docPage++; loadDocs(); }
function esc(s){ return (s==null?'':String(s)).replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
async function view(id){
  const r = await api('/api/pages/'+id); const d = await r.json();
  $('viewtitle').textContent = d.name; $('viewer').innerHTML = d.html || '<em>(no content)</em>';
  $('modal').style.display='flex';
}
function closeModal(){ $('modal').style.display='none'; }
async function downloadDoc(id, el){
  if(el && el.dataset.busy==='1') return;               // block repeat clicks
  const orig = el ? el.innerHTML : '';
  const setLabel = (t)=>{ if(el) el.textContent = t; };
  if(el){ el.dataset.busy='1'; el.style.pointerEvents='none'; el.style.opacity='0.55'; }
  setLabel('Preparing...');
  try{
    const r = await api('/api/documents/'+id+'/download');
    if(!r.ok){ msg('Download failed: '+r.status, false); return; }
    let fn='document';
    const cd = r.headers.get('Content-Disposition')||'';
    let m = cd.match(/filename[*]=UTF-8''([^;]+)/i);
    if(m){ try{ fn=decodeURIComponent(m[1]); }catch(e){ fn=m[1]; } }
    else { m = cd.match(/filename="?([^";]+)"?/i); if(m) fn=m[1]; }
    const total = parseInt(r.headers.get('Content-Length')||'0', 10);
    let blob;
    if(r.body && r.body.getReader){
      const reader = r.body.getReader(); const chunks=[]; let got=0;
      while(true){ const s = await reader.read(); if(s.done) break; chunks.push(s.value); got += s.value.length;
        setLabel(total ? ('Downloading '+Math.floor(got*100/total)+'%')
                       : ('Downloading '+(got/1048576).toFixed(1)+'MB')); }
      blob = new Blob(chunks);
    } else { blob = await r.blob(); }
    const url = URL.createObjectURL(blob);
    const a=document.createElement('a'); a.href=url; a.download=fn; a.style.display='none';
    document.body.appendChild(a); a.click();
    setLabel('Downloaded'); msg('Downloaded '+fn, true);
    setTimeout(function(){ URL.revokeObjectURL(url); a.remove(); }, 2000);
  }catch(e){ msg('Download error: '+e, false); }
  finally{ if(el){ el.dataset.busy='0'; el.style.pointerEvents=''; el.style.opacity=''; const html=orig; setTimeout(function(){ el.innerHTML = html; }, 1200); } }
}
async function del(id){
  if(!confirm('Delete this document?')) return;
  const r = await api('/api/documents/'+id, {method:'DELETE'});
  if(r.status===204){ msg('Deleted.', true); loadDocs(); } else { msg('Delete failed: '+r.status, false); }
}
async function loadTokens(){
  const r = await api('/api/tokens'); const d = await r.json();
  const tb=$('toks'); tb.innerHTML='';
  (d||[]).forEach(t=>{ const tr=document.createElement('tr');
    tr.innerHTML='<td>'+esc(t.name)+'</td><td><code>'+esc(t.token_id)+'</code></td>'+
      '<td>'+(t.created_at||'').slice(0,19).replace('T',' ')+'</td>'+
      '<td>'+(t.is_admin?'yes':'no')+'</td>'+
      '<td><a class="btn-sm btn-del" onclick="delToken('+t.id+')">'+IC_DEL+'Delete</a></td>';
    tb.appendChild(tr); });
}
async function createToken(){
  const name=$('tokname').value.trim(); if(!name){ msg('Enter a token name.', false); return; }
  const r=await api('/api/tokens',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name, is_admin: $('tokadmin').checked})});
  if(r.status===201){ const t=await r.json(); const full=t.token_id+':'+t.secret;
    const box=$('newtok'); box.style.display='block';
    box.innerHTML='<strong>New token &mdash; copy now, the secret is shown only once:</strong><br><code style="user-select:all;font-size:13px">'+esc(full)+'</code>';
    $('tokname').value=''; loadTokens(); msg('Token created.', true);
  } else { const e=await r.text(); msg('Create failed: '+r.status+' '+e, false); }
}
async function delToken(id){
  if(!confirm('Delete this token? Apps/connectors using it will lose access.')) return;
  const r=await api('/api/tokens/'+id,{method:'DELETE'});
  if(r.status===204){ msg('Token deleted.', true); loadTokens(); }
  else { const e=await r.text(); msg('Delete failed: '+r.status+' '+e, false); }
}
function showView(v){
  ['card-settings','card-upload','card-docs','card-tokens','card-links'].forEach(id=>{ const e=$(id); if(e) e.style.display='none'; });
  const show=(id)=>{ const e=$(id); if(e) e.style.display=''; };
  if(v==='docs'){ show('card-upload'); show('card-docs'); }
  else if(v==='tokens'){ show('card-tokens'); }
  else if(v==='settings'){ show('card-settings'); }
  else if(v==='links'){ show('card-links'); }
  if($('modal')) $('modal').style.display='none';
  document.querySelectorAll('.navlink').forEach(a=>a.classList.remove('active'));
  const na=$('nav-'+v); if(na) na.classList.add('active');
  if(v==='docs') loadDocs();
  if(v==='tokens') loadTokens();
}
async function init(){
  if(!tok()){ msg('Enter and save an API token to begin (default demo token is pre-filled).', false); return; }
  try{ await loadBooks(); showView('docs'); msg('Ready.', true); }catch(e){}
}
document.addEventListener('keydown', e=>{ if(e.key==='Escape' && $('modal')) $('modal').style.display='none'; });
$('token').value = tok() || 'kb_demo_token_id:kb_demo_token_secret';
if(!tok()) localStorage.setItem('kb_token', $('token').value);
init();
</script>
</body>
</html>
"""


@router.get("/ui", response_class=HTMLResponse)
async def ui(_: str = Depends(require_ui_auth)) -> str:
    return _PAGE


_MANUAL_TEMPLATE = """<!doctype html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Connect to SurfWise - Admin Guide</title>
<style>
 body{margin:0;font:15px/1.6 system-ui,Segoe UI,Roboto,sans-serif;color:#1f2937;background:#f8fafc}
 .wrap{max-width:820px;margin:0 auto;padding:24px 18px}
 .bar{background:#0f172a;color:#fff;padding:12px 18px}
 .bar a{color:#93c5fd;text-decoration:none}
 h1{font-size:24px}h2{margin-top:1.6em;border-bottom:1px solid #e5e7eb;padding-bottom:4px}
 code{background:#f1f5f9;padding:1px 5px;border-radius:4px}
 pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;overflow:auto}
 pre code{background:none;color:inherit;padding:0}
 table{border-collapse:collapse;width:100%}th,td{border:1px solid #e5e7eb;padding:8px;text-align:left}
 th{background:#f1f5f9}
</style></head><body>
<div class="bar"><a href="/ui">&larr; Back to Knowledge Base</a></div>
<div class="wrap">__BODY__</div></body></html>"""


@router.get("/manual", response_class=HTMLResponse)
async def manual() -> str:
    return _MANUAL_TEMPLATE.replace("__BODY__", render_html(MANUAL_MD))
