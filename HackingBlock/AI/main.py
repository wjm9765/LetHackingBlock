import json
from pathlib import Path
import sys

# Ensure the parent directory is in the Python path to allow for module imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

from HackingBlock.AI.state_class import State, StateFields
from HackingBlock.AI.parser import llm_based_parser, parse_output

# --- Configuration ---
AI_DIR = Path(__file__).parent
COMMANDS_PATH = AI_DIR.parent / "Command" / "shell_command.json"
INITIAL_STATE_PATH = AI_DIR / "state_initial.json"
FINAL_STATE_PATH = AI_DIR / "state.json"


def load_commands(path: Path) -> list:
    """Loads commands from a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Commands file not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)


def execute_command_mock(command_name: str) -> str:
    """
    Mocks the execution of a shell command for testing purposes.
    Returns realistic sample raw string output for each command.
    """
    print(f"[*] Simulating execution for: '{command_name}'")
    
    # if command_name == "whoami_command":
    #     return "root"
    
    if command_name == "ls_command":
        return """total 24
drwxr-xr-x 2 root root 4096 Jul 22 10:30 Documents
-rw-r--r-- 1 root root  156 Jul 22 09:15 config.txt
-rwxr-xr-x 1 root root 8192 Jul 22 08:45 exploit.sh
-rw------- 1 root root  512 Jul 21 14:20 .ssh_key"""
    
    # elif command_name == "cat_command":
    #     return """# Configuration File
    # username=admin
    # password=secretpass123
    # database_host=localhost
    # port=3306
    # debug=true
    # api_key=sk-abcd1234efgh5678ijkl"""
    
    if command_name == "nmap_command":
        # Regex 패턴에 맞춘 출력: (\\d+)/(tcp|udp)\\s+(open|closed|filtered)\\s+(\\w+)\\s*(.*)$
        return """Starting Nmap 7.80 ( https://nmap.org ) at 2024-07-22 10:30 UTC
Nmap scan report for target.htb (192.168.1.100)
Host is up (0.050s latency).
Not shown: 997 closed ports
PORT     STATE SERVICE    VERSION
22/tcp open ssh OpenSSH 8.2p1 Ubuntu 4ubuntu0.5
80/tcp open http Apache httpd 2.4.41
443/tcp open https Apache httpd 2.4.41 ((Ubuntu))
3306/tcp open mysql MySQL 8.0.32-0ubuntu0.20.04.2

Nmap done: 1 IP address (1 host up) scanned in 15.23 seconds"""
    
    # elif command_name == "gobuster_dir_command":
    #     return """/admin              (Status: 200) [Size: 1024]
    # /backup             (Status: 403) [Size: 512]
    # /config             (Status: 200) [Size: 2048]
    # /uploads            (Status: 301) [Size: 314] [--> http://target.htb/uploads/]
    # /api                (Status: 200) [Size: 156]
    # /login              (Status: 200) [Size: 3412]"""
    
    else:
        return ""


def print_separator(title: str):
    """Prints a nice separator for test sections"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)


def print_step_header(step_num: int, command_name: str):
    """Prints a header for each test step"""
    print(f"\n--- STEP {step_num}: Testing '{command_name}' ---")


def test_parsing_and_state_updates():
    """
    Comprehensive test that verifies each parser type and state update mechanism
    """
    print_separator("PARSER & STATE UPDATE TEST SUITE")
    
    # Define which commands to test
    COMMANDS_TO_TEST = ["ls_command"]  # Testing ls_command with new LLM parser
    
    # 1. Load commands and initialize state
    try:
        commands = load_commands(COMMANDS_PATH)
        state_manager = State(INITIAL_STATE_PATH)
    except FileNotFoundError as e:
        print(f"[ERROR] Failed to load initial files: {e}")
        return

    print("\n--- INITIAL STATE ---")
    print(json.dumps(state_manager.get_state(), indent=2, ensure_ascii=False))
    
    # Test each command
    for i, command_info in enumerate(commands, 1):
        command_name = command_info["name"]
        parser_info = command_info["parser_info"]
        target_field = parser_info["target_field"]
        
        # Skip if command is not in test list
        if command_name not in COMMANDS_TO_TEST:
            print(f"\n--- STEP {i}: Skipping '{command_name}' (not in test list) ---")
            continue
        
        print_step_header(i, command_name)
        
        # a. Show command info
        print(f"  📋 Command: {command_info['description']}")
        print(f"  🎯 Parser Type: {parser_info['type']}")
        print(f"  📍 Target Field: {target_field}")
        print(f"  📝 Template: {command_info.get('command_template', 'N/A')}")
        
        # b. Simulate command execution
        raw_output = execute_command_mock(command_name)
        print(f"\n  📤 Raw Output:")
        print(f"    {repr(raw_output)}")
        
        # c. Parse the raw output
        try:

            parsed_data = parse_output(raw_output, parser_info)
            print(f"\n  ✅ Parsed Data:")
            print(f"    {parsed_data}")
        except Exception as e:
            print(f"\n  ❌ PARSING FAILED: {e}")
            continue
        
        # d. Update the state
        print(f"\n  🔄 Updating state at '{target_field}'...")
        state_before = json.dumps(state_manager.get_state(), indent=2, ensure_ascii=False)
        
        state_manager.update_state(command_name, parsed_data, target_field)
        
        # e. Show what changed
        state_after = json.dumps(state_manager.get_state(), indent=2, ensure_ascii=False)
        print(f"\n  📊 State After Update:")
        print(json.dumps(state_manager.get_state(), indent=2, ensure_ascii=False))
        
        # f. Highlight the specific change
        keys = target_field.split('.')
        current_level = state_manager.get_state()
        for key in keys:
            current_level = current_level.get(key, {})
        
        print(f"\n  🎯 Value at '{target_field}':")
        print(f"    {current_level}")
        
        print("\n" + "-"*60)

    # 3. Save the final state
    state_manager.save_state(FINAL_STATE_PATH)
    print_separator("TEST COMPLETE")
    print(f"✅ Final state saved to: {FINAL_STATE_PATH}")
    print(f"📊 Total commands tested: {len(commands)}")


def test_state_field_constants():
    """Test that our StateFields constants work correctly"""
    print_separator("STATE FIELD CONSTANTS TEST")
    
    # Test field path construction
    print("Testing StateFields constants:")
    print(f"  KNOWLEDGE_BASE: '{StateFields.KNOWLEDGE_BASE}'")
    print(f"  TARGETS: '{StateFields.TARGETS}'")
    print(f"  KNOWN_FACTS: '{StateFields.KNOWN_FACTS}'")
    
    # Test path construction
    state_manager = State(INITIAL_STATE_PATH)
    target_path = state_manager.get_field_path(StateFields.KNOWLEDGE_BASE, StateFields.TARGETS)
    facts_path = state_manager.get_field_path(StateFields.KNOWLEDGE_BASE, StateFields.KNOWN_FACTS)
    
    print(f"\n  Constructed paths:")
    print(f"    Targets path: '{target_path}'")
    print(f"    Facts path: '{facts_path}'")
    
    print("✅ StateFields constants working correctly!")


if __name__ == "__main__":
    """
    Main test runner - executes comprehensive tests for parsing and state management
    """
    print("🚀 Starting comprehensive parser and state management tests...")
    
    # Test 1: StateFields constants
    test_state_field_constants()
    
    # Test 2: Full parsing and state update pipeline
    test_parsing_and_state_updates()
    
    print("\n🎉 All tests completed!")
    print("📁 Check the generated 'state.json' file to see the final accumulated state.")
