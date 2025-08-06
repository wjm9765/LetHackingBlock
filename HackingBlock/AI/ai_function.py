import openai
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import sys
from AI.count_token import count_tokens

# load.py import를 위한 경로 설정
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# DB 연결을 위한 import로 변경
from load import (
    load_json, 
    load_file,
    USER_STATES,
    TO_AI_INFORMATION
)

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
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

        token_count = count_tokens(prompt, model="gpt-4o-mini")
        if(token_count > 6000):
            return f"Error: The prompt exceeds the token limit for gpt-4o model. Current token count: {token_count}. Please reduce the input size."

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

=== 현재 state 정보 (JSON) ===(history는 그동안 사용했던 명령어 목록입니다, 저장된 결과는 명령어 실행 순서에 따라 [번호]로 구분된다)
{state_json_str}

=== 사용 가능한 Shell 명령어 ===
{available_commands}

=== Shell 메타 정보 ===
{shell_meta}

=== 해킹 목표 ===
현재 State 정보에 들어있는 goal_description

=== 요구사항 ===
1. 총 1~3개의 명령어 순서 패턴을 제시하세요
2. 각 패턴은 1~4개의 명령어 블록을 사용하세요 (실행 순서에 따라 명령어 나열, 쉘에 바로 입력할 수 있는 형태로 제시)
3. 위의 Shell 명령어 리스트에 있는 명령어만 사용하세요. 리눅스 메타 정보를 읽고 입출력에 필요한 메타 정보를 함께 제공해. 예시) "-" 파일을 읽어야 할 때 : cat ./- , flag test.txt 파일을 읽어야 할 때 : cat flag\ test.txt
4. 현재 state.json의 goal을 분석하여(현재 해킹 상태를 요약한 정보), history(지금까지 실행했던 명령어 기록)이후에 실행하면 도움이 될 것 같은 패턴을 제시하세요
5. 각 패턴에 대해 목적과 예상 결과를 한국어로 설명하세요

=== 응답 형식 ===
1.
- 명령어: [명령어1]->[명령어2]->[명령어3]->[명령어4]
- 목적: [이 패턴의 목적]
- 예상 결과: [기대할 수 있는 결과]

2.
- 명령어: [명령어1]->[명령어2]->[명령어3]
- 목적: [이 패턴의 목적]
- 예상 결과: [기대할 수 있는 결과]

3.
- 명령어: [명령어1] -> [명령어2]
- 목적: [이 패턴의 목적]
- 예상 결과: [기대할 수 있는 결과]

예시)
1.
- 명령어: [ls -al] -> [cat ./-] -> [grep "password" flag.txt]
- 목적: 시스템 파일 구조를 파악하고 중요한 파일을 찾기
- 예상 결과: /etc/passwd 파일을 통해 사용자 정보를 확인할 수 있음

1.
- 명령어: [whoami] -> [chmod 777 flag/ test.txt] -> [cat flag/ test.txt]
- 목적: 메타 문자를 사용하여 공백 있는 파일의 입력을 제대로 처리하고, 권한을 변경하여 파일 내용을 읽기
- 예상 결과: flag/test.txt 파일의 내용을 성공적으로 읽을 수 있음

"""

    # 토큰 수 계산
    token_count = count_tokens(prompt, model="gpt-4o")
    if(token_count > 8000):
        return f"Error: The prompt exceeds the token limit for gpt-4o model. Current token count: {token_count}. Please reduce the input size."
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
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

def control_ai_function(option: str, last_command: str, output: str, user_id: str) -> str:
    """
    AI 기능을 제어하는 메인 함수
    
    :param option: "comment" 또는 "pattern" - 실행할 기능 선택
    :param last_command: 마지막으로 실행된 명령어 이름
    :param output: 명령어 실행 결과
    :param user_id: 사용자 ID
    :return: 코멘트 또는 패턴 추천 결과
    """
    if option.lower() == "comment":
        # 코멘트 옵션: get_hacking_comment 실행
        return get_hacking_comment(last_command, output)
    
    elif option.lower() == "pattern":
        # DB에서 사용자 상태 로드
        current_state = load_json(USER_STATES, user_id)
        
        # 사용자 상태가 없으면 종료
        if not current_state:
            print(f"❌ 사용자 ID '{user_id}'의 상태가 비어있습니다")
            return "현재 비어있는 상태입니다. 먼저 명령어를 실행하여 상태를 생성해주세요."
        
        # DB에서 명령어 목록과 메타데이터 로드
        shell_commands = load_file(TO_AI_INFORMATION, "shell_command_list.txt")
        shell_meta_lines = load_file(TO_AI_INFORMATION, "shell_meta.txt")
        shell_meta = "\n".join(shell_meta_lines) if shell_meta_lines else ""
        
        # 명령어 목록이 없으면 기본값 사용
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

