"""
대화 기록 관리 서비스
"""

from typing import List, Dict, Any
import os
import json
import traceback


def save_conversation_history(history: List[Dict[str, Any]]) -> None:
    """대화 기록을 파일에 저장"""
    try:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        conversation_dir = os.path.join(base_dir, "..", "data", "conversations")
        conversation_file = os.path.join(conversation_dir, "conversation_history.json")
        os.makedirs(conversation_dir, exist_ok=True)
        with open(conversation_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"대화 내용 저장 중 오류 발생: {str(e)}")
        traceback.print_exc()


def load_conversation_history() -> List[Dict[str, Any]]:
    """파일에서 대화 기록 불러오기"""
    try:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        conversation_file = os.path.join(
            base_dir, "..", "data", "conversations", "conversation_history.json"
        )
        if os.path.exists(conversation_file):
            with open(conversation_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        print(f"대화 내용 불러오기 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return []
