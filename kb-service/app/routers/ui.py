"""Minimal self-contained web GUI for document management (upload/download/delete)."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

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
</style>
</head>
<body>
<header>
  <h1>Knowledge Base &mdash; Document Management</h1>
  <small>Upload, download and delete documents. Content is indexable by SurfWise via the BookStack-compatible API.</small>
</header>
<main>
  <div class="card">
    <div class="row">
      <div>
        <div><label>API token (id:secret)</label></div>
        <input id="token" type="password" placeholder="tokenid:tokensecret"/>
      </div>
      <button class="sec" onclick="saveToken()">Save token</button>
      <span id="whoami" style="color:var(--muted)"></span>
    </div>
  </div>

  <div class="card">
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

  <div class="card">
    <div class="row" style="justify-content:space-between">
      <strong>Documents</strong>
      <button class="sec" onclick="loadDocs()">Refresh</button>
    </div>
    <table>
      <thead><tr><th>Name</th><th>Book</th><th>Type</th><th>Size</th><th>Updated</th><th>Actions</th></tr></thead>
      <tbody id="docs"></tbody>
    </table>
  </div>

  <div class="card" id="viewcard" style="display:none">
    <div class="row" style="justify-content:space-between">
      <strong id="viewtitle">Preview</strong>
      <button class="sec" onclick="document.getElementById('viewcard').style.display='none'">Close</button>
    </div>
    <div id="viewer"></div>
  </div>
</main>
<script>
const $ = (id) => document.getElementById(id);
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
  const r = await api('/api/books', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})});
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
async function loadDocs(){
  const r = await api('/api/documents'); const d = await r.json();
  const tb = $('docs'); tb.innerHTML='';
  (d.data||[]).forEach(doc=>{
    const tr=document.createElement('tr');
    const type = doc.is_file ? (doc.content_type||'file') : 'markdown';
    tr.innerHTML = '<td>'+esc(doc.name)+'</td><td>'+esc(doc.book_name)+'</td>'+
      '<td><span class="tag">'+esc(type)+'</span></td><td>'+fmtSize(doc.size)+'</td>'+
      '<td>'+(doc.updated_at||'').slice(0,19).replace('T',' ')+'</td>'+
      '<td><a class="dl" onclick="view('+doc.id+')">View</a> &middot; '+
      '<a class="dl" onclick="downloadDoc('+doc.id+', this)">Download</a> &middot; '+
      '<a class="dl" style="color:#dc2626" onclick="del('+doc.id+')">Delete</a></td>';
    tb.appendChild(tr);
  });
}
function esc(s){ return (s==null?'':String(s)).replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
async function view(id){
  const r = await api('/api/pages/'+id); const d = await r.json();
  $('viewtitle').textContent = d.name; $('viewer').innerHTML = d.html || '<em>(no content)</em>';
  $('viewcard').style.display='block'; window.scrollTo(0, document.body.scrollHeight);
}
async function downloadDoc(id, el){
  if(el && el.dataset.busy==='1') return;               // block repeat clicks
  const orig = el ? el.textContent : '';
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
  finally{ if(el){ el.dataset.busy='0'; el.style.pointerEvents=''; el.style.opacity=''; setTimeout(()=>setLabel(orig||'Download'), 1500); } }
}
async function del(id){
  if(!confirm('Delete this document?')) return;
  const r = await api('/api/documents/'+id, {method:'DELETE'});
  if(r.status===204){ msg('Deleted.', true); loadDocs(); } else { msg('Delete failed: '+r.status, false); }
}
async function init(){
  if(!tok()){ msg('Enter and save an API token to begin (default demo token is pre-filled).', false); return; }
  try{ await loadBooks(); await loadDocs(); msg('Ready.', true); }catch(e){}
}
$('token').value = tok() || 'kb_demo_token_id:kb_demo_token_secret';
if(!tok()) localStorage.setItem('kb_token', $('token').value);
init();
</script>
</body>
</html>
"""


@router.get("/ui", response_class=HTMLResponse)
async def ui() -> str:
    return _PAGE
