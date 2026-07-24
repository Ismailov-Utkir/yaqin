# -*- coding: utf-8 -*-
# yaqin — admin panel (lokal). Mashinalar + reklama boshqaruvi, GitHub'ga e'lon qilish.
import os, json, base64, subprocess, time, webbrowser, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = os.path.dirname(os.path.abspath(__file__))
CARS = os.path.join(REPO, "cars.json")
ADS = os.path.join(REPO, "ads.json")
CAR_IMG = os.path.join(REPO, "cars", "img")
AD_IMG = os.path.join(REPO, "ads", "img")
PORT = 8765
PASSWORD = os.environ.get("YAQIN_ADMIN_PASSWORD", "test1234")   # serverda: YAQIN_ADMIN_PASSWORD env orqali o'rnating
LIVE_URL = "https://ismailov-utkir.github.io/yaqin/"

os.makedirs(CAR_IMG, exist_ok=True)
os.makedirs(AD_IMG, exist_ok=True)

def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, list) else []
    except Exception:
        return []

def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True)

def save_images(items, folder, prefix):
    for i, c in enumerate(items):
        data = c.pop("_img", None)
        if data and "," in data:
            head, b64 = data.split(",", 1)
            ext = "png" if "png" in head else ("webp" if "webp" in head else "jpg")
            fn = "%s_%d_%d.%s" % (prefix, int(time.time()), i, ext)
            with open(os.path.join(folder, fn), "wb") as f:
                f.write(base64.b64decode(b64))
            rel = os.path.relpath(os.path.join(folder, fn), REPO).replace("\\", "/")
            c["img"] = rel

def publish(cars, ads):
    save_images(cars, CAR_IMG, "car")
    save_images(ads, AD_IMG, "ad")
    with open(CARS, "w", encoding="utf-8") as f:
        json.dump(cars, f, ensure_ascii=False, indent=1)
    with open(ADS, "w", encoding="utf-8") as f:
        json.dump(ads, f, ensure_ascii=False, indent=1)
    git("add", "-A")
    r = git("commit", "-m", "Mashinalar/reklama yangilandi")
    p = git("push")
    ok = (p.returncode == 0) or ("up to date" in (p.stdout + p.stderr).lower())
    return ok, (r.stdout + r.stderr + "\n" + p.stdout + p.stderr)[-600:]

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if isinstance(body, str): body = body.encode("utf-8")
        self.wfile.write(body)
    def do_GET(self):
        if self.path.startswith("/api/cars"):
            self._send(200, "application/json; charset=utf-8", json.dumps(read_json(CARS), ensure_ascii=False))
        elif self.path.startswith("/api/ads"):
            self._send(200, "application/json; charset=utf-8", json.dumps(read_json(ADS), ensure_ascii=False))
        else:
            self._send(200, "text/html; charset=utf-8", PAGE)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try: data = json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception: data = {}
        if data.get("password") != PASSWORD:
            self._send(403, "application/json", json.dumps({"ok": False, "err": "Parol xato"})); return
        if self.path == "/api/login":
            self._send(200, "application/json", json.dumps({"ok": True})); return
        if self.path == "/api/save":
            try:
                ok, log = publish(data.get("cars", []), data.get("ads", []))
                self._send(200, "application/json; charset=utf-8", json.dumps({"ok": ok, "log": log, "url": LIVE_URL}, ensure_ascii=False))
            except Exception as e:
                self._send(200, "application/json; charset=utf-8", json.dumps({"ok": False, "err": str(e)}, ensure_ascii=False))
            return
        self._send(404, "application/json", "{}")

PAGE = r"""<!doctype html><html lang="uz"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>yaqin — Admin panel</title>
<style>
:root{--b:#2563EB;--bg:#0f1830;--card:#182444;--line:#28345a;--ink:#eaf0fb;--mut:#93a2c4}
*{box-sizing:border-box;margin:0;padding:0;font-family:"Segoe UI",system-ui,Arial,sans-serif}
body{background:var(--bg);color:var(--ink);min-height:100vh}
.wrap{max-width:820px;margin:0 auto;padding:22px 16px 90px}
h1{font-size:22px;margin-bottom:2px} .tag{color:var(--mut);font-size:13px;margin-bottom:22px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:16px}
.sect{font-weight:800;margin-bottom:6px;font-size:15px}
label{display:block;font-size:12px;color:var(--mut);margin:10px 0 5px;font-weight:600}
input,textarea,select{width:100%;background:#0e1730;border:1px solid var(--line);border-radius:10px;padding:11px 13px;color:var(--ink);font-size:14px}
textarea{min-height:70px;resize:vertical} .row{display:flex;gap:12px;flex-wrap:wrap} .row>div{flex:1;min-width:130px}
button{cursor:pointer;border:0;border-radius:10px;font-weight:700;font-size:14px;padding:11px 18px}
.pri{background:var(--b);color:#fff} .pri:hover{filter:brightness(1.08)}
.ghost{background:transparent;border:1px solid var(--line);color:var(--ink)}
.del{background:#3a1620;color:#ff8a9c;border:1px solid #5a2230}
.hidden{display:none} .save{position:sticky;bottom:0;padding:14px 0;background:linear-gradient(transparent,var(--bg) 40%)}
.save button{width:100%;padding:15px;font-size:15px}
.item{display:flex;gap:12px;align-items:center;border:1px solid var(--line);border-radius:12px;padding:10px;margin-top:10px;background:#0e1730}
.item img{width:64px;height:48px;object-fit:cover;border-radius:8px;background:#1b2748}
.item .ph{width:64px;height:48px;display:grid;place-items:center;border-radius:8px;background:#1b2748;font-size:22px}
.item .info{flex:1;min-width:0} .item .nm{font-weight:700} .item .pr{color:#6ea8ff;font-size:13px}
.item .sm{color:var(--mut);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.status{padding:12px;border-radius:10px;margin-top:12px;font-size:13px;display:none}
.ok{background:#12301f;color:#7ee6a8;display:block} .bad{background:#331620;color:#ff96a6;display:block}
.pv{width:100%;max-height:170px;object-fit:contain;border-radius:10px;margin-top:8px;display:none;background:#0e1730}
.hint{color:var(--mut);font-size:12px;margin-top:6px}
.tabs{display:flex;gap:8px;margin-bottom:14px}
.tabs button{flex:1;background:#0e1730;border:1px solid var(--line);color:var(--mut)}
.tabs button.on{background:var(--b);color:#fff;border-color:var(--b)}
.stat-box{background:#0e1730;border:1px solid var(--line);border-radius:12px;padding:14px 18px;min-width:110px;flex:1}
.stat-box .sv{font-size:24px;font-weight:800;color:#6ea8ff;font-variant-numeric:tabular-nums}
.stat-box .sl{font-size:12px;color:var(--mut);margin-top:2px}
.chart{display:flex;align-items:flex-end;gap:8px;height:210px;padding-top:26px;overflow-x:auto}
.bar-col{flex:1;min-width:36px;display:flex;flex-direction:column;align-items:center;gap:6px;height:100%}
.bar-wrap{flex:1;width:100%;display:flex;align-items:flex-end}
.bar{width:100%;background:linear-gradient(180deg,#3f8cff,#2563EB);border-radius:6px 6px 0 0;position:relative;min-height:3px}
.bar.best{background:linear-gradient(180deg,#38d39f,#12a366)}
.bar .bv{position:absolute;top:-20px;left:0;right:0;text-align:center;font-size:11px;font-weight:700;color:var(--ink)}
.bar-lbl{font-size:10px;color:var(--mut);text-align:center;line-height:1.2}
</style></head><body><div class="wrap">
<h1>yaqin — Admin panel 🚗</h1><div class="tag">Mashinalar va reklamani boshqarish</div>

<div id="login" class="card">
  <label>Parol</label>
  <input id="pw" type="password" placeholder="Admin parol" onkeydown="if(event.key==='Enter')login()">
  <div style="margin-top:14px"><button class="pri" onclick="login()">Kirish</button></div>
  <div id="lerr" class="status"></div>
</div>

<div id="app" class="hidden">
  <div class="tabs">
    <button class="on" id="tabCars" onclick="tab('cars')">🚗 Mashinalar</button>
    <button id="tabAds" onclick="tab('ads')">📢 Reklama</button>
    <button id="tabStats" onclick="tab('stats')">📊 Statistika</button>
  </div>

  <!-- ===== CARS ===== -->
  <div id="paneCars">
    <div class="card">
      <div class="sect" id="carFormTitle">➕ Yangi mashina qo'shish</div>
      <div class="row">
        <div><label>Model / nomi</label><input id="f_name" placeholder="Masalan: Chevrolet Cobalt"></div>
        <div><label>Yili</label><input id="f_year" inputmode="numeric" placeholder="2021"></div>
      </div>
      <div class="row">
        <div style="flex:2"><label>Narxi</label><input id="f_price" inputmode="numeric" placeholder="150000000"></div>
        <div style="flex:1"><label>Valyuta</label><select id="f_cur"><option value="sum">so'm</option><option value="usd">$ dollar</option></select></div>
        <div style="flex:2"><label>Telefon</label><input id="f_phone" placeholder="+998 90 123 45 67"></div>
      </div>
      <label>Tavsif</label><textarea id="f_desc" placeholder="Holati, rangi, probeg, qo'shimcha ma'lumot..."></textarea>
      <label>Rasm</label><input id="f_img" type="file" accept="image/*" onchange="prev(this,'pv')">
      <img id="pv" class="pv"><div class="hint">Rasm ixtiyoriy. Bir nechta mashina bo'lsa, bittalab qo'shing.</div>
      <div style="margin-top:14px;display:flex;gap:10px">
        <button class="pri" onclick="addCar()" id="carAddBtn">Ro'yxatga qo'shish</button>
        <button class="ghost hidden" onclick="cancelCar()" id="carCancelBtn">Bekor qilish</button>
      </div>
    </div>
    <div class="card">
      <div class="sect">📋 Mashinalar (<span id="cnt">0</span>)</div>
      <div id="list"></div>
    </div>
  </div>

  <!-- ===== ADS ===== -->
  <div id="paneAds" class="hidden">
    <div class="card">
      <div class="sect" id="adFormTitle">➕ Yangi reklama qo'shish</div>
      <label>Sarlavha (ixtiyoriy)</label><input id="a_title" placeholder="Masalan: Yangi shina do'koni">
      <label>Havola / link (ixtiyoriy)</label><input id="a_link" placeholder="https://... yoki tel:+998...">
      <label>Reklama rasmi (banner)</label><input id="a_img" type="file" accept="image/*" onchange="prev(this,'apv')">
      <img id="apv" class="pv"><div class="hint">Eng yaxshisi keng (banner) rasm. Bosilganda havolaga o'tadi.</div>
      <div style="margin-top:14px;display:flex;gap:10px">
        <button class="pri" onclick="addAd()" id="adAddBtn">Ro'yxatga qo'shish</button>
        <button class="ghost hidden" onclick="cancelAd()" id="adCancelBtn">Bekor qilish</button>
      </div>
    </div>
    <div class="card">
      <div class="sect">📢 Reklamalar (<span id="acnt">0</span>)</div>
      <div id="alist"></div>
    </div>
  </div>

  <!-- ===== STATS ===== -->
  <div id="paneStats" class="hidden">
    <div class="card">
      <div class="sect">👥 Foydalanuvchilar statistikasi</div>
      <div class="hint" style="margin-bottom:14px">Saytga tashrif buyurgan odamlar soni. Oylar bo'yicha — qaysi oy faolroq bo'lganini ko'rsatadi.</div>
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px">
        <div class="stat-box"><div class="sv" id="stTotal">—</div><div class="sl">Jami (12 oy)</div></div>
        <div class="stat-box"><div class="sv" id="stMonth">—</div><div class="sl">Shu oy</div></div>
        <div class="stat-box"><div class="sv" id="stBest">—</div><div class="sl">Eng faol oy</div></div>
      </div>
      <div class="chart" id="chart"><div class="hint">Yuklanmoqda...</div></div>
    </div>
  </div>

  <div class="save"><button class="pri" onclick="saveAll()" id="saveBtn">💾 Saqlash va e'lon qilish</button></div>
  <div id="status" class="status"></div>
</div>
</div>
<script>
let PW="", cars=[], ads=[], carEdit=-1, adEdit=-1, imgCar=null, imgAd=null;
function tab(w){['Cars','Ads','Stats'].forEach(x=>{document.getElementById('pane'+x).classList.toggle('hidden',x.toLowerCase()!==w);document.getElementById('tab'+x).classList.toggle('on',x.toLowerCase()===w);});
  if(w==='stats')loadStats();}
const OYNOM=['Yan','Fev','Mar','Apr','May','Iyun','Iyul','Avg','Sen','Okt','Noy','Dek'];
async function loadStats(){
  const chart=document.getElementById('chart');chart.innerHTML='<div class="hint">Yuklanmoqda...</div>';
  const now=new Date(),months=[];
  for(let i=11;i>=0;i--){months.push(new Date(now.getFullYear(),now.getMonth()-i,1));}
  const data=await Promise.all(months.map(d=>{
    const key='oy'+d.getFullYear()+String(d.getMonth()+1).padStart(2,'0');
    return fetch('https://api.counterapi.dev/v1/yaqin_ismailov/'+key+'/').then(r=>r.ok?r.json():null).then(j=>({d:d,c:j?Number(j.count):0})).catch(()=>({d:d,c:0}));
  }));
  const max=Math.max(1,...data.map(x=>x.c)),total=data.reduce((s,x)=>s+x.c,0),best=data.reduce((a,b)=>b.c>a.c?b:a,data[0]),thisM=data[data.length-1].c;
  document.getElementById('stTotal').textContent=total.toLocaleString('ru-RU');
  document.getElementById('stMonth').textContent=thisM.toLocaleString('ru-RU');
  document.getElementById('stBest').textContent=best.c>0?(OYNOM[best.d.getMonth()]+" '"+(''+best.d.getFullYear()).slice(2)):'—';
  chart.innerHTML=data.map(x=>{const h=Math.round(x.c/max*100),bb=(x.c===best.c&&x.c>0);
    return '<div class="bar-col"><div class="bar-wrap"><div class="bar '+(bb?'best':'')+'" style="height:'+h+'%"><span class="bv">'+(x.c||'')+'</span></div></div><div class="bar-lbl">'+OYNOM[x.d.getMonth()]+'<br>'+(''+x.d.getFullYear()).slice(2)+'</div></div>';}).join('');
}
function prev(inp,pid){const f=inp.files[0];const pv=document.getElementById(pid);
  if(!f){pv.style.display='none';if(pid==='pv')imgCar=null;else imgAd=null;return;}
  const r=new FileReader();r.onload=e=>{pv.src=e.target.result;pv.style.display='block';if(pid==='pv')imgCar=e.target.result;else imgAd=e.target.result;};r.readAsDataURL(f);}
async function login(){PW=document.getElementById('pw').value;
  const r=await fetch('/api/login',{method:'POST',body:JSON.stringify({password:PW})});const d=await r.json();
  const e=document.getElementById('lerr');
  if(d.ok){document.getElementById('login').classList.add('hidden');document.getElementById('app').classList.remove('hidden');loadAll();}
  else{e.className='status bad';e.textContent='Parol xato';}}
async function loadAll(){cars=await (await fetch('/api/cars')).json();ads=await (await fetch('/api/ads')).json();render();renderAds();}

/* ---- cars ---- */
function money(c){if(!c.price)return '';const n=Number((''+c.price).replace(/\D/g,'')).toLocaleString('ru-RU');return c.currency==='usd'?('$ '+n):(n+" so'm");}
function render(){const L=document.getElementById('list');document.getElementById('cnt').textContent=cars.length;
  L.innerHTML=cars.map((c,i)=>{const im=c.img?`<img src="../${c.img}?_=${Date.now()}">`:(c._img?`<img src="${c._img}">`:`<div class="ph">🚗</div>`);
   return `<div class="item">${im}<div class="info"><div class="nm">${esc(c.name||'')}</div>
   <div class="pr">${money(c)} ${c.year?'· '+esc(''+c.year):''}</div>
   <div class="sm">${esc((c.desc||'').slice(0,60))}</div></div>
   <button class="ghost" onclick="editCar(${i})">✏️</button><button class="del" onclick="delCar(${i})">🗑</button></div>`;}).join('')
   || '<div class="sm" style="padding:14px 0">Hozircha mashina yo\'q.</div>';}
function addCar(){const c={name:v('f_name'),year:v('f_year'),price:(v('f_price')||'').replace(/\D/g,''),currency:document.getElementById('f_cur').value,phone:v('f_phone'),desc:v('f_desc')};
  if(!c.name){alert('Model/nomini kiriting');return;}
  if(imgCar)c._img=imgCar;
  if(carEdit>=0){const old=cars[carEdit];if(!c._img&&old.img)c.img=old.img;cars[carEdit]=c;carEdit=-1;}else cars.push(c);
  clearCar();render();}
function editCar(i){carEdit=i;const c=cars[i];set('f_name',c.name);set('f_year',c.year);set('f_price',c.price);set('f_phone',c.phone);set('f_desc',c.desc);
  document.getElementById('f_cur').value=c.currency==='usd'?'usd':'sum';imgCar=null;
  const pv=document.getElementById('pv');if(c.img){pv.src='../'+c.img;pv.style.display='block';}else if(c._img){pv.src=c._img;pv.style.display='block';}else pv.style.display='none';
  document.getElementById('carFormTitle').textContent='✏️ Mashinani tahrirlash';document.getElementById('carAddBtn').textContent='Saqlash';document.getElementById('carCancelBtn').classList.remove('hidden');window.scrollTo(0,0);}
function cancelCar(){carEdit=-1;clearCar();}
function delCar(i){if(confirm('Mashinani o\'chirasizmi?')){cars.splice(i,1);render();}}
function clearCar(){['f_name','f_year','f_price','f_phone','f_desc'].forEach(id=>document.getElementById(id).value='');document.getElementById('f_cur').value='sum';
  document.getElementById('f_img').value='';imgCar=null;document.getElementById('pv').style.display='none';
  document.getElementById('carFormTitle').textContent="➕ Yangi mashina qo'shish";document.getElementById('carAddBtn').textContent="Ro'yxatga qo'shish";document.getElementById('carCancelBtn').classList.add('hidden');}

/* ---- ads ---- */
function renderAds(){const L=document.getElementById('alist');document.getElementById('acnt').textContent=ads.length;
  L.innerHTML=ads.map((a,i)=>{const im=a.img?`<img src="../${a.img}?_=${Date.now()}">`:(a._img?`<img src="${a._img}">`:`<div class="ph">📢</div>`);
   return `<div class="item">${im}<div class="info"><div class="nm">${esc(a.title||'(sarlavhasiz)')}</div>
   <div class="sm">${esc(a.link||'havolasiz')}</div></div>
   <button class="ghost" onclick="editAd(${i})">✏️</button><button class="del" onclick="delAd(${i})">🗑</button></div>`;}).join('')
   || '<div class="sm" style="padding:14px 0">Hozircha reklama yo\'q.</div>';}
function addAd(){const a={title:v('a_title'),link:v('a_link')};
  if(!imgAd && adEdit<0){alert('Reklama rasmini tanlang');return;}
  if(imgAd)a._img=imgAd;
  if(adEdit>=0){const old=ads[adEdit];if(!a._img&&old.img)a.img=old.img;ads[adEdit]=a;adEdit=-1;}else ads.push(a);
  clearAd();renderAds();}
function editAd(i){adEdit=i;const a=ads[i];set('a_title',a.title);set('a_link',a.link);imgAd=null;
  const pv=document.getElementById('apv');if(a.img){pv.src='../'+a.img;pv.style.display='block';}else if(a._img){pv.src=a._img;pv.style.display='block';}else pv.style.display='none';
  document.getElementById('adFormTitle').textContent='✏️ Reklamani tahrirlash';document.getElementById('adAddBtn').textContent='Saqlash';document.getElementById('adCancelBtn').classList.remove('hidden');window.scrollTo(0,0);}
function cancelAd(){adEdit=-1;clearAd();}
function delAd(i){if(confirm('Reklamani o\'chirasizmi?')){ads.splice(i,1);renderAds();}}
function clearAd(){['a_title','a_link'].forEach(id=>document.getElementById(id).value='');document.getElementById('a_img').value='';imgAd=null;document.getElementById('apv').style.display='none';
  document.getElementById('adFormTitle').textContent="➕ Yangi reklama qo'shish";document.getElementById('adAddBtn').textContent="Ro'yxatga qo'shish";document.getElementById('adCancelBtn').classList.add('hidden');}

async function saveAll(){const b=document.getElementById('saveBtn');b.disabled=true;b.textContent='⏳ E\'lon qilinmoqda...';
  const s=document.getElementById('status');
  try{const r=await fetch('/api/save',{method:'POST',body:JSON.stringify({password:PW,cars:cars,ads:ads})});const d=await r.json();
   if(d.ok){s.className='status ok';s.innerHTML='✅ E\'lon qilindi! ~1 daqiqada saytda ko\'rinadi.<br><a href="'+d.url+'" target="_blank" style="color:#7ee6a8">'+d.url+'</a>';loadAll();}
   else{s.className='status bad';s.textContent='Xato: '+(d.err||d.log||'noma\'lum');}}
  catch(e){s.className='status bad';s.textContent='Xato: '+e;}
  b.disabled=false;b.textContent='💾 Saqlash va e\'lon qilish';}
function v(id){return document.getElementById(id).value.trim();}
function set(id,val){document.getElementById(id).value=val==null?'':val;}
function esc(s){return (s||'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
</script></body></html>"""

if __name__ == "__main__":
    print("yaqin admin panel: http://localhost:%d" % PORT)
    threading.Timer(1.0, lambda: webbrowser.open("http://localhost:%d" % PORT)).start()
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
