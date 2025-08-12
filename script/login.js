
const API_ENDPOINT = 'http://127.0.0.1:8000'; 
/**
 * 환경 정보를 가져오는 함수
 * API 서버에서 환경 목록을 가져와 화면에 표시
 */
async function fetchEnvironments() {
    try {
        // 로딩 상태 표시
        const itemsContainer = document.querySelector('.items-container');
        itemsContainer.innerHTML = '<div class="loading">데이터를 불러오는 중...</div>';
        
        // API 요청
        const response = await fetch(`${API_ENDPOINT}/api/return_environment`);
        
        if (!response.ok) {
            throw new Error(`API 응답 오류: ${response.status}`);
        }
        
        // JSON 데이터 파싱
        const data = await response.json();
        
        // 환경 목록 표시
        displayEnvironments(data.environments || []);
        
    } catch (error) {
        console.error('환경 정보 로드 실패:', error);
        
        // 오류 메시지 표시
        const itemsContainer = document.querySelector('.items-container');
        itemsContainer.innerHTML = `
            <div class="error-message">
                <p>환경 정보를 불러올 수 없습니다.</p>
                <p>오류: ${error.message}</p>
                <button onclick="fetchEnvironments()">다시 시도</button>
            </div>
        `;
    }
}

/**
 * 환경 목록을 화면에 표시하는 함수
 * @param {Array} environments - 환경 정보 배열
 */
function displayEnvironments(environments) {
    const itemsContainer = document.querySelector('.items-container');
    
    // 목록이 비어있는 경우
    if (!environments || environments.length === 0) {
        itemsContainer.innerHTML = '<div class="empty-message">사용 가능한 환경이 없습니다.</div>';
        return;
    }
    
    // 각 환경에 대한 HTML 생성
    const environmentsHTML = environments.map(env => `
        <div class="item" data-level="${env.hack_environment}">
            <div class="item-content">
                <span class="item-number">${env.hack_environment}</span>
                <span class="item-description">${env.goal_description || '설명 없음'}</span>
            </div>
        </div>
    `).join('');
    
    // HTML 삽입
    itemsContainer.innerHTML = environmentsHTML;
    
    // 항목 클릭 이벤트 리스너 추가
    initializeItems();
}

/**
 * 로그인 처리 함수
 * 사용자 입력을 검증하고 로컬 스토리지에 저장한 후 메인 페이지로 이동
 */
function handleLogin() {
    // 사용자 입력 가져오기
    const username = document.getElementById('username').value;
    
    // 입력값 검증
    if (username.trim() === '') {
        alert('유저이름을 입력해주세요.');
        return;
    }
    
    // 선택된 환경 확인
    const selectedItem = document.querySelector('.item.selected');
    if (!selectedItem) {
        alert('환경을 선택해주세요.');
        return;
    }
    
    // 선택된 레벨 가져오기
    const level = selectedItem.dataset.level;
    
    // 로컬 스토리지에 사용자 정보 저장
    localStorage.setItem('username', username);
    localStorage.setItem('level', level);
    
    console.log('로그인 성공:', username, 'Level:', level);
    
    // 메인 페이지로 이동
    window.location.href = '../html/main.html';
}

/**
 * 권한 항목 선택 처리 함수
 * 권한 목록에서 항목 클릭 시 선택 상태를 토글
 */
function initializeItems() {
    const items = document.querySelectorAll('.item');
    
    items.forEach(item => {
        item.addEventListener('click', function() {
            // 이전에 선택된 항목 선택 해제
            document.querySelectorAll('.item.selected').forEach(selected => {
                selected.classList.remove('selected');
            });
            
            // 현재 항목 선택
            this.classList.add('selected');
        });
    });
}

// 페이지 로드 시 실행되는 초기화 함수
document.addEventListener('DOMContentLoaded', function() {
    // 환경 정보 로드
    fetchEnvironments();
    
    // 로그인 버튼에 이벤트 리스너 추가
    const loginButton = document.querySelector('.login-button');
    if (loginButton) {
        loginButton.addEventListener('click', handleLogin);
    }
});