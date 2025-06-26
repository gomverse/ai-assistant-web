# AI 개인비서 웹앱

이 프로젝트는 AI를 이용해서 제작한 **AI 개인비서 웹 애플리케이션**입니다. 
대화, 음성 변환, 대화 내보내기, 세션 관리 등 다양한 기능을 제공합니다.

## 주요 기능

- **AI와 자연스러운 대화**: GPT-4.1 nano 모델을 사용하여 실시간 대화 지원
- **음성 응답**: Naver TTS를 통해 AI 답변을 음성으로 변환 및 재생
- **대화 내보내기**: 대화 내용을 TXT 또는 PDF 파일로 저장
- **대화 세션 관리**: 대화 세션 저장/불러오기/삭제 기능
- **AI 응답 길이 설정**: 간결/일반/상세 중 선택 가능
- **AI 페르소나 설정**: 친근한 친구, 전문가, 냉소적 스타일 중 선택
- **대화 내용 검색**: 키워드로 대화 내역 검색
- **다크모드 지원**: UI 테마 전환
- **알림 예약**: "30분 뒤 알림" 등 자연어로 알림 예약 가능

## 프로젝트 구조

### 메인 파일들
- `app.py` : Flask 기반 백엔드 서버 (메인 애플리케이션)
- `config.py` : 환경 설정, 경로, 상수 등 통합 관리
- `utils.py` : 공통 유틸리티 함수들
- `requirements.txt` : 필요 패키지 목록

### 서비스 모듈 (`services/`)
- `conversation_service.py` : AI 대화 처리 및 대화 기록 관리
- `tts_service.py` : 텍스트 음성 변환 (Naver TTS)
- `pdf_service.py` : PDF 파일 생성 및 내보내기
- `session_service.py` : 대화 세션 관리 (저장/불러오기/삭제)

### 프론트엔드 (`app/`)
- `templates/index.html` : 메인 프론트엔드 페이지 (Tailwind CSS, JavaScript)
- `static/` : 정적 파일들 (CSS, 폰트, 생성된 오디오 파일 등)

### 데이터 및 테스트
- `data/` : 대화 기록, 세션, 내보내기 파일 저장
- `tests/` : 단위 테스트 파일들 (pytest 기반)

## 설치 및 실행 방법

1. **필수 패키지 설치**
   ```bash
   pip install -r requirements.txt
   ```

2. **환경 변수 설정**
   - `.env` 파일에 아래 항목을 추가:
     ```env
     OPENAI_API_KEY=여기에_본인_API_키
     NAVER_CLIENT_ID=네이버_클라이언트_ID
     NAVER_CLIENT_SECRET=네이버_클라이언트_시크릿
     ```

3. **서버 실행**
   ```bash
   python app.py
   ```
   - 기본 주소: http://localhost:5000

## 개발 및 테스트

### 테스트 실행
```bash
# 모든 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_conversation_service.py

# 테스트 커버리지 확인
pytest --cov=services
```

### 개발 모드 실행
```bash
# 디버그 모드로 실행 (자동 재시작)
python app.py --debug
```

## 아키텍처

이 프로젝트는 **모듈화된 서비스 아키텍처**를 채택하여 유지보수성과 확장성을 높였습니다:

- **설정 통합**: `config.py`에서 모든 환경변수, 경로, 상수를 중앙 관리
- **서비스 분리**: 각 기능별로 독립적인 서비스 모듈로 분리
- **타입 힌트**: 모든 함수에 타입 힌트 적용으로 코드 안정성 향상
- **예외 처리**: 체계적인 예외 처리 및 로깅
- **테스트 코드**: 각 서비스별 단위 테스트 제공

## 참고 사항
- PDF 내보내기를 위해 `app/static/fonts/NanumGothic.ttf` 폰트가 필요합니다.
- Naver TTS 사용을 위해 NAVER API 키가 필요합니다.
- 알림 기능은 웹에서 예약 시간(예: "10분 뒤 알림")을 인식해 안내합니다.
- 대화 세션은 `data/sessions/`에 저장됩니다.

- Cursor, Chat gpt, Github Copilot
- GPT 4o, GPT 4.1 Gemini 2.5 Pro, Claude Sonnet 4

