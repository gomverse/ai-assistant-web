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
from config import Config


def export_conversation_to_pdf(history: List[Dict[str, Any]]) -> str:
    """대화 기록을 PDF로 저장하고 파일 경로 반환"""
    os.makedirs(Config.EXPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversation_{timestamp}.pdf"
    filepath = os.path.join(Config.EXPORTS_DIR, filename)

    # 한글 폰트 등록
    font_path = os.path.join(Config.FONTS_DIR, "NanumGothic.ttf")
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
        font_name = "NanumGothic"
    else:
        print("한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
        font_name = "Helvetica"

    c = canvas.Canvas(filepath, pagesize=A4)
    c.setFont(font_name, 16)
    c.drawString(2 * cm, 28 * cm, "=== AI 개인비서 대화 내용 ===")

    c.setFont(font_name, 12)
    c.drawString(
        2 * cm,
        27 * cm,
        f"내보내기 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )

    y = 25 * cm
    for msg in history:
        if y < 5 * cm:  # 새 페이지가 필요한 경우
            c.showPage()
            c.setFont(font_name, 12)
            y = 28 * cm

        role = "사용자" if msg["role"] == "user" else "AI 비서"
        c.drawString(2 * cm, y, f"[{role}]")
        y -= 0.7 * cm

        # 텍스트 줄 바꿈 처리 개선
        words = msg["content"].split()
        line = ""
        for word in words:
            test_line = line + word + " "
            if len(test_line) * 12 < (A4[0] - 4 * cm):  # 페이지 너비 확인
                line = test_line
            else:
                if line:  # 현재 줄에 내용이 있으면 출력
                    c.drawString(2 * cm, y, line.strip())
                    y -= 0.7 * cm
                line = word + " "

        if line:  # 마지막 줄 출력
            c.drawString(2 * cm, y, line.strip())
        y -= 1.5 * cm

    c.save()
    return filepath


def export_conversation_to_txt(history: List[Dict[str, Any]]) -> str:
    """대화 기록을 TXT로 저장하고 파일 경로 반환"""
    os.makedirs(Config.EXPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversation_{timestamp}.txt"
    filepath = os.path.join(Config.EXPORTS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("=== AI 개인비서 대화 내용 ===\n\n")
        f.write(f"내보내기 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for msg in history:
            role = "사용자" if msg["role"] == "user" else "AI 비서"
            f.write(f"[{role}]\n{msg['content']}\n\n")

    return filepath
