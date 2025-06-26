import unittest
import os
from services.session_service import (
    save_session,
    list_sessions,
    load_session,
    delete_session,
)
from config import Config


class TestSessionService(unittest.TestCase):
    def setUp(self):
        """테스트 전 임시 세션 디렉토리 설정"""
        self.original_sessions_dir = Config.SESSIONS_DIR
        Config.SESSIONS_DIR = "data/sessions/test"
        # 테스트 디렉토리 생성
        os.makedirs(Config.SESSIONS_DIR, exist_ok=True)

    def tearDown(self):
        """테스트 후 설정 복원 및 정리"""
        # 테스트 파일들 정리
        if os.path.exists(Config.SESSIONS_DIR):
            for file in os.listdir(Config.SESSIONS_DIR):
                os.remove(os.path.join(Config.SESSIONS_DIR, file))
            os.rmdir(Config.SESSIONS_DIR)
        Config.SESSIONS_DIR = self.original_sessions_dir

    def test_session_lifecycle(self):
        history = [
            {"role": "user", "content": "테스트"},
            {"role": "assistant", "content": "테스트 응답"},
        ]

        # 세션 저장
        filename = save_session(history, "unittest", Config.SESSIONS_DIR)

        # 세션 목록 확인
        sessions = list_sessions(Config.SESSIONS_DIR)
        self.assertTrue(any(s["filename"] == filename for s in sessions))

        # 세션 로드
        session_data = load_session(filename, Config.SESSIONS_DIR)
        self.assertEqual(session_data, history)

        # 세션 삭제
        delete_session(filename, Config.SESSIONS_DIR)
        filepath = os.path.join(Config.SESSIONS_DIR, filename)
        self.assertFalse(os.path.exists(filepath))


if __name__ == "__main__":
    unittest.main()
