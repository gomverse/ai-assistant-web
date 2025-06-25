import unittest
import os
from services.session_service import (
    save_session,
    list_sessions,
    load_session,
    delete_session,
)


class TestSessionService(unittest.TestCase):
    def test_session_lifecycle(self):
        history = [
            {"role": "user", "content": "테스트"},
            {"role": "assistant", "content": "테스트 응답"},
        ]
        filename = save_session(history, "unittest", sessions_dir="data/sessions/test")
        sessions = list_sessions(sessions_dir="data/sessions/test")
        self.assertTrue(any(s["filename"] == filename for s in sessions))
        loaded = load_session(filename, sessions_dir="data/sessions/test")
        self.assertEqual(loaded, history)
        delete_session(filename, sessions_dir="data/sessions/test")
        self.assertFalse(os.path.exists(os.path.join("data/sessions/test", filename)))


if __name__ == "__main__":
    unittest.main()
