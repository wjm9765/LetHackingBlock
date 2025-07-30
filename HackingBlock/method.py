import subprocess
import json
import os
import sys
from pathlib import Path


# state_class 임포트를 위한 경로 설정
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

# load.py 임포트
sys.path.append(str(current_dir))
from load import (
    USER_STATES,
    STATE_INITIAL,
    load_json,
    load_command_json
)

from HackingBlock.AI.state_class import State
from HackingBlock.AI.parser import parse_output

# --- 1. 실행 엔진 함수들 ---

# 지금을 쉘 실행 명령어만 있지만 나중에는 웹이나 네트워크 등 다른 범용 실행 명령어가 들어올 수 있음

def run_generic_shell_command(state_manager: State, command_template: str, params: dict, block_spec: dict = None) -> tuple:
    """
    쉘 명령어를 실행하는 범용 엔진
    
    Returns:
        tuple: (state_manager, output_string)
    """
    final_command = command_template.format(**params)
    print(f"---EXECUTING [Shell Command]---")
    print(f"COMMAND: {final_command}")
    
    # 명령어 실행
    try:
        result = subprocess.run(
            final_command, shell=True, capture_output=True, text=True, check=True
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        execution_success = True
           
    except subprocess.CalledProcessError as e:
        stdout = ""
        stderr = e.stderr.strip() if e.stderr else ""
        execution_success = False
        
        print(f"COMMAND FAILED - STDERR:\n{stderr}")
    
    # 파서 처리
    if block_spec and "parser_info" in block_spec:
        parser_info = block_spec.get("parser_info", {})
        parser_type = parser_info.get("type", "none")
        command_name = block_spec.get("name", "unknown_command")
        
        if parser_type == "state_only":
            # state_only 파서 처리 (기존 코드)
            print("🔄 Processing state_only parser...")
            _handle_state_only_parser(state_manager, block_spec, params, execution_success, stdout, stderr)
            
        elif parser_type in ["rule_based", "regex_based", "llm_based"] and execution_success:
            # 다른 타입 파서 처리 (간소화된 코드)
            print(f"🔄 Processing {parser_type} parser...")
            target_field = parser_info.get("target_field")
            
            if target_field:
                # 파서 실행 (parser.py의 parse_output 활용)
                used_options = params.get("options", "")
                parsed_result = parse_output(
                    raw_output=stdout,
                    parser_info=parser_info,
                    used_options=used_options,
                    command_block=block_spec,
                    command_name=command_name
                )
                
                # 결과 저장 (state_class.py의 update_state 활용)
                #state_manager.update_state(command_name, parsed_result, target_field)
                state_manager.update_state(command_name, parsed_result, target_field, used_options)
                print(f"✅ Parsed result saved to {target_field}")
            else:
                print(f"⚠️ Warning: target_field not specified in {parser_type} parser")
    
    print("----------------")
    # 상태 관리자와 명령어 출력을 함께 반환
    output = stdout if stdout else stderr
    return state_manager, output

def _handle_state_only_parser(state_manager: State, block_spec: dict, params: dict, execution_success: bool, stdout: str, stderr: str):
    """
    state_only 파서 전용 처리 함수
    명령어 실행 성공시 실제 파라미터 값을 state에 저장
    """
    parser_info = block_spec.get("parser_info", {})
    target_field = parser_info.get("target_field")
    default_value = parser_info.get("default_value", "command_executed")
    command_name = block_spec.get("name", "unknown_command")
    
    if not target_field:
        print("⚠️ Warning: target_field not specified in state_only parser")
        return
    
    # 1. 실행 실패 체크
    if not execution_success:
        print(f"❌ Command failed, not updating state for {target_field}")
        return
    
    # 2. 에러 메시지 체크 (성공했지만 에러 메시지가 있는 경우)
    error_indicators = [
        "permission denied", "no such file", "command not found", 
        "cannot access", "error", "failed", "bash:", "cannot"
    ]
    
    combined_output = (stdout + " " + stderr).lower()
    for error in error_indicators:
        if error in combined_output:
            print(f"❌ Error detected in output: '{error}', not updating state")
            return
    
    # 3. 명령어별 실제 값 추출
    actual_value = _extract_actual_value_from_params(command_name, params, default_value)
    
    # 4. State 클래스를 통해 저장
    state_manager.update_state_only_field(command_name, target_field, actual_value)
    
    print(f"✅ State updated: {target_field} = {actual_value}")

def _extract_actual_value_from_params(command_name: str, params: dict, default_value: str) -> str:
    """
    명령어 이름과 파라미터를 기반으로 실제 저장할 값을 추출
    """
    if command_name == "cd_command":
        path = params.get("path", ".")
        if path == "{path}":
            return default_value
        return path
    
    elif command_name == "mkdir_command":
        dirname = params.get("dirname", "")
        if dirname and dirname != "{dirname}":
            return dirname
        return default_value
    
    elif command_name == "touch_command":
        filename = params.get("filename", "")
        if filename and filename != "{filename}":
            return filename
        return default_value
    
    elif command_name == "rm_command":
        filepath = params.get("filepath", "")
        if filepath and filepath != "{filepath}":
            return f"deleted_{filepath}"
        return default_value
    
    elif command_name == "mv_command":
        source = params.get("source", "")
        destination = params.get("destination", "")
        if source and destination:
            return f"moved_{source}_to_{destination}"
        return default_value
    
    elif command_name == "cp_command":
        source = params.get("source", "")
        destination = params.get("destination", "")
        if source and destination:
            return f"copied_{source}_to_{destination}"
        return default_value
    
    elif command_name == "chmod_command":
        permissions = params.get("permissions", "")
        filepath = params.get("filepath", "")
        if permissions and filepath:
            return f"chmod_{permissions}_{filepath}"
        return default_value
    
    elif command_name == "chown_command":
        owner = params.get("owner", "")
        filepath = params.get("filepath", "")
        if owner and filepath:
            return f"chown_{owner}_{filepath}"
        return default_value
    
    elif command_name == "export_command":
        var_name = params.get("variable_name", "")
        value = params.get("value", "")
        if var_name and value:
            return f"{var_name}={value}"
        return default_value
    
    elif command_name == "unset_command":
        var_name = params.get("variable_name", "")
        if var_name:
            return f"unset_{var_name}"
        return default_value
    
    elif command_name == "alias_command":
        alias_name = params.get("alias_name", "")
        command = params.get("command", "")
        if alias_name and command:
            return f"{alias_name}={command}"
        return default_value
    
    elif command_name == "source_command":
        script_path = params.get("script_path", "")
        if script_path:
            return script_path
        return default_value
    
    else:
        return default_value

# --- 2. 블록 데이터 로더 ---
EXECUTION_ENGINES = {
    'generic_shell_command': run_generic_shell_command,
}

# --- 3. 명령어 제어 함수 ---
def control(engine_type: str, command_template: str, params: dict, block_spec: dict = None, user_id: str = None, environment_number: str = "001") -> str:
    """
    인자로 들어온 명령어 엔진에 따라 적절한 실행 함수를 호출하는 제어 함수
    
    Args:
        engine_type: 실행 엔진 타입 (generic_shell_command 등)
        command_template: 명령어 템플릿
        params: 명령어 파라미터
        block_spec: 블록 명세
        user_id: 사용자 ID
        environment_number: 환경 번호 (기본값: "001")
        
    Returns:
        str: 명령어 실행 결과 출력
    """
    # 사용자별 상태가 있으면 로드, 없으면 초기 상태 사용
    try:
        # 초기 상태로 먼저 초기화
        state_manager = State(environment_number)
        print(f"✅ 초기 상태 로드 성공 (environment: {environment_number})")
        
        # 사용자 상태가 있으면 적용 (실패시 초기 상태 유지)
        if user_id:
            success = state_manager.set_state(user_id)
            if success:
                print(f"✅ 사용자 상태 로드 성공 (user_id: {user_id})")
            else:
                print(f"⚠️ 사용자 상태를 찾을 수 없음: {user_id}. 초기 상태를 사용합니다.")
    except Exception as e:
        # 초기 상태로만 시작
        state_manager = State(environment_number)
        print(f"⚠️ 상태 로드 중 오류 발생: {e}. 초기 상태만 사용합니다.")
    

   #4 print(f"현재 상태\n", state_manager.state)




    if engine_type == 'generic_shell_command':
        # 쉘 명령어 실행
        state_manager, output = run_generic_shell_command(state_manager, command_template, params, block_spec)
        
        # 상태 저장 (user_id가 제공된 경우에만)
        if user_id:
            state_manager.save_state(user_id)
        
        return output
    else:
        # 다른 엔진 타입이 추가될 수 있음
        return f"Error: Unsupported engine type '{engine_type}'"

# --- 4. 메인 테스트 함수 ---
if __name__ == "__main__":
    
    # state_only 파서를 사용하는 명령어 테스트 목록
    test_commands = [
        {
            "name": "cd_command",
            "engine": "generic_shell_command",
            "template": "cd {path}",
            "params": {"path": "HackingBlock"},
            "block_spec": {
                "name": "cd_command", 
                "parser_info": {"type": "state_only", "target_field": "session.current_path", "default_value": "directory_changed"}
            }
        },
        {
            "name": "mkdir_command",
            "engine": "generic_shell_command",
            "template": "mkdir {options} {dirname}",
            "params": {"options": "-p", "dirname": "test_dir/subdir"},
            "block_spec": {
                "name": "mkdir_command",
                "parser_info": {"type": "state_only", "target_field": "file_system.created_directories", "default_value": "directory_created"}
            }
        }
    ]
    
    print("🧪 state_only 명령어 실행 테스트 시작")
    print("="*60)
    
    # 명령어 실행 테스트
    for cmd in test_commands:
        print(f"\n🚀 명령어 실행: {cmd['name']}")
        print("-"*40)
        
        # control 함수 호출
        output = control(
            engine_type=cmd["engine"],
            command_template=cmd["template"],
            params=cmd["params"],
            block_spec=cmd["block_spec"]
        )
        
        # 결과 출력
        print(f"\n📋 명령어 실행 결과:")
        print("-"*40)
        print(output)
        print("-"*40)
        print(f"✅ 명령어 실행 완료: {cmd['name']}\n")
    
    print("\n🎉 모든 테스트 완료!")
    print("="*60)

