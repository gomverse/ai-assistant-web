"""
애플리케이션 설정 관리
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class Config:
    """애플리케이션 설정 클래스"""

    # Flask 설정
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    SESSION_TYPE = "filesystem"
    PERMANENT_SESSION_LIFETIME_DAYS = 5

    # OpenAI 설정
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4.1-nano"

    # Naver TTS 설정
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
    NAVER_TTS_SPEAKER = "nara"

    # 파일 경로 설정
    DATA_DIR = "data"
    CONVERSATIONS_DIR = os.path.join(DATA_DIR, "conversations")
    SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
    EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
    LOGS_DIR = os.path.join(DATA_DIR, "logs")
    AUDIO_DIR = os.path.join("app", "static", "audio")
    FONTS_DIR = os.path.join("app", "static", "fonts")

    # 대화 설정
    MAX_CONTEXT_MESSAGES = 20
    MAX_TTS_LENGTH = 3000

    # AI 응답 길이 설정
    AI_STYLE_SETTINGS: Dict[str, Dict[str, Any]] = {
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
    AI_PERSONAS: Dict[str, Dict[str, Any]] = {
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

    @classmethod
    def validate_config(cls) -> bool:
        """설정 유효성 검사"""
        if not cls.OPENAI_API_KEY:
            print("경고: OPENAI_API_KEY가 설정되지 않았습니다!")
            return False

        if not cls.NAVER_CLIENT_ID or not cls.NAVER_CLIENT_SECRET:
            print("경고: Naver TTS 설정이 되어있지 않습니다!")
            return False

        return True

    @classmethod
    def setup_directories(cls):
        """필요한 디렉토리 생성"""
        dirs = [
            cls.CONVERSATIONS_DIR,
            cls.SESSIONS_DIR,
            cls.EXPORTS_DIR,
            cls.LOGS_DIR,
            cls.AUDIO_DIR,
        ]

        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
