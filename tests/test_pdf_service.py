import unittest
import os
from services.pdf_service import export_conversation_to_pdf


class TestPDFService(unittest.TestCase):
    def test_export_conversation_to_pdf(self):
        history = [
            {"role": "user", "content": "안녕"},
            {"role": "assistant", "content": "안녕하세요!"},
        ]
        filepath = export_conversation_to_pdf(history, export_dir="data/exports/test")
        self.assertTrue(os.path.exists(filepath))
        os.remove(filepath)


if __name__ == "__main__":
    unittest.main()
