# API 문서

AI 개인비서 웹앱의 REST API 엔드포인트에 대한 상세 문서입니다.

## 베이스 URL
```
http://localhost:5000
```

## 엔드포인트 목록

### 1. 메인 페이지
```http
GET /
```

**설명**: 메인 웹 애플리케이션 페이지를 반환합니다.

**응답**:
- **200 OK**: HTML 페이지

---

### 2. AI 대화 요청
```http
POST /ask
```

**설명**: AI와 대화를 요청하고 응답을 받습니다.

**요청 본문**:
```json
{
  "message": "사용자 메시지",
  "session_id": "세션 ID (선택사항)",
  "response_length": "brief|normal|detailed",
  "persona": "friendly|expert|sarcastic"
}
```

**파라미터**:
- `message` (string, 필수): 사용자의 질문이나 메시지
- `session_id` (string, 선택): 기존 세션 ID. 없으면 새 세션 생성
- `response_length` (string, 선택): 응답 길이 (`brief`, `normal`, `detailed`)
- `persona` (string, 선택): AI 페르소나 (`friendly`, `expert`, `sarcastic`)

**응답**:
```json
{
  "response": "AI의 응답 메시지",
  "audio_url": "/static/audio/response_xxx.mp3",
  "session_id": "세션_ID",
  "notification": "알림 메시지 (선택사항)"
}
```

**상태 코드**:
- **200 OK**: 성공
- **400 Bad Request**: 잘못된 요청 (메시지 누락 등)
- **500 Internal Server Error**: 서버 오류

---

### 3. 대화 내보내기
```http
POST /export
```

**설명**: 대화 내용을 파일로 내보냅니다.

**요청 본문**:
```json
{
  "format": "txt|pdf",
  "session_id": "세션_ID (선택사항)"
}
```

**파라미터**:
- `format` (string, 필수): 내보낼 파일 형식 (`txt` 또는 `pdf`)
- `session_id` (string, 선택): 특정 세션만 내보내기. 없으면 전체 대화

**응답**:
```json
{
  "download_url": "/data/exports/conversation_xxx.txt",
  "filename": "conversation_20231120_143025.txt"
}
```

**상태 코드**:
- **200 OK**: 성공
- **400 Bad Request**: 지원하지 않는 형식
- **500 Internal Server Error**: 파일 생성 오류

---

### 4. 대화 검색
```http
GET /search
```

**설명**: 대화 내용에서 키워드를 검색합니다.

**쿼리 파라미터**:
- `q` (string, 필수): 검색할 키워드
- `session_id` (string, 선택): 특정 세션에서만 검색

**예시**:
```
GET /search?q=파이썬&session_id=123_20231120_143025
```

**응답**:
```json
{
  "results": [
    {
      "timestamp": "2023-11-20T14:30:25",
      "user_message": "파이썬 문법에 대해 알려줘",
      "ai_response": "파이썬은 간결하고 읽기 쉬운 프로그래밍 언어입니다...",
      "session_id": "123_20231120_143025"
    }
  ],
  "total_count": 1
}
```

**상태 코드**:
- **200 OK**: 성공 (결과 없어도 200)
- **400 Bad Request**: 검색어 누락

---

### 5. 세션 목록 조회
```http
GET /sessions
```

**설명**: 저장된 모든 대화 세션 목록을 반환합니다.

**응답**:
```json
{
  "sessions": [
    {
      "session_id": "123_20231120_143025",
      "session_name": "파이썬 학습",
      "created_at": "2023-11-20T14:30:25",
      "message_count": 15,
      "last_message": "감사합니다!"
    }
  ]
}
```

**상태 코드**:
- **200 OK**: 성공

---

### 6. 새 세션 생성
```http
POST /sessions
```

**설명**: 새로운 대화 세션을 생성합니다.

**요청 본문**:
```json
{
  "session_name": "세션 이름 (선택사항)"
}
```

**응답**:
```json
{
  "session_id": "123_20231120_143025",
  "session_name": "새 대화",
  "created_at": "2023-11-20T14:30:25"
}
```

**상태 코드**:
- **201 Created**: 성공
- **500 Internal Server Error**: 세션 생성 오류

---

### 7. 세션 불러오기
```http
GET /sessions/{session_id}
```

**설명**: 특정 세션의 대화 내용을 불러옵니다.

**경로 파라미터**:
- `session_id` (string, 필수): 불러올 세션의 ID

**응답**:
```json
{
  "session_id": "123_20231120_143025",
  "session_name": "파이썬 학습",
  "conversations": [
    {
      "timestamp": "2023-11-20T14:30:25",
      "user_message": "안녕하세요",
      "ai_response": "안녕하세요! 무엇을 도와드릴까요?"
    }
  ]
}
```

**상태 코드**:
- **200 OK**: 성공
- **404 Not Found**: 세션을 찾을 수 없음

---

### 8. 세션 삭제
```http
DELETE /sessions/{session_id}
```

**설명**: 특정 세션을 삭제합니다.

**경로 파라미터**:
- `session_id` (string, 필수): 삭제할 세션의 ID

**응답**:
```json
{
  "message": "세션이 성공적으로 삭제되었습니다.",
  "deleted_session_id": "123_20231120_143025"
}
```

**상태 코드**:
- **200 OK**: 성공
- **404 Not Found**: 세션을 찾을 수 없음

---

### 9. 세션 이름 변경
```http
PUT /sessions/{session_id}
```

**설명**: 세션의 이름을 변경합니다.

**경로 파라미터**:
- `session_id` (string, 필수): 수정할 세션의 ID

**요청 본문**:
```json
{
  "session_name": "새로운 세션 이름"
}
```

**응답**:
```json
{
  "message": "세션 이름이 변경되었습니다.",
  "session_id": "123_20231120_143025",
  "new_name": "새로운 세션 이름"
}
```

**상태 코드**:
- **200 OK**: 성공
- **400 Bad Request**: 잘못된 세션명
- **404 Not Found**: 세션을 찾을 수 없음

---

## 오류 응답 형식

모든 오류 응답은 다음 형식을 따릅니다:

```json
{
  "error": "오류 메시지",
  "code": "ERROR_CODE",
  "details": "상세 오류 정보 (선택사항)"
}
```

### 일반적인 오류 코드

- `INVALID_REQUEST`: 잘못된 요청 형식
- `MISSING_PARAMETER`: 필수 파라미터 누락
- `SESSION_NOT_FOUND`: 세션을 찾을 수 없음
- `API_ERROR`: 외부 API 오류 (OpenAI, Naver TTS)
- `FILE_ERROR`: 파일 생성/읽기 오류
- `INTERNAL_ERROR`: 서버 내부 오류

## 사용 예시

### JavaScript (Fetch API)

```javascript
// AI 대화 요청
async function askAI(message) {
  const response = await fetch('/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      response_length: 'normal',
      persona: 'friendly'
    })
  });
  
  const data = await response.json();
  return data;
}

// 세션 목록 조회
async function getSessions() {
  const response = await fetch('/sessions');
  const data = await response.json();
  return data.sessions;
}
```

### Python (requests)

```python
import requests

# AI 대화 요청
def ask_ai(message, session_id=None):
    payload = {
        'message': message,
        'response_length': 'normal',
        'persona': 'friendly'
    }
    if session_id:
        payload['session_id'] = session_id
    
    response = requests.post('http://localhost:5000/ask', json=payload)
    return response.json()

# 대화 내보내기
def export_conversation(format='txt', session_id=None):
    payload = {'format': format}
    if session_id:
        payload['session_id'] = session_id
    
    response = requests.post('http://localhost:5000/export', json=payload)
    return response.json()
```

## 인증

현재 버전에서는 인증이 구현되어 있지 않습니다. 프로덕션 환경에서는 적절한 인증 메커니즘을 추가하는 것을 권장합니다.

## 요청 제한

- 최대 요청 크기: 10MB
- 메시지 최대 길이: 4000자
- 세션명 최대 길이: 100자
- 동시 요청 제한: 사용자당 5개

## 변경 이력

### v1.1.0 (2023-11-20)
- 세션 관리 API 추가
- 대화 검색 기능 추가
- 오류 응답 형식 표준화

### v1.0.0 (2023-11-15)
- 초기 API 릴리스
- 기본 대화, 내보내기 기능
