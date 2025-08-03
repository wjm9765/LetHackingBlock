# ### ## `mission` (임무)
# * **`goal_description`**: AI가 달성해야 할 **최종 임무 목표**를 사람이 이해할 수 있는 문장으로 설명합니다.
# * **`objective_type`**: 임무의 종류를 **기계가 인식할 수 있도록 분류**합니다. (예: `FLAG_CAPTURE`)

# ### ## `session` (세션)
# * **`current_user`**: AI 에이전트가 현재 **어떤 사용자 권한**으로 활동하는지 나타냅니다.
# * **`current_host`**: AI 에이전트가 현재 **어떤 시스템(IP 주소)**에 접속해 있는지 나타냅니다.
# * **`current_path`**: 현재 작업 중인 **파일 시스템의 경로**를 나타냅니다.

# ### ## `knowledge_base` (지식 베이스)
# * **`hosts`**: 공격을 통해 발견한 **모든 서버(호스트)의 상세 정보를 저장**하는 목록입니다.

# ### \#\# `knowledge_base` 상세 설명

# AI가 수집한 모든 정보를 저장하는 핵심 데이터베이스입니다.

#   * **`hosts`**: `(List)` 발견된 모든 개별 컴퓨터(서버) 정보를 저장하는 목록입니다. 각 컴퓨터는 아래의 속성을 가진 하나의 객체로 표현됩니다.
#       * **`ip_address`**: `(String)` 해당 컴퓨터의 고유 IP 주소입니다. (예: "10.10.10.5")
#       * **`hostnames`**: `(List of Strings)` 해당 IP에 연결된 도메인 이름 목록입니다. (예: ["https://www.google.com/search?q=api.example.com"])
#       * **`os`**: `(String)` `nmap` 등으로 알아낸 컴퓨터의 운영체제 정보입니다. (예: "Linux (Ubuntu 22.04)")
#       * **`open_ports`**: `(List of Objects)` 해당 컴퓨터에서 열려있는 네트워크 포트 목록입니다.
#           * **`port`**: `(Integer)` 포트 번호입니다. (예: 80)
#           * **`service`**: `(String)` 해당 포트에서 실행되는 서비스 이름입니다. (예: "http")
#           * **`version`**: `(String)` 서비스의 구체적인 버전 정보입니다. (예: "Apache/2.4.52")
#       * **`vulnerabilities`**: `(List of Objects)` 해당 컴퓨터 또는 서비스에서 발견된 보안 취약점 목록입니다.
#           * **`cve_id`**: `(String)` 알려진 취약점의 공식적인 고유 번호입니다. (예: "CVE-2021-41773")
#           * **`description`**: `(String)` 취약점에 대한 간단한 설명입니다. (예: "Apache Path Traversal")
#       * **`credentials`**: `(List of Objects)` 해당 컴퓨터에서 탈취한 계정 정보 목록입니다.
#           * **`username`**: `(String)` 계정의 사용자 이름입니다. (예: "admin")
#           * **`hash`**: `(String)` 비밀번호 원문 또는 암호화된 해시값입니다.
#           * **`source`**: `(String)` 이 계정 정보를 획득한 출처입니다. (예: "Found in /var/www/config.php")
#   * **`files_of_interest`**: `(List of Strings)` 특정 호스트에 종속되지 않거나, 여러 호스트에 걸쳐 중요하다고 판단되는 파일들의 전체 경로 목록입니다. (예: ["/share/common\_passwords.txt"])


# ### ## `achievements` (달성 과제)
# * **`achievements`**: "사용자 쉘 획득" 등 **중요한 중간 목표 달성 여부**를 기록하여, AI가 중복된 행동을 피하게 합니다.

# ### ## `history` (기록)
# * **`last_n_commands`**: AI가 최근 **어떤 명령어들을 실행했는지** 단기 기억을 위해 저장합니다.

from calendar import c
import json
from pathlib import Path
from typing import Dict, List, Union, Any

# DB에서 데이터 로드를 위한 임포트
import sys

from sqlalchemy import false
sys.path.append(str(Path(__file__).parent.parent))
from load import load_json, STATE_INITIAL, USER_STATES
import boto3

class State:
    """
    Manages the state of the hacking process.

    The state is a JSON object with the following structure:
    {
      "network": {
        "target_ip": "...",
        "open_ports": [...]
      },
      "system": {
        "os_version": "...",
        "users": [...]
      },
      "vulnerabilities": [...]
    }
    """
    def __init__(self, initial_key=None):
        """기존 상태 또는 초기 상태로 초기화
        
        Args:
            initial_key: STATE_INITIAL 테이블에서 조회할 키 값 (예: "001")
        """
        self.state = self._load_state(STATE_INITIAL, initial_key)
        self.max_history_length = 50  # 최대 히스토리 개수


    def set_state(self, user_id=None):  
        """사용자 ID에 해당하는 상태 데이터로 현재 상태를 설정합니다.
        
        Args:
            user_id: USER_STATES 테이블에서 조회할 사용자 ID
            
        Returns:
            bool: 상태 로드 성공 여부. 실패시 False 반환
        """
        new_state = self._load_state(USER_STATES, user_id)
        if new_state is False:  # 상태 로드 실패시
            return False
            
        # 상태 로드 성공
        self.state = new_state
        self.max_history_length = 50
        return True
       
        
        

    def _load_state(self, table_info=None, key_value=None) -> Union[dict, bool]:
        """
        상태 데이터를 로드합니다.
        
        Args:
            table_info: 테이블 정보 (예: STATE_INITIAL 또는 USER_STATES)
            key_value: 테이블에서 검색할 키 값 (예: "001" 또는 사용자 ID)
        
        Returns:
            상태 데이터 딕셔너리 또는 로드 실패시 False
        """
        # 이미 딕셔너리인 경우 그대로 반환
        if isinstance(table_info, dict) and not key_value:
            return table_info
        
                
        # DB에서 데이터 로드
        if table_info and key_value:
            try:
                state_data = load_json(table_info, key_value)
                if not state_data:
                    print(f"❌ 상태 데이터를 찾을 수 없음: {table_info['table_name']}/{key_value}")
                    # 로드 실패 반환
                    return False
                return state_data
            except Exception as e:
                print(f"❌ 상태 로드 중 오류: {e}")
                # 로드 실패 반환
                return False
        
        # 아무것도 제공되지 않은 경우
        print("⚠️ 테이블 정보와 키 값이 모두 제공되지 않아 빈 상태를 생성합니다")
        return False

    def _add_to_history(self, command_name: str, options: str = None):
        """
        명령어 이름을 history에 추가 (옵션 포함)
        
        Args:
            command_name: 실행된 명령어 이름
            options: 명령어에 사용된 옵션 (없으면 None)
        """
        # 옵션이 있으면 명령어_옵션 형태로 저장
        if options and options.strip():
            full_command = f"{command_name} {options}"
        else:
            full_command = command_name
        
        # 히스토리에 추가
        history_list = self.state["history"]["last_n_commands"]
        history_list.append(full_command)
        
        # 최대 길이 제한
        if len(history_list) > self.max_history_length:
            self.state["history"]["last_n_commands"] = history_list[-self.max_history_length:]
        
        print(f"📝 Added to history: {full_command}")

    def update_state(self, command_name: str, parsed_output: list | str, update_key: str, options: str = None):
        """
        Updates the state with the output of a command and adds command to history.
        
        Args:
            command_name: The name of the command that was executed.
            parsed_output: The parsed output of the command.
            update_key: The key in the state to update (e.g., "knowledge_base.targets").
            options: 명령어에 사용된 옵션 (없으면 None)
        """
        
        # 1. 명령어 히스토리에 추가 (옵션 포함)
        self._add_to_history(command_name, options)
        
        # 2. 실제 데이터 저장
        keys = update_key.split('.')
        current_level = self.state
        
        # 명령어 번호 계산
        command_number = len(self.state["history"]["last_n_commands"])

        # 리스트인 경우 처리
        if isinstance(parsed_output, list):
            # 첫 항목으로 명령어 번호 표시 추가
            parsed_output.insert(0, f"[Command #{command_number}]")
        # 문자열인 경우 처리
        elif isinstance(parsed_output, str):
            parsed_output = f"[Command #{command_number}] {parsed_output}"
        # 기타 데이터 타입인 경우
        else:
            print(f"Warning: Cannot add command number to data of type {type(parsed_output)}")

        # Navigate to the target location, creating intermediate dicts as needed
        for key in keys[:-1]:
            current_level = current_level.setdefault(key, {})
            
        final_key = keys[-1]
        
        # Special handling for different data types
        if isinstance(current_level.get(final_key), list):
            # If target is a list, append the new data
            if isinstance(parsed_output, list):
                current_level[final_key].extend(parsed_output)
            else:
                current_level[final_key].append(parsed_output)
        else:
            # Otherwise, overwrite with the new data
            current_level[final_key] = parsed_output
            
        print(f"State updated with result from '{command_name}'.")
        print(f"  - Key: {update_key}")
        print(f"  - New Value: {parsed_output}")
    
    def get_field_path(self, *field_names: str) -> str:
        """Helper method to construct field paths using constants"""
        return '.'.join(field_names)

    def get_command_history(self) -> list:
        """명령어 실행 이력 반환"""
        return self.state.get("history", {}).get("last_n_commands", [])

    def clear_history(self):
        """명령어 이력 초기화"""
        self.state["history"]["last_n_commands"] = []
        print("🗑️ Command history cleared")

    def save_state(self, user_id: str):
        """
        현재 상태를 DynamoDB의 UserStates 테이블에 저장합니다.
        
        Args:
            user_id: 사용자 ID (테이블 키)
        """
        try:
            # DynamoDB 리소스 생성
            dynamodb = boto3.resource('dynamodb', region_name="ap-northeast-2")
            table = dynamodb.Table(USER_STATES["table_name"])
            
            # 현재 상태 복사 (키 추가를 위해)
            state_data = self.state.copy()
            
            # 키 추가
            state_data[USER_STATES["key_field"]] = user_id
            
            # 테이블에 저장
            response = table.put_item(Item=state_data)
            print(f"✅ 상태가 사용자 ID '{user_id}'로 DB에 저장되었습니다")
            return True
        except Exception as e:
            print(f"❌ DB에 상태 저장 중 오류: {e}")
            return False

    def get_state(self) -> dict:
        """Returns the current state."""
        return self.state
    

    def update_state_only_field(self, command_name: str, target_field: str, value):
        """
        state_only 파서 전용 state 업데이트 함수
        
        Args:
            command_name: 실행된 명령어 이름
            target_field: 업데이트할 필드 경로 (예: "session.current_path")
            value: 저장할 값
        """
        print(f"🔄 Updating state_only field: {target_field} = {value}")
        
        # 명령어 히스토리에 추가
        self._add_to_history(command_name)
        
        # target_field 경로에 따라 state 업데이트
        keys = target_field.split('.')
        current_level = self.state
        
        # 중간 딕셔너리들을 생성하면서 이동
        for key in keys[:-1]:
            if key not in current_level:
                current_level[key] = {}
            elif not isinstance(current_level[key], dict):
                # 기존 값이 딕셔너리가 아니면 딕셔너리로 변경
                current_level[key] = {}
            current_level = current_level[key]
        
        final_key = keys[-1]
        
        # 마지막 키에 값 저장
        if isinstance(current_level.get(final_key), list):
            # 리스트인 경우 추가
            if isinstance(value, list):
                current_level[final_key].extend(value)
            else:
                current_level[final_key].append(value)
        else:
            # 그렇지 않으면 덮어쓰기 (단일 값 또는 새 리스트)
            current_level[final_key] = value
        
        print(f"✅ State field updated: {target_field} = {current_level[final_key]}")

