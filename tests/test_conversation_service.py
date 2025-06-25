import unittest
from services.conversation_service import (
    save_conversation_history,
    load_conversation_history,
)


class TestConversationService(unittest.TestCase):
    def test_save_and_load(self):
        test_history = [
            {"role": "user", "content": "안녕"},
            {"role": "assistant", "content": "안녕하세요!"},
        ]
        save_conversation_history(test_history)
        loaded = load_conversation_history()
        self.assertEqual(loaded, test_history)


if __name__ == "__main__":
    unittest.main()
