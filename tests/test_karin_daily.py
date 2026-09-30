import importlib.util
import sqlite3
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "karin-daily" / "karin_daily.py"
spec = importlib.util.spec_from_file_location("karin_daily", MODULE_PATH)
karin_daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(karin_daily)


class KarinDailyDisplayTests(unittest.TestCase):
    def test_formats_utc_as_jst(self):
        self.assertEqual(
            karin_daily.format_display_time("2026-09-30T00:00:36+00:00"),
            "2026-09-30 09:00 JST",
        )

    def test_render_labels_update_as_jst(self):
        db_path = Path("/tmp/karin-daily-display-test.sqlite3")
        try:
            db = sqlite3.connect(db_path)
            db.execute("CREATE TABLE articles (id INTEGER PRIMARY KEY, url TEXT, title TEXT, source TEXT, published_at TEXT, fetched_at TEXT, excerpt TEXT, category TEXT, summary TEXT, importance_score INTEGER, experience_score INTEGER, specificity_score INTEGER, practical_score INTEGER, noise_score INTEGER, karin_score INTEGER, selected INTEGER)")
            db.execute("CREATE TABLE runs (id INTEGER PRIMARY KEY, started_at TEXT, finished_at TEXT, fetched_count INTEGER, classified_count INTEGER, ai_calls INTEGER, ai_seconds REAL, errors TEXT)")
            db.execute("INSERT INTO runs(finished_at, fetched_count) VALUES (?, ?)", ("2026-09-30T00:00:36+00:00", 31))
            db.commit()
            db.close()
            rendered = karin_daily.render({"database": str(db_path)})
            self.assertIn("更新 2026-09-30 09:00 JST", rendered)
            self.assertNotIn("更新 2026-09-30 00:00", rendered)
        finally:
            db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
