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
 * 터미널에서 사용자 이름 업데이트
 */
function updateTerminalUsername(username) {
    const terminalUsernames = document.querySelectorAll('[id^="terminal-username"]');
    terminalUsernames.forEach(element => {
        element.textContent = username;
    });
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

    console.log('명령어 상세 정보 타입:', typeof(commandDetails)); // 디버깅용

    // 명령어 이름 결정 (command_name을 우선적으로 사용)
    const commandName = commandDetails.command_name || commandDetails.name || '알 수 없는 명령어';
    const description = commandDetails.description || '설명이 없습니다.';
    const commandTemplate = commandDetails.command_template || '';
    
    console.log('추출된 정보:', { commandName, description, commandTemplate }); // 디버깅용
    
    // 옵션 선택 HTML 생성
    let optionsHTML = '';
    if (commandDetails.available_options) {
        optionsHTML = `
            <div class="block-option">
                <label>옵션:</label>
                <select class="option-select">
                    <option value="">없음</option>
                    ${Object.entries(commandDetails.available_options).map(([key, desc]) => 
                        `<option value="${key}" title="${desc}">${key} - ${desc}</option>`
                    ).join('')}
                </select>
            </div>
        `;
    }
    
    // 템플릿에서 매개변수 추출
    const templateParams = commandTemplate.match(/\{(\w+)\}/g) || [];
    const inputFieldsHTML = templateParams.map(param => {
        const paramName = param.replace(/[{}]/g, '');
        if (paramName === 'options') return ''; // 옵션은 별도 처리
        
        return `
            <div class="block-input">
                <label>${paramName}:</label>
                <input type="text" class="param-input" data-param="${paramName}" placeholder="${paramName} 입력...">
            </div>
        `;
    }).join('');
    
    // 워크플로우 블록 HTML 생성
    const blockHTML = `
        <div class="workflow-block" id="${blockId}" style="left: ${x}px; top: ${y}px;">
            <div class="block-header">
                <span class="block-icon">&lt;/&gt;</span>
                <span class="block-name">${commandName}</span>
                <button class="delete-btn" onclick="deleteWorkflowBlock('${blockId}')">✕</button>
                <button class="play-btn">▶️</button>
            </div>
            <div class="block-content">
                <div class="block-description">${description}</div>
                ${optionsHTML}
                ${inputFieldsHTML}
            </div>
            <div class="connection-point left"></div>
            <div class="connection-point right"></div>
        </div>
    `;
    
    console.log('생성된 HTML:', blockHTML); // 디버깅용
    
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
    // 입력 필드 Enter 키 이벤트
    const inputFields = block.querySelectorAll('.param-input');
    inputFields.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const paramName = input.getAttribute('data-param');
                const value = input.value;
                console.log(`파라미터 ${paramName} 저장:`, value);
                
                // 값을 데이터 속성에 저장
                input.setAttribute('data-value', value);
                input.style.backgroundColor = '#2a4a2a'; // 저장된 것을 시각적으로 표시
            }
        });
    });
    
    // 옵션 선택 이벤트
    const optionSelect = block.querySelector('.option-select');
    if (optionSelect) {
        optionSelect.addEventListener('change', function() {
            console.log('선택된 옵션:', this.value);
        });
    }
    
    // 드래그 기능 추가
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    
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
    });
    
    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            block.style.zIndex = 2;
        }
    });
}

/**
 * 워크플로우 블록 삭제
 */
function deleteWorkflowBlock(blockId) {
    const block = document.getElementById(blockId);
    if (block) {
        block.remove();
    }
}

/**
 * 워크플로우 영역 초기화
 */
function initializeWorkflowArea() {
    const workflowArea = document.querySelector('.workflow-area');
    
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
            } else {
                console.error('명령어 상세 정보를 가져올 수 없습니다.');
            }
        }).catch(error => {
            console.error('fetchCommandDetails 오류:', error);
        });
    });
    
    // 초기화 버튼 이벤트
    const clearButton = document.querySelector('.palette-controls .control-btn:last-child');
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            const blocks = workflowArea.querySelectorAll('.workflow-block');
            blocks.forEach(block => block.remove());
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
 * 로그아웃 함수
 * 로컬 스토리지의 사용자 정보를 삭제하고 로그인 페이지로 이동
 */
function handleLogout() {
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
    
    // 로그아웃 버튼 이벤트 리스너 등록
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }
});