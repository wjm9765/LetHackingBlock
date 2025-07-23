# import subprocess
# import json
# import os
# import re
# from GTPyhop import gtpyhop

# # --- 1. 범용 실행 엔진 ---
# def run_shell_command(command_template: str, params: dict, input_data=None):
#     """명령어 템플릿과 파라미터를 받아 실제 쉘 명령을 실행하고 결과를 반환합니다."""
#     # 템플릿에 있는 모든 플레이스홀더를 찾습니다.
#     placeholders = re.findall(r'{(.*?)}', command_template)
    
#     # 제공된 파라미터에 없는 플레이스홀더는 빈 문자열로 채웁니다.
#     full_params = {ph: '' for ph in placeholders}
#     full_params.update(params)

#     # 명령어를 포맷팅합니다.
#     final_command = command_template.format(**full_params)
    
#     # 연속된 공백을 하나로 줄여줍니다. (e.g., "grep  'pattern'" -> "grep 'pattern'")
#     final_command = ' '.join(final_command.split())

#     print(f"\n> EXECUTING: {final_command}")
#     if input_data:
#         print(f"  (stdin): '{input_data}'")
#     try:
#         result = subprocess.run(
#             final_command, shell=True, capture_output=True, text=True, check=True, input=input_data
#         )
#         output = result.stdout.strip()
#         print(f"  OUTPUT: {output}")
#         return output
#     except subprocess.CalledProcessError as e:
#         print(f"  ERROR: {e.stderr.strip()}")
#         return None

# # --- 2. 데이터 관리 ---
# BLOCK_REGISTRY = {}
# METHOD_REGISTRY = {}

# def load_data():
#     """JSON 파일에서 명령어 블록과 메소드를 로드합니다."""
#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     with open(os.path.join(base_dir, "HackingBlock/Command", "shell_command.json"), 'r') as f:
#         for block in json.load(f):
#             BLOCK_REGISTRY[block["name"]] = block
#     with open(os.path.join(base_dir, "HackingBlock/Method", "methods.json"), 'r') as f:
#         for method in json.load(f):
#             METHOD_REGISTRY[method["target_task"]] = method
#     print("✅ All data loaded into registries.")

# # --- 3. GTPyhop 연동 ---
# def setup_planner():
#     """GTPyhop 도메인을 설정하고, JSON 데이터로부터 동적으로 액션과 메소드를 선언합니다."""
#     domain = gtpyhop.Domain('hacking_domain')
#     gtpyhop.current_domain = domain

#     # 3-1. Action 동적 생성
#     for name, spec in BLOCK_REGISTRY.items():
#         def create_action_func(action_name, block_spec):
#             def action_func(state, *args):
#                 for key, value in block_spec.get('preconditions', {}).items():
#                     if not getattr(state, key, None) == value:
#                         return False
#                 for key, value in block_spec.get('effects', {}).items():
#                     setattr(state, key, value)
#                 return state
#             action_func.__name__ = action_name
#             return action_func
#         gtpyhop.declare_actions(create_action_func(name, spec))

#     # 3-2. Method 동적 생성
#     for task_name, method_spec in METHOD_REGISTRY.items():
#         def create_method_func(spec):
#             def method_func(state, *args):
#                 return [tuple(step) for step in spec["sequence"]]
#             method_func.__name__ = spec["name"]
#             return method_func
#         gtpyhop.declare_task_methods(task_name, create_method_func(method_spec))
    
#     print("✅ Planner setup complete.")

# # --- 4. 메인 실행부 ---
# if __name__ == '__main__':
#     # 1. 테스트용 zip 파일 생성
#     if os.path.exists("secret.zip"):
#         os.remove("secret.zip")
#     if os.path.exists("flag.txt"):
#         subprocess.run("zip secret.zip flag.txt", shell=True, check=True, capture_output=True)
#         print("Created 'secret.zip' for the test scenario.")

#     # 2. 데이터 로드 및 플래너 설정
#     load_data()
#     setup_planner()

#     # 3. 초기 상태 및 목표 설정
#     initial_state = gtpyhop.State('start')
#     initial_state.shell_access = True
#     initial_state.target = False
#     initial_state.archive_extracted = False
#     initial_state.file_content_read = False
#     initial_state.pattern_filtered = False
#     initial_state.final_data_extracted = False

#     # 최종 목표: 't_get_secret_from_zip' 메소드 실행
#     task_to_achieve = ('t_extract_final_number',)
#     print(f"\n[GTPyhop 플래너에게 '{task_to_achieve[0]}' 작업 요청]")

#     # 4. 계획 수립
#     plan = gtpyhop.find_plan(initial_state, [task_to_achieve])

#     if plan:
#         print(f"\n✅ SUCCESS: Plan found for '{task_to_achieve[0]}'!")
#         print("Plan steps:")
#         for idx, step in enumerate(plan):
#             print(f"  {idx+1}. {step}")

#         # 5. 계획 실행
#         print("\n[실제 명령 실행 결과]")
#         last_output = None
#         pipe_input = None
#         for step in plan:
#             action_name = step[0]
#             params = step[1] if len(step) > 1 else {}

#             if action_name == "pipe_command":
#                 pipe_input = last_output
#                 print(f"  INFO: Pipe command triggered. Storing '{pipe_input}' for next command's input.")
#                 continue

#             block_spec = BLOCK_REGISTRY.get(action_name)
#             if not block_spec:
#                 print(f"  ERROR: Block spec for '{action_name}' not found.")
#                 break

#             command_template = block_spec.get("command_template")
#             if not command_template:
#                 print(f"  INFO: No command template for '{action_name}', skipping execution logic.")
#                 continue

#             if not isinstance(params, dict):
#                 match = re.search(r"{(.*?)}", command_template)
#                 key = match.group(1) if match else "filepath"
#                 params = {key: params}

#             for key, value in params.items():
#                 if value == "{PREVIOUS_OUTPUT}":
#                     params[key] = last_output

#             # pipe_input이 있으면 stdin으로 전달
#             current_input = pipe_input
#             pipe_input = None # 사용 후 초기화

#             last_output = run_shell_command(command_template, params, input_data=current_input)
#             print(f"Last output {last_output}\n")
            
#             if last_output is None:
#                 print("Execution failed. Aborting plan.")
#                 break
        
#         print("\n--------------------")
#         print(f" 최종 결과: {last_output}")
#         print("--------------------")

#     else:
#         print(f"\n❌ ERROR: No plan found for '{task_to_achieve[0]}'.")