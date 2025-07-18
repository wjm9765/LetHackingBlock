

import json
import os
from typing import Dict, List, Any

# .env 파일에서 환경 변수를 로드합니다.
from dotenv import load_dotenv
import openai

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("오류: OPENAI_API_KEY 환경 변수를 찾을 수 없습니다.")
    print("프로젝트 루트 디렉토리에 .env 파일을 생성하고 OPENAI_API_KEY='your_api_key' 형식으로 키를 추가해주세요.")
    client = None
else:
    client = openai.OpenAI(api_key=api_key)

# --- 경로 설정 ---
try:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    COMMAND_JSON_PATH = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'Command', 'shell_command.json'))
except NameError:
    CURRENT_DIR = os.getcwd()
    COMMAND_JSON_PATH = os.path.join(CURRENT_DIR, 'HackingBlock', 'Command', 'shell_command.json')


def summarize_execution_result(result_text: str) -> str:
    """
    사용자가 실행한 해킹 블록의 결과물을 GPT-4o-mini를 이용해 분석하고 요약합니다.
    """
    if not client:
        return "OpenAI 클라이언트가 초기화되지 않았습니다."

    prompt = f"""
    당신은 보안 전문가입니다. 다음 해킹 도구의 출력 결과를 분석하고, 가장 중요한 핵심 정보만 간결하게 요약해주세요.
    결과는 한글로 작성하고, 전문가가 아닌 사람도 이해할 수 있도록 쉽게 설명해주세요.

    **원본 결과:**
    ```
    {result_text}
    ```

    **요약:**
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful security assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        summary = f"[AI 요약 오류] API 호출에 실패했습니다: {e}"

    print("--- AI 결과 분석 코멘트 ---")
    print(summary)
    print("---------------------------\n")
    return summary

def _load_commands_from_json(file_path: str) -> List[Dict[str, Any]]:
    """
    지정된 경로의 JSON 파일에서 명령어 목록을 로드합니다.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"오류: 명령어 파일 '{file_path}'을(를) 찾을 수 없습니다.")
        return []
    except json.JSONDecodeError:
        print(f"오류: 명령어 파일 '{file_path}'의 형식이 잘못되었습니다.")
        return []

def recommend_next_action(state: Dict[str, Any]) -> Dict[str, str]:
    """
    현재 상태(state)를 기반으로 GPT-4o-mini를 이용해 다음 행동을 추천합니다.
    """
    if not client:
        return {"command": "오류", "reason": "OpenAI 클라이언트가 초기화되지 않았습니다."}

    available_commands = _load_commands_from_json(COMMAND_JSON_PATH)
    if not available_commands:
        return {"command": "오류", "reason": "사용 가능한 명령어 목록을 불러올 수 없습니다."}

    prompt = f"""
    당신은 최고의 화이트해커 조언가입니다. 주어진 현재 상황(state)과 사용 가능한 명령어 목록을 바탕으로, 해킹 목표를 달성하기 위한 다음 행동을 추천해주세요.

    **현재 상태:**
    - 미션: {state.get('mission', '정의되지 않음')}
    - 최종 목표: {state.get('goal', '정의되지 않음')}
    - 현재까지 파악한 정보: {json.dumps(state.get('current_knowledge', {}), indent=2, ensure_ascii=False)}
    - 이전 명령어 실행 내역:
    {json.dumps(state.get('history', []), indent=2, ensure_ascii=False)}

    **사용 가능한 명령어 목록:**
    {json.dumps(available_commands, indent=2, ensure_ascii=False)}

    **요청:**
    위 정보를 바탕으로, 다음에 실행할 가장 효과적인 명령어 하나와 그 이유를 **반드시 아래 JSON 형식에 맞춰 한글로** 제안해주세요.
    {{
      "command": "추천 명령어",
      "reason": "해당 명령어를 추천하는 상세한 이유"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a master white-hat hacker advisor who provides recommendations in Korean JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        recommendation_str = response.choices[0].message.content
        recommendation = json.loads(recommendation_str)
    except Exception as e:
        recommendation = {"command": "[AI 추천 오류]", "reason": f"API 호출 또는 JSON 파싱에 실패했습니다: {e}"}

    print("--- AI 조언 ---")
    print(f"추천 명령어: {recommendation.get('command')}")
    print(f"이유: {recommendation.get('reason')}")
    print("---------------")
    
    return recommendation

def say_hi_to_ai():
    """
    OpenAI API 연결을 테스트하기 위해 간단한 인사를 주고받는 함수.
    """
    if not client:
        print("OpenAI 클라이언트가 초기화되지 않아 인사할 수 없습니다.")
        return

    print("\n--- AI 연결 테스트 ---")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly assistant."},
                {"role": "user", "content": "Hi! Just say hello in Korean."}
            ],
            temperature=0.1,
        )
        greeting = response.choices[0].message.content.strip()
        print(f"나: Hi!")
        print(f"AI: {greeting}")
        print("----------------------")
    except Exception as e:
        print(f"AI 연결 테스트 중 오류가 발생했습니다: {e}")




# 이 파일이 직접 실행될 때를 위한 테스트 코드
if __name__ == '__main__':
    if not client:
        print("테스트를 진행할 수 없습니다. OpenAI API 키를 확인해주세요.")
    else:
        # --- 0. AI 연결 테스트 ---
        say_hi_to_ai()


        
    
        # # --- 1. AI 결과 분석 기능 테스트 ---
        # print("\n--- 1. AI 결과 분석 기능 테스트 ---")
        # sample_result = "Nmap scan report for scanme.nmap.org (45.33.32.156)\nHost is up (0.16s latency).\nNot shown: 995 closed tcp ports (reset)\nPORT      STATE    SERVICE      VERSION\n22/tcp    open     ssh          OpenSSH 6.6.1p1 Ubuntu 2ubuntu2.13 (Ubuntu Linux; protocol 2.0)\n80/tcp    open     http         Apache httpd 2.4.7 ((Ubuntu))\n135/tcp   filtered msrpc\n139/tcp   filtered netbios-ssn\n3389/tcp  closed   ms-wbt-server\nService Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel"
        # summarize_execution_result(sample_result)

        # # --- 2. AI 조언 기능 테스트 ---
        # print("\n--- 2. AI 조언 기능 테스트 (히스토리 있음) ---")
        # sample_state = {
        #   "mission": "웹 서버의 취약점을 찾아 루트 권한을 획득하시오.",
        #   "goal": "루트 권한 획득",
        #   "initial_conditions": {"target_ip": "45.33.32.156", "known_ports": [22, 80]},
        #   "current_knowledge": {
        #       "open_ports": {"22": "OpenSSH 6.6.1p1", "80": "Apache httpd 2.4.7"},
        #       "vulnerabilities": [],
        #   },
        #   "history": [
        #     {"command": "nmap -sV 45.33.32.156", "result": "Found open ports: 22/ssh, 80/http."}
        #   ]
        # }
        # recommend_next_action(sample_state)

        # # --- 3. AI 조언 기능 테스트 (히스토리 없음) ---
        # print("\n--- 3. AI 조언 기능 테스트 (히스토리 없음) ---")
        # empty_state = {
        #   "mission": "웹 서버의 취약점을 찾아 루트 권한을 획득하시오.",
        #   "goal": "루트 권한 획득",
        #   "initial_conditions": { "target_ip": "45.33.32.156" },
        #   "current_knowledge": {},
        #   "history": []
        # }
        # recommend_next_action(empty_state)
