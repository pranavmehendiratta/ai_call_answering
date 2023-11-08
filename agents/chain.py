from langchain.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate, ChatPromptTemplate
from langchain import  LLMChain
from langchain.chat_models import ChatOpenAI
from task_generation_human_prompt import task_generation_human_prompt
from task_generation_system_prompt import task_generation_system_prompt
import langchain
import os
import json
import random

task_generation_system_message_prompt = SystemMessagePromptTemplate(prompt=task_generation_system_prompt)
task_generation_human_message_prompt = HumanMessagePromptTemplate(prompt=task_generation_human_prompt)

llm = ChatOpenAI(temperature=0.9, model="gpt-3.5-turbo")
history = [task_generation_system_message_prompt, task_generation_human_message_prompt]

langchain.verbose = True

chat_prompt = ChatPromptTemplate.from_messages(history)
llm_chain = LLMChain(llm=llm, prompt=chat_prompt)

def count_files_in_directory(directory_path):
    """Counts the number of files in a directory.

    Args:
        directory_path (str): Path to the directory.

    Returns:
        int: Number of files in the directory.
    """
    if not os.path.exists(directory_path):
        raise ValueError("Directory does not exist.")
    
    if not os.path.isdir(directory_path):
        raise ValueError("Provided path is not a directory.")
    
    all_items = os.listdir(directory_path)
    
    # Filter out only files, exclude sub-directories
    files = [item for item in all_items if os.path.isfile(os.path.join(directory_path, item))]
    
    return len(files)

def write_to_file(directory, file_name, content):
    """Writes the given content to a file in the specified directory, overwriting if the file exists.

    Args:
        directory (str): Path to the directory.
        file_name (str): Name of the file.
        content (str): Content to write to the file.
    """
    
    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    file_path = os.path.join(directory, file_name)
    
    with open(file_path, 'w') as file:
        file.write(content)

def main_v2():
    dir = "generated_tasks/v2/"
    number = count_files_in_directory(dir)
    next_file_name = f"generated_task_{number}.txt"
    chain_input = "Role: "
    input_concatenation = ""
    role = input("Role (Leave empty for auto generation): ")
    if role.strip() != "":
        chain_input = f"{chain_input}{role}\nTask: "
        input_concatenation = f"{input_concatenation}Role: {role}\n"
        #task = input("Task (Leave empty for auto generation): ")
        #if task != "":
        #    input_concatenation = f"{input_concatenation}Task: {task}\n"
        #    chain_input = f"{chain_input}{task}\nEnd Goal: "
    #print("chain_input: ", chain_input) 
    answer = llm_chain.run(chain_input)
    #print("chain_answer: ", answer)
    final_answer = f"{input_concatenation}{answer}"
    #print("final_answer: ", final_answer)
    write_to_file(dir, next_file_name, final_answer)

def main_v3():
    restaurant_service_file = open(os.getenv('RESTAURANT_SERVICES_FILE'), 'r')
    restaurant_services = json.load(restaurant_service_file)
    restaurant_types = list(restaurant_services["restaurant_types"].keys())
    restaurant_types_list = "\n".join([f"{i}: {restaurant_type}" for i, restaurant_type in enumerate(restaurant_types)])
    restaurant_type_index = input(f"{restaurant_types_list}\nSelect using 0 through {len(restaurant_types) - 1}: ")
    restaurant_type_name = restaurant_types[int(restaurant_type_index)]
    services = restaurant_services["restaurant_types"][restaurant_type_name]["services"]
    randomly_selected_services_indexes = random.sample(range(len(services)), 3)
    services_to_test_name = f"[{', '.join([services[i] for i in randomly_selected_services_indexes])}]"
    print(f"restaurant_type_name: {restaurant_type_name}")
    print(f"services_to_test_name: {services_to_test_name}")
    dir = "generated_tasks/v3/"
    number = count_files_in_directory(dir)
    next_file_name = f"generated_task_{number}.txt"
    chain_input = "Actor Background: "
    answer = llm_chain.run(
        {
            "input": chain_input,
            "restaurant_type": restaurant_type_name,
            "services_to_test": services_to_test_name
        }
    )
    final_answer = f"Restaurant type: {restaurant_type_name}\nServices to test: {services_to_test_name}\nActor Background: {answer}"
    print(final_answer)
    write_to_file(dir, next_file_name, final_answer)

if __name__ == "__main__":
    main_v3()