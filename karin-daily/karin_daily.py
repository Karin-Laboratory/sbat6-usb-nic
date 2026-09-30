#!/usr/bin/env python3
"""Karin Daily: small RSS -> AI -> SQLite -> HTML news portal."""
import argparse, html, json, os, re, sqlite3, time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
DEFAULT = ROOT / "config.json"
JST = ZoneInfo("Asia/Tokyo")
PROMPT = '''/no_think
あなたは個人用ニュース編集者です。入力記事を日本語で短く分類してください。
JSONオブジェクトを1つだけ返し、Markdownや説明は不要です。categoryは「today」「dig」「general」「disaster」「energy」のいずれか。
summaryは40字以内。各スコアは0-100整数。具体的な実測、型番、金額、手順、失敗談、一次体験を高く評価し、SEO薄まとめ・広告誘導・煽り・人格攻撃を低く評価します。
興味: 科学、技術、経済、コンピュータ、Linux、Proxmox、AI/LLM、ネットワーク、電子工作、中古PC、修理、再利用、エネルギー、防災。
必須キー: category, summary, importance_score, experience_score, specificity_score, practical_score, noise_score, karin_score
記事:
タイトル: {title}
媒体: {source}
本文抜粋: {text}'''

def load_config():
    p = Path(os.getenv("KARIN_DAILY_CONFIG", DEFAULT))
    c = json.loads(p.read_text())
    c["database"] = str((ROOT / c["database"]).resolve()) if not os.path.isabs(c["database"]) else c["database"]
    return c

def db_open(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript('''CREATE TABLE IF NOT EXISTS articles(
      id INTEGER PRIMARY KEY, url TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
      source TEXT, published_at TEXT, fetched_at TEXT NOT NULL, excerpt TEXT,
      category TEXT, summary TEXT, importance_score INTEGER DEFAULT 0,
      experience_score INTEGER DEFAULT 0, specificity_score INTEGER DEFAULT 0,
      practical_score INTEGER DEFAULT 0, noise_score INTEGER DEFAULT 0,
      karin_score INTEGER DEFAULT 0, selected INTEGER DEFAULT 0);
      CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY, started_at TEXT,
      finished_at TEXT, fetched_count INTEGER, classified_count INTEGER,
      ai_calls INTEGER, ai_seconds REAL, errors TEXT);''')
    return db

def clean(s): return re.sub(r'\\s+', ' ', html.unescape(s or '')).strip()
def parse_date(s):
    try: return parsedate_to_datetime(s).astimezone(timezone.utc).isoformat()
    except Exception: return datetime.now(timezone.utc).isoformat()

def format_display_time(value):
    """Format an ISO-8601 timestamp for the Japanese-facing page."""
    if value == '未収集':
        return value
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(JST).strftime('%Y-%m-%d %H:%M JST')
    except (TypeError, ValueError):
        return value

def fetch_feed(source, url):
    req = Request(url, headers={"User-Agent":"KarinDaily/0.1 (+https://karin-news/)"})
    raw = urlopen(req, timeout=15).read()
    root = ET.fromstring(raw)
    out=[]
    for item in root.findall('.//item') + root.findall('.//{http://www.w3.org/2005/Atom}entry'):
        def val(names):
            for n in names:
                x=item.find(n)
                if x is not None and (x.text or x.attrib.get('href')): return x.text or x.attrib.get('href')
            return ''
        title=clean(val(['title','{http://www.w3.org/2005/Atom}title']))
        link=val(['link','{http://www.w3.org/2005/Atom}link'])
        if not link:
            x=item.find('{http://www.w3.org/2005/Atom}link'); link=x.attrib.get('href','') if x is not None else ''
        text=clean(val(['description','summary','content','{http://www.w3.org/2005/Atom}summary','{http://www.w3.org/2005/Atom}content']))[:600]
        date=val(['pubDate','published','updated','{http://www.w3.org/2005/Atom}published','{http://www.w3.org/2005/Atom}updated'])
        if title and link: out.append(dict(title=title, url=link, source=source, excerpt=text[:2000], published_at=parse_date(date)))
    return out

def fallback(a):
    t=(a['title']+' '+a['excerpt']).lower()
    exp=sum(1 for x in ['実測','やってみた','分解','修理','中古','改造','ハック','失敗','手順'] if x in t)
    cat='disaster' if any(x in t for x in ['地震','豪雨','台風','停電','災害']) else 'energy' if any(x in t for x in ['電力','省電力','電気','エネルギー']) else 'dig' if exp else 'general'
    return dict(category=cat,summary=a['title'][:40],importance_score=50,experience_score=min(95,30+exp*12),specificity_score=min(90,30+exp*10),practical_score=min(90,30+exp*10),noise_score=20,karin_score=min(90,50+exp*8))

def classify(a, cfg):
    payload={"model":cfg['ai_model'],"temperature":0.1,"max_tokens":140,"messages":[{"role":"system","content":"JSONだけ返してください。返答は必ず短く。"},{"role":"user","content":PROMPT.format(title=a['title'],source=a['source'],text=a['excerpt'])}]}
    try:
        req=Request(cfg['ai_url'],data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        started=time.monotonic(); raw=json.loads(urlopen(req,timeout=45).read()); elapsed=time.monotonic()-started
        s=raw['choices'][0]['message']['content']; s=re.sub(r'<think>.*?</think>','',s,flags=re.S).strip(); s=s[s.find('{'):s.rfind('}')+1]
        d=json.loads(s); return d, elapsed, True
    except Exception: return fallback(a), 0.0, False

def collect(cfg):
    started=datetime.now(timezone.utc).isoformat(); db=db_open(cfg['database']); fetched=[]; errors=[]
    for source,url in cfg['feeds']:
        try: fetched += fetch_feed(source,url)[:4]
        except Exception as e: errors.append(source+': '+str(e)[:120])
    unique={a['url']:a for a in fetched}; fetched=list(unique.values()); calls=0; sec=0.0
    for idx, a in enumerate(fetched):
        try:
            d,elapsed,called=classify(a,cfg) if idx < 8 else (fallback(a), 0.0, False); calls += int(called); sec += elapsed
            cols=['url','title','source','published_at','fetched_at','excerpt','category','summary','importance_score','experience_score','specificity_score','practical_score','noise_score','karin_score']
            vals=[a['url'],a['title'],a['source'],a['published_at'],datetime.now(timezone.utc).isoformat(),a['excerpt'],d.get('category','general'),d.get('summary',a['title'][:40])]+[int(max(0,min(100,d.get(k,0)))) for k in ['importance_score','experience_score','specificity_score','practical_score','noise_score','karin_score']]
            db.execute('INSERT INTO articles('+','.join(cols)+') VALUES('+','.join('?'*len(cols))+') ON CONFLICT(url) DO UPDATE SET title=excluded.title,excerpt=excluded.excerpt,category=excluded.category,summary=excluded.summary,published_at=excluded.published_at,fetched_at=excluded.fetched_at,importance_score=excluded.importance_score,experience_score=excluded.experience_score,specificity_score=excluded.specificity_score,practical_score=excluded.practical_score,noise_score=excluded.noise_score,karin_score=excluded.karin_score',vals)
        except Exception as e: errors.append('article: '+str(e)[:120])
    db.execute('UPDATE articles SET selected=0');
    for cat,limit in [('today',3),('dig',5),('general',8),('disaster',3),('energy',3)]:
        db.execute('UPDATE articles SET selected=1 WHERE id IN (SELECT id FROM articles WHERE category=? ORDER BY karin_score DESC, importance_score DESC, published_at DESC LIMIT ?)',(cat,limit))
    # Keep the front page useful even when a small local model classifies every
    # item as general: promote the strongest general items into the lead.
    if db.execute("SELECT 1 FROM articles WHERE category='today' LIMIT 1").fetchone() is None:
        db.execute("UPDATE articles SET category='today' WHERE id IN (SELECT id FROM articles WHERE category='general' ORDER BY importance_score DESC, karin_score DESC LIMIT 3)")
        db.execute('UPDATE articles SET selected=1 WHERE category=\'today\'')
    finished=datetime.now(timezone.utc).isoformat(); db.execute('INSERT INTO runs(started_at,finished_at,fetched_count,classified_count,ai_calls,ai_seconds,errors) VALUES(?,?,?,?,?,?,?)',(started,finished,len(fetched),len(fetched),calls,sec,'; '.join(errors))); db.commit(); db.close()
    return len(fetched),calls,sec,errors

LABELS={'today':'今日の3本','dig':'発掘','general':'一般ニュース','disaster':'防災・災害','energy':'エネルギー・節約'}
def render(cfg):
    db=db_open(cfg['database']); rows=db.execute('SELECT * FROM articles WHERE selected=1 ORDER BY CASE category WHEN "today" THEN 0 WHEN "dig" THEN 1 WHEN "general" THEN 2 WHEN "disaster" THEN 3 ELSE 4 END, karin_score DESC').fetchall(); run=db.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 1').fetchone(); db.close()
    groups={k:[] for k in LABELS}
    for r in rows: groups.setdefault(r['category'],[]).append(r)
    sections=[]
    for cat,label in LABELS.items():
        items=''.join(f'<li><a href="{html.escape(r["url"],quote=True)}" target="_blank" rel="noopener">{html.escape(r["title"])}</a><small>{html.escape(r["source"])} · {html.escape(r["summary"] or "")}</small></li>' for r in groups[cat])
        sections.append(f'<section class="{cat}"><h2>{label}</h2><ul>{items or "<li class=empty>該当記事なし</li>"}</ul></section>')
    updated=format_display_time(run['finished_at'] if run else '未収集'); count=run['fetched_count'] if run else 0
    amesh='<aside class="amesh"><strong>東京アメッシュ</strong><span>公式サイトの画像取得・埋め込みは利用条件を確認できないため保留中。</span><a href="https://www.gesui.metro.tokyo.lg.jp/" target="_blank" rel="noopener">東京都下水道局へ</a></aside>'
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Karin Daily</title><style>'+CSS+'</style></head><body><main><header><div><p class="eyebrow">KARIN NEWS / DAILY EDITION</p><h1>Karin Daily</h1><p class="sub">今日を、少し深く。科学・技術・暮らしの観測紙</p></div><div class="meta">更新 '+html.escape(updated)+'<br>収集 '+str(count)+' 件</div></header><div class="grid">'+''.join(sections)+'</div>'+amesh+'<footer>記事本文は各情報源のサイトでご確認ください。個人の位置情報・生活圏情報は掲載していません。</footer></main></body></html>'

CSS='''*{box-sizing:border-box}body{margin:0;background:#f4f1e9;color:#20231f;font-family:system-ui,-apple-system,"Noto Sans JP",sans-serif}main{max-width:1240px;margin:auto;padding:28px 34px}header{display:flex;justify-content:space-between;align-items:end;border-bottom:3px solid #20231f;padding-bottom:15px;margin-bottom:18px}h1{font-family:Georgia,serif;font-size:clamp(38px,5vw,64px);line-height:1;margin:0;letter-spacing:-.05em}.eyebrow{font-size:11px;letter-spacing:.18em;font-weight:700;margin:0 0 6px;color:#bd4e32}.sub{margin:8px 0 0;color:#65665f;font-size:13px}.meta{text-align:right;color:#77766f;font-size:11px;line-height:1.7}.grid{display:grid;grid-template-columns:1.25fr 1.1fr 1fr;grid-template-areas:"today dig general" "today disaster energy";gap:14px}.today{grid-area:today}.dig{grid-area:dig}.general{grid-area:general}.disaster{grid-area:disaster}.energy{grid-area:energy}section{background:#fffdf8;border-top:4px solid #20231f;padding:12px 16px 9px;box-shadow:0 2px 0 #ddd8ca}section.today{background:#20231f;color:#fffdf8;border-color:#bd4e32}.today h2{color:#f3b26d}h2{font-family:Georgia,serif;font-size:20px;margin:0 0 7px;display:flex;justify-content:space-between}h2:after{content:'✦';font-family:system-ui;font-size:13px;color:#bd4e32}ul{list-style:none;padding:0;margin:0}li{border-top:1px solid #e6e1d8;padding:8px 0;line-height:1.35}li:first-child{border-top:0}a{color:inherit;text-decoration:none;font-weight:700;font-size:14px}a:hover{text-decoration:underline}small{display:block;color:#85847d;font-size:10px;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.today small{color:#aaa9a2}.empty{color:#999;font-size:12px}.amesh{display:flex;gap:12px;align-items:baseline;margin-top:14px;padding:10px 14px;background:#e8eee9;border-left:4px solid #47715b;font-size:11px}.amesh span{color:#68736c}.amesh a{font-size:11px;color:#315d49}footer{padding-top:14px;color:#999;font-size:10px}@media(max-width:850px){main{padding:20px 14px}.grid{grid-template-columns:1fr;grid-template-areas:none}.grid section{grid-area:auto}header{align-items:start;gap:12px}.meta{font-size:10px}.amesh{display:block}.amesh>*{display:block;margin-top:3px}}'''

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/','/index.html'):
            b=render(load_config()).encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
        elif self.path=='/healthz': self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
        else: self.send_error(404)
    def log_message(self,*args): pass

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--once',action='store_true'); ap.add_argument('--serve',action='store_true'); ap.add_argument('--host',default='127.0.0.1'); ap.add_argument('--port',type=int); args=ap.parse_args(); cfg=load_config()
    if args.once:
        n,c,s,e=collect(cfg); print(json.dumps({'articles':n,'ai_calls':c,'ai_seconds':round(s,2),'errors':e},ensure_ascii=False))
    if args.serve or not args.once:
        ThreadingHTTPServer((args.host,args.port or cfg['port']),Handler).serve_forever()
