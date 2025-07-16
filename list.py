

import json

def generate_list_file():
    """
    Reads shell command and method data from JSON files and generates a
    human-readable list in list.txt.
    """
    try:
        with open('HackingBlock/Command/shell_command.json', 'r', encoding='utf-8') as f:
            shell_commands = json.load(f)
    except FileNotFoundError:
        print("Error: 'HackingBlock/Command/shell_command.json' not found.")
        return
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from 'HackingBlock/Command/shell_command.json'.")
        return

    try:
        with open('HackingBlock/Method/methods.json', 'r', encoding='utf-8') as f:
            methods = json.load(f)
    except FileNotFoundError:
        print("Error: 'HackingBlock/Method/methods.json' not found.")
        return
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from 'HackingBlock/Method/methods.json'.")
        return

    with open('list.txt', 'w', encoding='utf-8') as f:
        f.write("====================\n")
        f.write("    Shell Commands\n")
        f.write("====================\n\n")

        for command in shell_commands:
            f.write(f"Name: {command.get('name', 'N/A')}\n")
            f.write(f"  - Preconditions: {command.get('preconditions', {})}\n")
            f.write(f"  - Effects: {command.get('effects', {})}\n\n")

        f.write("====================\n")
        f.write("        Methods\n")
        f.write("====================\n\n")

        for method in methods:
            f.write(f"Name: {method.get('name', 'N/A')}\n")
            sequence = method.get('sequence', [])
            if sequence:
                f.write("  - Sequence:\n")
                for i, step in enumerate(sequence):
                    task_name = step[0]
                    if task_name.startswith('t_'):
                         f.write(f"    {i+1}. Method: {task_name}\n")
                    else:
                         f.write(f"    {i+1}. Operator: {task_name}\n")
            f.write("\n")

    print("'list.txt' has been created successfully.")

if __name__ == "__main__":
    generate_list_file()

