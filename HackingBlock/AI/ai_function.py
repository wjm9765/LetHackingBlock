import openai
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import sys

# load.py import를 위한 경로 설정
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# load.py에서 함수와 변수들 import
from load import (
    SHELL_COMMAND_LIST_PATH,
    SHELL_META_PATH, 
    CURRENT_STATE_PATH,
    load_file,
    load_json
)

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정 (.env 파일에서 가져오기)
openai.api_key = os.getenv("OPENAI_API_KEY")

# API 키가 제대로 로드되었는지 확인
if not openai.api_key:
    print("⚠️ Warning: OPENAI_API_KEY not found in .env file")
    print("📝 Please add OPENAI_API_KEY=your_api_key_here to your .env file")
else:
    print("✅ OpenAI API key loaded successfully")

def get_hacking_comment(command_name: str, output: str) -> str:
    """
    주어진 명령어와 결과에 대해 GPT-4o mini 모델을 사용하여 해킹 관련 코멘트를 생성합니다.

    :param command_name: 실행된 명령어 이름
    :param output: 명령어 실행 결과
    :return: GPT 모델이 생성한 해킹 코멘트
    """
    # API 키 체크
    if not openai.api_key:
        return "Error: OpenAI API key not configured. Please check your .env file."
    
    try:
        prompt = f"이 {command_name}으로 수행한 ouput 결과가 다음과 같을 때, 각각의 결과에 해킹에 도움이 될만한 짧은 한줄 해킹 코멘트를 달아주세요, 코멘트 이외의 불필요한 대답은 하지마\n\n{output}"

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant specializing in cybersecurity."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def recommend_hacking_patterns(state_data: dict, shell_commands: list, shell_meta: str, target_goal: str = "general_penetration") -> str:
    """
    현재 상태를 기반으로 해킹 패턴을 추천받습니다.
    
    :param state_data: 현재 state.json 데이터 (그대로 전송)
    :param shell_commands: 사용 가능한 shell 명령어 리스트
    :param shell_meta: shell 메타 정보
    :param target_goal: 해킹 목표 (기본값: general_penetration)
    :return: GPT가 추천한 해킹 패턴
    """
    # API 키 체크
    if not openai.api_key:
        return "Error: OpenAI API key not configured. Please check your .env file."
    
    # state.json을 문자열로 변환 (그대로 전송)
    state_json_str = json.dumps(state_data, indent=2, ensure_ascii=False)
    
    # 사용 가능한 명령어 리스트 생성
    available_commands = "\n".join([f"- {cmd}" for cmd in shell_commands])
    
    # GPT 프롬프트 생성
    prompt = f"""
현재 해킹 진행 상황과 사용 가능한 명령어를 기반으로 다음 해킹 패턴을 추천해주세요.

=== 현재 State 정보 (JSON) ===(history는 그동안 사용했던 명령어 목록입니다, 저장된 결과는 명령어 실행 순서에 따라 [번호]로 구분된다)
{state_json_str}

=== 사용 가능한 Shell 명령어 ===
{available_commands}

=== Shell 메타 정보 ===
{shell_meta}

=== 해킹 목표 ===
현재 State 정보에 들어있는 goal_description

=== 요구사항 ===
1. 총 1~3개의 패턴을 제시하세요
2. 각 패턴은 1~4개의 명령어 블록을 사용하세요
3. 위의 Shell 명령어 리스트에 있는 명령어만 사용하세요
4. 현재 state.json 데이터를 분석하여, history(지금까지 실행했던 명령어 기록)이후에 실행하면 도움이 될 것 같은 패턴을 제시하세요
5. 각 패턴에 대해 목적과 예상 결과를 설명하세요

=== 응답 형식 ===
1.
- 명령어: [명령어1],[명령어2],[명령어3],[명령어4]
- 목적: [이 패턴의 목적]
- 예상 결과: [기대할 수 있는 결과]

2.
- 명령어: [명령어1],[명령어2],[명령어3]
- 목적: [이 패턴의 목적]
- 예상 결과: [기대할 수 있는 결과]

3.
- 명령어: [명령어1],[명령어2]
- 목적: [이 패턴의 목적]
- 예상 결과: [기대할 수 있는 결과]

예시)
1.
- 명령어: ls_command,cat_command
- 목적: 시스템 파일 구조를 파악하고 중요한 파일을 찾기
- 예상 결과: /etc/passwd 파일을 통해 사용자 정보를 확인할 수 있음
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert cybersecurity consultant specializing in penetration testing and ethical hacking. Analyze the provided state.json data to understand the current hacking progress and recommend strategic next steps."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating hacking patterns: {e}"

def control_ai_function(option: str, last_command: str, output: str) -> str:
    """
    AI 기능을 제어하는 메인 함수
    
    :param option: "comment" 또는 "pattern" - 실행할 기능 선택
    :param last_command: 마지막으로 실행된 명령어 이름
    :param output: 명령어 실행 결과
    :return: 코멘트 또는 패턴 추천 결과
    """
    if option.lower() == "comment":
        # 코멘트 옵션: get_hacking_comment 실행
        return get_hacking_comment(last_command, output)
    
    elif option.lower() == "pattern":
        # 패턴 추천 옵션: load.py의 함수와 변수를 사용하여 파일 로드
        
        # load.py에서 import한 함수와 변수 사용
        current_state = load_json(CURRENT_STATE_PATH)
        shell_commands = load_file(SHELL_COMMAND_LIST_PATH)
        shell_meta_lines = load_file(SHELL_META_PATH)
        shell_meta = "\n".join(shell_meta_lines)  # 리스트를 문자열로 변환
        
        # 파일 로드 실패 시 기본값 사용
        if not current_state:
            print("❌ Failed to load current state, using default state.")
            current_state = {
                "command_history": [last_command],
                "last_output": output,
                "goal_description": "general_penetration"
            }
        
        if not shell_commands:
            print("❌ Failed to load shell commands, using default commands.")
            shell_commands = [
                "ls_command", "ps_command", "netstat_command", "find_command",
                "cat_command", "grep_command", "whoami_command", "uname_command",
                "ifconfig_command", "nmap_command", "wget_command", "curl_command"
            ]
        
        # 패턴 추천 실행
        pattern_result = recommend_hacking_patterns(
            state_data=current_state,
            shell_commands=shell_commands,
            shell_meta=shell_meta
        )
        
        return pattern_result
    
    else:
        return f"Error: Invalid option '{option}'. Use 'comment' or 'pattern'."

# def test_pattern_recommendation():
#     """
#     패턴 추천 함수 테스트
#     """
#     print("🎯 Testing hacking pattern recommendation...")
#     print("="*60)
    
#     # load.py의 함수와 변수를 사용하여 파일 로드
#     current_state = load_json(CURRENT_STATE_PATH)
#     shell_commands = load_file(SHELL_COMMAND_LIST_PATH)
#     shell_meta_lines = load_file(SHELL_META_PATH)
#     shell_meta = "\n".join(shell_meta_lines)
    
#     if not current_state:
#         print("❌ Could not load state.json. Using mock data...")
#         current_state = {
#             "command_history": ["ps_command", "netstat_command", "whoami_command"],
#             "system_info": {
#                 "processes": [
#                     {"pid": "1001", "name": "apache2", "user": "www-data"},
#                     {"pid": "1002", "name": "mysql", "user": "mysql"},
#                     {"pid": "1005", "name": "ssh", "user": "root"}
#                 ],
#                 "user_privileges": [
#                     {"user": "current_user", "privilege": "standard"}
#                 ]
#             },
#             "network_info": {
#                 "listening_ports": [
#                     {"port": "22", "service": "ssh", "state": "open"},
#                     {"port": "80", "service": "http", "state": "open"},
#                     {"port": "443", "service": "https", "state": "open"},
#                     {"port": "3306", "service": "mysql", "state": "open"}
#                 ]
#             },
#             "session": {
#                 "current_user": "user",
#                 "current_path": "/home/user"
#             },
#             "file_system": {
#                 "found_files": [
#                     "/etc/passwd", "/home/user/.bash_history", "/var/www/html/.htaccess"
#                 ]
#             }
#         }
    
#     if not shell_commands:
#         print("❌ Could not load shell commands. Using default list...")
#         shell_commands = [
#             "ls_command", "ps_command", "netstat_command", "find_command",
#             "cat_command", "grep_command", "whoami_command", "uname_command",
#             "ifconfig_command", "nmap_command", "wget_command", "curl_command",
#             "chmod_command", "chown_command", "sudo_command", "su_command"
#         ]
    
#     print("📊 Current State Data:")
#     print("-" * 40)
#     print(json.dumps(current_state, indent=2, ensure_ascii=False)[:500] + "...")
#     print("-" * 40)
    
#     print(f"\n🔧 Available Commands: {len(shell_commands)} commands")
#     print(f"📜 Shell Meta Info: {'Loaded' if shell_meta else 'Not available'}")
    
#     print("\n🤖 Generating hacking pattern recommendations...")
#     print("⏳ Please wait...")
    
#     # 패턴 추천 실행
#     patterns = recommend_hacking_patterns(
#         state_data=current_state,
#         shell_commands=shell_commands,
#         shell_meta=shell_meta,
#         target_goal="privilege_escalation_and_data_collection"
#     )
    
#     print("\n💡 RECOMMENDED HACKING PATTERNS:")
#     print("="*60)
#     print(patterns)
#     print("="*60)
    
#     print("\n🎉 Pattern recommendation test completed!")

# def main():
#     """
#     메인 함수 - nmap 테스트와 패턴 추천 테스트 실행
#     """
#     print("🎯 Starting AI function tests...")
#     print("="*60)
    
#     # 기존 nmap 테스트
#     print("📡 NMAP HACKING COMMENT TEST:")
#     nmap_output = """Starting Nmap 7.80 ( https://nmap.org ) at 2024-07-22 10:30 KST
# Nmap scan report for target.example.com (192.168.1.100)
# Host is up (0.0023s latency).
# Not shown: 997 closed ports
# PORT     STATE SERVICE
# 22/tcp   open  ssh
# 80/tcp   open  http
# 443/tcp  open  https
# 3306/tcp open  mysql"""
    
#     hacking_comment = get_hacking_comment("nmap_command", nmap_output)
#     print(f"💡 Nmap Analysis: {hacking_comment}")
    
#     print("\n" + "="*60)
    
#     # 패턴 추천 테스트
#     test_pattern_recommendation()

# if __name__ == "__main__":
#     # 메인 테스트 실행
#     main()

