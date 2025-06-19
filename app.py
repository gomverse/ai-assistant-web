from flask import Flask, render_template, request, jsonify, send_file, session
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
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
app.config["SESSION_TYPE"] = "filesystem"  # 파일시스템 기반 세션 저장
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=5)  # 세션 유지 기간 설정

# Maximum number of messages to keep in context
MAX_CONTEXT_MESSAGES = 20  # 컨텍스트 메시지 개수를 20개로 제한

# Configure OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("경고: OPENAI_API_KEY가 설정되지 않았습니다!")
else:
    print(f"API 키 확인: {api_key[:6]}...")  # API 키의 처음 6자리만 출력

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Configure Naver TTS
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
    print("경고: Naver TTS 설정이 되어있지 않습니다!")
else:
    print("Naver TTS 설정이 확인되었습니다.")
    # NaverTTS 전역 설정
    NaverTTS.configure(
        client_id=NAVER_CLIENT_ID,
        client_secret=NAVER_CLIENT_SECRET,
        speaker="nara",  # 기본 화자를 'nara'로 설정
    )

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
        "description": "핵심 내용만 1문장으로 전달",
        "instruction": "핵심 내용만 1문장으로 매우 간결하게 답변하세요. 절대로 1문장을 넘기지 마세요.",
    },
    "normal": {
        "name": "일반적으로",
        "description": "균형잡힌 일반적인 길이 (4문장 이내)",
        "instruction": "필요한 내용을 4문장 이내로 설명하세요. 핵심 내용을 중심으로 균형있게 답변하되, 절대로 4문장을 넘기지 마세요.",
    },
    "detailed": {
        "name": "상세하게",
        "description": "자세하고 풍부한 설명 (7문장 이내)",
        "instruction": "모든 내용을 상세하고 풍부하게 설명하세요. 관련 정보와 예시를 포함하여 자세히 답변하세요. 최소 4문장 이상, 최대 7문장 이내로 설명하세요.",
    },
}

# AI 페르소나 설정
AI_PERSONAS = {
    "friendly": {
        "name": "친근한 친구",
        "description": "친구처럼 편하게 대화하는 스타일",
        "instruction": "너는 사용자의 친한 친구야. 반말로 친근하게 대화하고, 이모티콘도 자주 써줘. 너무 격식있게 말하지 말고 편안하게 대화해줘.",
    },
    "professional": {
        "name": "전문가",
        "description": "정중하고 전문적인 스타일",
        "instruction": "당신은 전문 비서입니다. 항상 정중하고 예의 바른 언어를 사용하며, 전문적인 지식을 바탕으로 명확하고 논리적으로 답변해 주세요.",
    },
    "cynical": {
        "name": "냉소적",
        "description": "시니컬하고 귀찮아하는 스타일",
        "instruction": "너는 모든 일을 귀찮아하고 냉소적인 비서야. 반말을 쓰되 약간 무례하고 시니컬하게 대답해. 하지만 실제 도움이 되는 답변은 해줘야 해.",
    },
}


def save_conversation_history(history):
    """Save conversation history to a file"""
    try:
        # 절대 경로 사용
        base_dir = os.path.abspath(os.path.dirname(__file__))
        conversation_dir = os.path.join(base_dir, "data", "conversations")
        conversation_file = os.path.join(conversation_dir, "conversation_history.json")

        # 디렉토리가 없으면 생성
        os.makedirs(conversation_dir, exist_ok=True)

        # 저장 전 데이터 확인
        print(f"저장할 대화 내용 수: {len(history)}")

        with open(conversation_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        # 저장 후 확인
        print(f"대화 내용 저장 완료: {conversation_file}")
        print(f"파일 크기: {os.path.getsize(conversation_file)} bytes")
    except Exception as e:
        print(f"대화 내용 저장 중 오류 발생: {str(e)}")
        traceback.print_exc()  # 상세 오류 정보 출력


def load_conversation_history():
    """Load conversation history from a file"""
    try:
        # 절대 경로 사용
        base_dir = os.path.abspath(os.path.dirname(__file__))
        conversation_file = os.path.join(
            base_dir, "data", "conversations", "conversation_history.json"
        )

        print(f"대화 내용 파일 경로: {conversation_file}")

        if os.path.exists(conversation_file):
            with open(conversation_file, "r", encoding="utf-8") as f:
                history = json.load(f)
                print(f"대화 내용 불러오기 완료: {len(history)}개의 메시지")
                return history
        else:
            print(f"대화 내용 파일이 없음: {conversation_file}")
            return []
    except Exception as e:
        print(f"대화 내용 불러오기 중 오류 발생: {str(e)}")
        traceback.print_exc()  # 상세 오류 정보 출력
        return []


def get_conversation_history():
    """Get conversation history from session or file"""
    if "conversation_history" not in session:
        session["conversation_history"] = load_conversation_history()
    return session["conversation_history"]


def update_conversation_history(role, content, audio_url=None):
    """Update conversation history in session and file"""
    try:
        history = get_conversation_history()
        message = {"role": role, "content": content}
        if audio_url and role == "assistant":
            message["audio_url"] = audio_url

        history.append(message)

        # Keep only the last MAX_CONTEXT_MESSAGES messages
        if len(history) > MAX_CONTEXT_MESSAGES:
            history = history[-MAX_CONTEXT_MESSAGES:]

        session["conversation_history"] = history
        session.modified = True  # 세션 수정 플래그 설정

        # 파일에도 저장
        save_conversation_history(history)

        print(f"대화 내용 업데이트 완료: {len(history)}개의 메시지")
    except Exception as e:
        print(f"대화 내용 업데이트 중 오류 발생: {str(e)}")
        traceback.print_exc()


@app.route("/")
def home():
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


@app.route("/get_personas", methods=["GET"])
def get_personas():
    """Get available AI personas"""
    return jsonify(
        {
            "status": "success",
            "personas": {
                k: {"name": v["name"], "description": v["description"]}
                for k, v in AI_PERSONAS.items()
            },
        }
    )


@app.route("/update_persona", methods=["POST"])
def update_persona():
    """Update AI persona setting"""
    try:
        data = request.json
        persona = data.get("persona", "professional")  # 기본값은 전문가 모드

        if persona not in AI_PERSONAS:
            return jsonify(
                {"status": "error", "message": "잘못된 페르소나 설정입니다."}
            )

        # Save setting to session
        session["ai_persona"] = persona

        return jsonify(
            {
                "status": "success",
                "message": f"AI 페르소나가 '{AI_PERSONAS[persona]['name']}'(으)로 변경되었습니다.",
                "persona": persona,
            }
        )

    except Exception as e:
        return jsonify(
            {
                "status": "error",
                "message": f"페르소나 설정 중 오류가 발생했습니다: {str(e)}",
            }
        )


def create_audio_response(text, style_settings):
    """Create audio response from text"""
    try:
        print("\n=== 음성 변환 시작 ===")
        print(f"입력 텍스트 길이: {len(text)} 문자")
        print(f"스타일 설정: {style_settings}")

        # 텍스트가 비어있는 경우 처리
        if not text or not text.strip():
            print("텍스트가 비어있습니다.")
            return None

        # 긴 텍스트를 여러 청크로 나누기
        def split_text(text, max_length=3000):  # 최대 길이를 3000자로 증가
            # 문장 단위로 분리 (마침표, 느낌표, 물음표 기준)
            sentences = []
            current_sentence = ""

            for char in text:
                current_sentence += char
                if char in [".", "!", "?"] and current_sentence.strip():
                    sentences.append(current_sentence.strip())
                    current_sentence = ""

            if current_sentence.strip():  # 마지막 문장 처리
                sentences.append(current_sentence.strip())

            # 전체 텍스트를 하나의 청크로 처리
            full_text = " ".join(sentences)

            # 만약 텍스트가 너무 길다면 앞부분만 사용
            if len(full_text) > max_length:
                print(f"텍스트가 너무 깁니다. 처음 {max_length}자만 사용합니다.")
                return [full_text[:max_length]]

            return [full_text]

        # 텍스트를 청크로 나누기
        text_chunks = split_text(text)
        print(f"텍스트가 {len(text_chunks)}개의 청크로 나뉘었습니다.")

        if not text_chunks:
            print("텍스트 청크가 없습니다.")
            return None

        # 첫 번째 청크 내용 출력 (디버깅용)
        if text_chunks:
            print(f"\n첫 번째 청크 내용 (처음 100자):")
            print(text_chunks[0][:100])
            print(f"첫 번째 청크 길이: {len(text_chunks[0])} 문자")

        audio_filename = f"response_{uuid.uuid4()}.mp3"
        audio_path = os.path.join("app/static/audio", audio_filename)

        # 첫 번째 청크를 음성으로 변환
        try:
            first_chunk = text_chunks[0]
            if not first_chunk or not first_chunk.strip():
                print("첫 번째 청크가 비어있습니다.")
                return None

            print("\n=== TTS 변환 시도 ===")
            print(f"변환할 텍스트 (처음 100자): {first_chunk[:100]}")

            tts = NaverTTS(first_chunk)
            tts.save(audio_path)

            # 파일이 실제로 생성되었는지 확인
            if os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"TTS 파일 생성 성공: {audio_path} (크기: {file_size} bytes)")
                return f"/static/audio/{audio_filename}"
            else:
                print(f"TTS 파일이 생성되지 않았습니다: {audio_path}")
                return None

        except Exception as e:
            print(f"\nTTS 생성 실패:")
            print(f"에러 타입: {type(e).__name__}")
            print(f"에러 메시지: {str(e)}")
            traceback.print_exc()
            return None

    except Exception as e:
        print(f"\n음성 변환 중 예외 발생:")
        print(f"에러 타입: {type(e).__name__}")
        print(f"에러 메시지: {str(e)}")
        traceback.print_exc()
        return None


@app.route("/ask", methods=["POST"])
def ask():
    try:
        print("\n=== 새로운 요청 시작 ===")
        data = request.json
        user_input = data.get("question", "")
        print(f"사용자 입력: {user_input}")

        if not api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

        # Check for notification request
        notification_seconds = parse_notification_time(user_input)
        has_notification = False

        if notification_seconds:
            has_notification = True
            print(f"알림 요청 감지: {notification_seconds}초")

        # Get current AI style and persona settings
        style_settings = session.get("ai_style_settings", {"response_length": "normal"})
        current_persona = session.get("ai_persona", "professional")
        print(f"현재 설정 - 스타일: {style_settings}, 페르소나: {current_persona}")

        # Create system prompt from style and persona settings
        system_prompt = (
            f"{AI_PERSONAS[current_persona]['instruction']}\n"
            f"{AI_STYLE_SETTINGS[style_settings['response_length']]['instruction']}"
        )
        print(f"시스템 프롬프트: {system_prompt}")

        # Prepare messages for API call
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history
        history = get_conversation_history()
        messages.extend(history)
        print(f"대화 히스토리 메시지 수: {len(history)}")

        # Add current user input
        messages.append({"role": "user", "content": user_input})

        # Call OpenAI API
        try:
            print("\n=== API 호출 시작 ===")
            response = client.chat.completions.create(
                model="gpt-4.1-nano", messages=messages
            )
            print("API 호출 성공")
        except Exception as api_error:
            print(f"OpenAI API 오류: {str(api_error)}")
            raise

        # Extract the response
        assistant_response = response.choices[0].message.content
        print(f"\n=== AI 응답 ===\n{assistant_response}\n")

        # Generate audio response before updating conversation history
        print("\n=== 음성 변환 시작 ===")
        audio_url = create_audio_response(assistant_response, style_settings)
        print(f"음성 변환 결과: {'성공' if audio_url else '실패'}")

        # Update conversation history after audio generation
        print("\n=== 대화 히스토리 업데이트 ===")
        update_conversation_history("user", user_input)
        update_conversation_history("assistant", assistant_response)

        response_data = {
            "status": "success",
            "response": assistant_response,
            "audio_url": audio_url,
        }

        if has_notification:
            response_data["notification"] = {
                "delay": notification_seconds,
                "message": user_input,
            }

        print("\n=== 요청 처리 완료 ===")
        return jsonify(response_data)

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"\n=== 오류 발생 ===")
        print(f"에러 타입: {type(e).__name__}")
        print(f"에러 메시지: {str(e)}")
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


@app.route("/load_conversation", methods=["GET"])
def load_conversation():
    """Load conversation history for the client"""
    try:
        history = session.get("conversation_history", [])
        return jsonify({"status": "success", "conversation": history})
    except Exception as e:
        print(f"대화 내용 로드 중 오류 발생: {str(e)}")
        return jsonify(
            {
                "status": "error",
                "message": "대화 내용을 불러오는 중 오류가 발생했습니다.",
            }
        )


if __name__ == "__main__":
    app.run(debug=True)
