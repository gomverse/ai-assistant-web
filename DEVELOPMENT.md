# 개발 가이드

이 문서는 AI 개인비서 웹앱의 개발 환경 설정과 코드 구조에 대한 상세한 가이드입니다.

## 개발 환경 설정

### 1. 프로젝트 클론 및 의존성 설치

```bash
git clone <repository-url>
cd ai-assistant-web
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가:

```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Naver TTS API
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# Flask 설정 (선택사항)
FLASK_ENV=development
FLASK_DEBUG=True
```

### 3. 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 실행
pytest tests/test_conversation_service.py -v

# 커버리지 리포트 생성
pytest --cov=services --cov-report=html
```

## 코드 구조

### 설정 관리 (`config.py`)

모든 설정값들이 중앙화되어 관리됩니다:

- **환경 변수**: API 키, 서버 설정
- **경로 설정**: 데이터 저장 경로들
- **AI 설정**: 모델명, 페르소나, 응답 길이
- **UI 설정**: 스타일, 색상, 폰트

### 서비스 모듈들

#### `conversation_service.py`
- AI와의 대화 처리
- 대화 기록 저장/불러오기
- 대화 검색 기능

#### `tts_service.py`
- Naver TTS API 연동
- 음성 파일 생성 및 관리
- 오디오 파일 정리

#### `pdf_service.py`
- PDF 문서 생성
- 대화 내용 포매팅
- 한글 폰트 지원

#### `session_service.py`
- 대화 세션 관리
- 세션 저장/불러오기/삭제
- 세션 목록 조회

### 유틸리티 함수들 (`utils.py`)

- 알림 시간 파싱
- 대화 내용 검색
- 세션명 검증
- 파일 관리 유틸리티

## 개발 가이드라인

### 1. 코딩 스타일

- **타입 힌트**: 모든 함수 매개변수와 반환값에 타입 힌트 사용
- **Docstring**: 모든 함수에 설명 추가
- **예외 처리**: 적절한 예외 처리 및 로깅
- **네이밍**: 명확하고 일관된 변수/함수명 사용

### 2. 새로운 기능 추가

1. **서비스 모듈 생성**: `services/` 디렉토리에 새 서비스 추가
2. **테스트 코드 작성**: `tests/` 디렉토리에 테스트 파일 추가
3. **설정 추가**: 필요한 설정은 `config.py`에 추가
4. **라우트 연결**: `app.py`에서 새 엔드포인트 추가

### 3. 테스트 작성

```python
import pytest
from unittest.mock import patch, MagicMock
from services.your_service import YourService

def test_your_function():
    """테스트 함수 설명"""
    # Given
    service = YourService()
    
    # When
    result = service.your_function()
    
    # Then
    assert result is not None
```

## API 엔드포인트

### 주요 엔드포인트

- `GET /` - 메인 페이지
- `POST /ask` - AI 대화 요청
- `POST /export` - 대화 내보내기
- `GET /sessions` - 세션 목록 조회
- `POST /sessions` - 새 세션 생성
- `DELETE /sessions/<session_id>` - 세션 삭제

### 요청/응답 형식

```json
// POST /ask
{
  "message": "사용자 메시지",
  "session_id": "세션 ID (선택사항)",
  "response_length": "brief|normal|detailed",
  "persona": "friendly|expert|sarcastic"
}

// 응답
{
  "response": "AI 응답",
  "audio_url": "/static/audio/response_xxx.mp3",
  "session_id": "세션 ID"
}
```

## 배포

### 프로덕션 환경

1. **환경 변수 설정**
   ```bash
   export FLASK_ENV=production
   export FLASK_DEBUG=False
   ```

2. **WSGI 서버 사용**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

### Docker 배포

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 문제 해결

### 일반적인 문제들

1. **API 키 오류**: `.env` 파일의 API 키 확인
2. **포트 충돌**: 다른 포트 사용 (`python app.py --port 5001`)
3. **모듈 import 오류**: Python 경로 확인
4. **TTS 오류**: Naver API 키 및 네트워크 연결 확인

### 로그 확인

```bash
# 애플리케이션 로그
tail -f data/logs/app.log

# 디버그 모드에서 실행
python app.py --debug
```

## 기여하기

1. 이슈 생성 또는 기존 이슈 확인
2. 새 브랜치 생성 (`git checkout -b feature/new-feature`)
3. 변경사항 커밋 (`git commit -am 'Add new feature'`)
4. 브랜치에 푸시 (`git push origin feature/new-feature`)
5. Pull Request 생성

### 커밋 메시지 규칙

```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 스타일 변경
refactor: 코드 리팩토링
test: 테스트 코드 추가/수정
chore: 빌드 설정 등 기타 변경사항
```
