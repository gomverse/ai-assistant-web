import logging

logger = logging.getLogger(__name__)

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
