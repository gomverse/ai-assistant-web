// 비공개 모드 관리 모듈을 IIFE로 감싸 전역 오염 방지
(function() {
    // 실제 존재하는 버튼 id로 수정
    const disableButtons = [
        document.getElementById('exportChat'),
        document.getElementById('sessionBtn')
    ];
    
    class PrivateMode {
        constructor() {
            // DOM이 완전히 로드된 후에 초기화
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.initialize());
            } else {
                this.initialize();
            }
        }

        initialize() {
            this.isPrivate = false;
            this.privateModeBtn = document.getElementById('privateMode');
            this.body = document.body;
            this.disableButtons = disableButtons;
            this.normalModeMessages = null;
            this.privateModeMessages = null;
            this.normalModeSettings = {
                style: localStorage.getItem('ai_style') || 'normal',
                persona: localStorage.getItem('ai_persona') || 'professional'
            };

            if (!this.privateModeBtn) {
                console.error('Private mode button not found');
                return;
            }

            this.setupEventListeners();
        }

        setupEventListeners() {
            this.privateModeBtn.addEventListener('click', () => {
                this.togglePrivateMode();
            });
            
            // 브라우저 닫을 때 비공개 모드 상태 및 데이터 초기화
            window.addEventListener('beforeunload', () => {
                if (this.isPrivate) {
                    this.clearPrivateData();
                }
            });
        }

        clearPrivateData() {
            sessionStorage.clear();  // 비공개 모드의 모든 데이터 삭제
        }

        togglePrivateMode() {
            this.isPrivate = !this.isPrivate;
            this.privateModeBtn.classList.toggle('active', this.isPrivate);
            document.body.classList.toggle('private-mode', this.isPrivate);
            // 상태 동기화: 모드에 따라 세부 동작 분리
            if (this.isPrivate) {
                this.switchToPrivateMode();
            } else {
                this.switchToNormalMode();
            }
        }

        async switchToPrivateMode() {
            // 현재 일반 모드 대화 내용과 설정 저장
            this.normalModeMessages = this.getCurrentMessages();
            this.normalModeSettings = {
                style: localStorage.getItem('ai_style') || 'normal',
                persona: localStorage.getItem('ai_persona') || 'professional'
            };
            
            // 비공개 모드 초기화
            this.clearChat();
            this.resetPrivateSettings();
            
            const message = '비공개 모드가 활성화되었습니다. 이 모드에서는:\n- 대화 내용이 서버에 저장되지 않습니다.\n- 브라우저를 닫으면 모든 데이터가 삭제됩니다.\n- 대화 내용 저장 및 내보내기가 비활성화됩니다.';
            this.appendMessage('assistant', message);

            // 서버에 비공개 세션 시작 알림
            await fetch('/clear_context', {
                method: 'POST',
                headers: {
                    'X-Private-Mode': 'true'
                }
            });
        }

        async switchToNormalMode() {
            // 비공개 모드 데이터 삭제
            this.clearPrivateData();
            
            // 일반 모드 대화 내용과 설정 복원
            if (this.normalModeMessages) {
                this.setMessages(this.normalModeMessages);
            }
            
            // 일반 모드 설정 복원
            if (window.settings) {
                window.settings.updateStyle(this.normalModeSettings.style, false);
                window.settings.updatePersona(this.normalModeSettings.persona, false);
            }
            
            const message = '비공개 모드가 비활성화되었습니다. 일반 모드로 전환되었습니다.';
            this.appendMessage('assistant', message);
            
            // 서버에 일반 세션 복원 알림
            await fetch('/restore_session', {
                method: 'POST'
            });
        }

        resetPrivateSettings() {
            // 비공개 모드의 기본 설정
            sessionStorage.setItem('private_ai_style', 'normal');
            sessionStorage.setItem('private_ai_persona', 'professional');
            
            // Settings 객체에 반영
            if (window.settings) {
                window.settings.updateStyle('normal', false);
                window.settings.updatePersona('professional', false);
            }
        }

        getCurrentMessages() {
            const chatContainer = document.getElementById('chatContainer');
            return chatContainer.innerHTML;
        }

        setMessages(messages) {
            const chatContainer = document.getElementById('chatContainer');
            chatContainer.innerHTML = messages;
        }

        saveCurrentMessages() {
            if (this.isPrivate) {
                this.privateModeMessages = this.getCurrentMessages();
                sessionStorage.setItem('privateModeMessages', JSON.stringify(this.privateModeMessages));
            } else {
                this.normalModeMessages = this.getCurrentMessages();
            }
        }

        updateUI() {
            console.log('PrivateMode: Updating UI for state:', this.isPrivate);
            // 비공개 모드 표시 업데이트
            this.body.classList.toggle('private-mode-on', this.isPrivate);
            this.privateModeBtn.classList.toggle('private-mode-active', this.isPrivate);

            // 버튼 비활성화/활성화
            this.disableButtons.forEach(button => {
                if (button) {
                    if (this.isPrivate) {
                        button.classList.add('disabled-in-private');
                        button.setAttribute('disabled', 'disabled');
                    } else {
                        button.classList.remove('disabled-in-private');
                        button.removeAttribute('disabled');
                    }
                }
            });
        }

        saveState() {
            console.log('PrivateMode: Saving state:', this.isPrivate);
            if (this.isPrivate) {
                sessionStorage.setItem('privateMode', 'true');
            } else {
                sessionStorage.removeItem('privateMode');
            }
        }

        loadState() {
            const savedState = sessionStorage.getItem('privateMode');
            console.log('PrivateMode: Loading saved state:', savedState);
            if (savedState === 'true') {
                this.isPrivate = true;
                this.updateUI();
                this.resetPrivateSettings();
            }
        }

        clearChat() {
            console.log('PrivateMode: Clearing chat');
            const chatContainer = document.getElementById('chatContainer');
            if (chatContainer) {
                chatContainer.innerHTML = '';
            }
        }

        appendMessage(role, content) {
            console.log('PrivateMode: Appending message with role:', role);
            if (window.appendMessage) {
                window.appendMessage(role, content);
            }
        }

        isPrivateMode() {
            return this.isPrivate;
        }
    }

    // 인스턴스 한 번만 생성, 전역 오염 방지
    window.privateMode = new PrivateMode();
})();