// 전역 상태
let voiceState = {
    isEnabled: false,
    utterance: null
};

// AI 설정 상태
const aiSettings = {
    persona: 'professional', // professional, friendly, creative
    responseLength: 'medium' // short, medium, long
};

// DOM이 로드된 후 초기화
document.addEventListener('DOMContentLoaded', initializeApp);

// 앱 초기화
function initializeApp() {
    // 필수 DOM 요소 가져오기
    const elements = {
        form: document.getElementById('questionForm'),
        userInput: document.getElementById('user-input'),
        chatMessages: document.getElementById('chatMessages'),
        loadingIndicator: document.getElementById('loadingIndicator'),
        voiceInputBtn: document.getElementById('voiceInput'),
        settingsBtn: document.getElementById('settingsToggle'),
        settingsMenu: document.getElementById('settingsMenu'),
        aiSettingsBtn: document.getElementById('aiSettings'),
        aiSettingsMenu: document.getElementById('aiSettingsMenu')
    };

    // 필수 요소 존재 여부 확인
    const requiredElements = ['form', 'userInput', 'chatMessages', 'loadingIndicator'];
    const missingElements = requiredElements.filter(key => !elements[key]);
    
    if (missingElements.length > 0) {
        console.error('Missing required DOM elements:', missingElements);
        return;
    }

    // 폼 제출 이벤트
    elements.form.addEventListener('submit', (e) => {
        e.preventDefault();
        handleFormSubmit();
    });

    // 텍스트 영역 자동 크기 조절
    elements.userInput.addEventListener('input', function() {
        adjustTextareaHeight(this);
    });

    // 키 이벤트 리스너
    elements.userInput.addEventListener('keypress', handleKeyPress);

    // 다크 모드 토글
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
        // 시스템 다크 모드 감지
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.classList.add('dark');
            updateThemeIcon(true);
        }
    }

    // 음성 출력 버튼 이벤트 리스너
    const voiceOutputBtn = document.getElementById('voiceOutput');
    if (voiceOutputBtn) {
        voiceOutputBtn.addEventListener('click', () => {
            voiceState.isEnabled = !voiceState.isEnabled;
            voiceOutputBtn.classList.toggle('active', voiceState.isEnabled);
            showNotification(
                voiceState.isEnabled ? '음성 출력이 활성화되었습니다.' : '음성 출력이 비활성화되었습니다.',
                'info'
            );
        });
    }

    // AI 설정 메뉴 토글 (옵셔널)
    if (elements.aiSettingsBtn && elements.aiSettingsMenu) {
        elements.aiSettingsBtn.addEventListener('click', () => {
            elements.aiSettingsMenu.classList.toggle('show');
            if (elements.settingsMenu) {
                elements.settingsMenu.classList.remove('show');
            }
        });
    }

    // 설정 메뉴 토글 (옵셔널)
    if (elements.settingsBtn && elements.settingsMenu) {
        elements.settingsBtn.addEventListener('click', () => {
            elements.settingsMenu.classList.toggle('show');
            if (elements.aiSettingsMenu) {
                elements.aiSettingsMenu.classList.remove('show');
            }
        });
    }

    // 메뉴 외부 클릭 시 닫기 (옵셔널)
    document.addEventListener('click', (event) => {
        if (elements.settingsMenu && elements.aiSettingsMenu) {
            const isClickInside = event.target.closest('#settingsToggle') || 
                                event.target.closest('#settingsMenu') ||
                                event.target.closest('#aiSettings') || 
                                event.target.closest('#aiSettingsMenu');

            if (!isClickInside) {
                elements.settingsMenu.classList.remove('show');
                elements.aiSettingsMenu.classList.remove('show');
            }
        }
    });

    // AI 설정 버튼 이벤트 리스너 (옵셔널)
    document.querySelectorAll('[data-persona]').forEach(button => {
        button.addEventListener('click', (e) => {
            const persona = e.target.closest('[data-persona]').dataset.persona;
            aiSettings.persona = persona;
            updateAISettingsUI();
            // 설정 메뉴 닫기
            if (elements.aiSettingsMenu) {
                elements.aiSettingsMenu.classList.remove('show');
            }
        });
    });

    document.querySelectorAll('[data-length]').forEach(button => {
        button.addEventListener('click', async (e) => {
            const length = e.target.closest('[data-length]').dataset.length;
            aiSettings.responseLength = length;
            updateAISettingsUI();

            // 서버에 스타일 변경 요청
            try {
                const response = await fetch('/update_style', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ style: length })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                if (data.status === 'success' && data.show_in_chat) {
                    // 채팅창에 메시지 표시
                    appendMessage('assistant', data.message);
                } else if (data.status === 'error') {
                    showNotification(data.message || '응답 길이 설정 변경 중 오류가 발생했습니다.', 'error');
                }
            } catch (error) {
                console.error('Style update error:', error);
                showNotification('응답 길이 설정 변경 중 오류가 발생했습니다.', 'error');
            }

            // 설정 메뉴 닫기
            if (elements.aiSettingsMenu) {
                elements.aiSettingsMenu.classList.remove('show');
            }
        });
    });

    // 시작 메시지 표시
    appendMessage('assistant', '안녕하세요! 무엇을 도와드릴까요?');
}

// 다크 모드 토글
function toggleTheme() {
    const isDark = document.documentElement.classList.toggle('dark');
    updateThemeIcon(isDark);
}

// 테마 아이콘 업데이트
function updateThemeIcon(isDark) {
    const icon = document.querySelector('.theme-toggle-icon');
    if (icon) {
        if (isDark) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            icon.classList.add('sun');
            icon.classList.remove('moon');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
            icon.classList.remove('sun');
            icon.classList.add('moon');
        }
    }
}

// 텍스트 영역 자동 크기 조절
function adjustTextareaHeight(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

// 키 이벤트 처리
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleFormSubmit();
    }
}

// AI 설정 UI 업데이트
function updateAISettingsUI() {
    document.querySelectorAll('[data-persona]').forEach(button => {
        if (button.dataset.persona === aiSettings.persona) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });

    document.querySelectorAll('[data-length]').forEach(button => {
        if (button.dataset.length === aiSettings.responseLength) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
}

// 폼 제출 처리
async function handleFormSubmit() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    if (!message) return;
    console.log('Submitting message:', message);
    appendMessage('user', message);
    userInput.value = '';
    userInput.disabled = true;
    userInput.style.height = 'auto';
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.classList.remove('hidden');
    }
    try {
        const settings = {
            persona: aiSettings.persona,
            responseLength: aiSettings.responseLength
        };
        console.log('Using settings:', settings);
        console.log('Sending request to server...');
        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ message, settings })
        });
        console.log('Received response status:', response.status);
        let data;
        const responseText = await response.text();
        console.log('Raw response:', responseText);
        try {
            data = JSON.parse(responseText);
            console.log('Parsed response data:', data);
        } catch (parseError) {
            console.error('JSON parse error:', parseError);
            console.error('Failed to parse response text:', responseText);
            showNotification('서버 응답을 파싱할 수 없습니다. 잠시 후 다시 시도해 주세요.', 'error');
            throw new Error('서버 응답을 파싱할 수 없습니다.');
        }
        if (!response.ok || data.status === 'error') {
            console.error('Server returned error:', data.error || response.statusText);
            showNotification(data.error || '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.', 'error');
            throw new Error(data.error || '서버 오류가 발생했습니다.');
        }
        if (!data || typeof data !== 'object') {
            console.error('Invalid response format:', data);
            showNotification('서버로부터 유효하지 않은 응답 형식을 받았습니다.', 'error');
            throw new Error('서버로부터 유효하지 않은 응답 형식을 받았습니다.');
        }
        if (!data.response || typeof data.response !== 'string') {
            console.error('Missing or invalid response message:', data);
            showNotification('서버 응답에 메시지가 없습니다.', 'error');
            throw new Error('서버 응답에 메시지가 없습니다.');
        }
        console.log('Adding AI response to chat');
        appendMessage('assistant', data.response);
    } catch (error) {
        console.error('Request failed:', error);
        appendMessage('error', `오류가 발생했습니다: ${error.message}`);
        // 네트워크 오류 등도 사용자에게 안내
        if (error.name === 'TypeError') {
            showNotification('네트워크 오류가 발생했습니다. 인터넷 연결을 확인해 주세요.', 'error');
        } else {
            showNotification(error.message || '알 수 없는 오류가 발생했습니다.', 'error');
        }
    } finally {
        userInput.disabled = false;
        if (loadingIndicator) {
            loadingIndicator.classList.add('hidden');
        }
        userInput.focus();
    }
}

// 메시지 엘리먼트 생성 함수 (HTML/JS 분리)
function createMessageElement(role, content, timeString) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <span class="message-text">${content}</span>
            <span class="message-time">${timeString}</span>
        </div>
    `;
    return messageDiv;
}

// 메시지 추가 함수
function appendMessage(role, content) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) {
        console.error('Chat messages container not found');
        return;
    }

    // 메시지 시간 포맷
    const now = new Date();
    const timeString = now.toLocaleTimeString('ko-KR', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
    });
    
    // 메시지 엘리먼트 생성 및 추가
    const messageDiv = createMessageElement(role, content, timeString);
    chatMessages.appendChild(messageDiv);

    // 애니메이션 적용
    requestAnimationFrame(() => {
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
        scrollToBottom();
    });
}

// 스크롤을 최하단으로 이동
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }
}

// 알림 표시 함수
function showNotification(message, type = 'info') {
    // 기존 알림 제거
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 스타일 추가
    Object.assign(notification.style, {
        position: 'fixed',
        bottom: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        padding: '12px 24px',
        borderRadius: '8px',
        backgroundColor: type === 'error' ? '#FF3B30' : 
                       type === 'success' ? '#34C759' : '#007AFF',
        color: 'white',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
        zIndex: '1000',
        animation: 'fadeInUp 0.3s ease'
    });
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// 음성 출력 함수
function playTextToSpeech(text) {
    if (!text) return;

    // 이전 음성 출력 중지
    if (voiceState.utterance) {
        window.speechSynthesis.cancel();
    }

    voiceState.utterance = new SpeechSynthesisUtterance(text);
    voiceState.utterance.lang = 'ko-KR';
    window.speechSynthesis.speak(voiceState.utterance);
}

// 전역 함수로 등록
window.appendMessage = appendMessage;
window.showNotification = showNotification;