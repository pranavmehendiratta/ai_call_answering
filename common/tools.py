from typing import List
from pydantic import BaseModel, Field
from langchain.tools import tool
import pytz
import datetime
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseOutputParser
from langchain.prompts import PromptTemplate
import re
import json
from ..common.utils import extract_phone_number
import os

SCRATCH_SPACE = os.getenv("SCRATCH_SPACE_DIR")

class SendTextMessageSchema(BaseModel):
    message: str = Field(description="Your message to the customer")
    phone_number: str = Field(description="Phone number of the customer")

@tool("send_text_message", args_schema=SendTextMessageSchema)
def send_text_message(
    message: str,
    phone_number: str    
) -> str:
    """ Use this to send a text message to the customer """
    if len(phone_number) != 10:
        return "Invalid phone number. It should be 10 digits long."
    
    with (f"{SCRATCH_SPACE}/send_text_message.txt", "a") as f:
        formatted_text_message = {
            "message": message,
            "phone_number": phone_number
        }
        f.write(json.dumps(formatted_text_message))
        f.write("\n")
    return "Text message sent."

class NotesSchema(BaseModel):
    name: str = Field(description="Name of the customer")
    date: str = Field(description="Today's date in YYYY-MM-DD format")
    phone_number: str = Field(description="Phone number of the customer")
    notes: str = Field(description="Question you weren't able to answer")

@tool("notepad", args_schema=NotesSchema)
def notepad(
    name: str,
    date: str,
    phone_number: str,
    notes: str
) -> str:
    """ Use this to take notes for for questions you can't answer """
    if len(phone_number) != 10:
        return "Invalid phone number. It should be 10 digits long."

    with open(f"{SCRATCH_SPACE}/notepad.txt", "a") as f:
        formatted_notes = {
            "name": name,
            "date": date,
            "phone_number": phone_number,
            "notes": notes    
        }
        f.write(json.dumps(formatted_notes))
        f.write("\n")
    
    return "Notes saved."

class OrderNotepadSchema(BaseModel):
    name: str = Field(description="Name of the customer")
    phone_number: str = Field(description="Phone number of the customer")
    order_info: str = Field(description="customer's order")

@tool("order_notepad", args_schema=OrderNotepadSchema)
def order_notepad(
    name: str,
    phone_number: str,
    order_info: str
) -> str:
    """ Use this to take notes for for questions you can't answer """
    extracted_phone_number = extract_phone_number(phone_number)
    if len(extracted_phone_number) != 10:
        return "Invalid phone number. Please provide a valid phone number"

    with open(f"{SCRATCH_SPACE}/notepad.txt", "a") as f:
        formatted_notes = {
            "name": name,
            "phone_number": phone_number,
            "order_info": order_info    
        }
        f.write(json.dumps(formatted_notes))
        f.write("\n")
    
    return "Notes saved."

class MakeNoteForManagerSchema(BaseModel):
    name: str = Field(description="Name of the customer")
    date: str = Field(description="Today's date in YYYY-MM-DD format")
    phone_number: str = Field(description="Phone number of the customer")
    notes: str = Field(description="Question you weren't able to answer")

@tool("make_note_for_manager", args_schema=MakeNoteForManagerSchema)
def make_note_for_manager(
    name: str,
    date: str,
    phone_number: str,
    notes: str
) -> str:
    """ Use this to take notes for for questions you can't answer """
    if len(phone_number) != 10:
        return "Invalid phone number. It should be 10 digits long."

    with open(f"{SCRATCH_SPACE}/manager_notepad.txt", "a") as f:
        formatted_notes = {
            "name": name,
            "date": date,
            "phone_number": phone_number,
            "notes": notes    
        }
        f.write(json.dumps(formatted_notes))
        f.write("\n")
    
    return "Note saved for manager."

@tool("date_time_tool")
def date_time_tool() -> str:
    """ Use this to get metadata such as today's date, day, and current time"""
    formatted_datetime_components = _get_formatted_datetime_components()
    #max_num_of_reservations_for_1_hour_time_slot = 5
    return f"date: {formatted_datetime_components['day']}, {formatted_datetime_components['today_date']}, current_time: {formatted_datetime_components['current_time']}, timeZone: {formatted_datetime_components['current_time_zone_name']}" 

def _get_formatted_datetime_components():
    # Get current local time and date
    local_timezone = pytz.timezone("America/Los_Angeles")  # This will default to your system's local timezone
    local_time = datetime.datetime.now(tz=local_timezone)
    
    # Extract individual components
    date_str = local_time.strftime('%Y-%m-%d')
    time_str = local_time.strftime('%H:%M:%S')
    day_str = local_time.strftime('%A')
    
    offset = local_time.utcoffset().total_seconds() / 3600
    hours, minutes = divmod(abs(offset) * 60, 60)
    tz_format = '{:+03d}:{:02d}'.format(int(hours), int(minutes))
    
    return {
        'today_date': date_str,
        'current_time': time_str,
        'day': day_str,
        'current_time_zone_name': str(local_timezone),
        'current_time_zone_format': tz_format
    }

class DateOutputParser(BaseOutputParser):
    def parse(self, text: str) -> str:
        pattern = r"Final Answer: (.+)"
        match = re.search(pattern, text)
        
        if match:
            answer = match.group(1)
            return answer
        else:
            return "Unable to find the date. Please try again."

llm_date_chain_prompt_template = """{input} 

Format the answer as "Final Answer: <date>" where date is in YYYY-MM-DD

Let's think step by step.
"""

prompt = PromptTemplate.from_template(template=llm_date_chain_prompt_template)

llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613")

llm_date_chain = LLMChain(prompt=prompt, llm=llm, output_parser=DateOutputParser(), verbose=True)

#result = llm_date_chain.run(input="Today is Wednesday, 2023-08-23. What is the date on Friday?")

class RelativeDateCalculatorSchema(BaseModel):
    question: str = Field(description="Date question")

@tool("relative_date_calculator", args_schema=RelativeDateCalculatorSchema)
def relative_date_calculator(question: str) -> str:
    """ Use this whenever you want to calculate the relative date. For example: question = "Today is Wednesday, 2023-08-23. What is the date on Friday?" output will be the date on Friday. """
    return llm_date_chain.run(question)

class CalendarSchema(BaseModel):
    query: str = Field("Only possible values: \"this_week\", \"next_week\", or \"this_month\"")

@tool("calendar", args_schema=CalendarSchema)
def calendar(query: str) -> str:
    """ Use this to get the calendar for a time period. Usage calendar({"query"="this_week"}), calendar({"query"="this_month"}) or calendar({"query"="next_week"})"""
    today = datetime.date.today()

    if query == "this_week":
        # Find the start of the week (assuming Monday is the start)
        start_of_week = today - datetime.timedelta(days=today.weekday())
        # Generate dates for the week from start to the end (Sunday)
        dates = [start_of_week + datetime.timedelta(days=i) for i in range(7) if start_of_week + datetime.timedelta(days=i) >= today]
    
    elif query == "this_month":
        # Start date is today
        start_date = today
        # Find the last day of the month
        # The day before the first day of the next month
        last_date = (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
        # Generate dates from today to the end of the month
        dates = [start_date + datetime.timedelta(days=i) for i in range((last_date - start_date).days + 1)]
    
    elif query == "next_week":
        # Find the start of the next week (assuming Monday is the start)
        start_of_next_week = today + datetime.timedelta(days=(7 - today.weekday()))
        # Generate dates for the week from start to the end of next week (Sunday)
        dates = [start_of_next_week + datetime.timedelta(days=i) for i in range(7)]

    else:
        return ("Usage: The function accepts one of the following values as input:\n"
                "- 'this_week': Returns dates for the current week starting from today.\n"
                "- 'this_month': Returns dates for the current month starting from today.\n"
                "- 'next_week': Returns dates for the entire next week.")

    # Convert dates list to desired JSON format with days as keys
    result = {date.strftime('%Y-%m-%d'): "value" for date in dates}
    return json.dumps(result, indent=4)