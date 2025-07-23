import json
from typing import List, Dict, Any
from pathlib import Path

# ===== 파일 경로 정의 (AI 폴더 기준) =====
CURRENT_PATH = Path(__file__).parent
AI_DIR = Path(__file__).parent / "AI"
COMMANDS_DIR = Path(__file__).parent / "Command"
SHELL_COMMAND_LIST_PATH = AI_DIR / "shell_command_list.txt"
SHELL_META_PATH = AI_DIR / "shell_meta.txt"
STATE_INITIAL_PATH = CURRENT_PATH/"State_initial"/ "state_initial.json"
CURRENT_STATE_PATH = CURRENT_PATH/"State"/ "state.json"
SHELL_COMMAND_JSON_PATH = COMMANDS_DIR/ "shell_command.json"
SHELL_JSON_PATH = COMMANDS_DIR / "shell.json"

def load_file(file_path: Path) -> List[str]:
    """
    텍스트 파일을 로드하여 라인별로 리스트로 반환합니다.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return []
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return []

def load_json(file_path: Path) -> Dict[str, Any]:
    """
    JSON 파일을 로드하여 딕셔너리로 반환합니다.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ JSON file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON from file {file_path}: {e}")
        return {}
    except Exception as e:
        print(f"❌ Error reading JSON file {file_path}: {e}")
        return {}
