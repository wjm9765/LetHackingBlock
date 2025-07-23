import sys
import json
from pathlib import Path

# 프로젝트 루트를 경로에 추가하여 모듈을 임포트할 수 있도록 설정
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from HackingBlock.method import control as method_control
from HackingBlock.AI.ai_function import control_ai_function
from HackingBlock.load import load_json, SHELL_COMMAND_JSON_PATH

def display_menu():
    """메인 메뉴를 출력하는 함수"""
    print("\n" + "="*50)
    print("HackingBlock CLI")
    print("="*50)
    print("1. 명령어 실행")
    print("2. 이전 명령어 실행 결과에 대한 코멘트 받기")
    print("3. 현재 상태를 기반으로 패턴 추천받기")
    print("4. 종료")
    print("="*50)

# 전역변수 선언 (main 함수 외부에 위치)
LAST_COMMAND = None
LAST_OUTPUT = None

def execute_command():
    """사용자로부터 명령어를 입력받아 실행하는 함수"""
    global LAST_COMMAND, LAST_OUTPUT
    
    print("\n--- 명령어 실행 ---")
    
    # 사용 가능한 명령어 목록 로드 및 출력
    shell_commands = load_json(SHELL_COMMAND_JSON_PATH)
    if not shell_commands:
        print("오류: 'HackingBlock/Command/shell_command.json' 파일을 찾을 수 없습니다.")
        return None, None

    print("사용 가능한 명령어:")
    for cmd in shell_commands:
        print(f"- {cmd['name']}: {cmd['description']}")
    
    command_name = input("실행할 명령어 이름을 입력하세요: ").strip()
    
    command_block = next((cmd for cmd in shell_commands if cmd['name'] == command_name), None)
    
    if not command_block:
        print(f"오류: '{command_name}' 명령어를 찾을 수 없습니다.")
        return None, None
    
    # 파라미터 처리
    params = {}
    
    # 옵션 처리 (명령어에 옵션이 있는 경우)
    if "available_options" in command_block:
        print(f"\n{command_name}의 사용 가능한 옵션:")
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
        block_spec=command_block
    )
    
    print("\n--- 실행 결과 ---")
    print(output)
    
    # 전역변수에 결과 저장
    LAST_COMMAND = command_name
    LAST_OUTPUT = output
    
    return command_name, output

def get_comment(last_command=None, last_output=None):
    """이전 명령어 실행 결과에 대한 코멘트를 받는 함수"""
    global LAST_COMMAND, LAST_OUTPUT
    
    print("\n--- 이전 결과에 대한 코멘트 받기 ---")
    
    # 함수 인자 대신 전역변수 사용
    if not LAST_COMMAND or not LAST_OUTPUT:
        print("오류: 명령어를 최소 1번 실행해야 합니다.")
        return
        
    print("AI에게 코멘트를 요청하는 중...")
    comment = control_ai_function("comment", LAST_COMMAND, LAST_OUTPUT)
    
    print("\n--- AI 코멘트 ---")
    print(comment)

def get_pattern_recommendation():
    """현재 상태를 기반으로 패턴을 추천받는 함수"""
    print("\n--- 현재 상태 기반 패턴 추천받기 ---")
    print("AI에게 패턴 추천을 요청하는 중...")
    
    # 'pattern' 옵션으로 AI 함수 호출, 다른 인자는 필요 없음
    recommendation = control_ai_function("pattern", "", "")
    
    print("\n--- 추천 패턴 ---")
    print(recommendation)

def main():
    """메인 루프를 실행하는 함수"""
    while True:
        display_menu()
        choice = input("원하는 작업의 번호를 입력하세요: ").strip()
        
        if choice == '1':
            execute_command()
            # 결과는 전역변수에 저장되므로 반환값을 사용할 필요 없음
        elif choice == '2':
            get_comment()
            # 전역변수를 사용하므로 인자 전달 필요 없음
        elif choice == '3':
            get_pattern_recommendation()
        elif choice == '4':
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다. 1, 2, 3, 4 중 하나를 입력하세요.")

if __name__ == "__main__":
    main()
