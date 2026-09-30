"""SQLite schema with additive migration from the original Karin Daily DB."""
import sqlite3
from pathlib import Path

def open_db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS articles(
      id INTEGER PRIMARY KEY, url TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
      source TEXT, published_at TEXT, fetched_at TEXT NOT NULL, excerpt TEXT,
      category TEXT, summary TEXT, importance_score INTEGER DEFAULT 0,
      experience_score INTEGER DEFAULT 0, specificity_score INTEGER DEFAULT 0,
      practical_score INTEGER DEFAULT 0, noise_score INTEGER DEFAULT 0,
      karin_score INTEGER DEFAULT 0, selected INTEGER DEFAULT 0,
      normalized_url TEXT, content_hash TEXT, body_text TEXT, language TEXT,
      cluster_id INTEGER, source_count INTEGER DEFAULT 1, source_hosts TEXT,
      representative INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS clusters(
      id INTEGER PRIMARY KEY, representative_article_id INTEGER,
      title TEXT, summary TEXT, category TEXT, karin_score INTEGER DEFAULT 0,
      source_count INTEGER DEFAULT 1, source_hosts TEXT, updated_at TEXT);
    CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY, started_at TEXT,
      finished_at TEXT, fetched_count INTEGER, classified_count INTEGER,
      ai_calls INTEGER, ai_seconds REAL, errors TEXT, cluster_count INTEGER DEFAULT 0);
    """)
    columns = {r[1] for r in db.execute("PRAGMA table_info(articles)")}
    additions = {"normalized_url": "TEXT", "content_hash": "TEXT", "body_text": "TEXT", "language": "TEXT", "cluster_id": "INTEGER", "source_count": "INTEGER DEFAULT 1", "source_hosts": "TEXT", "representative": "INTEGER DEFAULT 1"}
    for name, typ in additions.items():
        if name not in columns:
            db.execute(f"ALTER TABLE articles ADD COLUMN {name} {typ}")
    return db
