// 대화 초기화 기능
document.getElementById('clearContext').addEventListener('click', async () => {
    if (confirm('정말 대화 내용을 초기화하시겠습니까?')) {
        try {
            const response = await fetch('/clear_context', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Private-Mode': isPrivateMode ? 'true' : 'false'
                }
            });
            
            const data = await response.json();
            if (data.status === 'success') {
                // 대화 컨테이너 비우기
                document.getElementById('chatContainer').innerHTML = '';
                showNotification(data.message, 'success');
            } else {
                showNotification(data.message, 'error');
            }
        } catch (error) {
            console.error('Error clearing context:', error);
            showNotification('대화 내용 초기화 중 오류가 발생했습니다.', 'error');
        }
    }
});

// 음성 출력 기능
let isVoiceOutputEnabled = false;

document.getElementById('voiceOutput').addEventListener('click', function() {
    isVoiceOutputEnabled = !isVoiceOutputEnabled;
    this.classList.toggle('voice-output-active', isVoiceOutputEnabled);
    
    // 로컬 스토리지에 설정 저장
    localStorage.setItem('voiceOutputEnabled', isVoiceOutputEnabled);
    
    // 알림 표시
    showNotification(
        isVoiceOutputEnabled ? '음성 출력이 활성화되었습니다.' : '음성 출력이 비활성화되었습니다.',
        'success'
    );
});

// 페이지 로드 시 음성 출력 설정 복원
document.addEventListener('DOMContentLoaded', () => {
    const savedVoiceOutput = localStorage.getItem('voiceOutputEnabled');
    if (savedVoiceOutput === 'true') {
        isVoiceOutputEnabled = true;
        document.getElementById('voiceOutput').classList.add('voice-output-active');
    }
});

// AI 응답에 대한 음성 출력 처리
async function handleAIResponse(response) {
    if (!isVoiceOutputEnabled || !response.text) return;

    try {
        const audioResponse = await fetch('/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: response.text })
        });

        if (audioResponse.ok) {
            const audioBlob = await audioResponse.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play();
        }
    } catch (error) {
        console.error('Error playing audio:', error);
        showNotification('음성 출력 중 오류가 발생했습니다.', 'error');
    }
}

// 알림 표시 함수
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 p-4 rounded-lg shadow-lg text-white ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        'bg-blue-500'
    }`;
    notification.textContent = message;
    document.body.appendChild(notification);

    // 3초 후 알림 제거
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 전역 변수로 isPrivateMode 선언
let isPrivateMode = false; 