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


def execute_command_mock(command_name: str, used_options: str = "") -> str:
    """
    Mock 명령어 실행 결과 - LLM 기반 명령어들
    """
    print(f"[*] Simulating execution for: '{command_name}' with options: '{used_options}'")
    
    if command_name == "ps_command":
        return """  PID TTY          TIME CMD
    1 ?        00:00:02 systemd
  123 ?        00:00:00 kthreadd
  456 ?        00:00:01 rcu_gp
  789 ?        00:00:00 migration/0
 1001 ?        00:00:05 apache2
 1002 ?        00:00:03 mysql
 1003 pts/0    00:00:00 bash
 1004 pts/0    00:00:00 python3
 1005 pts/1    00:00:00 ssh
 1006 ?        00:00:02 nginx
 1007 ?        00:00:01 redis-server
 1008 pts/0    00:00:00 ps"""
    
    elif command_name == "netstat_command":
        return """Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      1005/sshd: /usr/sbi
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      1001/apache2
tcp        0      0 0.0.0.0:443             0.0.0.0:*               LISTEN      1001/apache2
tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN      1002/mysqld
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN      1006/nginx: master
tcp6       0      0 :::22                   :::*                    LISTEN      1005/sshd: /usr/sbi
tcp6       0      0 :::80                   :::*                    LISTEN      1001/apache2
tcp6       0      0 :::443                  :::*                    LISTEN      1001/apache2"""
    
    elif command_name == "find_command":
        return """/home/user/documents/passwords.txt
/home/user/backup/config.bak
/var/www/html/.htaccess
/var/www/html/admin/login.php
/var/www/html/uploads/shell.php
/etc/passwd
/etc/shadow
/home/user/.ssh/id_rsa
/home/user/.bash_history
/tmp/exploit.py
/var/log/auth.log
/var/log/apache2/access.log"""
    
    elif command_name == "cat_command":
        return """# Database Configuration
DB_HOST=localhost
DB_USER=admin
DB_PASSWORD=supersecret123
DB_NAME=webapp

# API Keys
API_KEY=sk-1234567890abcdef
SECRET_KEY=mysecretkey2023

# Admin Credentials
ADMIN_USER=administrator
ADMIN_PASS=P@ssw0rd123!

# Debug Mode
DEBUG=true
LOG_LEVEL=debug"""
    
    elif command_name == "whoami_command":
        return """root"""
    
    elif command_name == "uname_command":
        return """Linux target 5.4.0-74-generic #83-Ubuntu SMP Sat May 8 02:35:39 UTC 2021 x86_64 x86_64 x86_64 GNU/Linux"""
    
    elif command_name == "ls_command":
        return """total 48
drwxr-xr-x  8 user user 4096 Jul 22 10:30 .
drwxr-xr-x  3 root root 4096 Jul 20 15:20 ..
-rw-------  1 user user  220 Jul 20 15:20 .bash_logout
-rw-------  1 user user 3771 Jul 20 15:20 .bashrc
drwx------  2 user user 4096 Jul 22 08:15 .cache
-rw-rw-r--  1 user user  807 Jul 22 10:25 config.txt
drwxrwxr-x  2 user user 4096 Jul 22 09:45 documents
-rwxrwxr-x  1 user user 8192 Jul 22 10:30 exploit.bin
-rw-rw-r--  1 user user  156 Jul 22 10:20 passwords.txt
-rw-------  1 user user  807 Jul 20 15:20 .profile
drwx------  2 user user 4096 Jul 22 08:30 .ssh
drwxrwxr-x  2 user user 4096 Jul 22 09:30 temp"""
    
    elif command_name == "ifconfig_command":
        return """eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255
        inet6 fe80::a00:27ff:fe8b:c5d7  prefixlen 64  scopeid 0x20<link>
        ether 08:00:27:8b:c5:d7  txqueuelen 1000  (Ethernet)
        RX packets 12345  bytes 1234567 (1.2 MB)
        TX packets 6789  bytes 987654 (987.6 KB)

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0x10<host>
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 100  bytes 8000 (8.0 KB)
        TX packets 100  bytes 8000 (8.0 KB)"""
    
    elif command_name == "w_command":
        return """ 10:30:45 up  2:15,  3 users,  load average: 0.45, 0.32, 0.28
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     tty1     -                08:15    2:15m  0.03s  0.03s -bash
user     pts/0    192.168.1.50     09:30    1.00s  0.25s  0.01s w
admin    pts/1    192.168.1.75     10:20    5:10   0.15s  0.05s ssh server.local"""
    
    else:
        return ""


def print_separator(title: str):
    """Prints a nice separator for test sections"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)


def print_step_header(step_num: int, command_name: str, options: str = ""):
    """Prints a header for each test step"""
    option_text = f" (options: {options})" if options else ""
    print(f"\n--- STEP {step_num}: Testing '{command_name}'{option_text} ---")


def test_llm_parsing_and_state_updates():
    """
    shell.json의 LLM 기반 명령어들을 테스트
    """
    print_separator("LLM-BASED PARSER TEST SUITE (from shell.json)")
    
    # LLM 기반 명령어들 테스트
    LLM_TEST_CASES = [
        #(("ps_command", "aux", "Process listing and analysis"),
        #("netstat_command", "-tulpn", "Network connections and listening ports"),
        #("find_command", "/ -name '*.txt' 2>/dev/null", "File system search for interesting files"),
        ("cat_command", "/etc/passwd", "File content reading and credential extraction"),
        #("whoami_command", "", "Current user identification"),
        #("uname_command", "-a", "System information gathering"),
        #("ls_command", "-la", "Directory listing and file permissions"),
        #("ifconfig_command", "", "Network interface configuration"),
        #("w_command", "", "Currently logged in users and activities"),
    ]
    
    # 1. Load commands and initialize state
    try:
        commands = load_commands(COMMANDS_PATH)
        state_manager = State(INITIAL_STATE_PATH)
    except FileNotFoundError as e:
        print(f"[ERROR] Failed to load initial files: {e}")
        return

    print("\n--- INITIAL STATE ---")
    initial_state = state_manager.get_state()
    print(json.dumps(initial_state, indent=2, ensure_ascii=False))
    
    # Create command lookup for faster access
    command_lookup = {cmd["name"]: cmd for cmd in commands}
    
    # Test each LLM case
    for i, (command_name, options, description) in enumerate(LLM_TEST_CASES, 1):
        print_step_header(i, command_name, options)
        
        # Find command info from shell.json
        if command_name not in command_lookup:
            print(f"  ❌ Command '{command_name}' not found in shell.json")
            continue
            
        command_info = command_lookup[command_name]
        
        # Check if it's actually LLM-based
        parser_info = command_info["parser_info"]
        if parser_info.get("type") != "llm_based":
            print(f"  ⚠️ Command '{command_name}' is not LLM-based (type: {parser_info.get('type')})")
            continue
        
        target_field = parser_info["target_field"]
        
        # a. Show command info
        print(f"  📋 Description: {description}")
        print(f"  📝 Command: {command_info['description']}")
        print(f"  🎯 Parser Type: {parser_info['type']}")
        print(f"  📍 Target Field: {target_field}")
        print(f"  🤖 LLM Prompt: {parser_info.get('llm_prompt', 'N/A')[:100]}...")
        
        # b. Simulate command execution
        raw_output = execute_command_mock(command_name, options)
        print(f"\n  📤 Raw Output:")
        print(f"    {repr(raw_output[:200])}..." if len(raw_output) > 200 else f"    {repr(raw_output)}")
        
        # c. Parse the raw output using LLM
        try:
            print(f"\n  🤖 Calling LLM parser...")
            parsed_data = parse_output(raw_output, parser_info, options, command_info)
            print(f"\n  ✅ LLM Parsed Data:")
            if isinstance(parsed_data, dict):
                print(json.dumps(parsed_data, indent=4, ensure_ascii=False))
            else:
                print(f"    {parsed_data}")
        except Exception as e:
            print(f"\n  ❌ LLM PARSING FAILED: {e}")
            # LLM이 실패하면 기본값 사용
            parsed_data = {"raw_output": raw_output, "parsing_failed": True}
            print(f"  🔄 Using fallback data: {parsed_data}")
        
        # d. Update the state
        print(f"\n  🔄 Updating state at '{target_field}'...")
        
        state_manager.update_state(command_name, parsed_data, target_field)
        
        # e. Show what changed
        updated_state = state_manager.get_state()
        
        # f. Highlight the specific change
        keys = target_field.split('.')
        current_level = updated_state
        for key in keys:
            if isinstance(current_level, dict):
                current_level = current_level.get(key, {})
            else:
                current_level = "N/A"
                break
        
        print(f"\n  🎯 Value at '{target_field}':")
        if isinstance(current_level, dict) and len(str(current_level)) > 300:
            print(f"    {json.dumps(current_level, indent=2, ensure_ascii=False)[:300]}...")
        else:
            print(f"    {current_level}")
        
        print("\n" + "-"*60)

    # 3. Show final summary
    print_separator("FINAL STATE SUMMARY")
    final_state = state_manager.get_state()
    
    # Show key sections
    print("\n🔍 KEY STATE SECTIONS:")
    
    # System Information
    system_info = final_state.get("system_info", {})
    if system_info:
        print(f"\n  💻 SYSTEM INFORMATION:")
        processes = system_info.get("processes", [])
        detailed_processes = system_info.get("detailed_processes", [])
        user_privileges = system_info.get("user_privileges", [])
        print(f"    Processes: {len(processes) if isinstance(processes, list) else 'N/A'} items")
        print(f"    Detailed Processes: {len(detailed_processes) if isinstance(detailed_processes, list) else 'N/A'} items")
        print(f"    User Privileges: {len(user_privileges) if isinstance(user_privileges, list) else 'N/A'} items")

    # Network Information
    network_info = final_state.get("network_info", {})
    if network_info:
        print(f"\n  🌐 NETWORK INFORMATION:")
        connections = network_info.get("connections", [])
        listening_ports = network_info.get("listening_ports", [])
        all_connections = network_info.get("all_connections", [])
        print(f"    Connections: {len(connections) if isinstance(connections, list) else 'N/A'} items")
        print(f"    Listening Ports: {len(listening_ports) if isinstance(listening_ports, list) else 'N/A'} items")
        print(f"    All Connections: {len(all_connections) if isinstance(all_connections, list) else 'N/A'} items")

    # File System
    file_system = final_state.get("file_system", {})
    if file_system:
        print(f"\n  📁 FILE SYSTEM:")
        found_files = file_system.get("found_files", [])
        file_details = file_system.get("file_details", [])
        print(f"    Found Files: {len(found_files) if isinstance(found_files, list) else 'N/A'} items")
        print(f"    File Details: {len(file_details) if isinstance(file_details, list) else 'N/A'} items")

    # Session Information
    session = final_state.get("session", {})
    if session:
        print(f"\n  👤 SESSION:")
        current_user = session.get("current_user", "N/A")
        current_path = session.get("current_path", "N/A")
        env_vars = session.get("environment_variables", [])
        print(f"    Current User: {current_user}")
        print(f"    Current Path: {current_path}")
        print(f"    Environment Variables: {len(env_vars) if isinstance(env_vars, list) else 'N/A'} items")

    # Command history
    print("\n📝 COMMAND HISTORY:")
    history = state_manager.get_command_history()
    if history:
        print(f"    Total commands executed: {len(history)}")
        print(f"    Commands: {history}")
        print(f"    Recent 5: {history[-5:] if len(history) >= 5 else history}")
    else:
        print("    No commands in history")

    # 4. Save the final state
    state_manager.save_state(FINAL_STATE_PATH)
    print_separator("TEST COMPLETE")
    print(f"✅ Final state saved to: {FINAL_STATE_PATH}")
    print(f"📊 Total test cases: {len(LLM_TEST_CASES)}")
    print(f"📝 Total commands in history: {len(state_manager.get_command_history())}")


if __name__ == "__main__":
    """
    Main test runner - shell.json의 LLM 명령어들을 테스트
    """
    print("🚀 Starting LLM parser tests using shell.json commands...")
    
    # Test LLM-based parsing using shell.json
    test_llm_parsing_and_state_updates()
    
    print("\n🎉 All LLM parser tests completed!")
    print("📁 Check the generated 'state.json' file to see the final accumulated state.")
    print("🤖 Note: LLM parsing results may vary depending on the AI model's response.")
