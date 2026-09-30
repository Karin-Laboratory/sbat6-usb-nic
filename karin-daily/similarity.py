"""Small, dependency-free similarity primitives for news clustering."""
import hashlib
import re
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid", "ref", "ref_src"}
WORD_RE = re.compile(r"[a-z0-9][a-z0-9._+-]*|[\u3040-\u30ff\u3400-\u9fff]")

def normalize_url(url):
    p = urlsplit((url or "").strip())
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in TRACKING]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/", urlencode(query), ""))

def normalize_title(value):
    value = (value or "").lower()
    value = re.sub(r"[\[【(（].*?[\]】)）]", " ", value)
    value = re.sub(r"https?://\S+", " ", value)
    return re.sub(r"[^\w\u3040-\u30ff\u3400-\u9fff]+", " ", value).strip()

def tokens(value):
    text = normalize_title(value)
    out = set(WORD_RE.findall(text))
    cjk = "".join(re.findall(r"[\u3040-\u30ff\u3400-\u9fff]", text))
    out.update(cjk[i:i + 2] for i in range(max(0, len(cjk) - 1)))
    return {x for x in out if len(x) > 1}

def title_similarity(a, b):
    aa, bb = normalize_title(a), normalize_title(b)
    if not aa or not bb:
        return 0.0
    seq = SequenceMatcher(None, aa, bb).ratio()
    ta, tb = tokens(aa), tokens(bb)
    jac = len(ta & tb) / len(ta | tb) if ta and tb else 0.0
    return max(seq, jac)

def content_fingerprint(value):
    text = " ".join(sorted(tokens(value)))
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else ""

def host(url):
    value = urlsplit(url).netloc.lower().split(":")[0]
    return value[4:] if value.startswith("www.") else value
