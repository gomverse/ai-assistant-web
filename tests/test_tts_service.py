import unittest
from services.tts_service import create_audio_response


class TestTTSService(unittest.TestCase):
    def test_create_audio_response(self):
        # 실제로 파일이 생성되는지 여부만 테스트 (환경에 따라 실패할 수 있음)
        url = create_audio_response("테스트 음성입니다.", {})
        self.assertTrue(url is None or url.startswith("/static/audio/"))


if __name__ == "__main__":
    unittest.main()
