# utils/parser.py
from urllib.parse import urlparse

def parse_gitlab_link(link):
    try:
        parsed = urlparse(link)
        if "/-/" not in parsed.path: return None
        path, tail = parsed.path.split("/-/", 1)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if "commit/" in tail:
            return {"path": path.strip("/"), "type": "commit", "id": tail.split("/")[-1], "base": base}
        if "merge_requests/" in tail:
            parts = tail.split("/")
            return {"path": path.strip("/"), "type": "mr", "id": parts[parts.index("merge_requests") + 1], "base": base}
    except: return None
