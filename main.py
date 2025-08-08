from nt import environ
from pickle import GLOBAL
import sys
import json
from fastapi import FastAPI
from regex import F
import boto3
import paramiko
from pathlib import Path

from sqlalchemy import false

# 프로젝트 루트를 경로에 추가하여 모듈을 임포트할 수 있도록 설정
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from HackingBlock.method import control as method_control
from HackingBlock.AI.ai_function import control_ai_function
from HackingBlock.load import USER_STATES, load_json, get_dynamodb_resource
from HackingBlock.load import load_command_json, COMMAND_BLOCK,BANDIT_SSH




def delete_user_state(user_id: str):
    """
    지정된 사용자 ID에 해당하는 상태 데이터를 DynamoDB에서 삭제합니다.
    
    Args:
        user_id: 삭제할 사용자 상태의 ID
    """
    try:
        # DynamoDB 리소스 생성
        dynamodb = boto3.resource('dynamodb', region_name="ap-northeast-2")
        table = dynamodb.Table(USER_STATES["table_name"])
        
        # 항목 삭제
        response = table.delete_item(
            Key={
                USER_STATES["key_field"]: user_id
            }
        )
        
        print(f"✅ 사용자 '{user_id}'의 상태 데이터가 성공적으로 삭제되었습니다.")
        return True
    except Exception as e:
        print(f"❌ 사용자 상태 삭제 중 오류 발생: {e}")
        return False

# 전역변수 선언 (main 함수 외부에 위치)
LAST_COMMAND = None
LAST_OUTPUT = None

def execute_command(user_id: str, environment_number: str, ssh_client: paramiko.SSHClient, command_data: dict = None):
    """
    명령어를 실행하는 함수
    
    Args:
        user_id: 사용자 ID
        environment_number: 환경 번호
        ssh_client: SSH 클라이언트
        command_data: JSON 형태로 전달된 명령어 실행 정보 (명령어 이름, 파라미터 등)
    
    Returns:
        tuple: (command_name, output) 또는 실패 시 (None, None)
    """
    global LAST_COMMAND, LAST_OUTPUT
    
    print("\n--- 명령어 실행 ---")
    
    # 사용 가능한 명령어 목록 로드
    shell_commands = load_command_json("Command_Block")
    if not shell_commands:
        print("오류: 명령어 목록을 불러오는데 실패했습니다.")
        return None, None

    # JSON 데이터가 없으면 기존 방식으로 입력 받기
    if command_data is None:
        print("사용 가능한 명령어:")
        for cmd in shell_commands:
            print(f"- {cmd['name']}: {cmd['description']}")
        
        command_name = input("실행할 명령어 이름을 입력하세요: ").strip()
    else:
        # JSON 데이터에서 명령어 이름 추출
        command_name = command_data.get("command_name", "").strip()
    
    # 명령어 블록 찾기
    command_block = next((cmd for cmd in shell_commands if cmd['name'] == command_name), None)
    
    if not command_block:
        print(f"오류: '{command_name}' 명령어를 찾을 수 없습니다.")
        return None, None
    
    # 파라미터 처리
    params = {}
    
    # JSON 데이터가 있으면 해당 파라미터 사용, 없으면 입력 받기
    if command_data and "params" in command_data:
        params = command_data["params"]
    else:
        # 옵션 처리 (명령어에 옵션이 있는 경우)
        if "available_options" in command_block:
            print(f"\n{command_name}의 사용 가능한 옵션 :")
            for opt, desc in command_block["available_options"].items():
                print(f"- {opt}: {desc}")
            
            options_input = input("사용할 옵션을 입력하세요 (없으면 엔터): ").strip()
            # 엔터키만 입력했으면 빈 문자열 할당
            params["options"] = options_input
        
        # 나머지 파라미터 처리
        template = command_block['command_template']
        import re
        # 중괄호 안의 파라미터 이름 추출 (정규식)
        param_names = re.findall(r'\{([^{}]+)\}', template)
        
        for param_name in param_names:
            if param_name != "options" or param_name not in params:  # 옵션은 이미 처리했으므로 건너뜀
                param_value = input(f"'{param_name}' 파라미터 값을 입력하세요: ").strip()
                params[param_name] = param_value

    print(f"\n'{command_name}' 명령어 실행 중...")
    
    # method_control 함수 호출 (인자 구조 일치)
    output = method_control(
        engine_type=command_block['base_block_type'],
        command_template=command_block['command_template'],
        params=params,
        block_spec=command_block,
        user_id=user_id,
        environment_number=environment_number,
        ssh_client=ssh_client  # SSH 클라이언트 전달
    )
    
    if output is False:
        print("명령어 실행에 실패했습니다. here is main.py")
        # 프론트엔드에서 이 부분을 받아서 분기 처리할 수 있도록 수정
        return None, None

    print("\n--- 실행 결과 ---")
    print(output)
    
    # 전역변수에 결과 저장
    LAST_COMMAND = command_name
    LAST_OUTPUT = output
    
    return command_name, output

def get_comment(ast_command=None, last_output=None):
    """이전 명령어 실행 결과에 대한 코멘트를 받는 함수"""
    global LAST_COMMAND, LAST_OUTPUT
    
    print("\n--- 이전 결과에 대한 코멘트 받기 ---")
    
    # 함수 인자 대신 전역변수 사용
    if not LAST_COMMAND or not LAST_OUTPUT:
        print("오류: 명령어를 최소 1번 실행해야 합니다.")
        return
        
    print("AI에게 코멘트를 요청하는 중...")
    comment = control_ai_function("comment", LAST_COMMAND, LAST_OUTPUT, user_id=None)
    print("\n--- AI 코멘트 ---")
    print(comment)

def get_pattern_recommendation(user_id: str):
    """현재 상태를 기반으로 패턴을 추천받는 함수"""
    print("\n--- 현재 상태 기반 패턴 추천받기 ---")
    print("AI에게 패턴 추천을 요청하는 중...")
    
    # 'pattern' 옵션으로 AI 함수 호출, 다른 인자는 필요 없음
    recommendation = control_ai_function("pattern", "", "", user_id)
    
    print("\n--- 추천 패턴 ---")
    print(recommendation)

    return recommendation
    
def login_ssh(level: int):
    """
    Bandit SSH 서버에 접속하기 위한 SSH 클라이언트를 생성합니다.
    
    Args:
        level: Bandit 레벨 번호
        
    Returns:
        paramiko.SSHClient: 접속된 SSH 클라이언트 또는 접속 실패 시 None
    """
    try:
        
        # load.py의 함수를 사용하여 레벨에 해당하는 접속 정보 조회
        item = load_json(BANDIT_SSH, str(level))
        
        # 접속 정보가 없는 경우 처리
        if not item:
            print(f"❌ 레벨 {level}에 대한 접속 정보를 찾을 수 없습니다.")
            return False
        
        # 접속 정보 추출
        username = item.get("id")
        password = item.get("password")
        
        if not username or not password:
            print(f"❌ 레벨 {level}의 접속 정보가 불완전합니다.")
            return False
        
        # 고정 접속 정보
        hostname = "bandit.labs.overthewire.org"
        port = 2220
        
        print(f"🔄 SSH 접속 시도 중: {username}@{hostname}:{port} (레벨 {level})")
        
        # SSH 클라이언트 생성
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 접속
        ssh_client.connect(
            hostname=hostname,
            port=port,
            username=username,
            password=password
        )
        
        print(f"✅ SSH 접속 성공: {username}@{hostname}")
        return ssh_client
        
    except paramiko.AuthenticationException:
        print("❌ 인증 실패: 사용자 이름 또는 비밀번호가 잘못되었습니다.")
        return False
    except paramiko.SSHException as e:
        print(f"❌ SSH 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False


app = FastAPI()





@app.post("/api/login_ssh")
async def login_ssh_api(level: int):
    ssh_client = login_ssh(level)
    if ssh_client:
        return {"success": True, "message": "SSH 접속 성공"}
    else:
        return {"success": False, "message": "SSH 접속 실패"}


@app.post("/api/execute_command")
async def execute_command_api(command_block : json):
    command_name, output = execute_command(
        user_id=command_block.get("user_id", ""),
        environment_number=command_block.get("environment_number", ""),
        ssh_client=login_ssh(command_block.get("environment_number", "")),
        command_data=command_block
    )

    return {
        "command_name": command_name,
        "output": output
    }




@app.post("/api/delete_user_state")
async def delete_user_state(user_id: str):
    """
    사용자 상태를 삭제하는 API 엔드포인트
    """
    # 사용자 상태 삭제 로직
    result = delete_user_state(user_id)
    return {"success": result, "user_id": user_id}


@app.get("/api/return_environment")
async def return_environment():
    """
    모든 환경 정보를 반환하는 API 엔드포인트
    Returns:
        JSON 형태의 환경 목록 (level과 goal을 매칭)
    """
    # DynamoDB 리소스 얻기
    dynamodb = get_dynamodb_resource()
    
    # BANDIT_SSH 테이블 접근
    table = dynamodb.Table(BANDIT_SSH["table_name"])
    
    # 전체 테이블 스캔
    response = table.scan()
    items = response.get('Items', [])
    
    # 페이지네이션 처리
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    
    # level과 goal 정보만 포함하는 딕셔너리 생성
    result = []
    for item in items:
        level = item.get(BANDIT_SSH["key_field"])
        goal = item.get("goal", "")
        
        # 필요한 정보만 포함
        result.append({
            "level": level,
            "goal": goal
        })
    
    # 레벨 기준으로 정렬 (숫자 정렬)
    result.sort(key=lambda x: int(x["level"]) if x["level"].isdigit() else 999)
    
    return {"environments": result}

@app.get("/api/return_commands")
async def return_commands():
    """
    모든 명령어 정보를 반환하는 API 엔드포인트
    Returns:
        JSON 형태의 명령어 목록 (command_name과 description을 매칭)
    """
    # 명령어 목록 로드
    commands = load_command_json("Command_Block")
    
    # 명령어와 설명만 포함하는 결과 생성
    result = []
    for command in commands:
        command_name = command.get("name", "")
        description = command.get("description", "")
        
        # 필요한 정보만 포함
        result.append({
            "command_name": command_name,
            "description": description
        })
    
    # 명령어 이름 기준으로 정렬
    result.sort(key=lambda x: x["command_name"])
    
    return {"commands": result}

@app.get("/api/return_ai_comment")
async def return_ai_comment():
    """
    AI 코멘트를 반환하는 API 엔드포인트
    Returns:
        JSON 형태의 AI 코멘트
    """
    # AI 코멘트 생성 로직
    ai_comment = get_comment()
    return {"ai_comment": ai_comment}


@app.post("/api/return_ai_pattern")
async def return_ai_pattern(user_id: str):
    """
    AI 패턴 추천을 반환하는 API 엔드포인트
    Returns:
        JSON 형태의 AI 추천 패턴
    """
    # AI 패턴 추천 생성 로직
    ai_pattern = get_pattern_recommendation(user_id)
    return {"ai_pattern": ai_pattern}





# #테스트 메인 함수
# def display_menu():
#     """메인 메뉴를 출력하는 함수"""
#     print("\n" + "="*50)
#     print("HackingBlock CLI")
#     print("="*50)
#     print("1. 명령어 실행")
#     print("2. 이전 명령어 실행 결과에 대한 코멘트 받기")
#     print("3. 현재 상태를 기반으로 패턴 추천받기")
#     print("4. 종료")
#     print("="*50)
    




# def main():
#     """메인 루프를 실행하는 함수"""
#     print("사용자 아이디를 입력하세요")
#     user_id = input("User ID: ").strip()
#     print("해킹 환경 번호를 입력하세요")
#     environment_number = input("Environment Number: ").strip()
    
#     ssh_client = login_ssh(environment_number)

#     if(ssh_client is False):
#         print("SSH 접속에 실패했습니다. 프로그램을 종료합니다.")
#         return
    


#     while True:
#         display_menu()
#         choice = input("원하는 작업의 번호를 입력하세요: ").strip()
        
#         if choice == '1':
#             execute_command(user_id, environment_number,ssh_client)
#             # 결과는 전역변수에 저장되므로 반환값을 사용할 필요 없음
#         elif choice == '2':
#             get_comment()
#         elif choice == '3':
#             get_pattern_recommendation(user_id)
#         elif choice == '4':
            

#             ssh_client.close() 
#             print("SSH 접속을 종료합니다.")

#             # 사용자 상태 삭제
#             delete_user_state(user_id)
#             print("프로그램을 종료합니다.")
#             break
#         else:
#             print("잘못된 입력입니다. 1, 2, 3, 4 중 하나를 입력하세요.")

# if __name__ == "__main__":
#     main()
