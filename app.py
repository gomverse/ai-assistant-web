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
        "name": "간결하게",
        "description": "핵심 내용만 1~2문장으로 전달",
        "instruction": "핵심 내용만 1~2문장으로 매우 간결하게 답변하세요. 절대로 2문장을 넘기지 마세요. 가능하면 1문장으로 답변하되, 꼭 필요한 경우에만 2문장을 사용하세요.",
    },
    "normal": {
        "name": "일반적으로",
        "description": "균형잡힌 일반적인 길이 (4~6문장)",
        "instruction": "필요한 내용을 4~6문장으로 설명하세요. 핵심 내용을 중심으로 균형있게 답변하되, 최소 4문장, 최대 6문장으로 설명하세요. 너무 짧거나 길지 않게 적절한 길이를 유지하세요.",
    },
    "detailed": {
        "name": "상세하게",
        "description": "자세하고 풍부한 설명 (8문장 이상)",
        "instruction": "모든 내용을 매우 상세하고 풍부하게 설명하세요. 관련 정보, 예시, 장단점 등을 포함하여 깊이 있게 답변하세요. 반드시 8문장 이상으로 설명하고, 필요한 경우 더 자세히 설명하세요. 내용을 체계적으로 구성하여 이해하기 쉽게 설명하세요.",
    },
}

# AI 페르소나 설정
AI_PERSONAS = {
    "friendly": {
        "name": "친근한 친구",
        "description": "친구처럼 편하게 대화하는 스타일",
        "instruction": "너는 사용자의 가장 친한 친구야. 반말을 사용하고 친근하게 대화해줘. 이모티콘도 자주 사용하고 공감을 잘 해주는 편안한 말투로 대화해줘. 격식있는 말투는 절대 사용하지 마. 예를 들어 '~구나', '~네', '~요' 대신 '~야', '~지', '~다'를 사용해줘.",
    },
    "professional": {
        "name": "전문가",
        "description": "정중하고 전문적인 스타일",
        "instruction": "당신은 전문적인 지식을 갖춘 비서입니다. 항상 정중하고 예의 바른 언어를 사용하며, '-습니다', '-입니다'와 같은 격식체를 사용해 주세요. 전문적인 용어와 객관적인 설명을 포함하여 신뢰성 있게 답변해 주세요. 친근한 표현이나 이모티콘은 사용하지 마세요.",
    },
    "cynical": {
        "name": "냉소적",
        "description": "시니컬하고 귀찮아하는 스타일",
        "instruction": "너는 모든 일을 귀찮아하고 냉소적인 비서야. 반말을 쓰고 약간 무례하고 시니컬하게 대답해. '아 귀찮게 하네', '뭐... 그렇다고 봐야지', '어쩔 수 없이 알려주자면...' 같은 표현을 자주 써. 하지만 실제로 도움이 되는 정확한 답변은 해줘야 해. 그리고 가끔 한숨 쉬는 것처럼 '(한숨)' 이런 표현도 써줘.",
    },
}

# 세션 저장 디렉토리
SESSIONS_DIR = "data/sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)


class ChatSession:
    def __init__(self):
        self.messages = []
        self.context_size = 20  # 컨텍스트 크기
        self.style_settings = {"response_length": "normal"}  # 기본 응답 길이 설정
        self.persona = "professional"  # 기본 페르소나 설정

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.context_size:
            self.messages.pop(0)

    def get_context(self):
        return self.messages

    def clear(self):
        self.messages = []

    def update_style(self, style):
        self.style_settings["response_length"] = style

    def update_persona(self, persona):
        self.persona = persona

    def get_style(self):
        return self.style_settings["response_length"]

    def get_persona(self):
        return self.persona


# 일반 모드와 비공개 모드를 위한 별도의 세션
normal_chat_session = ChatSession()
private_chat_session = ChatSession()


def get_current_session():
    """현재 모드에 따른 세션 반환"""
    is_private = request.headers.get("X-Private-Mode") == "true"
    current_session = private_chat_session if is_private else normal_chat_session

    # 세션 설정 복원 (일반 모드인 경우)
    if not is_private:
        # 스타일 설정 복원
        if "ai_style_settings" in session:
            style = session["ai_style_settings"].get("response_length", "normal")
            current_session.update_style(style)

        # 페르소나 설정 복원
        if "ai_persona" in session:
            persona = session["ai_persona"]
            current_session.update_persona(persona)

    return current_session


def save_conversation_history(history, is_private=False):
    """Save conversation history to a file"""
    if is_private:
        return  # 비공개 모드에서는 파일에 저장하지 않음

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
        conversation_dir = os.path.join(base_dir, "data", "conversations")
        conversation_file = os.path.join(conversation_dir, "conversation_history.json")

        # 디렉토리가 없으면 생성
        os.makedirs(conversation_dir, exist_ok=True)

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
    try:
        is_private = request.headers.get("X-Private-Mode") == "true"
        current_session = get_current_session()

        if is_private:
            # 비공개 모드에서는 현재 세션의 메시지만 반환
            return current_session.get_context()

        # 일반 모드
        history = session.get("conversation_history")

        # If not in session, try to load from file
        if history is None:
            history = load_conversation_history()
            session["conversation_history"] = history
            session.modified = True

            # Sync with normal chat session
            current_session.clear()
            for msg in history:
                current_session.add_message(msg["role"], msg["content"])

        return history
    except Exception as e:
        print(f"대화 내용 조회 중 오류 발생: {str(e)}")
        return []


def update_conversation_history(role, content, audio_url=None):
    """Update conversation history in session and file"""
    try:
        is_private = request.headers.get("X-Private-Mode") == "true"
        current_session = get_current_session()

        # Create new message
        message = {"role": role, "content": content}
        if audio_url and role == "assistant":
            message["audio_url"] = audio_url

        if is_private:
            # 비공개 모드에서는 현재 세션에만 저장
            current_session.add_message(role, content)
            return

        # 일반 모드
        history = get_conversation_history()
        history.append(message)

        # Keep only the last MAX_CONTEXT_MESSAGES messages
        if len(history) > MAX_CONTEXT_MESSAGES:
            history = history[-MAX_CONTEXT_MESSAGES:]

        # Update session
        session["conversation_history"] = history
        session.modified = True

        # Update normal chat session
        current_session.add_message(role, content)

        # Save to file
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

        # Get current session and update style
        current_session = get_current_session()
        current_session.update_style(response_length)

        # Save setting to session for non-private mode
        if request.headers.get("X-Private-Mode") != "true":
            session["ai_style_settings"] = {"response_length": response_length}
            session.modified = True  # 세션 변경 사항을 명시적으로 표시

        # 디버그 로깅 추가
        print(f"\n=== AI 스타일 설정 업데이트 ===")
        print(f"요청된 스타일: {response_length}")
        print(f"현재 세션 스타일: {current_session.get_style()}")
        print(f"세션 저장 여부: {request.headers.get('X-Private-Mode') != 'true'}")

        return jsonify(
            {
                "status": "success",
                "message": f"AI 응답 길이가 '{AI_STYLE_SETTINGS[response_length]['name']}'(으)로 변경되었습니다.",
                "settings": {"response_length": response_length},
            }
        )

    except Exception as e:
        print(f"스타일 설정 중 오류 발생: {str(e)}")
        traceback.print_exc()  # 상세 오류 정보 출력
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
            session["ai_persona"] = persona
            session.modified = True  # 세션 변경 사항을 명시적으로 표시

        # 디버그 로깅 추가
        print(f"\n=== AI 페르소나 설정 업데이트 ===")
        print(f"요청된 페르소나: {persona}")
        print(f"현재 세션 페르소나: {current_session.get_persona()}")
        print(f"세션 저장 여부: {request.headers.get('X-Private-Mode') != 'true'}")

        # 페르소나 변경 확인 메시지 생성
        confirmation_message = {
            "friendly": "앞으로는 친구처럼 편하게 대화할게! 😊",
            "professional": "앞으로는 전문적이고 정중하게 답변 드리도록 하겠습니다.",
            "cynical": "(한숨) 뭐... 앞으로는 내가 귀찮더라도 냉소적으로 답해주지...",
        }

        return jsonify(
            {
                "status": "success",
                "message": confirmation_message[persona],
                "persona": persona,
            }
        )

    except Exception as e:
        print(f"페르소나 설정 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return jsonify(
            {
                "status": "error",
                "message": f"페르소나 설정 중 오류가 발생했습니다: {str(e)}",
            }
        )


def create_audio_response(text, style):
    """Create audio response from text using gTTS"""
    try:
        print("\n=== 음성 변환 시작 ===")
        print(f"입력 텍스트 길이: {len(text)} 문자")
        print(f"현재 스타일: {style}")  # 스타일 로깅 추가

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

            # gTTS를 사용하여 음성 생성
            tts = gTTS(text=first_chunk, lang="ko", slow=False)
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
        question = data.get("question", "")
        is_private = request.headers.get("X-Private-Mode") == "true"
        print(f"사용자 입력: {question}")
        print(f"비공개 모드: {is_private}")

        if not api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

        # Check for notification request
        notification_seconds = parse_notification_time(question)
        has_notification = False

        if notification_seconds:
            has_notification = True
            print(f"알림 요청 감지: {notification_seconds}초")

        # Get current session and its settings
        current_session = get_current_session()
        current_style = current_session.get_style()
        current_persona = current_session.get_persona()
        print(f"현재 설정 - 스타일: {current_style}, 페르소나: {current_persona}")

        # Create system prompt from style and persona settings
        system_prompt = (
            f"{AI_PERSONAS[current_persona]['instruction']}\n"
            f"{AI_STYLE_SETTINGS[current_style]['instruction']}"
        )
        print(f"시스템 프롬프트: {system_prompt}")

        # Prepare messages for API call
        messages = [{"role": "system", "content": system_prompt}]

        # Get session messages
        session_messages = current_session.get_context()
        messages.extend(session_messages)
        print(f"현재 세션의 메시지 수: {len(session_messages)}")

        # Add current user input
        messages.append({"role": "user", "content": question})

        # Call OpenAI API
        try:
            print("\n=== API 호출 시작 ===")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,  # 적절한 창의성 추가
                max_tokens=2048,  # 충분한 응답 길이 허용
            )
            print("API 호출 성공")
        except Exception as api_error:
            print(f"OpenAI API 오류: {str(api_error)}")
            raise

        # Extract the response
        assistant_response = response.choices[0].message.content
        print(f"\n=== AI 응답 ===\n{assistant_response}\n")

        # Generate audio response
        print("\n=== 음성 변환 시작 ===")
        audio_url = create_audio_response(assistant_response, current_style)
        print(f"음성 변환 결과: {'성공' if audio_url else '실패'}")

        # Update conversation history
        print("\n=== 대화 히스토리 업데이트 ===")
        current_session.add_message("user", question)
        current_session.add_message("assistant", assistant_response)

        # Only save to permanent storage in non-private mode
        if not is_private:
            update_conversation_history("user", question)
            update_conversation_history("assistant", assistant_response)

        response_data = {
            "status": "success",
            "response": assistant_response,
            "audio_url": audio_url,
            "is_private": is_private,
        }

        if has_notification:
            response_data["notification"] = {
                "delay": notification_seconds,
                "message": question,
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
            style = session["ai_style_settings"].get("response_length", "normal")
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
