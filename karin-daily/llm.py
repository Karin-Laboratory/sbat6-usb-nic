"""OpenAI-compatible karin-ai client; every call has a deterministic fallback."""
import json
import re
import time
from urllib.request import Request, urlopen

def model_name(cfg):
    if cfg.get("ai_model"):
        return cfg["ai_model"]
    try:
        with urlopen(cfg["ai_models_url"], timeout=5) as response:
            data = json.loads(response.read())
        return data.get("data", [{}])[0].get("id", "Qwen3-1.7B-Q4_K_M")
    except Exception:
        return "Qwen3-1.7B-Q4_K_M"

def summarize(cluster, cfg):
    fallback = {"category": cluster.get("category", "general"), "summary": cluster["title"][:80], "importance_score": 50, "experience_score": 20, "specificity_score": 30, "practical_score": 30, "noise_score": 10, "karin_score": 50}
    prompt = """/no_think\n日本語のニュース編集者です。JSONオブジェクトだけを返してください。\ncategoryは today/dig/general/disaster/energy のいずれか、summaryは80字以内。各scoreは0-100整数。複数の独立ソースがある話題は一定程度評価しますが、転載だけなら加点しません。\nキー: category, summary, importance_score, experience_score, specificity_score, practical_score, noise_score, karin_score\nタイトル: {title}\nソース数: {source_count}\n本文: {body}""".format(title=cluster["title"], source_count=cluster.get("source_count", 1), body=cluster.get("body", "")[:5000])
    payload = {"model": model_name(cfg), "temperature": 0.1, "max_tokens": 220, "messages": [{"role": "system", "content": "JSONだけ返してください。"}, {"role": "user", "content": prompt}]}
    try:
        started = time.monotonic()
        req = Request(cfg["ai_url"], data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=45) as response:
            raw = json.loads(response.read())
        text = re.sub(r"<think>[\s\S]*?</think>", "", raw["choices"][0]["message"]["content"]).strip()
        text = text[text.find("{"):text.rfind("}") + 1]
        data = json.loads(text)
        for key in ("importance_score", "experience_score", "specificity_score", "practical_score", "noise_score", "karin_score"):
            data[key] = max(0, min(100, int(data.get(key, fallback[key]))))
        return {**fallback, **data}, time.monotonic() - started, True
    except Exception:
        return fallback, 0.0, False
