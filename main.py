import os
import sys
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
import paramiko
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware


# 프로젝트 루트를 경로에 추가하여 모듈을 임포트할 수 있도록 설정
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from HackingBlock.method import control as method_control
from HackingBlock.AI.ai_function import control_ai_function
from HackingBlock.load import USER_STATES, load_json, get_dynamodb_resource
from HackingBlock.load import load_command_json, COMMAND_BLOCK, BANDIT_SSH

def delete_user_state(user_id: str):
    """
    지정된 사용자 ID에 해당하는 상태 데이터를 DynamoDB에서 삭제합니다.
    
    Args:
        user_id: 삭제할 사용자 상태의 ID
    """
    global SSH_CLIENT  # 전역 변수 사용 선언
    
    try:
        # SSH 연결이 있으면 종료
        if SSH_CLIENT and SSH_CLIENT is not False:
            try:
                SSH_CLIENT.close()
                SSH_CLIENT = None
                print(f"✅ SSH 연결이 종료되었습니다.")
            except Exception as ssh_error:
                print(f"⚠️ SSH 연결 종료 중 오류: {ssh_error}")
        
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
SSH_CLIENT = None  # SSH 클라이언트 전역 변수 추가

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
        return None, None, False

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
        return None, None, False

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
        return None, None , False

    print("\n--- 실행 결과 ---")
    print(output)
    
    # 전역변수에 결과 저장
    LAST_COMMAND = command_name
    LAST_OUTPUT = output
    
    return command_name, output, True

def get_pattern_recommendation(user_id: str):
    """현재 상태 기반으로 패턴을 추천받는 함수"""
    print("\n--- 현재 상태 기반 패턴 추천받기 ---")
    print("AI에게 패턴 추천을 요청하는 중...")
    
    # 'pattern' 옵션으로 AI 함수 호출, 다른 인자는 필요 없음
    recommendation = control_ai_function("pattern", "", "", user_id)
    
    print("\n--- 추천 패턴 ---")
    print(recommendation)

    # AI로부터 받은 응답을 파싱하여 구조화된 형식으로 변환
    try:
        # AI 응답을 파싱하여 구조화된 형식으로 변환
        structured_patterns = parse_ai_pattern_response(recommendation)
        return structured_patterns
    except Exception as e:
        print(f"패턴 파싱 중 오류 발생: {e}")
        # 파싱 실패 시 원본 응답 반환
        return {"raw_response": recommendation}

def parse_ai_pattern_response(ai_response: str):
    """
    AI 응답을 구조화된 패턴 형식으로 변환하는 함수
    
    Args:
        ai_response: AI로부터 받은 원본 응답 텍스트
    
    Returns:
        dict: 구조화된 패턴 정보
    """
    try:
        patterns = []
        
        # AI 응답을 줄 단위로 분할
        lines = ai_response.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 패턴 번호 감지 (1., 2., 3. 등)
            if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                pattern_commands = []
                purpose = ""
                expect = ""
                
                # 다음 줄부터 패턴 정보 파싱
                i += 1
                
                # 명령어 추출 (대괄호로 시작하는 줄들)
                while i < len(lines) and lines[i].strip().startswith('[') and not '[이 패턴의 목적]' in lines[i]:
                    cmd_line = lines[i].strip()
                    if cmd_line.startswith('[') and cmd_line.endswith(']'):
                        command = cmd_line[1:-1]  # 대괄호 제거
                        pattern_commands.append(command)
                    i += 1
                
                # [이 패턴의 목적] 찾기
                if i < len(lines) and '[이 패턴의 목적]' in lines[i]:
                    i += 1
                    # 목적 내용 수집 ([기대할 수 있는 결과]가 나올 때까지)
                    purpose_lines = []
                    while i < len(lines) and '[기대할 수 있는 결과]' not in lines[i]:
                        purpose_lines.append(lines[i].strip())
                        i += 1
                    purpose = ' '.join(purpose_lines).strip()
                
                # [기대할 수 있는 결과] 찾기
                if i < len(lines) and '[기대할 수 있는 결과]' in lines[i]:
                    i += 1
                    # 기대 결과 내용 수집 (다음 숫자 패턴이 나올 때까지)
                    expect_lines = []
                    while i < len(lines):
                        next_line = lines[i].strip()
                        # 다음 패턴 번호가 나오면 중단
                        if next_line.startswith('1.') or next_line.startswith('2.') or next_line.startswith('3.'):
                            break
                        expect_lines.append(next_line)
                        i += 1
                    expect = ' '.join(expect_lines).strip()
                
                # 패턴 추가
                if pattern_commands:
                    patterns.append({
                        "pattern": pattern_commands,
                        "purpose": purpose,
                        "expect": expect
                    })
                
                # i는 이미 다음 패턴의 위치에 있으므로 continue
                continue
            
            i += 1
        
        # 패턴이 없으면 기본 구조 반환
        if not patterns:
            patterns = [
                {
                    "pattern": ["ls -al", "cat ./flag.txt", "grep 'password' flag.txt"],
                    "purpose": "기본 파일 탐색 및 내용 확인",
                    "expect": "파일 구조 파악 및 중요한 정보 발견"
                }
            ]
        
        return {"patterns": patterns}
        
    except Exception as e:
        print(f"패턴 파싱 오류: {e}")
        return {
            "patterns": [
                {
                    "pattern": ["ls -al", "cat ./flag.txt", "grep 'password' flag.txt"],
                    "purpose": "기본 파일 탐색 및 내용 확인",
                    "expect": "파일 구조 파악 및 중요한 정보 발견"
                }
            ]
        }

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



# FastAPI 애플리케이션 생성
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],  # 프론트엔드 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델 추가
class CommandRequest(BaseModel):
    user_id: str
    environment_number: str
    command_name: str
    params: dict = {}

class Answer(BaseModel):
    answer : str
    level: int

class UserRequest(BaseModel):
    user_id: str

class LevelRequest(BaseModel):
    level: int

class CommandSearchRequest(BaseModel):
    search_term: str

# API 엔드포인트 수정
@app.post("/api/login_ssh")
async def login_ssh_api(request: LevelRequest):
    global SSH_CLIENT  # 전역 변수 사용
    
    # 기존 SSH 연결이 있다면 종료
    if SSH_CLIENT and SSH_CLIENT is not False:
        try:
            SSH_CLIENT.close()
        except:
            pass
    
    SSH_CLIENT = login_ssh(request.level)
    
    if SSH_CLIENT:
        return {"success": True, "message": "SSH 접속 성공"}
    else:
        return {"success": False, "message": "SSH 접속 실패"}

@app.post("/api/execute_command")
async def execute_command_api(request: CommandRequest):
    global SSH_CLIENT  # 전역 변수 사용
    
    # 전역 SSH 클라이언트가 없거나 연결이 끊어진 경우 에러 반환
    if SSH_CLIENT is None or SSH_CLIENT is False:
        raise HTTPException(status_code=400, detail="SSH 연결이 필요합니다. 먼저 /api/login_ssh를 호출하세요.")
    
    try:
        command_data = {
            "command_name": request.command_name,
            "params": request.params
        }
        
        command_name, output , success = execute_command(
            user_id=request.user_id,
            environment_number=request.environment_number,
            ssh_client=SSH_CLIENT,  # 전역 SSH 클라이언트 사용
            command_data=command_data
        )
        
        if command_name is None or output is None:
            if success is False:
                print("명령어 실행에 실패했습니다. excute_command_api")
                raise HTTPException(status_code=400, success=False, detail="명령어 실행에 실패했습니다.")

        print(f"실행결과 at fastapi: {output}")



        return {
            "success": True,
            "command_name": command_name,
            "output": output
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"명령어 실행 중 오류 발생: {str(e)}")

@app.delete("/api/delete_user_state")
async def delete_user_state_api(request: UserRequest):
    result = delete_user_state(request.user_id)
    return {"success": result, "user_id": request.user_id}

@app.post("/api/return_ai_pattern")
async def return_ai_pattern_api(request: UserRequest):
    """
    AI 패턴 추천을 반환하는 API 엔드포인트
    Returns:
        JSON 형태의 구조화된 패턴 정보
    """
    try:
        ai_pattern = get_pattern_recommendation(request.user_id)
        return ai_pattern
    except Exception as e:
        print(f"AI 패턴 추천 중 오류 발생: {e}")
        # 오류 발생 시 기본 패턴 반환
        raise HTTPException(status_code=500, detail=f"AI 패턴 추천 중 오류 발생: {str(e)}")


    

def get_comment():
    """이전 명령어 실행 결과에 대한 AI 코멘트를 반환하는 함수"""
    global LAST_COMMAND, LAST_OUTPUT
    
    if not LAST_COMMAND or not LAST_OUTPUT:
        print("이전 명령어가 없습니다. 최소 1번 명령어를 실행해야 합니다.")
        return "명령어를 최소 1번 실행해야 합니다. 또는 실행한 명령어 결과가 없습니다."
    
    try:
        # control_ai_function 호출 시 user_id는 None으로 설정
        comment = control_ai_function("comment", LAST_COMMAND, LAST_OUTPUT, user_id=None)
        print(f"AI 코멘트 생성 결과: {comment}")
        return comment
    except Exception as e:
        print(f"AI 코멘트 생성 중 오류 발생: {e}")
        return "AI 코멘트 생성 중 오류 발생"

@app.get("/api/return_ai_comment")
async def return_ai_comment_api():
    """
    이전 명령어 실행 결과에 대한 AI 코멘트를 반환하는 API 엔드포인트
    Returns:
        JSON 형태의 AI 코멘트
    """
    global LAST_COMMAND, LAST_OUTPUT
    
    if not LAST_COMMAND or not LAST_OUTPUT:
        print("이전 명령어가 없습니다. 최소 1번 명령어를 실행해야 합니다.")
        comment = "명령어를 최소 1번 실행해야 합니다. 또는 실행한 명령어 결과가 없습니다."
        return {"ai_comment": comment}

    try:
        comment = control_ai_function("comment", LAST_COMMAND, LAST_OUTPUT, user_id=None)
        print(f"AI 코멘트 생성 결과: {comment}")

        return {"ai_comment": comment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 코멘트 생성 중 오류 발생: {str(e)}")



@app.get("/api/return_environment")
async def return_environment():
    """
    모든 환경 정보를 반환하는 API 엔드포인트
    Returns:
        JSON 형태의 환경 목록 (hack_environment와 goal_description을 매칭)
    """
    try:
        # DynamoDB 리소스 얻기
        dynamodb = get_dynamodb_resource()
        if not dynamodb:
            raise HTTPException(status_code=500, detail="DynamoDB 연결 실패")
        
        # STATE_INITIAL 테이블 접근
        table = dynamodb.Table("State_initial")
        
        # 전체 테이블 스캔
        response = table.scan()
        items = response.get('Items', [])
        
        # 페이지네이션 처리 (DynamoDB는 한 번에 1MB 제한이 있음)
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        # hack_environment와 goal_description 정보만 포함하는 딕셔너리 생성
        result = []
        for item in items:
            hack_environment = item.get("hack_enviornment")
            goal_description = item.get("mission", {}).get("goal_description", "")
            
            # 필요한 정보만 포함
            result.append({
                "hack_environment": hack_environment,
                "goal_description": goal_description
            })
        
        # hack_environment 기준으로 정렬 (숫자 정렬)
        result.sort(key=lambda x: int(x["hack_environment"]) if str(x["hack_environment"]).isdigit() else 999)
        

       
        return {"environments": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"환경 정보 로드 중 오류 발생: {str(e)}")

@app.post("/api/correct_answer")
async def correct_answer(request: Answer):
    """
    사용자가 입력한 정답을 비교하는 API 엔드포인트
    """

    level = request.level + 1 # 레벨은 user_id로 전달된다고 가정
    # load.py의 함수를 사용하여 레벨에 해당하는 접속 정보 조회
    item = load_json(BANDIT_SSH, str(level))

    # 비밀번호 정보 추출
    password = item.get("password")

    if(password == request.answer):
        print(f"정답입니다! ")
        return{
            "success": True
        }
    else:
        print("오답입니다")
        return{
            "success": False,
        }
    

        
    
@app.post("/api/return_commands")
async def return_commands(request: CommandSearchRequest):
    """
    명령어 정보를 반환하는 API 엔드포인트
    Args:
        request: search_term이 "all"이면 전체 명령어, 아니면 특정 명령어 검색
    Returns:
        JSON 형태의 명령어 목록 또는 특정 명령어 정보
    """
    try:
        # 명령어 목록 로드
        commands = load_command_json("Command_Block")
        
        if not commands:
            raise HTTPException(status_code=500, detail="명령어 목록 로드 실패")
        
        search_term = request.search_term.strip()
        
        # "all"인 경우 전체 명령어 목록 반환
        if search_term.lower() == "all":
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
        
        # 특정 명령어 검색
        else:
            # 해당 명령어 블록 찾기
            command_block = next((cmd for cmd in commands if cmd.get('name') == search_term), None)
            
            if not command_block:
                raise HTTPException(status_code=404, detail=f"명령어 '{search_term}'를 찾을 수 없습니다.")

            print(f"명령어 '{command_block['name']}' 정보 반환")

            # 전체 명령어 블록 정보 반환
            return {"command": command_block}
        
    except HTTPException:
        # HTTPException은 그대로 다시 발생시킴
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"명령어 정보 로드 중 오류 발생: {str(e)}")



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

if __name__ == "__main__":
    import uvicorn
    # app 객체 대신 "main:app" 문자열로 전달
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)