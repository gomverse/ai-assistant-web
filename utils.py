"""
유틸리티 함수들
"""

import re
from typing import Optional, List, Dict, Any


def parse_notification_time(text: str) -> Optional[int]:
    """자연어에서 알림 시간을 파싱하여 초 단위로 반환"""
    time_pattern = r"(\d+)\s*(분|초|시간)\s*뒤"
    match = re.search(time_pattern, text)
    if not match:
        return None

    number = int(match.group(1))
    unit = match.group(2)

    # 초 단위로 변환
    if unit == "초":
        return number
    elif unit == "분":
        return number * 60
    elif unit == "시간":
        return number * 3600

    return None


def search_in_conversation(
    history: List[Dict[str, Any]], query: str
) -> List[Dict[str, Any]]:
    """대화 기록에서 키워드 검색"""
    if not query.strip():
        return []

    results = []
    for i, msg in enumerate(history):
        if re.search(query, msg["content"], re.IGNORECASE):
            # 검색 결과에 앞뒤 문맥 포함
            context = {
                "before": history[i - 1] if i > 0 else None,
                "match": msg,
                "after": history[i + 1] if i < len(history) - 1 else None,
                "index": i,
            }
            results.append(context)

    return results


def limit_conversation_history(
    history: List[Dict[str, Any]], max_messages: int
) -> List[Dict[str, Any]]:
    """대화 기록을 최대 개수로 제한"""
    if len(history) > max_messages:
        return history[-max_messages:]
    return history


def validate_session_name(name: str) -> bool:
    """세션 이름 유효성 검사"""
    if not name or not name.strip():
        return False
    # 파일명으로 사용할 수 없는 문자 확인
    invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    return not any(char in name for char in invalid_chars)


def sanitize_filename(filename: str) -> str:
    """파일명에서 사용할 수 없는 문자 제거"""
    invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename.strip()
