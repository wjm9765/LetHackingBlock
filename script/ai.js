/**
 * AI 조언 기능을 담당하는 JavaScript 파일
 * main.js와 연동하여 작동
 */

// API 엔드포인트는 main.js에서 가져옴
// const API_ENDPOINT = 'http://127.0.0.1:8000'; // main.js에서 이미 정의됨

// 현재 표시된 패턴들을 저장하는 전역 변수
let currentPatterns = [];

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
 * AI 조언 초기화 함수
 * main.js에서 호출되어 이벤트 리스너를 설정
 */
function initializeAIAdvice() {
    console.log('AI 조언 기능 초기화 시작');
    
    // 기존 AI 조언 버튼 이벤트 리스너 설정
    const adviceButton = document.getElementById('ai-advice-btn');
    if (adviceButton) {
        // 기존 이벤트 리스너 제거 (중복 방지)
        adviceButton.removeEventListener('click', handleAIAdviceClick);
        // 새 이벤트 리스너 추가
        adviceButton.addEventListener('click', handleAIAdviceClick);
        console.log('AI 조언 버튼 이벤트 리스너 설정 완료');
    } else {
        console.error('AI 조언 버튼을 찾을 수 없습니다.');
    }
    
    // 새로운 AI 패턴 추천 버튼 이벤트 리스너 설정
    const patternButton = document.getElementById('ai-pattern-btn');
    if (patternButton) {
        // 기존 이벤트 리스너 제거 (중복 방지)
        patternButton.removeEventListener('click', handleAIPatternClick);
        // 새 이벤트 리스너 추가
        patternButton.addEventListener('click', handleAIPatternClick);
        console.log('AI 패턴 추천 버튼 이벤트 리스너 설정 완료');
    } else {
        console.error('AI 패턴 추천 버튼을 찾을 수 없습니다.');
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

/**
 * AI 패턴 추천 버튼 클릭 핸들러
 */
function handleAIPatternClick() {
    console.log('AI 패턴 추천 버튼 클릭됨');
    requestAIPattern();
}

/**
 * AI 패턴 추천 요청 함수
 * 백엔드에서 명령어 패턴을 가져와서 모달로 표시
 */
async function requestAIPattern() {
    try {
        console.log('AI 패턴 추천 요청 시작');
        
        // 모달 열기
        openPatternModal();
        
        // 사용자 이름 가져오기
        const username = localStorage.getItem('username');
        if (!username) {
            alert('사용자 정보를 찾을 수 없습니다.');
            closePatternModal();
            return;
        }
        
        console.log('패턴 추천 API 요청:', username);
        
        // API 요청
        const response = await fetch(`${API_ENDPOINT}/api/return_ai_pattern`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: username
            })
        });
        
        console.log('패턴 추천 API 응답:', response.status);
        
        const data = await response.json();
        console.log('패턴 추천 데이터:', data);
        
        // 패턴 표시
        displayPatterns(data.patterns || []);
        
    } catch (error) {
        console.error('패턴 추천 요청 중 오류 발생:', error);
        
        // 오류 메시지 표시
        const patternContent = document.getElementById('pattern-content');
        if (patternContent) {
            patternContent.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #ef4444;">
                    <p>패턴을 불러오는 중 오류가 발생했습니다.</p>
                    <p style="font-size: 12px; color: #888; margin-top: 8px;">${error.message}</p>
                </div>
            `;
            patternContent.style.display = 'block';
        }
        
        // 로딩 숨기기
        const patternLoading = document.getElementById('pattern-loading');
        if (patternLoading) {
            patternLoading.style.display = 'none';
        }
    }
}

/**
 * 패턴 모달 열기
 */
function openPatternModal() {
    const modal = document.getElementById('pattern-modal');
    const patternLoading = document.getElementById('pattern-loading');
    const patternContent = document.getElementById('pattern-content');
    
    if (modal) {
        modal.style.display = 'block';
        
        // 로딩 표시, 콘텐츠 숨기기
        if (patternLoading) patternLoading.style.display = 'block';
        if (patternContent) {
            patternContent.style.display = 'none';
            patternContent.innerHTML = '';
        }
    }
}

/**
 * 패턴 모달 닫기
 */
function closePatternModal() {
    const modal = document.getElementById('pattern-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * 패턴 표시 함수
 */
function displayPatterns(patterns) {
    const patternContent = document.getElementById('pattern-content');
    const patternLoading = document.getElementById('pattern-loading');
    
    if (!patternContent) return;
    
    // 패턴을 전역 변수에 저장
    currentPatterns = patterns;
    
    // 로딩 숨기기
    if (patternLoading) {
        patternLoading.style.display = 'none';
    }
    
    // 패턴이 없는 경우
    if (!patterns || patterns.length === 0) {
        patternContent.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #888;">
                <p>추천할 패턴이 없습니다.</p>
            </div>
        `;
        patternContent.style.display = 'block';
        return;
    }
    
    // 패턴 HTML 생성
    let patternsHTML = '';
    patterns.forEach((pattern, index) => {
        let commandsHTML = '';
        
        // pattern.pattern이 문자열인 경우 쉼표로 분리, 배열인 경우 그대로 사용
        let commands = [];
        console.log('패턴 원본 데이터:', pattern.pattern);
        console.log('패턴 타입:', typeof pattern.pattern);
        
        if (typeof pattern.pattern === 'string') {
            console.log('문자열로 인식됨, 쉼표로 분리 시작');
            // 쉼표로 분리하고 각 명령어의 앞뒤 공백 제거
            commands = pattern.pattern.split(',').map(cmd => cmd.trim()).filter(cmd => cmd.length > 0);
            console.log('분리된 명령어들:', commands);
        } else if (Array.isArray(pattern.pattern)) {
            console.log('배열로 인식됨, 배열 내부 항목들을 쉼표로 분리 확인');
            // 배열의 각 항목에 대해 쉼표 분리 시도
            commands = [];
            pattern.pattern.forEach(item => {
                if (typeof item === 'string' && item.includes(',')) {
                    // 배열 항목이 문자열이고 쉼표를 포함하는 경우 분리
                    const splitCommands = item.split(',').map(cmd => cmd.trim()).filter(cmd => cmd.length > 0);
                    commands.push(...splitCommands);
                    console.log(`"${item}"을 분리함:`, splitCommands);
                } else {
                    // 쉼표가 없는 경우 그대로 추가
                    commands.push(item);
                }
            });
            console.log('배열 처리 후 명령어들:', commands);
        } else {
            console.log('기타 타입으로 인식됨, 문자열로 변환');
            commands = [String(pattern.pattern)];
        }
        
        console.log('최종 명령어 목록:', commands);
        
        // 각 명령어를 번호와 함께 표시
        commands.forEach((command, cmdIndex) => {
            commandsHTML += `
                <div class="pattern-command">
                    <span class="command-number">${cmdIndex + 1}</span>
                    <span class="command-text">${command}</span>
                </div>
            `;
        });
        
        patternsHTML += `
            <div class="pattern-item">
                <div class="pattern-header">
                    <button class="pattern-apply-btn" onclick="applyPattern(${index})">적용</button>
                </div>
                <div class="pattern-purpose">${pattern.purpose}</div>
                <div class="pattern-commands">
                    ${commandsHTML}
                </div>
                <div class="pattern-expect">${pattern.expect}</div>
            </div>
        `;
    });
    
    patternContent.innerHTML = patternsHTML;
    patternContent.style.display = 'block';
}

/**
 * 패턴 적용 함수
 * 선택된 패턴의 명령어들을 워크플로우 팔레트에 추가
 */
async function applyPattern(patternIndex) {
    if (!currentPatterns || !currentPatterns[patternIndex]) {
        console.error('패턴을 찾을 수 없습니다:', patternIndex);
        return;
    }
    
    const pattern = currentPatterns[patternIndex];
    console.log('패턴 적용:', pattern);
    
    // pattern.pattern이 문자열인 경우 쉼표로 분리, 배열인 경우 그대로 사용
    let commands = [];
    console.log('적용할 패턴 원본 데이터:', pattern.pattern);
    console.log('적용할 패턴 타입:', typeof pattern.pattern);
    
    if (typeof pattern.pattern === 'string') {
        console.log('문자열로 인식됨, 쉼표로 분리 시작');
        commands = pattern.pattern.split(',').map(cmd => cmd.trim()).filter(cmd => cmd.length > 0);
        console.log('분리된 명령어들:', commands);
    } else if (Array.isArray(pattern.pattern)) {
        console.log('배열로 인식됨, 배열 내부 항목들을 쉼표로 분리 확인');
        // 배열의 각 항목에 대해 쉼표 분리 시도
        commands = [];
        pattern.pattern.forEach(item => {
            if (typeof item === 'string' && item.includes(',')) {
                // 배열 항목이 문자열이고 쉼표를 포함하는 경우 분리
                const splitCommands = item.split(',').map(cmd => cmd.trim()).filter(cmd => cmd.length > 0);
                commands.push(...splitCommands);
                console.log(`"${item}"을 분리함:`, splitCommands);
            } else {
                // 쉼표가 없는 경우 그대로 추가
                commands.push(item);
            }
        });
        console.log('배열 처리 후 명령어들:', commands);
    } else {
        console.log('기타 타입으로 인식됨, 문자열로 변환');
        commands = [String(pattern.pattern)];
    }
    
    console.log('적용할 최종 명령어 목록:', commands);
    
    try {
        // 기존 워크플로우에서 가장 오른쪽 블록의 위치 가져오기
        let startPosition = { x: 50, y: 50 }; // 기본 시작 위치
        
        if (typeof window.getRightmostBlockPosition === 'function') {
            const rightmostPos = window.getRightmostBlockPosition();
            if (rightmostPos.x > 0) {
                // 기존 블록이 있다면 그 오른쪽에 50px 간격으로 배치
                startPosition.x = rightmostPos.x + 50;
                startPosition.y = rightmostPos.y; // 같은 높이에 배치
            }
        }
        
        console.log('시작 위치:', startPosition);
        
        // 각 명령어를 순서대로 워크플로우 팔레트에 추가
        for (let i = 0; i < commands.length; i++) {
            const command = commands[i];
            console.log(`${i + 1}번째 명령어 처리:`, command);
            
            // 명령어에서 첫 번째 단어 추출 (공백 전까지)
            const commandName = command.split(' ')[0];
            const searchTerm = `${commandName}_command`;
            
            console.log(`"${commandName}"을 "${searchTerm}"로 검색`);
            
            // main.js의 fetchCommandDetails 함수 사용
            const commandDetails = await window.fetchCommandDetails(searchTerm);
            
            if (commandDetails) {
                console.log(`${i + 1}번째 명령어 상세 정보:`, commandDetails);
                
                // main.js의 createWorkflowBlock 함수 사용
                // 가로로 배치: X 위치를 300px씩 증가 (블록 너비 250px + 간격 50px)
                const x = startPosition.x + (i * 300);
                const y = startPosition.y;
                
                console.log(`${i + 1}번째 블록 생성 위치: x=${x}, y=${y}`);
                
                if (typeof window.createWorkflowBlock === 'function') {
                    window.createWorkflowBlock(commandDetails, x, y);
                    
                    // 블록 생성 후 잠시 대기 (DOM 업데이트 시간)
                    await new Promise(resolve => setTimeout(resolve, 200));
                } else {
                    console.error('createWorkflowBlock 함수를 찾을 수 없습니다.');
                    break;
                }
            } else {
                console.warn(`${i + 1}번째 명령어 "${searchTerm}"의 상세 정보를 가져올 수 없습니다.`);
                // 실패해도 다음 명령어 계속 처리
            }
        }
        
        // 모든 블록 추가 완료 후 자동 연결
        setTimeout(() => {
            if (typeof window.autoConnectBlocks === 'function') {
                window.autoConnectBlocks();
                console.log('블록 자동 연결 완료');
            }
        }, 500); // 충분한 대기 시간
        
        // 모달 닫기
        closePatternModal();
        
        // 성공 메시지 표시
        alert(`패턴이 적용되었습니다! ${commands.length}개의 명령어가 워크플로우에 추가되었습니다.`);
        
    } catch (error) {
        console.error('패턴 적용 중 오류 발생:', error);
        alert('패턴 적용 중 오류가 발생했습니다. 콘솔을 확인해주세요.');
    }
}

// main.js에서 호출할 수 있도록 전역 함수로 노출
window.initializeAIAdvice = initializeAIAdvice;
window.requestAIAdvice = requestAIAdvice;
window.requestAIPattern = requestAIPattern;
window.closePatternModal = closePatternModal;
window.applyPattern = applyPattern;

// ai.js에서는 자동 초기화를 하지 않음 (main.js에서만 호출)
// 이렇게 하면 중복 등록을 완전히 방지할 수 있음
