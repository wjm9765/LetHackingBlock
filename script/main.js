/**
 * 사용자 정보 표시 함수
 * 로컬 스토리지에서 사용자 정보를 가져와 화면에 표시
 */

// API 엔드포인트 설정
const API_ENDPOINT = 'http://127.0.0.1:8000';

function displayUserInfo() {
    // 로컬 스토리지에서 사용자 이름 가져오기
    const username = localStorage.getItem('username');
    const level = localStorage.getItem('level');
    
    console.log('사용자 정보:', username, 'Level:', level);

    // 사용자 이름이 없으면 로그인 페이지로 리다이렉트
    if (!username) {
        alert('로그인이 필요합니다.');
        window.location.href = '../html/login.html';
        return;
    }
    
    // SSH 로그인 API 호출 (main.html 첫 접속 시)
    loginSSH(parseInt(level) || 1);
    
    // 사용자 이름 표시
    const userDisplayElement = document.getElementById('user-display');
    if (userDisplayElement) {
        userDisplayElement.textContent = username;
    }
    
    // 레벨 정보 표시
    const levelDisplayElement = document.getElementById('level-display');
    if (levelDisplayElement) {
        levelDisplayElement.textContent = level || '미설정';
    }
    
    // 터미널에서 사용자 이름 표시
    updateTerminalUsername(username);
    
    // 권한 정보 가져오기 및 표시 (선택적)
    const permissionsString = localStorage.getItem('permissions');
    if (permissionsString) {
        try {
            const permissions = JSON.parse(permissionsString);
            displayPermissions(permissions);
        } catch (e) {
            console.error('권한 정보 파싱 실패:', e);
        }
    }
}

/**
 * SSH 로그인 API 호출 함수
 * main.html 첫 접속 시 호출
 */
async function loginSSH(level) {
    try {
        console.log('SSH 로그인 요청:', level); // 디버깅용
        
        const response = await fetch(`${API_ENDPOINT}/api/login_ssh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                level: level
            })
        });
        
        if (!response.ok) {
            throw new Error(`SSH 로그인 API 응답 오류: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('SSH 로그인 응답:', data); // 디버깅용
        
        // SSH 로그인 성공 시 터미널에 메시지 출력
        addTerminalOutput('해킹 환경 접속 성공', true);
        
    } catch (error) {
        console.error('SSH 로그인 실패:', error);
        // SSH 로그인 실패 시 터미널에 오류 메시지 출력
        addTerminalOutput('해킹 환경 접속 실패', false);
    }
}

/**
 * 터미널에서 사용자 이름 업데이트
 */
function updateTerminalUsername(username) {
    const terminalUsernames = document.querySelectorAll('[id^="terminal-username"]');
    terminalUsernames.forEach(element => {
        element.textContent = username;
    });
}

/**
 * 터미널에 명령어 출력 추가
 */
function addTerminalOutput(message, isSuccess = true, commandName = null) {
    const terminalContent = document.getElementById('terminal-content');
    if (!terminalContent) return;
    
    const username = localStorage.getItem('username') || 'user';
    
    // 기존 커서 제거
    const existingCursor = terminalContent.querySelector('.terminal-cursor');
    if (existingCursor) {
        existingCursor.parentElement.remove();
    }
    
    // SSH 접속 관련 메시지인지 확인
    const isSSHMessage = message.includes('해킹 환경 접속');
    
    if (isSSHMessage) {
        // SSH 접속 메시지인 경우 기존 방식으로 표시
        const newLine = document.createElement('div');
        newLine.className = 'terminal-line';
        newLine.innerHTML = `
            <span class="terminal-prompt">~/${username} &gt;</span>
            <span class="terminal-command">${message}</span>
        `;
        
        const outputLine = document.createElement('div');
        outputLine.className = 'terminal-line';
        outputLine.innerHTML = `
            <span class="terminal-output">${isSuccess ? '✓' : '✗'} ${message}</span>
        `;
        
        terminalContent.appendChild(newLine);
        terminalContent.appendChild(outputLine);
    } else {
        // 명령어 실행인 경우 명령어 이름 먼저 표시
        if (commandName) {
            const commandLine = document.createElement('div');
            commandLine.className = 'terminal-line';
            commandLine.innerHTML = `
                <span class="terminal-prompt">~/${username} &gt;</span>
                <span class="terminal-command">${commandName}</span>
            `;
            terminalContent.appendChild(commandLine);
        }
        
        // 줄바꿈을 처리하여 output 표시
        const lines = message.split('\n');
        lines.forEach(line => {
            const outputLine = document.createElement('div');
            outputLine.className = 'terminal-line';
            outputLine.innerHTML = `<span class="terminal-output">${line}</span>`;
            terminalContent.appendChild(outputLine);
        });
    }
    
    // 새 커서 라인 추가
    const cursorLine = document.createElement('div');
    cursorLine.className = 'terminal-line';
    cursorLine.innerHTML = `
        <span class="terminal-prompt">~/${username} &gt;</span>
        <span class="terminal-cursor">_</span>
    `;
    
    terminalContent.appendChild(cursorLine);
    
    // 스크롤을 맨 아래로
    terminalContent.scrollTop = terminalContent.scrollHeight;
}

/**
 * 명령어 블록 정보를 가져오는 함수
 */
async function fetchCommands() {
    try {
        // 로딩 상태 표시
        const commandBlocksContainer = document.getElementById('command-blocks-container');
        commandBlocksContainer.innerHTML = '<div class="loading">명령어 블록을 불러오는 중...</div>';
        
        // API 요청 (POST 방식)
        const response = await fetch(`${API_ENDPOINT}/api/return_commands`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                search_term: "all"
            })
        });
        
        if (!response.ok) {
            throw new Error(`API 응답 오류: ${response.status}`);
        }
        
        // JSON 데이터 파싱
        const data = await response.json();
        
        
        // 데이터 구조 확인 및 처리
        let commands;
        if (Array.isArray(data)) {
            commands = data;
        } else if (data.commands && Array.isArray(data.commands)) {
            commands = data.commands;
        } else if (typeof data === 'object') {
            // 객체인 경우 배열로 변환
            commands = Object.values(data);
        } else {
            throw new Error('올바르지 않은 데이터 형식입니다.');
        }
        
        // 명령어 블록 표시
        displayCommandBlocks(commands);
        
    } catch (error) {
        console.error('명령어 블록 로드 실패:', error);
        
        // 오류 메시지 표시
        const commandBlocksContainer = document.getElementById('command-blocks-container');
        commandBlocksContainer.innerHTML = `
            <div class="error-message">
                <p>명령어 블록을 불러올 수 없습니다.</p>
                <p>오류: ${error.message}</p>
                <button onclick="fetchCommands()">다시 시도</button>
            </div>
        `;
    }
}

/**
 * 명령어 블록을 화면에 표시하는 함수
 */
function displayCommandBlocks(commands) {
    const commandBlocksContainer = document.getElementById('command-blocks-container');
    
    console.log('표시할 명령어:', commands); // 디버깅용
    
    if (!commands || !Array.isArray(commands) || commands.length === 0) {
        commandBlocksContainer.innerHTML = '<div class="empty-message">사용 가능한 명령어 블록이 없습니다.</div>';
        return;
    }
    
    // 전역 변수로 저장 (검색에서 사용)
    window.allCommands = commands;
    
    // 각 명령어에 대한 HTML 생성
    const commandBlocksHTML = commands.map(command => `
        <div class="command-block" draggable="true" data-command="${command.command_name || '알 수 없음'}">
            <div class="block-icon">&lt;/&gt;</div>
            <div class="block-info">
                <div class="block-name">${command.command_name || '알 수 없는 명령어'}</div>
            </div>
            <div class="block-tooltip">
                <div class="tooltip-content">${command.description || '설명이 없습니다.'}</div>
            </div>
        </div>
    `).join('');
    
    // HTML 삽입
    commandBlocksContainer.innerHTML = commandBlocksHTML;
    
    // 툴팁 이벤트 리스너 추가
    initializeCommandBlocks();
    
    // 검색 기능 초기화
    initializeSearch();
}

/**
 * 검색 기능 초기화
 */
function initializeSearch() {
    const searchInput = document.querySelector('.search-input');
    if (!searchInput) return;
    
    // 이전 이벤트 리스너 제거
    searchInput.removeEventListener('input', handleSearch);
    
    // 새 이벤트 리스너 추가
    searchInput.addEventListener('input', handleSearch);
}

/**
 * 검색 처리 함수
 */
function handleSearch(event) {
    const searchTerm = event.target.value.toLowerCase().trim();
    
    if (!window.allCommands) return;
    
    // 검색어가 없으면 모든 명령어 표시
    if (searchTerm === '') {
        displayFilteredCommands(window.allCommands);
        return;
    }
    
    // 검색어에 맞는 명령어 필터링
    const filteredCommands = window.allCommands.filter(command => {
        const commandName = (command.command_name || '').toLowerCase();
        const description = (command.description || '').toLowerCase();
        
        return commandName.includes(searchTerm) || description.includes(searchTerm);
    });
    
    displayFilteredCommands(filteredCommands);
}

/**
 * 필터링된 명령어 표시
 */
function displayFilteredCommands(commands) {
    const commandBlocksContainer = document.getElementById('command-blocks-container');
    
    if (!commands || commands.length === 0) {
        commandBlocksContainer.innerHTML = '<div class="empty-message">검색 결과가 없습니다.</div>';
        return;
    }
    
    // 각 명령어에 대한 HTML 생성
    const commandBlocksHTML = commands.map(command => `
        <div class="command-block" draggable="true" data-command="${command.command_name || '알 수 없음'}">
            <div class="block-icon">&lt;/&gt;</div>
            <div class="block-info">
                <div class="block-name">${command.command_name || '알 수 없는 명령어'}</div>
            </div>
            <div class="block-tooltip">
                <div class="tooltip-content">${command.description || '설명이 없습니다.'}</div>
            </div>
        </div>
    `).join('');
    
    // HTML 삽입
    commandBlocksContainer.innerHTML = commandBlocksHTML;
    
    // 툴팁 이벤트 리스너 추가
    initializeCommandBlocks();
}

/**
 * 명령어 블록에 툴팁 이벤트 리스너 추가
 */
function initializeCommandBlocks() {
    const commandBlocks = document.querySelectorAll('.command-block');
    
    commandBlocks.forEach(block => {
        const tooltip = block.querySelector('.block-tooltip');
        
        // 드래그 시작 이벤트
        block.addEventListener('dragstart', function(e) {
            const commandName = block.getAttribute('data-command');
            e.dataTransfer.setData('text/plain', commandName);
            e.dataTransfer.effectAllowed = 'copy';
        });
        
        block.addEventListener('mouseenter', function(e) {
            // 모든 다른 툴팁 숨기기
            document.querySelectorAll('.block-tooltip').forEach(t => {
                if (t !== tooltip) {
                    t.style.opacity = '0';
                    t.style.visibility = 'hidden';
                }
            });
            
            // 블록의 위치 계산
            const blockRect = block.getBoundingClientRect();
            const tooltipWidth = 300; // CSS에서 설정한 툴팁 너비
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            
            // 기본 위치 (블록 오른쪽)
            let tooltipLeft = blockRect.right + 15;
            let tooltipTop = blockRect.top + (blockRect.height / 2);
            
            // 화면 오른쪽을 벗어나는 경우 왼쪽에 표시
            if (tooltipLeft + tooltipWidth > viewportWidth) {
                tooltipLeft = blockRect.left - tooltipWidth - 15;
            }
            
            // 화면 상단/하단을 벗어나는 경우 조정
            const tooltipHeight = 80; // 예상 툴팁 높이
            if (tooltipTop - (tooltipHeight / 2) < 0) {
                tooltipTop = tooltipHeight / 2 + 10;
            } else if (tooltipTop + (tooltipHeight / 2) > viewportHeight) {
                tooltipTop = viewportHeight - (tooltipHeight / 2) - 10;
            }
            
            // 툴팁 위치 설정
            tooltip.style.position = 'fixed';
            tooltip.style.left = tooltipLeft + 'px';
            tooltip.style.top = tooltipTop + 'px';
            tooltip.style.transform = 'translateY(-50%)';
            
            // 현재 툴팁 표시
            tooltip.style.opacity = '1';
            tooltip.style.visibility = 'visible';
        });
        
        block.addEventListener('mouseleave', function() {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
        });
        
        // 툴팁에 마우스가 올라갔을 때도 유지
        tooltip.addEventListener('mouseenter', function() {
            tooltip.style.opacity = '1';
            tooltip.style.visibility = 'visible';
        });
        
        tooltip.addEventListener('mouseleave', function() {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
        });
    });
}

/**
 * 명령어 상세 정보를 가져오는 함수
 */
async function fetchCommandDetails(commandName) {
    try {
        console.log('명령어 상세 정보 요청:', commandName); // 디버깅용
        
        const response = await fetch(`${API_ENDPOINT}/api/return_commands`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                search_term: commandName
            })
        });
        
        if (!response.ok) {
            throw new Error(`API 응답 오류: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('받은 명령어 상세 정보:', data); // 디버깅용
        return data;
        
    } catch (error) {
        console.error('명령어 상세 정보 로드 실패:', error);
        return null;
    }
}

/**
 * 워크플로우 블록 생성 함수
 */
function createWorkflowBlock(commandDetails, x, y) {
    console.log('워크플로우 블록 생성 시작:', commandDetails, 'x:', x, 'y:', y); // 디버깅용
    
    if (!commandDetails) {
        console.error('명령어 상세 정보가 없습니다.');
        return;
    }
    
    const blockId = 'workflow-block-' + Date.now();
    const workflowArea = document.querySelector('.workflow-area');
    
    if (!workflowArea) {
        console.error('워크플로우 영역을 찾을 수 없습니다.');
        return;
    }

    // 실제 명령어 데이터 추출 (commandDetails.command 안에 있음)
    const actualCommand = commandDetails.command || commandDetails;
    console.log('실제 명령어 데이터:', actualCommand); // 디버깅용

    // 명령어 이름 결정 (command_name을 우선적으로 사용)
    const commandName = actualCommand.command_name || actualCommand.name || '알 수 없는 명령어';
    const description = actualCommand.description || '설명이 없습니다.';
    const commandTemplate = actualCommand.command_template || '';
    
    console.log('추출된 정보:', { commandName, description, commandTemplate }); // 디버깅용
    
    // 템플릿에서 매개변수 추출 (순서대로)
    const templateParams = commandTemplate.match(/\{(\w+)\}/g) || [];
    console.log('템플릿 파라미터:', templateParams); // 디버깅용
    
    // 순서대로 변수 처리를 위한 HTML 생성
    const inputFieldsHTML = templateParams.map((param, index) => {
        const paramName = param.replace(/[{}]/g, '');
        
        // options인 경우 드롭다운 선택
        if (paramName === 'options' && actualCommand.available_options) {
            return `
                <div class="block-variable" data-index="${index}" data-param="${paramName}">
                    <label>${paramName}</label>
                    <select class="variable-select" data-param="${paramName}" data-index="${index}">
                        <option value="">없음</option>
                        ${Object.entries(actualCommand.available_options).map(([key, desc]) => 
                            `<option value="${key}" title="${desc}">${key} - ${desc}</option>`
                        ).join('')}
                    </select>
                </div>
            `;
        } else {
            // 일반 입력 필드
            return `
                <div class="block-variable" data-index="${index}" data-param="${paramName}">
                    <label>${paramName} (${index + 1}번째):</label>
                    <input type="text" class="variable-input" data-param="${paramName}" data-index="${index}" placeholder="${paramName} 입력...">
                </div>
            `;
        }
    }).join('');
    
    // 워크플로우 블록 HTML 생성
    const blockHTML = `
        <div class="workflow-block" id="${blockId}" style="left: ${x}px; top: ${y}px;" data-template="${commandTemplate}">
            <div class="block-header">
                <span class="block-icon">&lt;/&gt;</span>
                <span class="block-name">${commandName}</span>
                <button class="delete-btn" onclick="deleteWorkflowBlock('${blockId}')">✕</button>
                <button class="play-btn" onclick="executeBlock('${blockId}')">▶️</button>
            </div>
            <div class="block-content">
                <div class="block-description">${description}</div>
                ${inputFieldsHTML}
            </div>
            <div class="connection-point left"></div>
            <div class="connection-point right"></div>
        </div>
    `;
   
    // DOM에 추가
    workflowArea.insertAdjacentHTML('beforeend', blockHTML);
    
    // 이벤트 리스너 추가
    const newBlock = document.getElementById(blockId);
    if (newBlock) {
        console.log('블록이 성공적으로 추가되었습니다:', newBlock);
        initializeWorkflowBlock(newBlock);
    } else {
        console.error('블록 추가에 실패했습니다.');
    }
}

/**
 * 워크플로우 블록 초기화
 */
function initializeWorkflowBlock(block) {
    // command_template에서 {} 패턴 추출
    const commandTemplate = block.getAttribute('data-template') || '';
    const templateParams = commandTemplate.match(/\{(\w+)\}/g) || [];
    
    // 블록별 변수 저장 객체 생성 (순서대로)
    const blockData = {
        variables: new Array(templateParams.length).fill('') // 순서에 따라 저장
    };
    
    // 블록에 데이터 저장
    block.workflowData = blockData;
    
    console.log(`블록 ${block.id} 초기화 - 템플릿 파라미터:`, templateParams);
    console.log(`블록 ${block.id} 초기화 - 변수 배열 크기:`, blockData.variables.length);
    
    // 일반 입력 필드 이벤트 처리
    const inputFields = block.querySelectorAll('.variable-input');
    inputFields.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const index = parseInt(input.getAttribute('data-index'));
                const paramName = input.getAttribute('data-param');
                const value = input.value; // 빈 문자열도 그대로 저장
                
                // 순서대로 변수 배열에 저장 (빈 문자열 포함)
                block.workflowData.variables[index] = value;
                
                console.log(`블록 ${block.id} - ${index}번째 변수 (${paramName}) 저장:`, value);
                console.log(`블록 ${block.id} - 전체 변수 배열:`, block.workflowData.variables);
                
                // 값을 데이터 속성에 저장 (시각적 표시용)
                input.setAttribute('data-value', value);
                
                if (value === '') {
                    // 빈 문자열인 경우 어두운 연두색 배경
                    input.style.backgroundColor = '#2d4a2b'; // 어두운 연두색
                    input.style.color = '#ffffff'; // 글자색은 흰색
                    input.style.fontWeight = '600';
                } else {
                    // 값이 있는 경우 기존 스타일
                    input.style.backgroundColor = ''; // 배경색 초기화
                    input.style.color = '#22c55e'; // 글자를 초록색으로 변경
                    input.style.fontWeight = '600'; // 글자를 굵게
                }
            }
        });
    });
    
    // 드롭다운 선택 필드 이벤트 처리
    const selectFields = block.querySelectorAll('.variable-select');
    selectFields.forEach(select => {
        select.addEventListener('change', function() {
            const index = parseInt(select.getAttribute('data-index'));
            const paramName = select.getAttribute('data-param');
            const value = select.value;
            
            // 순서대로 변수 배열에 저장
            block.workflowData.variables[index] = value;
            
            console.log(`블록 ${block.id} - ${index}번째 변수 (${paramName}) 선택:`, value);
            console.log(`블록 ${block.id} - 전체 변수 배열:`, block.workflowData.variables);
            
            // 시각적 표시
            if (value) {
                select.style.color = '#22c55e';
                select.style.fontWeight = '600';
            } else {
                select.style.color = '#ffffff';
                select.style.fontWeight = 'normal';
            }
        });
    });
    
    // 드래그 기능 추가
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    
    // throttled 업데이트 함수 생성
    const throttledUpdate = throttle(updateAllConnections, 16); // 60fps
    
    const header = block.querySelector('.block-header');
    header.addEventListener('mousedown', function(e) {
        if (e.target.classList.contains('delete-btn') || e.target.classList.contains('play-btn')) {
            return; // 버튼 클릭은 드래그하지 않음
        }
        
        isDragging = true;
        const rect = block.getBoundingClientRect();
        dragOffset.x = e.clientX - rect.left;
        dragOffset.y = e.clientY - rect.top;
        
        block.style.zIndex = 1000;
    });
    
    document.addEventListener('mousemove', function(e) {
        if (!isDragging) return;
        
        const workflowArea = document.querySelector('.workflow-area');
        const areaRect = workflowArea.getBoundingClientRect();
        
        const newX = e.clientX - areaRect.left - dragOffset.x;
        const newY = e.clientY - areaRect.top - dragOffset.y;
        
        block.style.left = Math.max(0, newX) + 'px';
        block.style.top = Math.max(0, newY) + 'px';
        
        // 드래그 중에도 연결선 실시간 업데이트 (throttled)
        throttledUpdate();
    });
    
    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            block.style.zIndex = 2;
            
            // 드래그 종료 시 연결선 업데이트
            updateAllConnections();
        }
    });
}

/**
 * 함수 실행을 제한하는 throttle 함수
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

/**
 * 두 블록 사이의 연결선 생성
 */
function createConnection(fromBlock, toBlock) {
    const svg = document.querySelector('.connection-svg');
    if (!svg) return null;
    
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.classList.add('connection-line');
    path.setAttribute('data-from', fromBlock.id);
    path.setAttribute('data-to', toBlock.id);
    
    svg.appendChild(path);
    updateConnectionPath(path, fromBlock, toBlock);
    
    return path;
}

/**
 * 연결선 경로 업데이트
 */
function updateConnectionPath(path, fromBlock, toBlock) {
    const workflowArea = document.querySelector('.workflow-area');
    const areaRect = workflowArea.getBoundingClientRect();
    
    // connection-point 요소들 찾기
    const fromConnectionPoint = fromBlock.querySelector('.connection-point.right');
    const toConnectionPoint = toBlock.querySelector('.connection-point.left');
    
    if (!fromConnectionPoint || !toConnectionPoint) {
        console.warn('Connection points not found');
        return;
    }
    
    // connection-point의 정확한 위치 계산
    const fromRect = fromConnectionPoint.getBoundingClientRect();
    const toRect = toConnectionPoint.getBoundingClientRect();
    
    // 워크플로우 영역 기준 상대 좌표로 변환
    const fromX = fromRect.left + (fromRect.width / 2) - areaRect.left;
    const fromY = fromRect.top + (fromRect.height / 2) - areaRect.top;
    const toX = toRect.left + (toRect.width / 2) - areaRect.left;
    const toY = toRect.top + (toRect.height / 2) - areaRect.top;
    
    // 수평 거리 계산
    const deltaX = toX - fromX;
    const deltaY = toY - fromY;
    
    // 부드러운 베지어 곡선을 위한 제어점 계산
    const controlDistance = Math.max(Math.abs(deltaX) * 0.6, 80); // 최소 80px 거리 보장
    const controlPoint1X = fromX + controlDistance;
    const controlPoint1Y = fromY;
    const controlPoint2X = toX - controlDistance;
    const controlPoint2Y = toY;
    
    // SVG path 데이터 생성
    const pathData = `M ${fromX} ${fromY} C ${controlPoint1X} ${controlPoint1Y}, ${controlPoint2X} ${controlPoint2Y}, ${toX} ${toY}`;
    path.setAttribute('d', pathData);
}

/**
 * 모든 연결선 업데이트
 */
function updateAllConnections() {
    const connections = document.querySelectorAll('.connection-line');
    connections.forEach(path => {
        const fromId = path.getAttribute('data-from');
        const toId = path.getAttribute('data-to');
        const fromBlock = document.getElementById(fromId);
        const toBlock = document.getElementById(toId);
        
        if (fromBlock && toBlock) {
            updateConnectionPath(path, fromBlock, toBlock);
        } else {
            // 블록이 삭제된 경우 연결선도 제거
            path.remove();
        }
    });
}

/**
 * 자동으로 블록들을 연결
 */
function autoConnectBlocks() {
    const blocks = Array.from(document.querySelectorAll('.workflow-block'));
    
    // 생성 시간순으로 정렬 (ID에 타임스탬프가 포함되어 있음)
    blocks.sort((a, b) => {
        const aTime = parseInt(a.id.split('-').pop());
        const bTime = parseInt(b.id.split('-').pop());
        return aTime - bTime;
    });
    
    // 연속된 블록들을 연결
    for (let i = 0; i < blocks.length - 1; i++) {
        const fromBlock = blocks[i];
        const toBlock = blocks[i + 1];
        
        // 이미 연결되어 있는지 확인
        const existingConnection = document.querySelector(
            `.connection-line[data-from="${fromBlock.id}"][data-to="${toBlock.id}"]`
        );
        
        if (!existingConnection) {
            createConnection(fromBlock, toBlock);
        }
    }
}

/**
 * 워크플로우 블록 삭제
 */
function deleteWorkflowBlock(blockId) {
    const block = document.getElementById(blockId);
    if (block) {
        console.log(`블록 ${blockId} 삭제 - 저장된 데이터:`, block.workflowData);
        
        // 해당 블록과 연결된 모든 연결선 제거
        const connections = document.querySelectorAll(
            `.connection-line[data-from="${blockId}"], .connection-line[data-to="${blockId}"]`
        );
        connections.forEach(connection => connection.remove());
        
        // 블록 제거
        block.remove();
        
        // 남은 연결선들 재정렬
        setTimeout(() => {
            autoConnectBlocks();
        }, 100);
    }
}

/**
 * 블록의 완성된 명령어 생성
 */
function generateCommand(block) {
    if (!block.workflowData) {
        console.error('블록 데이터가 없습니다.');
        return null;
    }
    
    const blockName = block.querySelector('.block-name').textContent;
    const commandTemplate = block.getAttribute('data-template') || '';
    const variables = block.workflowData.variables;
    
    // 템플릿에서 {} 패턴 추출 (순서대로)
    const templateParams = commandTemplate.match(/\{(\w+)\}/g) || [];
    
    // 템플릿에 변수들을 순서대로 적용
    let finalCommand = commandTemplate;
    
    templateParams.forEach((param, index) => {
        const value = variables[index] || '';
        finalCommand = finalCommand.replace(param, value);
    });
    
    // 여러 공백을 하나로 줄이고 trim
    finalCommand = finalCommand.replace(/\s+/g, ' ').trim();
    
    console.log(`블록 ${block.id} 명령어 생성:`, {
        blockName,
        template: commandTemplate,
        templateParams,
        variables,
        finalCommand
    });
    
    return finalCommand;
}

/**
 * 모든 워크플로우 블록의 데이터 조회
 */
function getAllWorkflowData() {
    const blocks = document.querySelectorAll('.workflow-block');
    const allData = [];
    
    blocks.forEach(block => {
        if (block.workflowData) {
            const blockName = block.querySelector('.block-name').textContent;
            const command = generateCommand(block);
            const commandTemplate = block.getAttribute('data-template') || '';
            const templateParams = commandTemplate.match(/\{(\w+)\}/g) || [];
            
            // 블록의 현재 좌표 가져오기
            const x = parseInt(block.style.left) || 0;
            const y = parseInt(block.style.top) || 0;
            
            allData.push({
                blockId: block.id,
                blockName,
                template: commandTemplate,
                templateParams,
                variables: block.workflowData.variables,
                command,
                coordinates: { x, y } // 좌표 정보 추가
            });
        }
    });
    
    console.log('전체 워크플로우 데이터:', allData);
    return allData;
}

/**
 * 워크플로우 블록들의 좌표 정보만 조회
 */
function getAllBlockCoordinates() {
    const blocks = document.querySelectorAll('.workflow-block');
    const coordinates = [];
    
    blocks.forEach(block => {
        const blockName = block.querySelector('.block-name').textContent;
        const x = parseInt(block.style.left) || 0;
        const y = parseInt(block.style.top) || 0;
        
        coordinates.push({
            blockId: block.id,
            blockName,
            x,
            y
        });
    });
    
    console.log('블록 좌표 정보:', coordinates);
    return coordinates;
}

/**
 * 가장 오른쪽에 위치한 블록의 좌표 반환
 */
function getRightmostBlockPosition() {
    const blocks = document.querySelectorAll('.workflow-block');
    let rightmostX = 0;
    let rightmostY = 50; // 기본 Y 좌표
    
    blocks.forEach(block => {
        const x = parseInt(block.style.left) || 0;
        const y = parseInt(block.style.top) || 0;
        const blockWidth = 250; // CSS에서 설정한 블록 너비
        
        if (x + blockWidth > rightmostX) {
            rightmostX = x + blockWidth;
            rightmostY = y; // 가장 오른쪽 블록의 Y 좌표 사용
        }
    });
    
    return { x: rightmostX, y: rightmostY };
}

/**
 * 블록 실행 함수
 */
async function executeBlock(blockId) {
    const block = document.getElementById(blockId);
    if (!block) {
        console.error('블록을 찾을 수 없습니다:', blockId);
        return;
    }
    
    // 사용자 정보 가져오기
    const username = localStorage.getItem('username');
    const level = localStorage.getItem('level');
    
    if (!username || !level) {
        addTerminalOutput('사용자 정보가 없습니다. 다시 로그인해주세요.', false);
        return;
    }
    
    // 블록에서 명령어 정보 추출
    const commandName = block.querySelector('.block-name').textContent;
    const commandTemplate = block.getAttribute('data-template') || '';
    
    if (!block.workflowData || !block.workflowData.variables) {
        addTerminalOutput('블록 데이터가 없습니다.', false);
        return;
    }
    
    // 템플릿 파라미터와 변수를 매칭하여 params 객체 생성
    const templateParams = commandTemplate.match(/\{(\w+)\}/g) || [];
    const params = {};
    
    templateParams.forEach((param, index) => {
        const paramName = param.replace(/[{}]/g, '');
        const value = block.workflowData.variables[index];
        // 값이 정의되어 있으면 (빈 문자열 포함) params에 추가
        if (value !== undefined) {
            params[paramName] = value;
        }
    });
    
    console.log(`블록 ${blockId} 실행 준비:`, {
        commandName,
        username,
        level,
        params
    });
    
    try {
        // 백엔드 API 호출
        const response = await fetch(`${API_ENDPOINT}/api/execute_command`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: username,
                environment_number: level,
                command_name: commandName,
                params: params
            })
        });
        
        // 응답이 JSON 형태인지 확인
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error(`서버에서 올바르지 않은 응답 형식을 반환했습니다: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('명령어 실행 결과:', result);

        // success가 false인 경우 처리 (HTTP 상태 코드와 관계없이)
        if (result.success === false) {
            addTerminalOutput('명령어 실행 실패 ! 명령어 조합을 고려해보세요', false, commandName);
            console.log('명령어 실행 실패:', result.detail || result.message || '상세 정보 없음');
        }
        // 성공인 경우 처리
        else if (result.success === true) {
            // 성공 시 output을 터미널에 출력 (명령어 이름 포함)
            addTerminalOutput(result.output || '명령어가 성공적으로 실행되었습니다.', true, commandName);
        }
        // success 필드가 없거나 예상치 못한 응답 형태인 경우
        else {
            // None, None이 반환된 경우 처리 (파이썬에서 None은 JavaScript에서 null로 변환됨)
            if (result.output === null || result.output === "None" || 
                (typeof result.output === 'string' && result.output.trim() === '')) {
                addTerminalOutput('명령어 실행 실패 ! 명령어 조합을 고려해보세요', false, commandName);
            } else {
                // 일반적인 실패 처리
                addTerminalOutput(result.output || '명령어 실행에 실패했습니다.', false, commandName);
            }
        }
        
    } catch (error) {
        console.error('명령어 실행 API 호출 실패:', error);
        addTerminalOutput(`명령어 실행 실패: ${error.message}`, false, commandName);
    }
}

/**
 * 워크플로우 영역 초기화
 */
function initializeWorkflowArea() {
    const workflowArea = document.querySelector('.workflow-area');
    
    // SVG 연결선 컨테이너 생성
    if (!workflowArea.querySelector('.connection-svg')) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.classList.add('connection-svg');
        svg.style.position = 'absolute';
        svg.style.top = '0';
        svg.style.left = '0';
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.style.pointerEvents = 'none';
        svg.style.zIndex = '1';
        workflowArea.appendChild(svg);
    }
    
    // 드롭 이벤트 설정
    workflowArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    });
    
    workflowArea.addEventListener('drop', function(e) {
        e.preventDefault();
        
        const commandName = e.dataTransfer.getData('text/plain');
        const rect = workflowArea.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        console.log('드롭 이벤트 발생:', { commandName, x, y }); // 디버깅용
        
        // 명령어 상세 정보 가져오기
        fetchCommandDetails(commandName).then(commandDetails => {
            console.log('상세 정보 받음:', commandDetails); // 디버깅용
            if (commandDetails) {
                createWorkflowBlock(commandDetails, x, y);
                
                // 새 블록 생성 후 자동 연결
                setTimeout(() => {
                    autoConnectBlocks();
                }, 100);
            } else {
                console.error('명령어 상세 정보를 가져올 수 없습니다.');
            }
        }).catch(error => {
            console.error('fetchCommandDetails 오류:', error);
        });
    });
    
    // 초기화 버튼 이벤트 (이제 유일한 버튼이므로 first-child로 선택)
    const clearButton = document.querySelector('.palette-controls .control-btn');
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            const blocks = workflowArea.querySelectorAll('.workflow-block');
            blocks.forEach(block => block.remove());
            
            // 모든 연결선도 제거
            const connections = document.querySelectorAll('.connection-line');
            connections.forEach(connection => connection.remove());
            
            workflowArea.removeAttribute('data-initialized');
        });
    }
}

/**
 * 권한 정보 표시 함수
 * 사용자의 권한 정보를 화면에 표시
 */
function displayPermissions(permissions) {
    const permissionsElement = document.getElementById('user-permissions');
    if (!permissionsElement) return;
    
    // 권한 목록 생성
    const permissionsList = permissions.map(permission => 
        `<div class="permission-item">
            <span class="permission-number">${permission.number}</span>
            <span class="permission-description">${permission.description}</span>
        </div>`
    ).join('');
    
    // 권한 목록 표시
    permissionsElement.innerHTML = `
        <h3>보유 권한</h3>
        <div class="permissions-list">
            ${permissionsList}
        </div>
    `;
}

/**
 * 사용자 상태 삭제 API 호출 함수
 * 로그아웃 또는 창 닫기 시 호출
 */
async function deleteUserState(username) {
    try {
        console.log('사용자 상태 삭제 요청:', username); // 디버깅용
        
        const response = await fetch(`${API_ENDPOINT}/api/delete_user_state`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: username
            })
        });
        
        if (!response.ok) {
            throw new Error(`사용자 상태 삭제 API 응답 오류: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('사용자 상태 삭제 응답:', data); // 디버깅용
        
    } catch (error) {
        console.error('사용자 상태 삭제 실패:', error);
        // 상태 삭제 실패는 로그아웃 과정을 방해하지 않음
    }
}

/**
 * 로그아웃 함수
 * 로컬 스토리지의 사용자 정보를 삭제하고 로그인 페이지로 이동
 */
function handleLogout() {
    const username = localStorage.getItem('username');
    
    // 사용자 상태 삭제 API 호출
    if (username) {
        deleteUserState(username);
    }
    
    // 로컬 스토리지에서 사용자 정보 삭제
    localStorage.removeItem('username');
    localStorage.removeItem('level');
    localStorage.removeItem('permissions');
    
    // 로그인 페이지로 이동
    window.location.href = '../html/login.html';
}

// 페이지 로드 시 실행되는 초기화 함수
document.addEventListener('DOMContentLoaded', function() {
    // 사용자 정보 표시
    displayUserInfo();
    
    // 명령어 블록 로드
    fetchCommands();
    
    // 워크플로우 영역 초기화
    initializeWorkflowArea();
    
    // AI 조언 기능 초기화 (ai.js에서 제공)
    // setTimeout을 사용하여 ai.js가 완전히 로드된 후 초기화
    setTimeout(() => {
        if (typeof window.initializeAIAdvice === 'function') {
            window.initializeAIAdvice();
        } else {
            console.warn('AI 조언 기능이 아직 로드되지 않았습니다.');
        }
    }, 200);
    
    // 로그아웃 버튼 이벤트 리스너 등록
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }
    
    // 정답 확인 버튼 이벤트 리스너
    const answerCheckButton = document.getElementById('answer-check-btn');
    if (answerCheckButton) {
        answerCheckButton.addEventListener('click', openAnswerModal);
    }
    
    // 정답 확인 모달 이벤트 리스너
    setupAnswerModal();
    
    // 패턴 추천 모달 이벤트 리스너
    setupPatternModal();
    
    // 창 닫기 또는 페이지 이탈 시 사용자 상태 삭제
    window.addEventListener('beforeunload', function(e) {
        const username = localStorage.getItem('username');
        if (username) {
            // navigator.sendBeacon을 사용하여 비동기적으로 API 호출
            // 이는 페이지가 닫히더라도 요청이 완료될 가능성을 높임
            const data = JSON.stringify({ user_id: username });
            navigator.sendBeacon(`${API_ENDPOINT}/api/delete_user_state`, data);
        }
    });
    
    // 페이지 이탈 시에도 처리 (브라우저 호환성을 위해)
    window.addEventListener('unload', function(e) {
        const username = localStorage.getItem('username');
        if (username) {
            navigator.sendBeacon(`${API_ENDPOINT}/api/delete_user_state`, 
                JSON.stringify({ user_id: username }));
        }
    });
});

/**
 * 정답 확인 모달 열기
 */
function openAnswerModal() {
    const modal = document.getElementById('answer-modal');
    if (modal) {
        modal.style.display = 'block';
        // 입력 필드에 포커스
        const answerInput = document.getElementById('answer-input');
        if (answerInput) {
            answerInput.focus();
        }
    }
}

/**
 * 정답 확인 모달 닫기
 */
function closeAnswerModal() {
    const modal = document.getElementById('answer-modal');
    if (modal) {
        modal.style.display = 'none';
        // 입력 필드 초기화
        const answerInput = document.getElementById('answer-input');
        if (answerInput) {
            answerInput.value = '';
        }
    }
}

/**
 * 정답 확인 모달 이벤트 설정
 */
function setupAnswerModal() {
    const modal = document.getElementById('answer-modal');
    const closeBtn = modal?.querySelector('.close');
    const answerForm = document.getElementById('answer-form');
    
    // 닫기 버튼 클릭 시
    if (closeBtn) {
        closeBtn.addEventListener('click', closeAnswerModal);
    }
    
    // 모달 외부 클릭 시 닫기
    if (modal) {
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeAnswerModal();
            }
        });
    }
    
    // 폼 제출 이벤트
    if (answerForm) {
        answerForm.addEventListener('submit', function(event) {
            event.preventDefault();
            submitAnswer();
        });
    }
    
    // ESC 키로 모달 닫기
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const answerModal = document.getElementById('answer-modal');
            const patternModal = document.getElementById('pattern-modal');
            
            if (answerModal && answerModal.style.display === 'block') {
                closeAnswerModal();
            }
            if (patternModal && patternModal.style.display === 'block') {
                closePatternModal();
            }
        }
    });
}

/**
 * 패턴 추천 모달 이벤트 설정
 */
function setupPatternModal() {
    const modal = document.getElementById('pattern-modal');
    const closeBtn = modal?.querySelector('.pattern-close');
    
    // 닫기 버튼 클릭 시
    if (closeBtn) {
        closeBtn.addEventListener('click', closePatternModal);
    }
    
    // 모달 외부 클릭 시 닫기
    if (modal) {
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                closePatternModal();
            }
        });
    }
}

/**
 * 정답 제출
 */
async function submitAnswer() {
    const answerInput = document.getElementById('answer-input');
    const answer = answerInput?.value.trim();
    
    if (!answer) {
        alert('답을 입력해주세요.');
        return;
    }
    
    const username = localStorage.getItem('username');
    const level = localStorage.getItem('level');
    
    if (!username || !level) {
        alert('사용자 정보를 찾을 수 없습니다.');
        return;
    }
    
    try {
        // 제출 버튼 비활성화
        const submitBtn = document.querySelector('.btn-submit');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = '제출 중...';
        }
        
        const response = await fetch(`${API_ENDPOINT}/api/correct_answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: username,
                level: parseInt(level),
                answer: answer
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('정답입니다! 축하합니다! 🎉');
            closeAnswerModal();
            // 필요시 다음 레벨로 이동하는 로직 추가
        } else {
            alert('틀렸습니다. 다시 시도해보세요.');
            // 입력 필드 선택하여 다시 입력할 수 있도록
            answerInput.select();
        }
        
    } catch (error) {
        console.error('정답 확인 중 오류 발생:', error);
        alert('서버 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
        // 제출 버튼 복원
        const submitBtn = document.querySelector('.btn-submit');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = '제출';
        }
    }
}

// AI.js에서 사용할 수 있도록 전역 함수로 노출
window.fetchCommandDetails = fetchCommandDetails;
window.createWorkflowBlock = createWorkflowBlock;
window.autoConnectBlocks = autoConnectBlocks;
window.getAllBlockCoordinates = getAllBlockCoordinates;
window.getRightmostBlockPosition = getRightmostBlockPosition;