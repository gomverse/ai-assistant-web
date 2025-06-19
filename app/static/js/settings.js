class Settings {
    constructor() {
        // DOM이 완전히 로드된 후에 초기화
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }

    initialize() {
        // 실제 HTML에 존재하는 id만 참조
        this.settingsToggle = document.getElementById('settingsToggle');
        this.settingsMenu = document.getElementById('settingsMenu');
        this.clearChatBtn = document.getElementById('clearChat'); // index.html 422
        this.exportChatBtn = document.getElementById('exportChat'); // index.html 426
        
        if (!this.settingsToggle || !this.settingsMenu) {
            console.error('Settings: Required DOM elements not found');
            return;
        }

        this.setupEventListeners();
    }

    setupEventListeners() {
        // 설정 메뉴 토글
        this.settingsToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleMenu();
        });

        // 메뉴 외부 클릭 시 닫기
        document.addEventListener('click', (e) => {
            if (this.settingsMenu.classList.contains('show') &&
                !this.settingsMenu.contains(e.target) && 
                !this.settingsToggle.contains(e.target)) {
                this.closeMenu();
            }
        });

        // 대화 내용 지우기
        if (this.clearChatBtn) {
            this.clearChatBtn.addEventListener('click', () => {
                this.clearChat();
                this.closeMenu();
            });
        }

        // 대화 내용 내보내기
        if (this.exportChatBtn) {
            this.exportChatBtn.addEventListener('click', () => {
                this.exportChat();
                this.closeMenu();
            });
        }
    }

    toggleMenu() {
        this.settingsMenu.classList.toggle('show');
        this.settingsToggle.classList.toggle('active');
    }

    closeMenu() {
        this.settingsMenu.classList.remove('show');
        this.settingsToggle.classList.remove('active');
    }

    clearChat() {
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            chatContainer.innerHTML = '';
            // 시작 메시지 다시 표시
            appendMessage('assistant', '안녕하세요! 무엇을 도와드릴까요?');
            showNotification('대화 내용이 삭제되었습니다.', 'success');
        }
    }

    exportChat() {
        const chatContainer = document.getElementById('chatContainer');
        if (!chatContainer) return;

        const messages = [];
        const messageElements = chatContainer.querySelectorAll('.message');

        messageElements.forEach(el => {
            const role = el.classList.contains('user-message') ? 'User' : 'Assistant';
            const content = el.querySelector('.message-content')?.textContent || '';
            const time = el.querySelector('.message-time')?.textContent || '';
            messages.push(`[${time}] ${role}: ${content}`);
        });

        if (messages.length === 0) {
            showNotification('내보낼 대화 내용이 없습니다.', 'error');
            return;
        }

        const text = messages.join('\n\n');
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        
        a.href = url;
        a.download = `chat-export-${timestamp}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showNotification('대화 내용이 저장되었습니다.', 'success');
    }
}

// 설정 초기화
(function() {
    window.settings = new Settings();
})();