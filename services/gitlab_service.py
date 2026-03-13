# services/gitlab_service.py
import requests
from urllib.parse import quote
from utils.filter import slim_filter

def fetch_gitlab_data(parsed, token):
    headers = {"PRIVATE-TOKEN": token}
    enc_path = quote(parsed["path"], safe="")
    base = parsed["base"]
    try:
        if parsed["type"] == "mr":
            c_res = requests.get(f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/commits", headers=headers).json()
            d_res = requests.get(f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/diffs", headers=headers).json()
            c_text = "\n".join([c.get("title", "") for c in c_res])
            d_text = slim_filter(d_res)
        else:
            c_res = requests.get(f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}", headers=headers).json()
            d_res = requests.get(f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}/diff", headers=headers).json()
            c_text = c_res.get("title", "")
            d_text = slim_filter(d_res)
        return c_text, d_text
    except Exception as e:
        return None, f"GitLab API 오류: {e}"
