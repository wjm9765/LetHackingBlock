/**
 * AI 조언 기능을 담당하는 JavaScript 파일
 * main.js와 연동하여 작동
 */

// API 엔드포인트는 main.js에서 가져옴
// const API_ENDPOINT = 'http://127.0.0.1:8000'; // main.js에서 이미 정의됨

/**
 * AI 조언 요청 함수
 * 백엔드에서 AI 코멘트를 가져와서 화면에 표시
 */
async function requestAIAdvice() {
    try {
        console.log('AI 조언 요청 시작'); // 디버깅용
        
        // 로딩 상태를 누적 방식으로 표시
        const aiTextElement = document.querySelector('.ai-text');
        if (aiTextElement) {
            const loadingElement = document.createElement('div');
            loadingElement.className = 'ai-loading-message';
            loadingElement.innerHTML = '<div class="ai-loading">AI가 조언을 생성 중입니다...</div>';
            aiTextElement.appendChild(loadingElement);
            
            // 스크롤을 맨 아래로 이동
            const aiContent = document.querySelector('.ai-content');
            if (aiContent) {
                aiContent.scrollTop = aiContent.scrollHeight;
            }
        }
        
        // 백엔드 API 호출
        const response = await fetch(`${API_ENDPOINT}/api/return_ai_comment`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`AI 조언 API 응답 오류: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('AI 조언 응답:', data); // 디버깅용
        
        // 로딩 메시지 제거
        const loadingMessage = aiTextElement?.querySelector('.ai-loading-message');
        if (loadingMessage) {
            loadingMessage.remove();
        }
        
        // AI 코멘트를 화면에 표시
        displayAIComment(data.ai_comment || 'AI 조언을 가져올 수 없습니다.');
        
    } catch (error) {
        console.error('AI 조언 요청 실패:', error);
        
        // 로딩 메시지 제거
        const aiTextElement = document.querySelector('.ai-text');
        const loadingMessage = aiTextElement?.querySelector('.ai-loading-message');
        if (loadingMessage) {
            loadingMessage.remove();
        }
        
        // 오류 메시지 표시
        displayAIComment(`AI 조언 요청에 실패했습니다: ${error.message}`);
    }
}

/**
 * AI 코멘트를 화면에 표시하는 함수
 * @param {string} comment - 표시할 AI 코멘트
 */
function displayAIComment(comment) {
    const aiTextElement = document.querySelector('.ai-text');
    if (!aiTextElement) {
        console.error('AI 텍스트 영역을 찾을 수 없습니다.');
        return;
    }
    
    // 줄바꿈 처리를 위해 \n을 <br>로 변환
    const formattedComment = comment.replace(/\n/g, '<br>');
    
    // 새로운 AI 코멘트를 기존 내용 아래에 추가
    const newCommentElement = document.createElement('div');
    newCommentElement.className = 'ai-comment';
    newCommentElement.innerHTML = `
        <div class="ai-comment-header">
            <span class="ai-icon">🤖</span>
            <span class="ai-title">AI 조언</span>
            <span class="ai-timestamp">${new Date().toLocaleTimeString()}</span>
        </div>
        <div class="ai-comment-content">${formattedComment}</div>
    `;
    
    // 기존 내용에 새로운 코멘트 추가
    aiTextElement.appendChild(newCommentElement);
    
    // 스크롤을 맨 아래로 이동
    const aiContent = document.querySelector('.ai-content');
    if (aiContent) {
        aiContent.scrollTop = aiContent.scrollHeight;
    }
    
    console.log('AI 코멘트 추가 완료:', comment);
}

/**
 * AI 조언 버튼 초기화
 * 페이지 로드 시 호출되어 이벤트 리스너를 설정
 */
function initializeAIAdvice() {
    const adviceButton = document.getElementById('ai-advice-btn');
    if (adviceButton) {
        // 기존 이벤트 리스너가 있다면 제거 (중복 방지)
        adviceButton.removeEventListener('click', handleAIAdviceClick);
        
        // 새로운 이벤트 리스너 추가
        adviceButton.addEventListener('click', handleAIAdviceClick);
        console.log('AI 조언 버튼 이벤트 리스너 설정 완료');
    } else {
        console.error('AI 조언 버튼을 찾을 수 없습니다.');
    }
}

/**
 * AI 조언 버튼 클릭 핸들러
 * 별도 함수로 분리하여 중복 등록 방지
 */
function handleAIAdviceClick() {
    console.log('AI 조언 버튼 클릭됨');
    requestAIAdvice();
}

// main.js에서 호출할 수 있도록 전역 함수로 노출
window.initializeAIAdvice = initializeAIAdvice;
window.requestAIAdvice = requestAIAdvice;

// ai.js에서는 자동 초기화를 하지 않음 (main.js에서만 호출)
// 이렇게 하면 중복 등록을 완전히 방지할 수 있음
