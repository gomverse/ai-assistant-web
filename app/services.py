from openai import OpenAI
import os
from .models import AI_STYLE_SETTINGS, AI_PERSONAS

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_ai_response(message, persona, response_length):
    system_messages = {
        "professional": AI_PERSONAS["professional"]["instruction"],
        "friendly": AI_PERSONAS["friendly"]["instruction"],
        "creative": AI_PERSONAS.get("creative", AI_PERSONAS["professional"]).get("instruction", ""),
    }
    max_tokens = {"short": 300, "medium": 1000, "long": 2000}
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_messages.get(persona, system_messages["professional"])},
            {"role": "user", "content": message},
        ],
        max_tokens=max_tokens.get(response_length, max_tokens["medium"]),
        temperature=0.7,
        top_p=1.0,
    )
    return response.choices[0].message.content.strip()
