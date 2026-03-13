# utils/filter.py
from config.settings import ALLOWED_EXTENSIONS, MAX_CHUNK_LENGTH, MAX_TOTAL_LENGTH

def slim_filter(diff_list):
    filtered = []
    curr_len = 0
    for d in diff_list:
        path = d.get("new_path", "unknown")
        if not any(path.endswith(ext) for ext in ALLOWED_EXTENSIONS): continue
        diff_text = d.get("diff", "")[:MAX_CHUNK_LENGTH]
        chunk = f"\n📄 {path}\n{diff_text}\n"
        if curr_len + len(chunk) > MAX_TOTAL_LENGTH: break
        filtered.append(chunk)
        curr_len += len(chunk)
    return "\n".join(filtered) if filtered else "소스 코드 변경 없음"
  
