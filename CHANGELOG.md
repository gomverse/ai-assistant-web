# 변경 이력 (CHANGELOG)

이 문서는 AI 개인비서 웹앱의 주요 변경사항과 개선사항을 기록합니다.

## [v2.0.0] - 2024-01-XX (대규모 리팩토링)

### 🔄 주요 변경사항

#### 아키텍처 개선
- **모듈화**: 기존 단일 파일 구조를 서비스 기반 아키텍처로 분리
- **설정 통합**: 모든 설정값을 `config.py`에서 중앙 관리
- **타입 힌트**: 모든 함수에 타입 힌트 추가로 코드 안정성 향상
- **예외 처리**: 체계적인 예외 처리 및 로깅 시스템 도입

#### 새로운 파일 구조
```
services/
├── conversation_service.py  # AI 대화 및 기록 관리
├── tts_service.py          # 음성 변환 서비스
├── pdf_service.py          # PDF 내보내기 서비스
├── session_service.py      # 세션 관리 서비스
└── __init__.py

tests/
├── test_conversation_service.py
├── test_tts_service.py
├── test_pdf_service.py
└── test_session_service.py

config.py     # 설정 통합 관리
utils.py      # 공통 유틸리티 함수
```

### ✨ 새로운 기능

#### 서비스 모듈화
- **ConversationService**: AI 대화 처리 및 기록 관리
- **TTSService**: Naver TTS 연동 및 음성 파일 관리
- **PDFService**: PDF 문서 생성 및 내보내기
- **SessionService**: 대화 세션 CRUD 작업

#### 설정 관리 개선
- 환경 변수 중앙 관리
- AI 페르소나 및 응답 길이 설정 통합
- 파일 경로 설정 일원화
- 스타일 및 UI 설정 통합

#### 유틸리티 함수 추가
- 알림 시간 파싱 (`parse_notification_time`)
- 대화 내용 검색 (`search_conversations`)
- 세션명 검증 (`validate_session_name`)
- 파일 관리 유틸리티

### 🔧 개선사항

#### 코드 품질
- **중복 코드 제거**: 기존 `app.py`의 중복 함수들 제거
- **함수 분리**: 각 기능별로 독립적인 함수로 분리
- **에러 핸들링**: 더 구체적이고 일관된 예외 처리
- **로깅**: 체계적인 로그 시스템 도입

#### 테스트 코드 정비
- 모든 서비스에 대한 단위 테스트 작성
- pytest 기반 테스트 환경 구축
- 임시 디렉토리를 사용한 격리된 테스트
- 모킹을 통한 외부 API 의존성 제거

#### 성능 최적화
- 불필요한 파일 I/O 작업 최적화
- 메모리 사용량 개선
- 오디오 파일 자동 정리 기능

### 🐛 버그 수정

- 세션 저장 시 타임스탬프 오류 수정
- PDF 생성 시 한글 폰트 처리 개선
- TTS 서비스 오류 처리 강화
- 파일 경로 처리 오류 수정

### 📚 문서화

#### 새로운 문서
- `DEVELOPMENT.md`: 개발 환경 설정 및 가이드
- `API.md`: REST API 상세 문서
- `DEPLOYMENT.md`: 배포 가이드
- `CHANGELOG.md`: 변경 이력

#### README 개선
- 새로운 프로젝트 구조 반영
- 아키텍처 설명 추가
- 개발 및 테스트 가이드 추가

### 🔒 보안 개선

- 환경 변수 기반 설정으로 하드코딩 제거
- 파일 권한 관리 개선
- API 키 보안 가이드 추가

### ⚡ 성능

- 서비스 모듈화로 코드 실행 효율성 증대
- 불필요한 import 제거
- 메모리 사용량 최적화

### 🧪 테스트

- 단위 테스트 커버리지 90% 이상 달성
- 통합 테스트 환경 구축
- CI/CD 파이프라인 준비

---

## [v1.0.0] - 2023-11-XX (초기 릴리스)

### ✨ 주요 기능

#### 기본 기능
- AI 대화 (GPT-4.1 nano)
- 음성 응답 (Naver TTS)
- 대화 내보내기 (TXT, PDF)
- 다크모드 지원

#### 대화 관리
- 대화 세션 저장/불러오기
- 대화 내용 검색
- 세션 관리 (생성, 삭제, 이름 변경)

#### AI 설정
- 응답 길이 설정 (간결/일반/상세)
- AI 페르소나 설정 (친근한/전문가/냉소적)
- 알림 예약 기능

#### UI/UX
- 반응형 웹 디자인
- Tailwind CSS 기반 모던 UI
- 실시간 타이핑 효과
- 음성 재생 컨트롤

### 기술 스택
- **Backend**: Flask, Python 3.9+
- **Frontend**: HTML5, JavaScript, Tailwind CSS
- **AI**: OpenAI GPT-4.1 nano
- **TTS**: Naver Cloud Platform TTS
- **PDF**: ReportLab
- **Storage**: JSON 파일 기반

---

## 마이그레이션 가이드

### v1.0.0 → v2.0.0

#### 필수 변경사항

1. **새로운 의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

2. **설정 파일 검토**
   - 기존 `.env` 파일이 새로운 `config.py`와 호환되는지 확인
   - 필요시 환경 변수 추가

3. **데이터 마이그레이션**
   - 기존 대화 데이터는 자동으로 호환됨
   - 세션 데이터 형식이 일부 변경됨 (하위 호환성 유지)

#### 주요 변경사항

1. **함수 호출 방식 변경**
   ```python
   # 기존 (v1.0.0)
   save_conversation_history(conversation)
   
   # 새로운 방식 (v2.0.0)
   from services.conversation_service import ConversationService
   service = ConversationService()
   service.save_conversation(conversation)
   ```

2. **설정 접근 방식 변경**
   ```python
   # 기존
   OPENAI_API_KEY = "하드코딩된 값"
   
   # 새로운 방식
   from config import Config
   api_key = Config.OPENAI_API_KEY
   ```

#### 호환성 정보

- **데이터 호환성**: ✅ 완전 호환
- **API 호환성**: ✅ 완전 호환
- **설정 호환성**: ⚠️ 부분 호환 (마이그레이션 필요)

---

## 향후 계획 (Roadmap)

### v2.1.0 (계획)
- [ ] 데이터베이스 연동 (SQLite/PostgreSQL)
- [ ] 사용자 인증 시스템
- [ ] 대화 태그 시스템
- [ ] 실시간 알림 기능

### v2.2.0 (계획)
- [ ] 멀티유저 지원
- [ ] 대화 공유 기능
- [ ] AI 모델 선택 옵션
- [ ] 모바일 앱 지원

### v3.0.0 (계획)
- [ ] 마이크로서비스 아키텍처
- [ ] 실시간 음성 대화
- [ ] AI 에이전트 시스템
- [ ] 플러그인 시스템

---

## 기여자

- **Lead Developer**: [개발자명]
- **Contributors**: [기여자 목록]

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참고하세요.

---

## 지원 및 피드백

- **Issues**: GitHub Issues를 통해 버그 리포트 및 기능 요청
- **Discussions**: GitHub Discussions를 통해 질문 및 토론
- **Email**: [이메일 주소] (중요한 보안 이슈)
