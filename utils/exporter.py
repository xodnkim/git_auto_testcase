import pandas as pd
import io
import re
import markdown
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font

def generate_html_report(md_text):
    # CSV 블록을 제거하여 보고서만 남깁니다.
    clean_text = re.sub(r'```csv\n(.*?)\n```', '', md_text, flags=re.DOTALL | re.IGNORECASE).strip()
    html_body = markdown.markdown(clean_text, extensions=['tables'])
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>QA 리스크 분석 보고서</title>
        <style>
            body {{ font-family: 'Malgun Gothic', sans-serif; padding: 40px; max-width: 900px; margin: auto; }}
            h1, h2, h3 {{ color: #2C3E50; border-bottom: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <h1>🛡️ QA 리스크 분석 보고서</h1>
        <hr>
        {html_body}
    </body>
    </html>
    """
    return html_template.encode('utf-8')

def generate_tc_excel(md_text):
    csv_match = re.search(r'```csv\n(.*?)\n```', md_text, re.DOTALL | re.IGNORECASE)
    if not csv_match: return None 
    csv_data = csv_match.group(1).strip()
    
    try:
        df = pd.read_csv(io.StringIO(csv_data))
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Test Cases')
            ws = writer.sheets['Test Cases']
            header_fill = PatternFill(start_color="EAEAEA", end_color="EAEAEA", fill_type="solid")
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")
            
            widths = {'A':12, 'B':15, 'C':15, 'D':15, 'E':30, 'F':25, 'G':25, 'H':25, 'I':10}
            for k, v in widths.items(): ws.column_dimensions[k].width = v
        return output.getvalue()
    except: return None
