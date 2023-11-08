from datetime import datetime, timedelta
import os
import re

def formatted_date_and_day():
    # Get the current date
    now = datetime.now()
    # Format the date
    return now.strftime('%A, %Y-%m-%d')

def formatted_date():
    # Get the current date
    now = datetime.now()
    # Format the date
    return now.strftime('%Y-%m-%d')

def formatted_date_time():
    # Get the current date and time
    now = datetime.now()
    # Format the date and time
    return now.strftime('%Y-%m-%d %H:%M:%S')

def add_days_to_date(date_str: str, days: int) -> str:
    # Convert the date string to a datetime object
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Add the specified number of days
    new_date_obj = date_obj + timedelta(days=days)
    
    # Convert the datetime object back to a string in the desired format
    return new_date_obj.strftime('%Y-%m-%d')

def extract_phone_number(s):
    """Extract digits from a string representing a phone number."""
    return ''.join(re.findall(r'\d', s))


SCRATCH_SPACE_DIR_NAME = formatted_date_time()
SCRATCH_SPACE_DIR_PATH = f"{os.getenv('SCRATCH_SPACE_DIR')}/{SCRATCH_SPACE_DIR_NAME}"

os.mkdir(SCRATCH_SPACE_DIR_PATH)