"""Karin Daily collect -> normalize -> dedup -> cluster -> score -> digest."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from llm import summarize
from similarity import content_fingerprint, host, title_similarity
from sources import fetch_article, fetch_feed
from storage import open_db

ROOT = Path(__file__).resolve().parent

def load_config():
    path = Path(os.getenv("KARIN_DAILY_CONFIG", ROOT / "config.json"))
    cfg = json.loads(path.read_text())
    cfg["database"] = str((ROOT / cfg["database"]).resolve()) if not os.path.isabs(cfg["database"]) else cfg["database"]
    cfg.setdefault("ai_models_url", cfg["ai_url"].rsplit("/chat/completions", 1)[0] + "/models")
    cfg.setdefault("article_fetch", True)
    cfg.setdefault("feed_limit", 12)
    return cfg

def _is_same_story(a, b):
    if a["content_hash"] and a["content_hash"] == b["content_hash"]:
        return True
    similarity = title_similarity(a["title"], b["title"])
    # High threshold avoids merging headlines that merely share a subject.
    return similarity >= 0.84 or (similarity >= 0.70 and len(set(a["title"].split()) & set(b["title"].split())) >= 2)

def cluster_articles(items):
    clusters = []
    for article in sorted(items, key=lambda x: x.get("published_at", ""), reverse=True):
        target = next((c for c in clusters if _is_same_story(article, c["items"][0])), None)
        if target:
            target["items"].append(article)
        else:
            clusters.append({"items": [article]})
    return clusters

def _fallback_score(cluster):
    items = cluster["items"]
    unique_hosts = {host(a["url"]) for a in items}
    score = 40 + min(18, max(0, len(unique_hosts) - 1) * 6)
    score += min(12, len(items) * 2)
    return score

def run_once(cfg):
    started = datetime.now(timezone.utc).isoformat()
    errors, raw = [], []
    for source, url in cfg["feeds"]:
        try:
            raw.extend(fetch_feed(source, url, cfg["feed_limit"]))
        except Exception as exc:
            errors.append(f"{source}: {str(exc)[:120]}")
    unique = {}
    for item in raw:
        unique.setdefault(item["normalized_url"], item)
    items = list(unique.values())
    for item in items:
        try:
            item["body"] = fetch_article(item["url"]) if cfg["article_fetch"] else ""
        except Exception as exc:
            item["body"] = ""
            errors.append(f"article {item['url']}: {str(exc)[:120]}")
        item["content_hash"] = content_fingerprint(item["body"] or item["excerpt"])
    clusters = cluster_articles(items)
    db = open_db(cfg["database"])
    now = datetime.now(timezone.utc).isoformat()
    ai_calls, ai_seconds = 0, 0.0
    db.execute("UPDATE articles SET selected=0, representative=0")
    db.execute("DELETE FROM clusters")
    for cluster in clusters:
        articles = cluster["items"]
        representative = max(articles, key=lambda x: (len(x.get("body", "")), x.get("published_at", "")))
        sources = sorted({a["source"] for a in articles})
        hosts = sorted({host(a["url"]) for a in articles})
        data = {"title": representative["title"], "body": representative.get("body") or representative.get("excerpt", ""), "source_count": len(hosts), "category": "general"}
        scored, elapsed, called = summarize(data, cfg)
        if scored.get("category") not in {"today", "dig", "general", "disaster", "energy"}:
            scored["category"] = "general"
        ai_calls += int(called); ai_seconds += elapsed
        scored["karin_score"] = max(scored["karin_score"], _fallback_score(cluster))
        db.execute("INSERT INTO clusters(representative_article_id,title,summary,category,karin_score,source_count,source_hosts,updated_at) VALUES(?,?,?,?,?,?,?,?)", (None, representative["title"], scored["summary"], scored["category"], scored["karin_score"], len(hosts), json.dumps(hosts), now))
        cluster_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        for article in articles:
            db.execute("INSERT INTO articles(url,title,source,published_at,fetched_at,excerpt,category,summary,importance_score,experience_score,specificity_score,practical_score,noise_score,karin_score,selected,normalized_url,content_hash,body_text,language,cluster_id,source_count,source_hosts,representative) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET title=excluded.title,source=excluded.source,published_at=excluded.published_at,fetched_at=excluded.fetched_at,excerpt=excluded.excerpt,category=excluded.category,summary=excluded.summary,importance_score=excluded.importance_score,experience_score=excluded.experience_score,specificity_score=excluded.specificity_score,practical_score=excluded.practical_score,noise_score=excluded.noise_score,karin_score=excluded.karin_score,normalized_url=excluded.normalized_url,content_hash=excluded.content_hash,body_text=excluded.body_text,cluster_id=excluded.cluster_id,source_count=excluded.source_count,source_hosts=excluded.source_hosts,representative=excluded.representative", (article["url"], article["title"], article["source"], article["published_at"], now, article["excerpt"], scored["category"], scored["summary"], scored["importance_score"], scored["experience_score"], scored["specificity_score"], scored["practical_score"], scored["noise_score"], scored["karin_score"], 1, article["normalized_url"], article["content_hash"], article.get("body", ""), "ja", cluster_id, len(hosts), json.dumps(hosts), int(article is representative)))
        db.execute("UPDATE clusters SET representative_article_id=(SELECT id FROM articles WHERE url=?) WHERE id=?", (representative["url"], cluster_id))
    db.execute("UPDATE articles SET selected=1 WHERE representative=1")
    finished = datetime.now(timezone.utc).isoformat()
    db.execute("INSERT INTO runs(started_at,finished_at,fetched_count,classified_count,ai_calls,ai_seconds,errors,cluster_count) VALUES(?,?,?,?,?,?,?,?)", (started, finished, len(items), len(clusters), ai_calls, ai_seconds, "; ".join(errors), len(clusters)))
    db.commit(); db.close()
    return json.dumps({"articles": len(items), "clusters": len(clusters), "ai_calls": ai_calls, "errors": errors}, ensure_ascii=False)
