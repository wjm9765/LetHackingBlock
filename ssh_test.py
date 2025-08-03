import paramiko

# --- 접속 정보 ---
hostname = "bandit.labs.overthewire.org"
port = 2220
username = "bandit0"
password = "bandit0"

# 1. SSH 클라이언트 생성
ssh_client = paramiko.SSHClient()
# 처음 접속하는 서버의 호스트 키를 자동으로 수락하는 정책
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # 2. 서버에 접속
    ssh_client.connect(hostname=hostname, port=port, username=username, password=password)
    print("✅ SSH 접속 성공!")

    # 3. 실행할 쉘 명령어
    command = "pwd"

    # 4. 명령어 실행 및 결과 받아오기
    stdin, stdout, stderr = ssh_client.exec_command(command)

    # 실행 결과(stdout)와 에러(stderr)를 읽어옵니다.
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    print("\n--- 명령어 실행 결과 ---")
    if output:
        print(output)
    if error:
        print("--- 에러 발생 ---")
        print(error)

finally:
    # 5. 접속 종료 (매우 중요)
    ssh_client.close()
    print("\n✅ SSH 접속 종료.")