from flask import Flask, render_template, request, jsonify, send_file, session
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from openai import OpenAI
import traceback
from navertts import NaverTTS
import uuid
import secrets
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import re
import time
from threading import Timer

# Load environment variables
load_dotenv()

# Initialize Flask app with correct template folder
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.secret_key = secrets.token_hex(16)  # 세션을 위한 비밀키 설정

# Maximum number of messages to keep in context
MAX_CONTEXT_MESSAGES = 15  # 컨텍스트 메시지 개수를 15개로 제한

# Configure OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("경고: OPENAI_API_KEY가 설정되지 않았습니다!")
else:
    print(f"API 키 확인: {api_key[:6]}...")  # API 키의 처음 6자리만 출력

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Ensure directories exist
os.makedirs("data/logs", exist_ok=True)
os.makedirs("data/conversations", exist_ok=True)  # 대화 내용 저장을 위한 디렉토리
os.makedirs("app/static/audio", exist_ok=True)

# Register Korean font for PDF
pdfmetrics.registerFont(TTFont("NanumGothic", "app/static/fonts/NanumGothic.ttf"))

# AI 응답 길이 설정
AI_STYLE_SETTINGS = {
    "concise": {
        "name": "간결하게",
        "description": "핵심 내용만 2문장 이내로 전달",
        "instruction": "핵심 내용만 2문장 이내로 매우 간결하게 답변하세요. 절대로 2문장을 넘기지 마세요.",
    },
    "normal": {
        "name": "일반적으로",
        "description": "균형잡힌 일반적인 길이 (6문장 이내)",
        "instruction": "필요한 내용을 6문장 이내로 설명하세요. 핵심 내용을 중심으로 균형있게 답변하되, 절대로 6문장을 넘기지 마세요.",
    },
    "detailed": {
        "name": "상세하게",
        "description": "자세하고 풍부한 설명 (제한 없음)",
        "instruction": "모든 내용을 상세하고 풍부하게 설명하세요. 관련 정보와 예시를 포함하여 자세히 답변하세요. 문장 수 제한이 없습니다.",
    },
}


def save_conversation_history(history):
    """Save conversation history to a file"""
    try:
        conversation_file = os.path.join(
            "data/conversations", "conversation_history.json"
        )
        with open(conversation_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"대화 내용 저장 중 오류 발생: {e}")


def load_conversation_history():
    """Load conversation history from a file"""
    try:
        conversation_file = os.path.join(
            "data/conversations", "conversation_history.json"
        )
        if os.path.exists(conversation_file):
            with open(conversation_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"대화 내용 불러오기 중 오류 발생: {e}")
    return []


def get_conversation_history():
    """Get conversation history from session or file"""
    if "conversation_history" not in session:
        session["conversation_history"] = load_conversation_history()
    return session["conversation_history"]


def update_conversation_history(role, content):
    """Update conversation history in session and file"""
    history = get_conversation_history()
    history.append({"role": role, "content": content})

    # Keep only the last MAX_CONTEXT_MESSAGES messages
    if len(history) > MAX_CONTEXT_MESSAGES:
        history = history[-MAX_CONTEXT_MESSAGES:]

    session["conversation_history"] = history
    session.modified = True

    # Save to file
    save_conversation_history(history)


@app.route("/")
def home():
    # Load existing conversation history instead of clearing it
    if "conversation_history" not in session:
        session["conversation_history"] = load_conversation_history()
    return render_template("index.html")


@app.route("/clear_context", methods=["POST"])
def clear_context():
    """Clear conversation context from both session and file"""
    session["conversation_history"] = []
    save_conversation_history([])  # 파일에서도 대화 내용 삭제
    return jsonify(
        {"status": "success", "message": "대화 컨텍스트가 초기화되었습니다."}
    )


def parse_notification_time(text):
    """Parse notification time from text"""
    time_pattern = r"(\d+)\s*(분|초|시간)\s*뒤"
    match = re.search(time_pattern, text)
    if not match:
        return None

    number = int(match.group(1))
    unit = match.group(2)

    # Convert to seconds
    if unit == "초":
        return number
    elif unit == "분":
        return number * 60
    elif unit == "시간":
        return number * 3600

    return None


@app.route("/schedule_notification", methods=["POST"])
def schedule_notification():
    """Schedule a notification"""
    try:
        data = request.json
        delay = data.get("delay")  # delay in seconds
        message = data.get("message")

        if not delay or not message:
            return jsonify(
                {"status": "error", "message": "필수 파라미터가 누락되었습니다."}
            )

        # Schedule the notification
        notification_time = datetime.now().timestamp() + delay

        return jsonify(
            {
                "status": "success",
                "notification_time": notification_time,
                "message": message,
            }
        )

    except Exception as e:
        return jsonify(
            {
                "status": "error",
                "message": f"알림 설정 중 오류가 발생했습니다: {str(e)}",
            }
        )


@app.route("/get_ai_style_settings", methods=["GET"])
def get_ai_style_settings():
    """Get available AI style settings"""
    return jsonify({"status": "success", "settings": AI_STYLE_SETTINGS})


@app.route("/update_ai_style", methods=["POST"])
def update_ai_style():
    """Update AI response length setting"""
    try:
        data = request.json
        response_length = data.get("response_length", "normal")

        # Validate setting
        if response_length not in AI_STYLE_SETTINGS:
            return jsonify(
                {"status": "error", "message": "잘못된 응답 길이 설정입니다."}
            )

        # Save setting to session
        session["ai_style_settings"] = {"response_length": response_length}

        return jsonify(
            {
                "status": "success",
                "message": f"AI 응답 길이가 '{AI_STYLE_SETTINGS[response_length]['name']}'(으)로 변경되었습니다.",
                "settings": {"response_length": response_length},
            }
        )

    except Exception as e:
        return jsonify(
            {
                "status": "error",
                "message": f"응답 길이 설정 중 오류가 발생했습니다: {str(e)}",
            }
        )


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.json
        user_input = data.get("question", "")

        if not api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

        # Check for notification request
        notification_seconds = parse_notification_time(user_input)
        has_notification = False

        if notification_seconds:
            has_notification = True

        print(f"사용자 입력: {user_input}")  # 디버깅용 로그

        # Update conversation history with user input
        update_conversation_history("user", user_input)

        # Get current AI style settings
        style_settings = session.get(
            "ai_style_settings", {"response_length": "normal"}  # 기본값은 일반적인 길이
        )

        # Create system prompt from style settings
        system_prompt = (
            "당신은 한국어를 사용하는 AI 개인비서입니다.\n"
            f"{AI_STYLE_SETTINGS[style_settings['response_length']]['instruction']}"
        )

        # Prepare messages for API call
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history
        messages.extend(get_conversation_history())

        # Call OpenAI API
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-nano", messages=messages  # GPT-4.1 nano 모델 사용
            )
            print("API 호출 성공")  # 디버깅용 로그
        except Exception as api_error:
            print(f"OpenAI API 오류: {str(api_error)}")  # 디버깅용 로그
            raise

        # Extract the response
        assistant_response = response.choices[0].message.content
        print(f"AI 응답: {assistant_response[:100]}...")  # 응답의 처음 100자만 출력

        # Update conversation history with assistant response
        update_conversation_history("assistant", assistant_response)

        # Generate audio file
        try:
            audio_filename = f"response_{uuid.uuid4()}.mp3"
            audio_path = os.path.join("app/static/audio", audio_filename)
            tts = NaverTTS(assistant_response)
            tts.save(audio_path)
            audio_url = f"/static/audio/{audio_filename}"
        except Exception as tts_error:
            print(f"TTS 오류: {str(tts_error)}")
            audio_url = None

        # Log the conversation
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "assistant_response": assistant_response,
            "audio_url": audio_url,
        }

        log_file = f'data/logs/conversation_{datetime.now().strftime("%Y%m%d")}.json'
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"대화 내용 저장 중 오류 발생: {e}")

        response_data = {
            "response": assistant_response,
            "status": "success",
            "audio_url": audio_url,
        }

        if has_notification:
            response_data["notification"] = {
                "delay": notification_seconds,
                "message": user_input,
            }

        return jsonify(response_data)

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"오류 발생: {str(e)}")
        print(f"상세 오류 내용:\n{error_trace}")
        return (
            jsonify(
                {
                    "error": str(e),
                    "status": "error",
                    "message": f"서버 처리 중 오류가 발생했습니다: {str(e)}",
                }
            ),
            500,
        )


@app.route("/export_conversation", methods=["POST"])
def export_conversation():
    """Export conversation history as a text or PDF file"""
    try:
        history = get_conversation_history()
        if not history:
            return jsonify({"status": "error", "message": "대화 내용이 없습니다."})

        # Get export format from request
        export_format = request.json.get("format", "txt")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if export_format == "pdf":
            filename = f"conversation_{timestamp}.pdf"
            filepath = os.path.join("data/exports", filename)

            # Ensure exports directory exists
            os.makedirs("data/exports", exist_ok=True)

            # Create PDF
            c = canvas.Canvas(filepath, pagesize=A4)
            c.setFont("NanumGothic", 12)

            # Write title
            c.setFont("NanumGothic", 16)
            c.drawString(2 * cm, 28 * cm, "=== AI 개인비서 대화 내용 ===")

            # Write timestamp
            c.setFont("NanumGothic", 12)
            c.drawString(
                2 * cm,
                27 * cm,
                f"내보내기 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            )

            y = 25 * cm
            for msg in history:
                if y < 5 * cm:  # New page if not enough space
                    c.showPage()
                    c.setFont("NanumGothic", 12)
                    y = 28 * cm

                role = "사용자" if msg["role"] == "user" else "AI 비서"
                c.drawString(2 * cm, y, f"[{role}]")
                y -= 0.7 * cm

                # Word wrap for content
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
        else:  # txt format
            filename = f"conversation_{timestamp}.txt"
            filepath = os.path.join("data/exports", filename)

            # Ensure exports directory exists
            os.makedirs("data/exports", exist_ok=True)

            # Write conversation to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("=== AI 개인비서 대화 내용 ===\n\n")
                f.write(
                    f"내보내기 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                for msg in history:
                    role = "사용자" if msg["role"] == "user" else "AI 비서"
                    f.write(f"[{role}]\n{msg['content']}\n\n")

        # Return file
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf" if export_format == "pdf" else "text/plain",
        )

    except Exception as e:
        print(f"대화 내보내기 중 오류 발생: {str(e)}")
        return jsonify(
            {
                "status": "error",
                "message": "대화 내용을 내보내는 중에 오류가 발생했습니다.",
            }
        )


@app.route("/search_conversation", methods=["POST"])
def search_conversation():
    """Search through conversation history"""
    try:
        query = request.json.get("query", "").strip()
        if not query:
            return jsonify({"status": "error", "message": "검색어를 입력해주세요."})

        history = get_conversation_history()
        results = []

        for i, msg in enumerate(history):
            if re.search(query, msg["content"], re.IGNORECASE):
                # Add context (previous and next messages if available)
                context = {
                    "before": history[i - 1] if i > 0 else None,
                    "match": msg,
                    "after": history[i + 1] if i < len(history) - 1 else None,
                }
                results.append(context)

        return jsonify({"status": "success", "results": results, "count": len(results)})

    except Exception as e:
        print(f"대화 검색 중 오류 발생: {str(e)}")
        return jsonify(
            {"status": "error", "message": "대화 내용 검색 중에 오류가 발생했습니다."}
        )


if __name__ == "__main__":
    app.run(debug=True)
