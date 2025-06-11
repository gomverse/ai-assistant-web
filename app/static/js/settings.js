class Settings {
    constructor() {
        this.style = 'normal';  // 기본 스타일
        this.persona = 'professional';  // 기본 페르소나

        // UI 요소
        this.styleModal = document.getElementById('styleModal');
        this.personaModal = document.getElementById('personaModal');
        this.styleButtons = document.querySelectorAll('.style-btn');
        this.personaButtons = document.querySelectorAll('.persona-btn');

        // 모달 열기/닫기 버튼
        this.styleSettingsBtn = document.getElementById('styleSettingsBtn');
        this.closeStyleModal = document.getElementById('closeStyleModal');
        this.personaSettingsBtn = document.getElementById('personaSettingsBtn');
        this.closePersonaModal = document.getElementById('closePersonaModal');

        this.setupEventListeners();
        this.loadSettings();
    }

    setupEventListeners() {
        // 스타일 설정 모달
        this.styleSettingsBtn.addEventListener('click', () => this.styleModal.classList.remove('hidden'));
        this.closeStyleModal.addEventListener('click', () => this.styleModal.classList.add('hidden'));

        // 페르소나 설정 모달
        this.personaSettingsBtn.addEventListener('click', () => this.personaModal.classList.remove('hidden'));
        this.closePersonaModal.addEventListener('click', () => this.personaModal.classList.add('hidden'));

        // 스타일 버튼 이벤트
        this.styleButtons.forEach(button => {
            button.addEventListener('click', async () => {
                const style = button.id.replace('Style', '');
                await this.updateStyle(style);
                this.styleModal.classList.add('hidden');
            });
        });

        // 페르소나 버튼 이벤트
        this.personaButtons.forEach(button => {
            button.addEventListener('click', async () => {
                const persona = button.id.replace('Persona', '');
                await this.updatePersona(persona);
                this.personaModal.classList.add('hidden');
            });
        });

        // ESC 키로 모달 닫기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.styleModal.classList.add('hidden');
                this.personaModal.classList.add('hidden');
            }
        });

        // 모달 외부 클릭 시 닫기
        window.addEventListener('click', (e) => {
            if (e.target === this.styleModal) this.styleModal.classList.add('hidden');
            if (e.target === this.personaModal) this.personaModal.classList.add('hidden');
        });
    }

    async updateStyle(style, showNotification = true) {
        try {
            const response = await fetch('/update_style', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Private-Mode': window.privateMode.isPrivateMode() ? 'true' : 'false'
                },
                body: JSON.stringify({ style })
            });

            const data = await response.json();
            if (data.status === 'success') {
                this.style = style;
                this.saveSettings();
                
                // 스타일 버튼 상태 업데이트
                this.styleButtons.forEach(button => {
                    button.classList.toggle('ring-2', button.id === `${style}Style`);
                    button.classList.toggle('ring-white', button.id === `${style}Style`);
                });

                if (showNotification) {
                    window.showNotification(data.message, 'success');
                }
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Error updating style:', error);
            window.showNotification('스타일 설정 중 오류가 발생했습니다.', 'error');
        }
    }

    async updatePersona(persona, showNotification = true) {
        try {
            const response = await fetch('/update_persona', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Private-Mode': window.privateMode.isPrivateMode() ? 'true' : 'false'
                },
                body: JSON.stringify({ persona })
            });

            const data = await response.json();
            if (data.status === 'success') {
                this.persona = persona;
                this.saveSettings();
                
                // 페르소나 버튼 상태 업데이트
                this.personaButtons.forEach(button => {
                    button.classList.toggle('ring-2', button.id === `${persona}Persona`);
                    button.classList.toggle('ring-white', button.id === `${persona}Persona`);
                });

                if (showNotification) {
                    window.showNotification(data.message, 'success');
                }
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Error updating persona:', error);
            window.showNotification('페르소나 설정 중 오류가 발생했습니다.', 'error');
        }
    }

    saveSettings() {
        const isPrivate = window.privateMode.isPrivateMode();
        const storage = isPrivate ? sessionStorage : localStorage;
        const prefix = isPrivate ? 'private_' : '';
        
        storage.setItem(`${prefix}ai_style`, this.style);
        storage.setItem(`${prefix}ai_persona`, this.persona);
    }

    loadSettings() {
        const isPrivate = window.privateMode.isPrivateMode();
        const storage = isPrivate ? sessionStorage : localStorage;
        const prefix = isPrivate ? 'private_' : '';
        
        const savedStyle = storage.getItem(`${prefix}ai_style`);
        const savedPersona = storage.getItem(`${prefix}ai_persona`);

        if (savedStyle) this.updateStyle(savedStyle, false);
        if (savedPersona) this.updatePersona(savedPersona, false);
    }
}

// 전역 설정 인스턴스 생성
window.settings = new Settings(); 