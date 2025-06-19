from flask import Blueprint, render_template, request, jsonify, current_app
import logging
from .models import AI_STYLE_SETTINGS, AI_PERSONAS
from .services import generate_ai_response

main_bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/ask", methods=["POST"])
def ask():
    try:
        current_app.logger.debug("Received request at /ask endpoint")
        data = request.get_json()
        current_app.logger.debug(f"Request data: {data}")

        if not data:
            current_app.logger.error("No request data received")
            return jsonify({"status": "error", "error": "요청 데이터가 없습니다."}), 400

        message = data.get("message", "")
        settings = data.get("settings", {})
        current_app.logger.debug(f"Message: {message}")
        current_app.logger.debug(f"Settings: {settings}")

        if not message:
            current_app.logger.error("Empty message received")
            return jsonify({"status": "error", "error": "메시지가 비어있습니다."}), 400

        persona = settings.get("persona", "professional")
        response_length = settings.get("responseLength", "medium")
        current_app.logger.debug(
            f"Using persona: {persona}, response length: {response_length}"
        )

        try:
            response_text = generate_ai_response(message, persona, response_length)
            current_app.logger.debug(f"Generated response: {response_text}")

            return jsonify({"status": "success", "response": response_text})

        except Exception as api_error:
            current_app.logger.error(f"OpenAI API error: {str(api_error)}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "AI 서비스 연결에 문제가 발생했습니다.",
                    }
                ),
                500,
            )

    except Exception as e:
        current_app.logger.exception("Error in ask endpoint")
        error_response = {
            "status": "error",
            "error": f"서버 오류가 발생했습니다: {str(e)}",
        }
        current_app.logger.error(f"Sending error response: {error_response}")
        return jsonify(error_response), 500
