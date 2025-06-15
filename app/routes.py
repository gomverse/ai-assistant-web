from flask import render_template, request, jsonify
import logging
from openai import OpenAI
import os
from . import app

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    try:
        logger.debug("Received request at /ask endpoint")
        data = request.get_json()
        logger.debug(f"Request data: {data}")

        if not data:
            logger.error("No request data received")
            return jsonify({"status": "error", "error": "요청 데이터가 없습니다."}), 400

        message = data.get("message", "")
        settings = data.get("settings", {})
        logger.debug(f"Message: {message}")
        logger.debug(f"Settings: {settings}")

        if not message:
            logger.error("Empty message received")
            return jsonify({"status": "error", "error": "메시지가 비어있습니다."}), 400

        # AI 설정
        persona = settings.get("persona", "professional")
        response_length = settings.get("responseLength", "medium")
        logger.debug(f"Using persona: {persona}, response length: {response_length}")

        # 시스템 메시지 설정
        system_messages = {
            "professional": "당신은 전문가입니다. 명확하고 정확하게 답변하세요. 전문 용어를 적절히 사용하되 이해하기 쉽게 설명하세요. 답변 시 적절히 단락을 나누고, 가독성 좋게 설명하세요.",
            "friendly": "당신은 친근한 대화 상대입니다. 편안하고 친근한 어조로 대화하세요. 이모티콘을 적절히 사용해도 좋습니다. 답변 시 적절히 단락을 나누고, 가독성 좋게 설명하세요.",
            "creative": "당신은 창의적인 사고가 가능한 AI입니다. 새롭고 독창적인 관점에서 답변하세요. 다양한 시각과 아이디어를 제시하세요. 답변 시 적절히 단락을 나누고, 가독성 좋게 설명하세요.",
        }

        # 응답 길이 설정
        max_tokens = {"short": 300, "medium": 1000, "long": 2000}

        try:
            # GPT API 호출
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": system_messages.get(
                            persona, system_messages["professional"]
                        ),
                    },
                    {"role": "user", "content": message},
                ],
                max_tokens=max_tokens.get(response_length, max_tokens["medium"]),
                temperature=0.7,
                top_p=1.0,
            )

            # API 응답에서 텍스트 추출
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"Generated response: {response_text}")

            return jsonify({"status": "success", "response": response_text})

        except Exception as api_error:
            logger.error(f"OpenAI API error: {str(api_error)}")
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
        logger.exception("Error in ask endpoint")
        error_response = {
            "status": "error",
            "error": f"서버 오류가 발생했습니다: {str(e)}",
        }
        logger.error(f"Sending error response: {error_response}")
        return jsonify(error_response), 500
