class SpeechRecognitionHandler {
    constructor() {
        // DOM이 완전히 로드된 후에 초기화
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }

    initialize() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.error('Speech recognition is not supported in this browser');
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'ko-KR';

        this.isListening = false;
        this.voiceButton = document.getElementById('voiceInput');
        
        if (!this.voiceButton) {
            console.error('Voice input button not found');
            return;
        }

        this.setupEventListeners();
    }

    setupEventListeners() {
        this.recognition.onstart = () => {
            this.isListening = true;
            this.updateButtonState('listening');
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.updateButtonState('idle');
        };

        this.recognition.onresult = (event) => {
            const last = event.results.length - 1;
            const text = event.results[last][0].transcript;
            
            // 입력 필드에 텍스트 설정
            const userInput = document.getElementById('user-input');
            if (userInput) {
                userInput.value = text;
                // 폼 제출 이벤트 생성
                const form = document.getElementById('questionForm');
                if (form) {
                    const submitEvent = new Event('submit', {
                        cancelable: true,
                        bubbles: true
                    });
                    form.dispatchEvent(submitEvent);
                }
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.updateButtonState('idle');

            if (event.error === 'not-allowed') {
                showNotification('마이크 사용 권한이 필요합니다. 브라우저 설정에서 마이크 권한을 허용해주세요.', 'error');
            } else {
                showNotification('음성 인식 중 오류가 발생했습니다.', 'error');
            }
        };

        this.voiceButton.addEventListener('click', async () => {
            if (this.isListening) {
                this.stopListening();
            } else {
                try {
                    // 마이크 권한 확인
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    stream.getTracks().forEach(track => track.stop());
                    this.startListening();
                } catch (error) {
                    console.error('Microphone permission denied:', error);
                    showNotification('마이크 사용 권한이 필요합니다. 브라우저 설정에서 마이크 권한을 허용해주세요.', 'error');
                }
            }
        });
    }

    updateButtonState(state) {
        if (!this.voiceButton) return;

        // 모든 상태 클래스 제거
        this.voiceButton.classList.remove('recording');
        
        if (state === 'listening') {
            this.voiceButton.classList.add('recording');
            showNotification('음성을 입력해 주세요.', 'info');
        }
    }

    startListening() {
        try {
            this.recognition.start();
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            this.updateButtonState('idle');
            showNotification('음성 인식을 시작할 수 없습니다.', 'error');
        }
    }

    stopListening() {
        try {
            this.recognition.stop();
        } catch (error) {
            console.error('Error stopping speech recognition:', error);
            showNotification('음성 인식을 중지할 수 없습니다.', 'error');
        }
    }
}

// 음성 인식 초기화
new SpeechRecognitionHandler(); 