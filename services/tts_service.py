"""
TTS(음성 변환) 서비스
"""

from typing import Optional, Dict, Any
import os
import uuid
import traceback
from navertts import NaverTTS


def create_audio_response(text: str, style_settings: Dict[str, Any]) -> Optional[str]:
    """텍스트를 mp3로 변환하고 파일 경로 반환"""
    try:
        if not text or not text.strip():
            return None

        def split_text(text, max_length=3000):
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
                return [full_text[:max_length]]
            return [full_text]

        text_chunks = split_text(text)
        if not text_chunks:
            return None
        audio_filename = f"response_{uuid.uuid4()}.mp3"
        audio_path = os.path.join("app/static/audio", audio_filename)
        try:
            first_chunk = text_chunks[0]
            tts = NaverTTS(first_chunk)
            tts.save(audio_path)
            if os.path.exists(audio_path):
                return f"/static/audio/{audio_filename}"
            else:
                return None
        except Exception as e:
            traceback.print_exc()
            return None
    except Exception as e:
        traceback.print_exc()
        return None
