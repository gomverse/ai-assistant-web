"""
대화 세션 관리 서비스
"""

from typing import List, Dict, Any
import os
import json
from datetime import datetime
from config import Config


def save_session(
    history: List[Dict[str, Any]], session_name: str, sessions_dir: str = None
) -> str:
    """세션을 저장하고 파일명 반환"""
    if sessions_dir is None:
        sessions_dir = Config.SESSIONS_DIR
    os.makedirs(sessions_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{session_name}_{timestamp}.json"
    filepath = os.path.join(sessions_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            {"name": session_name, "timestamp": timestamp, "messages": history},
            f,
            ensure_ascii=False,
            indent=2,
        )

    return filename


def list_sessions(sessions_dir: str = None) -> List[Dict[str, Any]]:
    """저장된 모든 세션 목록 반환"""
    if sessions_dir is None:
        sessions_dir = Config.SESSIONS_DIR
    if not os.path.exists(sessions_dir):
        return []

    sessions = []
    for filename in os.listdir(sessions_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(sessions_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                    sessions.append(
                        {
                            "filename": filename,
                            "name": session_data["name"],
                            "timestamp": session_data["timestamp"],
                            "message_count": len(session_data["messages"]),
                        }
                    )
            except (json.JSONDecodeError, KeyError) as e:
                print(f"세션 파일 읽기 오류 {filename}: {e}")
                continue

    sessions.sort(key=lambda x: x["timestamp"], reverse=True)
    return sessions


def load_session(filename: str) -> Dict[str, Any]:
    """세션을 로드하고 세션 데이터 반환"""
    filepath = os.path.join(Config.SESSIONS_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError("해당 세션을 찾을 수 없습니다.")

    with open(filepath, "r", encoding="utf-8") as f:
        session_data = json.load(f)
    return session_data


def delete_session(filename: str) -> None:
    """세션 파일 삭제"""
    filepath = os.path.join(Config.SESSIONS_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    else:
        raise FileNotFoundError("해당 세션을 찾을 수 없습니다.")


def load_session(filename: str, sessions_dir: str = None) -> List[Dict[str, Any]]:
    if sessions_dir is None:
        sessions_dir = Config.SESSIONS_DIR
    filepath = os.path.join(sessions_dir, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError("해당 세션을 찾을 수 없습니다.")
    with open(filepath, "r", encoding="utf-8") as f:
        session_data = json.load(f)
    return session_data["messages"]


def delete_session(filename: str, sessions_dir: str = None) -> None:
    if sessions_dir is None:
        sessions_dir = Config.SESSIONS_DIR
    filepath = os.path.join(sessions_dir, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
