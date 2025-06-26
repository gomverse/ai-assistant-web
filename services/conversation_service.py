"""
대화 기록 관리 서비스
"""

from typing import List, Dict, Any
import os
import json
import traceback
from config import Config


def save_conversation_history(history: List[Dict[str, Any]]) -> None:
    """대화 기록을 파일에 저장"""
    try:
        conversation_file = os.path.join(
            Config.CONVERSATIONS_DIR, "conversation_history.json"
        )
        os.makedirs(Config.CONVERSATIONS_DIR, exist_ok=True)

        print(f"저장할 대화 내용 수: {len(history)}")

        with open(conversation_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        print(f"대화 내용 저장 완료: {conversation_file}")
        print(f"파일 크기: {os.path.getsize(conversation_file)} bytes")
    except Exception as e:
        print(f"대화 내용 저장 중 오류 발생: {str(e)}")
        traceback.print_exc()


def load_conversation_history() -> List[Dict[str, Any]]:
    """파일에서 대화 기록 불러오기"""
    try:
        conversation_file = os.path.join(
            Config.CONVERSATIONS_DIR, "conversation_history.json"
        )

        print(f"대화 내용 파일 경로: {conversation_file}")

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
        traceback.print_exc()
        return []
