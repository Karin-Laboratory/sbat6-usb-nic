import importlib.util
import sys
import unittest
import tempfile
import json
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).parents[1] / "karin-daily"
sys.path.insert(0, str(ROOT))
from similarity import content_fingerprint, normalize_url, title_similarity
from pipeline import cluster_articles, run_once
from llm import summarize


class KarinPipelineTests(unittest.TestCase):
    def test_tracking_url_dedup(self):
        self.assertEqual(normalize_url("https://example.com/a/?utm_source=rss#top"), "https://example.com/a")

    def test_same_title_clusters_and_keeps_sources(self):
        items = [
            {"title": "政府、再生可能エネルギー政策を発表", "url": "https://a.example/1", "source": "A", "published_at": "2026-09-30T00:00:00+00:00", "content_hash": "x"},
            {"title": "政府、再生可能エネルギー政策を発表", "url": "https://b.example/2", "source": "B", "published_at": "2026-09-30T00:01:00+00:00", "content_hash": "x"},
        ]
        self.assertEqual(len(cluster_articles(items)), 1)
        self.assertEqual(len(cluster_articles(items)[0]["items"]), 2)

    def test_different_events_do_not_cluster(self):
        a = {"title": "東京で大雨、交通に影響", "url": "https://a.example/1", "source": "A", "published_at": "2026-09-30", "content_hash": content_fingerprint("東京で大雨")}
        b = {"title": "大阪で大雨、交通に影響", "url": "https://b.example/2", "source": "B", "published_at": "2026-09-30", "content_hash": content_fingerprint("大阪で大雨")}
        self.assertEqual(len(cluster_articles([a, b])), 2)

    def test_title_similarity_handles_english(self):
        self.assertGreaterEqual(title_similarity("OpenAI releases new model", "OpenAI releases a new model"), 0.84)

    def test_ai_failure_still_publishes_clusters(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = {"database": str(Path(tmp) / "daily.sqlite3"), "ai_url": "http://127.0.0.1:1/v1/chat/completions", "ai_models_url": "http://127.0.0.1:1/v1/models", "ai_model": "", "article_fetch": True, "feed_limit": 12, "feeds": [["test", "https://feed.invalid/rss"]]}
            item = {"title": "同じ事件を報じる記事", "url": "https://a.example/1?utm_source=x", "normalized_url": "https://a.example/1", "source": "test", "excerpt": "概要", "published_at": "2026-09-30T00:00:00+00:00"}
            with patch("pipeline.fetch_feed", return_value=[item]), patch("pipeline.fetch_article", side_effect=OSError("article unavailable")):
                result = run_once(cfg)
            self.assertEqual(json.loads(result)["clusters"], 1)
            self.assertEqual(json.loads(result)["ai_calls"], 0)

    def test_malformed_json_uses_llm_fallback(self):
        class BrokenResponse:
            def __enter__(self): return self
            def __exit__(self, *_args): return False
            def read(self): return b'{"choices":[{"message":{"content":"not json"}}]}'
        cluster = {"title": "テスト記事", "category": "general", "source_count": 1, "body": "本文"}
        with patch("llm.urlopen", return_value=BrokenResponse()):
            result, _elapsed, called = summarize(cluster, {"ai_url": "http://ai/v1/chat/completions", "ai_models_url": "http://ai/v1/models", "ai_model": "test"})
        self.assertFalse(called)
        self.assertEqual(result["summary"], "テスト記事")


if __name__ == "__main__":
    unittest.main()
