# AI 개인비서 웹앱

이 프로젝트는 OpenAI GPT와 Naver TTS를 활용한 **AI 개인비서 웹 애플리케이션**입니다. 대화, 음성 변환, 대화 내보내기, 세션 관리 등 다양한 기능을 제공합니다.

## 주요 기능

- **AI와 자연스러운 대화**: GPT-4.1 nano 모델을 사용하여 실시간 대화 지원
- **음성 응답**: Naver TTS를 통해 AI 답변을 음성(mp3)으로 변환 및 재생
- **대화 내보내기**: 대화 내용을 TXT 또는 PDF 파일로 저장
- **대화 세션 관리**: 대화 세션 저장/불러오기/삭제 기능
- **AI 응답 길이 설정**: 간결/일반/상세 중 선택 가능
- **AI 페르소나 설정**: 친근한 친구, 전문가, 냉소적 스타일 중 선택
- **대화 내용 검색**: 키워드로 대화 내역 검색
- **다크모드 지원**: UI 테마 전환
- **알림 예약**: "30분 뒤 알림" 등 자연어로 알림 예약 가능

## 폴더 구조

- `app.py` : Flask 기반 백엔드 서버
- `app/templates/index.html` : 메인 프론트엔드 페이지 (Tailwind CSS, JS)
- `app/static/` : 정적 파일 (CSS, 폰트, 오디오 등)
- `data/` : 대화 기록, 세션, 내보내기 파일 저장
- `requirements.txt` : 필요 패키지 목록

## 설치 및 실행 방법

1. **필수 패키지 설치**
   ```bash
   pip install -r requirements.txt
   ```
2. **환경 변수 설정**
   - `.env` 파일에 아래 항목을 추가
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

## 참고 사항
- PDF 내보내기를 위해 `app/static/fonts/NanumGothic.ttf` 폰트가 필요합니다.
- Naver TTS 사용을 위해 NAVER API 키가 필요합니다.
- 알림 기능은 웹에서 예약 시간(예: "10분 뒤 알림")을 인식해 안내합니다.
- 대화 세션은 `data/sessions/`에 저장됩니다.

## 라이선스
- 본 프로젝트는 개인 학습 및 비영리 목적에 한해 자유롭게 사용 가능합니다.

---
문의 및 피드백은 이슈로 남겨주세요.

