"""
대화 세션 관리 서비스
"""

from typing import List, Dict, Any
import os
import json
from datetime import datetime


def save_session(
    history: List[Dict[str, Any]],
    session_name: str,
    sessions_dir: str = "data/sessions",
) -> str:
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


def list_sessions(sessions_dir: str = "data/sessions") -> List[Dict[str, Any]]:
    if not os.path.exists(sessions_dir):
        return []
    sessions = []
    for filename in os.listdir(sessions_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(sessions_dir, filename)
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
    sessions.sort(key=lambda x: x["timestamp"], reverse=True)
    return sessions


def load_session(
    filename: str, sessions_dir: str = "data/sessions"
) -> List[Dict[str, Any]]:
    filepath = os.path.join(sessions_dir, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError("해당 세션을 찾을 수 없습니다.")
    with open(filepath, "r", encoding="utf-8") as f:
        session_data = json.load(f)
    return session_data["messages"]


def delete_session(filename: str, sessions_dir: str = "data/sessions") -> None:
    filepath = os.path.join(sessions_dir, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
