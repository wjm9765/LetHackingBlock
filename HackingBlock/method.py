import subprocess
import json
import os

# --- 1. 실행 엔진 함수들 ---

def run_generic_shell_command(state: dict, command_template: str, params: dict) -> dict:
    """쉘 명령어를 실행하는 범용 엔진"""
    final_command = command_template.format(**params)
    print(f"---EXECUTING [Shell Command]---")
    print(f"COMMAND: {final_command}")
    
    try:
        result = subprocess.run(
            final_command, shell=True, capture_output=True, text=True, check=True
        )
        state['last_output'] = result.stdout
        print(f"STDOUT:\n{result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        state['last_output'] = e.stderr
        print(f"STDERR:\n{e.stderr.strip()}")
        
    print("----------------")
    return state

# 나중에 추가될 다른 타입의 실행 엔진 (예시)
# def run_generic_web_request(state: dict, url_template: str, params: dict) -> dict:
#     print("---EXECUTING [Web Request]---")
#     # ... requests 라이브러리를 사용한 로직 ...
#     return state

# --- 2. 블록 데이터 로더 ---
BLOCK_REGISTRY = {}

def load_blocks_from_file(filepath: str):
    """파일에서 블록 명세 데이터를 읽어와 등록소에 적재"""
    try:
        with open(filepath, 'r') as f:
            block_data_list = json.load(f)
        for block_data in block_data_list:
            BLOCK_REGISTRY[block_data["name"]] = block_data
        print(f"✅ {len(BLOCK_REGISTRY)} blocks loaded successfully from {filepath}")
    except FileNotFoundError:
        print(f"❌ ERROR: Block data file not found at {filepath}")
    except json.JSONDecodeError:
        print(f"❌ ERROR: Could not decode JSON from {filepath}")

# --- 3. 실행 엔진 등록소 ---
# base_block_type 이름과 실제 실행 함수를 매핑
EXECUTION_ENGINES = {
    'generic_shell_command': run_generic_shell_command,
    # 'generic_web_request': run_generic_web_request, # 나중에 웹 블록 추가 시
}

def check_preconditions(state: dict, preconditions: dict) -> bool:
    """현재 상태가 사전 조건을 모두 만족하는지 검사"""
    for key, expected_value in preconditions.items():
        if state.get(key) != expected_value:
            print(f"⚠️ Precondition FAILED: '{key}' is not '{expected_value}'")
            return False
    print("👍 Preconditions met.")
    return True



# --- 4. 테스트 실행 ---
if __name__ == "__main__":
    
    # JSON 파일 로드
    file_path = os.path.join("Command", "shell_command.json")
    load_blocks_from_file(file_path)

    # 테스트를 위한 계획
    test_plan = [
        {"action": "ls_command", "params": {"options": "-l", "path": "."}},
        {"action": "cat_command", "params": {"filepath": "method.py"}}, # 이 파일 자신을 읽어봄
        {"action": "grep_command", "params": {"options": "-n", "pattern": "EXECUTION_ENGINES", "target": "main.py"}}
    ]
    
    # 초기 상태
    current_state = {"shell_access": True, "last_output": ""}
    
    print("\n🤖 Hacking Block Execution Test Start!\n")

    # 계획을 순서대로 실행
    for step in test_plan:
        action_name = step["action"]
        params = step["params"]
        
        block_spec = BLOCK_REGISTRY.get(action_name)
        
        if not block_spec:
            print(f"ERROR: Block spec for '{action_name}' not found.")
            continue
        
        #실행 전에 사존 조건 여부 검사
        preconditions = block_spec.get("preconditions", {})
        if check_preconditions(current_state, preconditions):
            # 조건 만족 시에만 실행
            block_type = block_spec.get("base_block_type")
            engine_function = EXECUTION_ENGINES.get(block_type)
            if engine_function:
                current_state = engine_function(
                    state=current_state,
                    command_template=block_spec["command_template"],
                    params=params
                )
            else:
                print(f"ERROR: No execution engine found for block type '{block_type}'")
        else:
            # 조건 불만족 시, 행동을 건너뜀
            print(f"Skipping action '{action_name}' due to unmet preconditions.")   
    print("✅ Test Finished.")