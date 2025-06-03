class SpeechRecognitionHandler {
    constructor() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.error('Speech recognition is not supported in this browser');
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'ko-KR';  // 한국어 설정

        this.isListening = false;
        this.voiceButton = document.getElementById('voice-input-btn');
        this.voiceIcon = this.voiceButton.querySelector('i');
        
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
            userInput.value = text;

            // 폼 제출 처리
            handleFormSubmit();
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.updateButtonState('idle');
        };

        this.voiceButton.addEventListener('click', () => {
            if (this.isListening) {
                this.stopListening();
            } else {
                this.startListening();
            }
        });
    }

    updateButtonState(state) {
        // 모든 상태 클래스 제거
        this.voiceButton.classList.remove('listening');
        this.voiceIcon.className = 'fas fa-microphone';
        
        if (state === 'listening') {
            this.voiceButton.classList.add('listening');
        }
    }

    startListening() {
        try {
            this.recognition.start();
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            this.updateButtonState('idle');
        }
    }

    stopListening() {
        try {
            this.recognition.stop();
        } catch (error) {
            console.error('Error stopping speech recognition:', error);
        }
    }
}

// Initialize speech recognition when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new SpeechRecognitionHandler();
}); 