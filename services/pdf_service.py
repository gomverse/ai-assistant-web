"""
PDF 내보내기 서비스
"""

from typing import List, Dict, Any
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm


def export_conversation_to_pdf(
    history: List[Dict[str, Any]], export_dir: str = "data/exports"
) -> str:
    """대화 기록을 PDF로 저장하고 파일 경로 반환"""
    os.makedirs(export_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversation_{timestamp}.pdf"
    filepath = os.path.join(export_dir, filename)
    pdfmetrics.registerFont(TTFont("NanumGothic", "app/static/fonts/NanumGothic.ttf"))
    c = canvas.Canvas(filepath, pagesize=A4)
    c.setFont("NanumGothic", 16)
    c.drawString(2 * cm, 28 * cm, "=== AI 개인비서 대화 내용 ===")
    c.setFont("NanumGothic", 12)
    c.drawString(
        2 * cm,
        27 * cm,
        f"내보내기 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )
    y = 25 * cm
    for msg in history:
        if y < 5 * cm:
            c.showPage()
            c.setFont("NanumGothic", 12)
            y = 28 * cm
        role = "사용자" if msg["role"] == "user" else "AI 비서"
        c.drawString(2 * cm, y, f"[{role}]")
        y -= 0.7 * cm
        words = msg["content"].split()
        line = ""
        for word in words:
            if len(line + word) * 12 < (A4[0] - 4 * cm):
                line += word + " "
            else:
                c.drawString(2 * cm, y, line)
                y -= 0.7 * cm
                line = word + " "
        if line:
            c.drawString(2 * cm, y, line)
        y -= 1.5 * cm
    c.save()
    return filepath
