import html
import sqlite3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from storage import open_db

JST = ZoneInfo("Asia/Tokyo")
LABELS = {"today": "今日の3本", "dig": "発掘", "general": "一般ニュース", "disaster": "防災・災害", "energy": "エネルギー・節約"}

def format_display_time(value):
    if value == "未収集": return value
    try:
        dt = datetime.fromisoformat(value)
        return dt.astimezone(JST).strftime("%Y-%m-%d %H:%M JST")
    except (TypeError, ValueError):
        return value

def render(cfg):
    db = open_db(cfg["database"])
    rows = db.execute("SELECT c.*, a.url AS representative_url FROM clusters c JOIN articles a ON a.id=c.representative_article_id ORDER BY c.karin_score DESC, c.updated_at DESC").fetchall()
    # A first deployment may still contain the old database before refresh.
    # Render its selected rows instead of showing an empty page; the next
    # successful run replaces them with cluster cards without deleting data.
    if not rows:
        rows = db.execute("SELECT id, url AS representative_url, title, summary, category, karin_score, 1 AS source_count FROM articles WHERE selected=1 ORDER BY karin_score DESC, published_at DESC").fetchall()
    run = db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    db.close()
    groups = {key: [] for key in LABELS}
    for row in rows:
        groups.setdefault(row["category"], []).append(row)
    sections = []
    for category, label in LABELS.items():
        items = []
        for row in groups[category]:
            related = ""
            # Related sources remain visible as provenance, while one cluster is one card.
            items.append(f'<li><a href="{html.escape(row["representative_url"], quote=True)}" target="_blank" rel="noopener">{html.escape(row["title"])}</a><small>{html.escape(row["summary"] or "")} · {int(row["source_count"])} source(s)</small></li>')
        sections.append(f'<section class="{category}"><h2>{label}</h2><ul>{"".join(items) or "<li class=empty>該当記事なし</li>"}</ul></section>')
    updated = format_display_time(run["finished_at"] if run else "未収集")
    count = run["fetched_count"] if run else 0
    amesh = '<aside class="amesh"><strong>東京アメッシュ</strong><span>公式サイトの画像取得・埋め込みは利用条件を確認できないため保留中。</span><a href="https://www.gesui.metro.tokyo.lg.jp/" target="_blank" rel="noopener">東京都下水道局へ</a></aside>'
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Karin Daily</title><style>'+CSS+'</style></head><body><main><header><div><p class="eyebrow">KARIN NEWS / DAILY EDITION</p><h1>Karin Daily</h1><p class="sub">今日を、少し深く。科学・技術・暮らしの観測紙</p></div><div class="meta">更新 '+html.escape(updated)+'<br>収集 '+str(count)+' 件 / '+str(len(rows))+' topics</div></header><div class="grid">'+''.join(sections)+'</div>'+amesh+'<footer>同じ話題は一つにまとめ、関連ソース数を表示しています。記事本文は各情報源のサイトでご確認ください。</footer></main></body></html>'

CSS = '''*{box-sizing:border-box}body{margin:0;background:#f4f1e9;color:#20231f;font-family:system-ui,-apple-system,"Noto Sans JP",sans-serif}main{max-width:1240px;margin:auto;padding:28px 34px}header{display:flex;justify-content:space-between;align-items:end;border-bottom:3px solid #20231f;padding-bottom:15px;margin-bottom:18px}h1{font-family:Georgia,serif;font-size:clamp(38px,5vw,64px);line-height:1;margin:0;letter-spacing:-.05em}.eyebrow{font-size:11px;letter-spacing:.18em;font-weight:700;margin:0 0 6px;color:#bd4e32}.sub{margin:8px 0 0;color:#65665f;font-size:13px}.meta{text-align:right;color:#77766f;font-size:11px;line-height:1.7}.grid{display:grid;grid-template-columns:1.25fr 1.1fr 1fr;gap:14px}section{background:#fffdf8;border-top:4px solid #20231f;padding:12px 16px 9px;box-shadow:0 2px 0 #ddd8ca}section.today{background:#20231f;color:#fffdf8;border-color:#bd4e32}h2{font-family:Georgia,serif;font-size:20px;margin:0 0 7px}ul{list-style:none;padding:0;margin:0}li{border-top:1px solid #e6e1d8;padding:8px 0;line-height:1.35}li:first-child{border-top:0}a{color:inherit;text-decoration:none;font-weight:700;font-size:14px}a:hover{text-decoration:underline}small{display:block;color:#85847d;font-size:10px;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.today small{color:#aaa9a2}.empty{color:#999;font-size:12px}.amesh{display:flex;gap:12px;align-items:baseline;margin-top:14px;padding:10px 14px;background:#e8eee9;border-left:4px solid #47715b;font-size:11px}.amesh span{color:#68736c}.amesh a{font-size:11px;color:#315d49}footer{padding-top:14px;color:#999;font-size:10px}@media(max-width:850px){main{padding:20px 14px}.grid{grid-template-columns:1fr}header{align-items:start;gap:12px}.meta{font-size:10px}.amesh{display:block}}'''
