
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


import json
from pathlib import Path

# =============================================================================
# STATE FIELD CONSTANTS - #define 스타일 필드명 정의
# =============================================================================
class StateFields:
    """State JSON 구조의 모든 필드명을 상수로 정의"""
    
    # Top-level fields
    MISSION_INFO = "mission_info"
    KNOWLEDGE_BASE = "knowledge_base"
    HISTORY = "history"
    
    # mission_info fields
    MISSION = "mission"
    GOAL = "goal"
    
    # knowledge_base fields
    TARGETS = "targets"
    CREDENTIALS = "credentials"
    KNOWN_FACTS = "known_facts"
    
    # Target object fields (within targets list)
    TARGET_IP = "ip_address"
    TARGET_HOSTNAME = "hostname"
    TARGET_OS = "os"
    TARGET_PORTS = "open_ports"
    TARGET_SERVICES = "services"
    TARGET_VULNERABILITIES = "vulnerabilities"
    
    # Service object fields (within services list)
    SERVICE_PORT = "port"
    SERVICE_NAME = "service"
    SERVICE_VERSION = "version"
    SERVICE_STATE = "state"
    
    # File system related
    FILE_SYSTEM = "file_system"
    KNOWN_FILES = "known_files"
    CURRENT_USER = "current_user"
    
    # Web application related
    WEB_APPLICATIONS = "web_applications"
    WEB_DIRECTORIES = "directories"
    
    # System information
    SYSTEM_INFO = "system_info"

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
    def __init__(self, initial_state_path: Path):
        """
        Initializes the State object.

        Args:
            initial_state_path: Path to the JSON file with the initial state.
        """
        self.state = self._load_state(initial_state_path)

    def _load_state(self, state_path: Path) -> dict:
        """Loads the state from a JSON file."""
        if not state_path.exists():
            raise FileNotFoundError(f"State file not found at {state_path}")
        with open(state_path, 'r') as f:
            return json.load(f)

    def update_state(self, command_name: str, parsed_output: list | str, update_key: str):
        """
        Updates the state with the output of a command.

        Args:
            command_name: The name of the command that was executed.
            parsed_output: The parsed output of the command.
            update_key: The key in the state to update (e.g., "knowledge_base.targets").
        """
        keys = update_key.split('.')
        current_level = self.state
        
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


    def save_state(self, output_path: Path):
        """Saves the current state to a JSON file with proper Korean encoding."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
        print(f"State saved to {output_path}")

    def get_state(self) -> dict:
        """Returns the current state."""
        return self.state