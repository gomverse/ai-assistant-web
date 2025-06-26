"""
TTS(음성 변환) 서비스
"""

from typing import Optional, Dict, Any
import os
import uuid
import traceback
from navertts import NaverTTS
from config import Config


def create_audio_response(text: str, style_settings: Dict[str, Any]) -> Optional[str]:
    """텍스트를 mp3로 변환하고 파일 경로 반환"""
    try:
        print(f"\n=== 음성 변환 시작 ===")
        print(f"입력 텍스트 길이: {len(text)} 문자")
        print(f"스타일 설정: {style_settings}")

        if not text or not text.strip():
            print("텍스트가 비어있습니다.")
            return None

        def split_text(text: str, max_length: int = Config.MAX_TTS_LENGTH):
            """텍스트를 적절한 크기로 분할"""
            sentences = []
            current_sentence = ""

            for char in text:
                current_sentence += char
                if char in [".", "!", "?"] and current_sentence.strip():
                    sentences.append(current_sentence.strip())
                    current_sentence = ""

            if current_sentence.strip():
                sentences.append(current_sentence.strip())

            full_text = " ".join(sentences)
            if len(full_text) > max_length:
                print(f"텍스트가 너무 깁니다. 처음 {max_length}자만 사용합니다.")
                return [full_text[:max_length]]
            return [full_text]

        text_chunks = split_text(text)
        print(f"텍스트가 {len(text_chunks)}개의 청크로 나뉘었습니다.")

        if not text_chunks:
            print("텍스트 청크가 없습니다.")
            return None

        # 첫 번째 청크 내용 출력 (디버깅용)
        print(f"\n첫 번째 청크 내용 (처음 100자):")
        print(text_chunks[0][:100])
        print(f"첫 번째 청크 길이: {len(text_chunks[0])} 문자")

        audio_filename = f"response_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(Config.AUDIO_DIR, audio_filename)

        # 오디오 디렉토리 생성
        os.makedirs(Config.AUDIO_DIR, exist_ok=True)

        try:
            first_chunk = text_chunks[0]
            if not first_chunk or not first_chunk.strip():
                print("첫 번째 청크가 비어있습니다.")
                return None

            print("\n=== TTS 변환 시도 ===")
            print(f"변환할 텍스트 (처음 100자): {first_chunk[:100]}")

            tts = NaverTTS(first_chunk)
            tts.save(audio_path)

            if os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"TTS 파일 생성 성공: {audio_path} (크기: {file_size} bytes)")
                return f"/static/audio/{audio_filename}"
            else:
                print(f"TTS 파일이 생성되지 않았습니다: {audio_path}")
                return None

        except Exception as e:
            print(f"\nTTS 생성 실패:")
            print(f"에러 타입: {type(e).__name__}")
            print(f"에러 메시지: {str(e)}")
            traceback.print_exc()
            return None

    except Exception as e:
        print(f"\n음성 변환 중 예외 발생:")
        print(f"에러 타입: {type(e).__name__}")
        print(f"에러 메시지: {str(e)}")
        traceback.print_exc()
        return None
