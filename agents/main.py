from test_human_zero_shot_agent import test_human_agent_executor, AGENT_DIR_PATH, TestOnToolCallbackHandler
from test_human_system_prompt import test_human_system_prompt
import os

def print_role_and_task_v2(tasks):
    for idx, task in enumerate(tasks):
        role = task.get('role', 'N/A')  # Use 'N/A' as default if the key is not present
        task_description = task.get('task', 'N/A')
        print(f"{idx}. Role: {role}\n   Task: {task_description}\n")

def print_role_and_task_v3(tasks):
    for idx, task in enumerate(tasks):
        name = task.get('name', 'N/A')  # Use 'N/A' as default if the key is not present
        task_description = task.get('task', 'N/A')
        print(f"{idx}. Name: {name}\n  Task: {task_description}\n")

def extract_task_data(directory):
    tasks = []

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            
            with open(file_path, 'r') as file:
                task_data = {}
                for line in file:
                    if ': ' in line:
                        key, value = line.split(': ', 1)
                        # Convert key to lowercase and strip any whitespace
                        key = key.lower().strip()
                        # Only strip trailing whitespace from value to preserve any necessary leading whitespace
                        value = value.rstrip()
                        task_data[key] = value
                tasks.append(task_data)

    return tasks

def main_v2():
    tasks_directory_path = "tasks/generated_tasks/v2/" 
    possible_tasks = extract_task_data(tasks_directory_path)
    print_role_and_task_v2(possible_tasks)
    num = input(f"Select role (0 to {len(possible_tasks) - 1}): ")
    num = int(num.strip())
    selected_role = possible_tasks[num] 

    arguments = {
        "user_role_name": selected_role["role"], 
        "assistant_role_name": "Call Center Agent for Restaurant named 'TimePlated'", 
        "task": selected_role["task"],
        "name": selected_role["name"],
        "email": selected_role["email"],
        "phone": selected_role["phone"]
    }

    system_prompt_file = open(f"{AGENT_DIR_PATH}/system_prompt.txt", "w")
    system_prompt_file.write(test_human_system_prompt.format(**arguments))

    result = test_human_agent_executor.run(
        arguments,
        callbacks=[TestOnToolCallbackHandler()]
    )
    print("Result:", result)

def main_v3():
    tasks_directory_path = "tasks/generated_tasks/v3/" 
    possible_tasks = extract_task_data(tasks_directory_path)
    print_role_and_task_v3(possible_tasks)
    num = input(f"Select role (0 to {len(possible_tasks) - 1}): ")
    num = int(num.strip())
    selected_role = possible_tasks[num] 

    arguments = {
        "user_role_name": "customer", 
        "assistant_role_name": "Call Center Agent for casual dining Restaurant named 'TimePlated'", 
        "task": selected_role["task"],
        "name": selected_role["name"],
        "email": selected_role["email"],
        "phone": selected_role["phone"]
    }

    system_prompt_file = open(f"{AGENT_DIR_PATH}/system_prompt.txt", "w")
    system_prompt_file.write(test_human_system_prompt.format(**arguments))

    result = test_human_agent_executor.run(
        arguments,
        callbacks=[TestOnToolCallbackHandler()]
    )
    print("Result:", result)


if __name__ == "__main__":
    main_v3()