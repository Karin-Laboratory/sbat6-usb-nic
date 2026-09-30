"""RSS/Atom adapters and conservative article text extraction."""
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from similarity import normalize_url

UA = "KarinDaily/0.2 (+https://daily.karin-lab.com/)"

def clean(value):
    value = html.unescape(value or "")
    value = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def parse_date(value):
    try:
        dt = parsedate_to_datetime(value)
    except Exception:
        try:
            dt = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).isoformat()

def fetch(url, timeout=15):
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/atom+xml, text/xml, text/html"})
    return urlopen(req, timeout=timeout).read()

def fetch_feed(source, url, limit=12):
    root = ET.fromstring(fetch(url))
    out = []
    entries = root.findall(".//item") + root.findall(".//{http://www.w3.org/2005/Atom}entry")
    for item in entries[:limit]:
        def val(names):
            for name in names:
                node = item.find(name)
                if node is not None:
                    value = node.text or node.attrib.get("href", "")
                    if value:
                        return value
            return ""
        link = val(["link", "guid", "{http://www.w3.org/2005/Atom}link"])
        if not link:
            node = item.find("{http://www.w3.org/2005/Atom}link")
            link = node.attrib.get("href", "") if node is not None else ""
        title = clean(val(["title", "{http://www.w3.org/2005/Atom}title"]))
        excerpt = clean(val(["description", "summary", "content", "{http://www.w3.org/2005/Atom}summary", "{http://www.w3.org/2005/Atom}content"]))[:3000]
        published = val(["pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"])
        if title and link.startswith("http"):
            out.append({"title": title, "url": link, "normalized_url": normalize_url(link), "source": source, "excerpt": excerpt, "published_at": parse_date(published)})
    return out

def fetch_article(url, timeout=10):
    try:
        text = fetch(url, timeout).decode("utf-8", "replace")[:200000]
        for pattern in (r"<article[^>]*>([\s\S]*?)</article>", r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)'):
            match = re.search(pattern, text, re.I)
            if match:
                content = clean(match.group(1))
                if len(content) >= 80:
                    return content[:8000]
        return clean(text)[:8000]
    except Exception:
        return ""
