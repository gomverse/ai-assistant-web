from flask import Flask, render_template, request, jsonify, send_file, session
import os
import json
from datetime import datetime, timedelta
from openai import OpenAI
import traceback
from navertts import NaverTTS
import secrets

# 프로젝트 모듈 import
from config import Config
from services.conversation_service import (
    save_conversation_history,
    load_conversation_history,
)
from services.tts_service import create_audio_response
from services.pdf_service import export_conversation_to_pdf, export_conversation_to_txt
from services.session_service import (
    save_session,
    list_sessions,
    load_session,
    delete_session,
)
from utils import (
    parse_notification_time,
    search_in_conversation,
    limit_conversation_history,
    validate_session_name,
)

# 설정 검증 및 디렉토리 생성
Config.validate_config()
Config.setup_directories()

# Initialize Flask app
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.secret_key = Config.SECRET_KEY
app.config["SESSION_TYPE"] = Config.SESSION_TYPE
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
    days=Config.PERMANENT_SESSION_LIFETIME_DAYS
)

# Initialize OpenAI client
client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Configure Naver TTS
if Config.NAVER_CLIENT_ID and Config.NAVER_CLIENT_SECRET:
    print("Naver TTS 설정이 확인되었습니다.")
    NaverTTS.configure(
        client_id=Config.NAVER_CLIENT_ID,
        client_secret=Config.NAVER_CLIENT_SECRET,
        speaker=Config.NAVER_TTS_SPEAKER,
    )


# 중복 함수 제거됨 - 서비스 모듈 사용


def get_conversation_history():
    """세션에서 대화 기록 가져오기 (없으면 파일에서 로드)"""
    if "conversation_history" not in session:
        session["conversation_history"] = load_conversation_history()
    return session["conversation_history"]


def update_conversation_history(role: str, content: str, audio_url: str = None):
    """대화 기록 업데이트 (세션 및 파일)"""
    try:
        history = get_conversation_history()
        message = {"role": role, "content": content}
        if audio_url and role == "assistant":
            message["audio_url"] = audio_url

        history.append(message)

        # 최대 개수 제한
        history = limit_conversation_history(history, Config.MAX_CONTEXT_MESSAGES)

        session["conversation_history"] = history
        session.modified = True

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


# parse_notification_time 함수 제거됨 - utils 모듈에서 import


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
    return jsonify({"status": "success", "settings": Config.AI_STYLE_SETTINGS})


@app.route("/update_ai_style", methods=["POST"])
def update_ai_style():
    """Update AI response length setting"""
    try:
        data = request.json
        response_length = data.get("response_length", "normal")

        # Validate setting
        if response_length not in Config.AI_STYLE_SETTINGS:
            return jsonify(
                {"status": "error", "message": "잘못된 응답 길이 설정입니다."}
            )

        # Save setting to session
        session["ai_style_settings"] = {"response_length": response_length}

        return jsonify(
            {
                "status": "success",
                "message": f"AI 응답 길이가 '{Config.AI_STYLE_SETTINGS[response_length]['name']}'(으)로 변경되었습니다.",
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
                for k, v in Config.AI_PERSONAS.items()
            },
        }
    )


@app.route("/update_persona", methods=["POST"])
def update_persona():
    """Update AI persona setting"""
    try:
        data = request.json
        persona = data.get("persona", "professional")  # 기본값은 전문가 모드

        if persona not in Config.AI_PERSONAS:
            return jsonify(
                {"status": "error", "message": "잘못된 페르소나 설정입니다."}
            )

        # Save setting to session
        session["ai_persona"] = persona

        return jsonify(
            {
                "status": "success",
                "message": f"AI 페르소나가 '{Config.AI_PERSONAS[persona]['name']}'(으)로 변경되었습니다.",
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


@app.route("/ask", methods=["POST"])
def ask():
    try:
        print("\n=== 새로운 요청 시작 ===")
        data = request.json
        user_input = data.get("question", "")
        print(f"사용자 입력: {user_input}")

        if not Config.OPENAI_API_KEY:
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
            f"{Config.AI_PERSONAS[current_persona]['instruction']}\n"
            f"{Config.AI_STYLE_SETTINGS[style_settings['response_length']]['instruction']}"
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
                model=Config.OPENAI_MODEL, messages=messages
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

        if export_format == "pdf":
            filepath = export_conversation_to_pdf(history)
            filename = os.path.basename(filepath)
        else:  # txt format
            filepath = export_conversation_to_txt(history)
            filename = os.path.basename(filepath)

        # Return file
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf" if export_format == "pdf" else "text/plain",
        )

    except Exception as e:
        print(f"대화 내보내기 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return jsonify(
            {
                "status": "error",
                "message": "대화 내용을 내보내는 중에 오류가 발생했습니다.",
            }
        )

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
        results = search_in_conversation(history, query)

        return jsonify({"status": "success", "results": results, "count": len(results)})

    except Exception as e:
        print(f"대화 검색 중 오류 발생: {str(e)}")
        traceback.print_exc()
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
def save_current_session():
    """Save current conversation session with a name"""
    try:
        data = request.json
        session_name = data.get("name")

        if not session_name or not validate_session_name(session_name):
            return jsonify(
                {"status": "error", "message": "유효하지 않은 세션 이름입니다."}
            )

        # Get current conversation history
        history = get_conversation_history()

        if not history:
            return jsonify(
                {"status": "error", "message": "저장할 대화 내용이 없습니다."}
            )

        # Save session using service
        filename = save_session(history, session_name)

        return jsonify(
            {
                "status": "success",
                "message": f"대화 세션 '{session_name}'이(가) 저장되었습니다.",
                "filename": filename,
            }
        )

    except Exception as e:
        print(f"세션 저장 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return jsonify(
            {"status": "error", "message": "세션 저장 중 오류가 발생했습니다."}
        )

    except Exception as e:
        print(f"세션 저장 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return jsonify(
            {"status": "error", "message": "세션 저장 중 오류가 발생했습니다."}
        )


@app.route("/list_sessions", methods=["GET"])
def list_saved_sessions():
    """List all saved conversation sessions"""
    try:
        sessions = list_sessions()
        return jsonify({"status": "success", "sessions": sessions})

    except Exception as e:
        print(f"세션 목록 조회 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return jsonify(
            {"status": "error", "message": "세션 목록 조회 중 오류가 발생했습니다."}
        )


@app.route("/load_session/<filename>", methods=["POST"])
def load_saved_session(filename):
    """Load a saved conversation session"""
    try:
        session_data = load_session(filename)

        # Update current session with loaded messages
        session["conversation_history"] = session_data["messages"]
        session.modified = True

        return jsonify(
            {
                "status": "success",
                "message": f"대화 세션 '{session_data['name']}'을(를) 불러왔습니다.",
                "messages": session_data["messages"],
            }
        )

    except FileNotFoundError:
        return jsonify({"status": "error", "message": "해당 세션을 찾을 수 없습니다."})
    except Exception as e:
        print(f"세션 불러오기 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return jsonify(
            {"status": "error", "message": "세션 불러오기 중 오류가 발생했습니다."}
        )


@app.route("/delete_session/<filename>", methods=["POST"])
def delete_saved_session(filename):
    """Delete a saved conversation session"""
    try:
        delete_session(filename)
        return jsonify({"status": "success", "message": "대화 세션이 삭제되었습니다."})

    except FileNotFoundError:
        return jsonify({"status": "error", "message": "해당 세션을 찾을 수 없습니다."})
    except Exception as e:
        print(f"세션 삭제 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return jsonify(
            {"status": "error", "message": "세션 삭제 중 오류가 발생했습니다."}
        )


if __name__ == "__main__":
    app.run(debug=True)
