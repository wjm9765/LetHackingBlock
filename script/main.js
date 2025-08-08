/**
 * 사용자 정보 표시 함수
 * 로컬 스토리지에서 사용자 정보를 가져와 화면에 표시
 */



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
    
    // 로그아웃 버튼 이벤트 리스너 등록
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }
});