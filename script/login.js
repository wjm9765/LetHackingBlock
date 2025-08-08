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
    
    // 로컬 스토리지에 사용자 정보 저장
    localStorage.setItem('username', username);
    
    // 선택된 권한 확인 (추가 기능)
    const selectedItems = document.querySelectorAll('.item.selected');
    const permissions = Array.from(selectedItems).map(item => {
        const number = item.querySelector('.item-number').textContent;
        const description = item.querySelector('.item-description').textContent;
        return { number, description };
    });
    
    // 권한 정보가 있으면 로컬 스토리지에 저장
    if (permissions.length > 0) {
        localStorage.setItem('permissions', JSON.stringify(permissions));
    }
    
    console.log('로그인 성공:', username);
    
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
            this.classList.toggle('selected');
        });
    });
}

// 페이지 로드 시 실행되는 초기화 함수
document.addEventListener('DOMContentLoaded', function() {
    // 이미 로그인된 사용자가 있는지 확인
    const username = localStorage.getItem('username');
    if (username) {
        // 이미 로그인되어 있으면 메인 페이지로 이동 (선택적)
        // window.location.href = '../html/main.html';
    }
    
    // 권한 항목 클릭 이벤트 초기화
    initializeItems();
    
    // 로그인 버튼에 이벤트 리스너 추가
    const loginButton = document.querySelector('.login-button');
    if (loginButton) {
        loginButton.addEventListener('click', handleLogin);
    }
});