class PrivateMode {
    constructor() {
        console.log('PrivateMode: Initializing...');
        this.isPrivate = false;
        this.privateModeBtn = document.getElementById('privateMode');
        this.body = document.body;
        
        // 비활성화될 버튼들
        this.disableButtons = [
            document.getElementById('exportChat'),
            document.getElementById('sessionManageBtn')
        ];

        this.setupEventListeners();
        this.loadState();
        console.log('PrivateMode: Initialized with state:', this.isPrivate);
    }

    setupEventListeners() {
        this.privateModeBtn.addEventListener('click', () => this.toggle());
        
        // 브라우저 닫을 때 비공개 모드 상태 초기화
        window.addEventListener('beforeunload', () => {
            if (this.isPrivate) {
                sessionStorage.removeItem('privateMode');
            }
        });
    }

    async toggle() {
        console.log('PrivateMode: Toggling state from', this.isPrivate);
        const wasPrivate = this.isPrivate;
        this.isPrivate = !this.isPrivate;
        this.updateUI();
        this.saveState();

        // 모드가 실제로 변경되었을 때만 처리
        if (wasPrivate !== this.isPrivate) {
            console.log('PrivateMode: State changed to', this.isPrivate);
            
            if (this.isPrivate) {
                // 비공개 모드로 전환
                this.clearChat();
                const message = '비공개 모드가 활성화되었습니다. 이 모드에서는:\n- 대화 내용이 서버에 저장되지 않습니다.\n- 브라우저를 닫으면 모든 데이터가 삭제됩니다.\n- 대화 내용 저장 및 내보내기가 비활성화됩니다.';
                this.appendMessage('assistant', message);
            } else {
                // 일반 모드로 전환 - 기존 대화 내용 복원
                const message = '비공개 모드가 비활성화되었습니다. 일반 모드로 전환되었습니다.';
                this.loadNormalModeMessages();
                this.appendMessage('assistant', message);
            }
        }
    }

    async loadNormalModeMessages() {
        try {
            const response = await fetch('/get_chat_history', {
                headers: {
                    'X-Private-Mode': 'false'
                }
            });
            const data = await response.json();
            if (data.status === 'success' && data.messages) {
                this.clearChat();
                data.messages.forEach(msg => this.appendMessage(msg.role, msg.content));
            }
        } catch (error) {
            console.error('Failed to load normal mode messages:', error);
        }
    }

    updateUI() {
        console.log('PrivateMode: Updating UI for state:', this.isPrivate);
        // 비공개 모드 표시 업데이트
        this.body.classList.toggle('private-mode-on', this.isPrivate);
        this.privateModeBtn.classList.toggle('private-mode-active', this.isPrivate);

        // 버튼 비활성화/활성화
        this.disableButtons.forEach(button => {
            if (this.isPrivate) {
                button.classList.add('disabled-in-private');
                button.setAttribute('disabled', 'disabled');
            } else {
                button.classList.remove('disabled-in-private');
                button.removeAttribute('disabled');
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
            this.clearChat();
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
        window.appendMessage(role, content);
    }

    // 현재 비공개 모드 상태 반환
    isPrivateMode() {
        return this.isPrivate;
    }
}

// 전역 비공개 모드 인스턴스 생성
window.privateMode = new PrivateMode();

// 비공개 모드 관리 모듈
window.privateMode = {
    isPrivateMode() {
        return document.body.classList.contains('private-mode-on');
    }
}; 