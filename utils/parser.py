# utils/parser.py
from urllib.parse import urlparse

def parse_vcs_link(link):
    """GitLab과 GitHub 링크를 모두 분석하여 구조화된 딕셔너리로 반환합니다."""
    try:
        parsed = urlparse(link)
        domain = parsed.netloc.lower()
        
        # [1] GitLab 처리 로직
        if "gitlab" in domain:
            if "/-/" not in parsed.path: return None
            path, tail = parsed.path.split("/-/", 1)
            base = f"{parsed.scheme}://{parsed.netloc}"
            
            if "commit/" in tail:
                return {"platform": "gitlab", "path": path.strip("/"), "type": "commit", "id": tail.split("/")[-1], "base": base}
            if "merge_requests/" in tail:
                parts = tail.split("/")
                return {"platform": "gitlab", "path": path.strip("/"), "type": "mr", "id": parts[parts.index("merge_requests") + 1], "base": base}
            if "compare/" in tail:
                compare_str = tail.split("compare/")[1]
                from_ref, to_ref = compare_str.split("...")
                return {"platform": "gitlab", "path": path.strip("/"), "type": "compare", "from": from_ref, "to": to_ref, "base": base}

        # [2] GitHub 처리 로직
        elif "github.com" in domain:
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) >= 4:
                owner, repo = parts[0], parts[1]
                if parts[2] == "pull":
                    return {"platform": "github", "owner": owner, "repo": repo, "type": "pr", "id": parts[3]}
                elif parts[2] == "commit":
                    return {"platform": "github", "owner": owner, "repo": repo, "type": "commit", "id": parts[3]}
                    
        return None 
    except Exception as e:
        print(f"파싱 에러: {e}")
        return None