# services/vcs_service.py
import requests
from urllib.parse import quote
from utils.filter import slim_filter

def fetch_vcs_data(parsed, token):
    """플랫폼(GitLab/GitHub)에 맞춰 API를 호출하고 데이터를 가져옵니다."""
    if not parsed: return None, "파싱된 데이터가 없습니다."
    
    # 🦊 GitLab 로직
    if parsed["platform"] == "gitlab":
        headers = {"PRIVATE-TOKEN": token} if token else {}
        enc_path = quote(parsed["path"], safe="")
        base = parsed["base"]
        
        try:
            if parsed["type"] == "mr":
                c_res = requests.get(f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/commits", headers=headers).json()
                d_res = requests.get(f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/diffs", headers=headers).json()
                c_text = "\n".join([c.get("title", "") for c in c_res])
                d_text = slim_filter(d_res)
            elif parsed["type"] == "commit":
                c_res = requests.get(f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}", headers=headers).json()
                d_res = requests.get(f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}/diff", headers=headers).json()
                c_text = c_res.get("title", "")
                d_text = slim_filter(d_res)
            return c_text, d_text
        except Exception as e:
            return None, f"GitLab API 오류: {e}"

    # 🐙 GitHub 로직
    elif parsed["platform"] == "github":
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"} if token else {}
        base_url = f"https://api.github.com/repos/{parsed['owner']}/{parsed['repo']}"
        
        try:
            if parsed["type"] == "pr":
                c_res = requests.get(f"{base_url}/pulls/{parsed['id']}/commits", headers=headers).json()
                if isinstance(c_res, dict) and "message" in c_res: return None, f"GitHub 에러: {c_res['message']}"
                c_text = "\n".join([c["commit"]["message"] for c in c_res])
                
                f_res = requests.get(f"{base_url}/pulls/{parsed['id']}/files", headers=headers).json()
                diff_list = [{"new_path": f["filename"], "diff": f.get("patch", "")} for f in f_res]
                d_text = slim_filter(diff_list)
                
            elif parsed["type"] == "commit":
                res = requests.get(f"{base_url}/commits/{parsed['id']}", headers=headers).json()
                if "message" in res and "commit" not in res: return None, f"GitHub 에러: {res['message']}"
                c_text = res["commit"]["message"]
                diff_list = [{"new_path": f["filename"], "diff": f.get("patch", "")} for f in res.get("files", [])]
                d_text = slim_filter(diff_list)
                
            return c_text, d_text
        except Exception as e:
            return None, f"GitHub API 오류: {e}"

    return None, "지원하지 않는 플랫폼입니다."