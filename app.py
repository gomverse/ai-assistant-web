from flask import Flask, render_template, request, jsonify, send_file, session
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
from openai import OpenAI
import traceback
from gtts import gTTS
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
import logging  # 로깅 모듈 추가
import io
import urllib.parse
import urllib.request

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("data/logs/app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

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
client = OpenAI()  # API key will be read from environment variable

# Ensure directories exist
os.makedirs("data/logs", exist_ok=True)
os.makedirs("data/conversations", exist_ok=True)  # 대화 내용 저장을 위한 디렉토리
os.makedirs("app/static/audio", exist_ok=True)

# Register Korean font for PDF
pdfmetrics.registerFont(TTFont("NanumGothic", "app/static/fonts/NanumGothic.ttf"))

# AI 응답 길이 설정
AI_STYLE_SETTINGS = {
    "concise": {
        "name": "짧게",
        "description": "2문장 이하로 간결하고 핵심만 요약",
        "instruction": "2문장 이하로 간결하게 핵심만 요약해서 답변하세요. 절대로 2문장을 넘기지 마세요. 가능하면 1문장으로 답변하되, 꼭 필요한 경우에만 2문장을 사용하세요.",
        "confirmation": "앞으로는 핵심 내용만 간단히 답변드리겠습니다.",
    },
    "normal": {
        "name": "보통",
        "description": "6문장 이하로 평범하고 일반적인 설명",
        "instruction": "6문장 이하로 평범하고 일반적인 설명을 해주세요. 핵심 내용을 중심으로 균형있게 답변하되, 최소 3문장, 최대 6문장으로 설명하세요. 너무 짧거나 길지 않게 적절한 길이를 유지하세요.",
        "confirmation": "앞으로는 적절한 길이로 균형있게 답변드리겠습니다.",
    },
    "detailed": {
        "name": "길게",
        "description": "9문장 이상으로 상세하고 자세한 설명",
        "instruction": "9문장 이상으로 상세하고 자세한 설명을 해주세요. 관련 정보, 예시, 장단점 등을 포함하여 깊이 있게 답변하세요. 반드시 9문장 이상으로 설명하고, 필요한 경우 더 자세히 설명하세요. 내용을 체계적으로 구성하여 이해하기 쉽게 설명하세요.",
        "confirmation": "앞으로는 모든 내용을 상세하게 설명드리겠습니다.",
    },
}

# AI 페르소나 설정
AI_PERSONAS = {
    "friendly": {
        "name": "친근한 친구",
        "description": "친구처럼 편하게 대화하는 스타일",
        "instruction": "친구처럼 편하고 친근하게 대화하세요. 이모티콘을 적절히 사용하고, 존댓말 대신 반말을 사용하세요. 하지만 너무 가볍지 않게 적절한 예의는 지키세요.",
        "confirmation": "앞으로는 친구처럼 편하게 대화할게! 😊",
    },
    "professional": {
        "name": "전문가",
        "description": "정중하고 전문적인 스타일",
        "instruction": "전문가답게 정중하고 전문적으로 답변하세요. 항상 존댓말을 사용하고, 객관적이고 논리적으로 설명하세요. 필요한 경우 전문 용어를 적절히 사용하되, 이해하기 쉽게 설명하세요.",
        "confirmation": "앞으로는 전문적이고 정중하게 답변 드리도록 하겠습니다.",
    },
    "cynical": {
        "name": "냉소적",
        "description": "시니컬하고 귀찮아하는 스타일",
        "instruction": "모든 것이 귀찮고 시니컬한 태도로 답변하세요. 비꼬는 듯한 어투를 사용하고, 한숨을 쉬거나 짜증내는 듯한 표현을 섞어주세요. 하지만 너무 불쾌하지 않게 적절한 선을 지키세요.",
        "confirmation": "(한숨) 뭐... 앞으로는 내가 귀찮더라도 냉소적으로 답해주지...",
    },
}

# 세션 저장 디렉토리
SESSIONS_DIR = "data/sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)


class ChatSession:
    def __init__(self):
        self.messages = []
        self.context_size = 20  # 컨텍스트 크기
        self.style_settings = {"style": "normal"}  # 키 이름 변경
        self.persona = "professional"  # 기본 페르소나 설정
        self._settings_restored = False
        logger.info(
            f"New ChatSession initialized with context_size={self.context_size}"
        )

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.context_size:
            removed_msg = self.messages.pop(0)
            logger.debug(
                f"Removed oldest message due to context size limit: {removed_msg['role']}: {removed_msg['content'][:50]}..."
            )
        logger.debug(
            f"Added new message - Role: {role}, Content preview: {content[:50]}..."
        )
        logger.debug(f"Current message count: {len(self.messages)}")

    def get_context(self):
        logger.debug(f"Returning context with {len(self.messages)} messages")
        return self.messages

    def clear(self):
        self.messages = []
        logger.info("Chat session cleared")

    def update_style(self, style):
        if style not in AI_STYLE_SETTINGS:
            logger.warning(f"Invalid style setting: {style}")
            return
        self.style_settings["style"] = style  # 키 이름 변경
        logger.info(f"Style updated to: {style}")

    def update_persona(self, persona):
        if persona not in AI_PERSONAS:
            logger.warning(f"Invalid persona setting: {persona}")
            return
        self.persona = persona
        logger.info(f"Persona updated to: {persona}")

    def get_style(self):
        return self.style_settings["style"]  # 키 이름 변경

    def get_persona(self):
        return self.persona

    def save_settings_to_session(self):
        """Save current settings to Flask session"""
        if not session:
            logger.warning("No Flask session available")
            return

        # 현재 모드 확인
        is_private = request.headers.get("X-Private-Mode") == "true"

        # 비공개 모드일 때는 'private_' 접두사를 붙여서 저장
        if is_private:
            session["private_ai_style_settings"] = self.style_settings
            session["private_ai_persona"] = self.persona
        else:
            session["ai_style_settings"] = self.style_settings
            session["ai_persona"] = self.persona

        session.modified = True
        logger.info(
            f"Settings saved to {'private' if is_private else 'normal'} session - Style: {self.get_style()}, Persona: {self.persona}"
        )

    def restore_settings_from_session(self):
        """Restore settings from Flask session"""
        if not session:
            logger.warning("No Flask session available")
            return

        if "ai_style_settings" in session:
            style = session["ai_style_settings"].get("style")  # 키 이름 변경
            if style:
                self.update_style(style)
                logger.debug(f"Restored style setting: {style}")

        if "ai_persona" in session:
            persona = session["ai_persona"]
            if persona:
                self.update_persona(persona)
                logger.debug(f"Restored persona setting: {persona}")

        self._settings_restored = True
        logger.info("Settings restored from session")


# Initialize chat sessions
normal_chat_session = ChatSession()
private_chat_session = ChatSession()


def get_current_session():
    """현재 모드에 따른 세션 반환"""
    is_private = request.headers.get("X-Private-Mode") == "true"
    current_session = private_chat_session if is_private else normal_chat_session

    logger.debug(f"Getting current session - Private mode: {is_private}")
    logger.debug(f"Session message count: {len(current_session.messages)}")
    logger.debug(f"Current style: {current_session.get_style()}")
    logger.debug(f"Current persona: {current_session.get_persona()}")

    # 세션 설정 복원 (모든 모드에서)
    if not current_session._settings_restored:
        logger.info(
            f"Attempting to restore session settings for {'private' if is_private else 'normal'} mode"
        )
        # 비공개 모드일 때는 세션에 'private_' 접두사를 붙여서 저장
        if is_private:
            if "private_ai_style_settings" in session:
                style = session["private_ai_style_settings"].get("style")
                if style:
                    current_session.update_style(style)
                    logger.debug(f"Restored private mode style setting: {style}")

            if "private_ai_persona" in session:
                persona = session["private_ai_persona"]
                if persona:
                    current_session.update_persona(persona)
                    logger.debug(f"Restored private mode persona setting: {persona}")
        else:
            current_session.restore_settings_from_session()

        current_session._settings_restored = True
        logger.info(
            f"Settings restored for {'private' if is_private else 'normal'} mode"
        )

    return current_session


def save_conversation_history(history, is_private=False):
    """Save conversation history to a file"""
    if is_private:
        logger.info("Skipping conversation save - Private mode active")
        return  # 비공개 모드에서는 파일에 저장하지 않음

    try:
        logger.info("Saving conversation history to file")
        # 절대 경로 사용
        base_dir = os.path.abspath(os.path.dirname(__file__))
        conversation_dir = os.path.join(base_dir, "data", "conversations")
        conversation_file = os.path.join(conversation_dir, "conversation_history.json")

        # 디렉토리가 없으면 생성
        os.makedirs(conversation_dir, exist_ok=True)

        # 저장 전 데이터 확인
        logger.debug(f"Saving {len(history)} messages to file")

        with open(conversation_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        # 저장 후 확인
        logger.info(f"Conversation saved to: {conversation_file}")
        logger.debug(f"File size: {os.path.getsize(conversation_file)} bytes")
    except Exception as e:
        logger.error(f"Error saving conversation: {str(e)}")
        logger.error(traceback.format_exc())


def load_conversation_history():
    """Load conversation history from a file"""
    try:
        logger.info("Loading conversation history from file")
        # 절대 경로 사용
        base_dir = os.path.abspath(os.path.dirname(__file__))
        conversation_dir = os.path.join(base_dir, "data", "conversations")
        conversation_file = os.path.join(conversation_dir, "conversation_history.json")

        # 디렉토리가 없으면 생성
        os.makedirs(conversation_dir, exist_ok=True)

        if os.path.exists(conversation_file):
            with open(conversation_file, "r", encoding="utf-8") as f:
                history = json.load(f)
                logger.info(f"Loaded {len(history)} messages from file")
                return history
        else:
            logger.warning(f"No conversation file found at: {conversation_file}")
            return []
    except Exception as e:
        logger.error(f"Error loading conversation: {str(e)}")
        logger.error(traceback.format_exc())
        return []


def get_conversation_history():
    """Get conversation history from session or file"""
    try:
        is_private = request.headers.get("X-Private-Mode") == "true"
        current_session = get_current_session()

        logger.debug(f"Getting conversation history - Private mode: {is_private}")

        if is_private:
            # 비공개 모드에서는 현재 세션의 메시지만 반환
            logger.debug("Returning private session messages")
            return current_session.get_context()

        # 일반 모드
        history = session.get("conversation_history")
        logger.debug(f"Session history found: {history is not None}")

        # If not in session, try to load from file
        if history is None:
            logger.info("No history in session, loading from file")
            history = load_conversation_history()
            session["conversation_history"] = history
            session.modified = True
            logger.debug("History loaded and stored in session")

            # Sync with normal chat session
            current_session.clear()
            for msg in history:
                current_session.add_message(msg["role"], msg["content"])
            logger.info("Synced history with normal chat session")

        return history
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        logger.error(traceback.format_exc())
        return []


def update_conversation_history(role, content, audio_url=None):
    """Update conversation history in session and file"""
    try:
        is_private = request.headers.get("X-Private-Mode") == "true"
        current_session = get_current_session()

        logger.debug(f"Updating conversation history - Private mode: {is_private}")
        logger.debug(f"Message - Role: {role}, Content preview: {content[:50]}...")

        # Create new message
        message = {"role": role, "content": content}
        if audio_url and role == "assistant":
            message["audio_url"] = audio_url

        if is_private:
            # 비공개 모드에서는 현재 세션에만 저장
            logger.debug("Adding message to private session only")
            current_session.add_message(role, content)
            return

        # 일반 모드
        history = get_conversation_history()
        history.append(message)
        logger.debug(f"Added message to history. New count: {len(history)}")

        # Keep only the last MAX_CONTEXT_MESSAGES messages
        if len(history) > MAX_CONTEXT_MESSAGES:
            history = history[-MAX_CONTEXT_MESSAGES:]
            logger.debug(f"Trimmed history to {MAX_CONTEXT_MESSAGES} messages")

        # Update session
        session["conversation_history"] = history
        session.modified = True
        logger.debug("Updated session with new history")

        # Update normal chat session
        current_session.add_message(role, content)
        logger.debug("Updated normal chat session")

        # Save to file
        save_conversation_history(history)
        logger.info("Saved updated history to file")

    except Exception as e:
        logger.error(f"Error updating conversation history: {str(e)}")
        logger.error(traceback.format_exc())


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/clear_context", methods=["POST"])
def clear_context():
    """Clear conversation context"""
    try:
        is_private = request.headers.get("X-Private-Mode") == "true"
        current_session = get_current_session()

        if is_private:
            # 비공개 모드에서는 현재 세션만 초기화
            current_session.clear()
        else:
            # 일반 모드에서는 세션과 파일 모두 초기화
            session["conversation_history"] = []
            current_session.clear()
            save_conversation_history([])

        return jsonify(
            {"status": "success", "message": "대화 내용이 초기화되었습니다."}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


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


@app.route("/update_style", methods=["POST"])
def update_style():
    """Update AI response style setting"""
    try:
        data = request.json
        style = data.get("style", "normal")

        if style not in AI_STYLE_SETTINGS:
            logger.warning(f"Invalid style setting requested: {style}")
            return jsonify({"status": "error", "message": "잘못된 스타일 설정입니다."})

        # Get current session and update style
        current_session = get_current_session()
        old_style = current_session.get_style()
        current_session.update_style(style)

        # Save setting to session for non-private mode
        if request.headers.get("X-Private-Mode") != "true":
            current_session.save_settings_to_session()

        # 로깅 추가
        logger.info(
            f"AI response style changed from '{AI_STYLE_SETTINGS[old_style]['name']}' to '{AI_STYLE_SETTINGS[style]['name']}'"
        )
        logger.debug(f"Style instruction: {AI_STYLE_SETTINGS[style]['instruction']}")

        # 응답 메시지 생성
        message = f"AI 응답 길이가 '{AI_STYLE_SETTINGS[style]['name']}'(으)로 변경되었습니다.\n{AI_STYLE_SETTINGS[style]['confirmation']}"

        return jsonify(
            {
                "status": "success",
                "message": message,
                "style": style,
                "show_in_chat": True,  # 채팅창에 메시지 표시 여부
            }
        )

    except Exception as e:
        logger.error(f"Style update error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)})


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
        persona = data.get("persona", "professional")

        if persona not in AI_PERSONAS:
            return jsonify(
                {"status": "error", "message": "잘못된 페르소나 설정입니다."}
            )

        # Get current session and update persona
        current_session = get_current_session()
        current_session.update_persona(persona)

        # Save setting to session for non-private mode
        if request.headers.get("X-Private-Mode") != "true":
            current_session.save_settings_to_session()

        # 응답 메시지 생성
        message = f"AI 성격이 '{AI_PERSONAS[persona]['name']}'(으)로 변경되었습니다.\n{AI_PERSONAS[persona]['confirmation']}"

        return jsonify({"status": "success", "message": message, "persona": persona})

    except Exception as e:
        logger.error(f"Persona update error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})


@app.route("/tts", methods=["POST"])
def text_to_speech():
    try:
        data = request.get_json()
        text = data.get("text", "")

        if not text:
            return jsonify({"error": "텍스트가 비어있습니다."}), 400

        # 오디오 파일 생성
        tts = gTTS(text=text, lang="ko")

        # 메모리에 오디오 파일 저장
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        return send_file(
            audio_buffer,
            mimetype="audio/mp3",
            as_attachment=True,
            download_name="speech.mp3",
        )

    except Exception as e:
        logger.error(f"TTS 처리 중 오류 발생: {str(e)}")
        return jsonify({"error": "음성 변환 중 오류가 발생했습니다."}), 500


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"status": "error", "message": "메시지가 없습니다."}), 400

        user_message = data["message"]
        is_private = request.headers.get("X-Private-Mode") == "true"

        # 현재 세션 가져오기
        chat_session = get_current_session()

        # 시스템 메시지 설정
        style_instruction = AI_STYLE_SETTINGS[chat_session.get_style()]["instruction"]
        persona_instruction = AI_PERSONAS[chat_session.get_persona()]["instruction"]
        system_message = f"{style_instruction}\n{persona_instruction}"

        # 사용자 메시지 추가
        chat_session.add_message("user", user_message)

        try:
            # OpenAI API 호출
            messages = [{"role": "system", "content": system_message}]
            messages.extend(
                [
                    {"role": m["role"], "content": m["content"]}
                    for m in chat_session.get_context()
                ]
            )

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=4000,  # 토큰 수 증가
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stream=False,  # 스트리밍 비활성화
            )

            # AI 응답 처리
            ai_message = response.choices[0].message.content.strip()

            # 응답이 비어있는지 확인
            if not ai_message:
                logger.error("Empty response from OpenAI API")
                return (
                    jsonify({"status": "error", "message": "AI 응답이 비어있습니다."}),
                    500,
                )

            # 응답 길이 로깅
            logger.debug(f"Response length: {len(ai_message)}")
            logger.debug(f"Response preview: {ai_message[:100]}...")

            chat_session.add_message("assistant", ai_message)

            # 비공개 모드가 아닐 때만 대화 내용 저장
            if not is_private:
                update_conversation_history("user", user_message)
                update_conversation_history("assistant", ai_message)

            return jsonify({"status": "success", "text": ai_message})

        except Exception as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            logger.error(traceback.format_exc())
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "AI 응답 생성 중 오류가 발생했습니다.",
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"General Error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": "서버 오류가 발생했습니다."}), 500


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


@app.route("/save_session", methods=["POST"])
def save_session():
    """Save current conversation session with a name"""
    try:
        # 비공개 모드 체크
        if request.headers.get("X-Private-Mode") == "true":
            return jsonify(
                {
                    "status": "error",
                    "message": "비공개 모드에서는 세션을 저장할 수 없습니다.",
                }
            )

        data = request.json
        session_name = data.get("name")

        if not session_name:
            return jsonify({"status": "error", "message": "세션 이름이 필요합니다."})

        # 파일명 생성 (타임스탬프 포함)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_name}_{timestamp}.json"
        filepath = os.path.join(SESSIONS_DIR, filename)

        # 세션 데이터 저장
        session_data = {
            "name": session_name,
            "timestamp": timestamp,
            "messages": get_conversation_history(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        return jsonify(
            {
                "status": "success",
                "message": "세션이 저장되었습니다.",
                "filename": filename,
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/list_sessions", methods=["GET"])
def list_sessions():
    """List all saved conversation sessions"""
    try:
        sessions = []
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(SESSIONS_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                    sessions.append(
                        {
                            "filename": filename,
                            "name": session_data["name"],
                            "timestamp": session_data["timestamp"],
                            "message_count": len(session_data["messages"]),
                        }
                    )

        return jsonify(
            {
                "status": "success",
                "sessions": sorted(
                    sessions, key=lambda x: x["timestamp"], reverse=True
                ),
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/load_session/<filename>", methods=["POST"])
def load_session(filename):
    """Load a saved conversation session"""
    try:
        # 비공개 모드 체크
        if request.headers.get("X-Private-Mode") == "true":
            return jsonify(
                {
                    "status": "error",
                    "message": "비공개 모드에서는 세션을 불러올 수 없습니다.",
                }
            )

        filepath = os.path.join(SESSIONS_DIR, filename)

        if not os.path.exists(filepath):
            return jsonify(
                {"status": "error", "message": "세션 파일을 찾을 수 없습니다."}
            )

        with open(filepath, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        # 현재 세션 업데이트
        chat_session.clear()
        for message in session_data["messages"]:
            chat_session.add_message(message["role"], message["content"])

        return jsonify(
            {
                "status": "success",
                "message": "세션을 불러왔습니다.",
                "messages": session_data["messages"],
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/delete_session/<filename>", methods=["POST"])
def delete_session(filename):
    """Delete a saved conversation session"""
    try:
        filepath = os.path.join(SESSIONS_DIR, filename)

        if not os.path.exists(filepath):
            return jsonify(
                {"status": "error", "message": "세션 파일을 찾을 수 없습니다."}
            )

        os.remove(filepath)

        return jsonify({"status": "success", "message": "세션이 삭제되었습니다."})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/get_chat_history", methods=["GET"])
def get_chat_history():
    """Get chat history based on current mode"""
    try:
        history = get_conversation_history()
        return jsonify({"status": "success", "messages": history})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/restore_session", methods=["POST"])
def restore_session():
    """일반 모드 세션 복원"""
    try:
        # 대화 내용 복원
        history = load_conversation_history()
        session["conversation_history"] = history

        # 설정 복원
        normal_chat_session.clear()

        # 스타일 설정 복원
        if "ai_style_settings" in session:
            style = session["ai_style_settings"].get("style", "normal")
            normal_chat_session.update_style(style)

        # 페르소나 설정 복원
        if "ai_persona" in session:
            persona = session["ai_persona"]
            normal_chat_session.update_persona(persona)

        # 대화 내용 복원
        for msg in history:
            normal_chat_session.add_message(msg["role"], msg["content"])

        print("\n=== 세션 복원 완료 ===")
        print(f"복원된 메시지 수: {len(history)}")
        print(f"현재 스타일: {normal_chat_session.get_style()}")
        print(f"현재 페르소나: {normal_chat_session.get_persona()}")

        return jsonify(
            {"status": "success", "message": "일반 모드 세션이 복원되었습니다."}
        )
    except Exception as e:
        print(f"세션 복원 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
