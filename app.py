from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import openai

# Load environment variables
load_dotenv()

# Initialize Flask app with correct template folder
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Ensure logs directory exists
os.makedirs("data/logs", exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.json
        user_input = data.get("question", "")

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 한국어를 사용하는 친절한 AI 개인비서입니다. 사용자의 일상적인 질문에 도움을 주세요.",
                },
                {"role": "user", "content": user_input},
            ],
        )

        # Extract the response
        assistant_response = response.choices[0].message.content

        # Log the conversation
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "assistant_response": assistant_response,
        }

        log_file = f'data/logs/conversation_{datetime.now().strftime("%Y%m%d")}.json'
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"대화 내용 저장 중 오류 발생: {e}")

        return jsonify({"response": assistant_response, "status": "success"})

    except Exception as e:
        return (
            jsonify(
                {
                    "error": str(e),
                    "status": "error",
                    "message": "서버 처리 중 오류가 발생했습니다.",
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(debug=True)
