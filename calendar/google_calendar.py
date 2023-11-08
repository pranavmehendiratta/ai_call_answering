from typing import Any, Dict, List
from ..calendar.base_calendar import BaseCalendar
import datetime
import pickle
import os.path
import os
import pytz
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

CREDENTIALS_PATH = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_PATH')

class GoogleCalendar(BaseCalendar):
    def create_event(
        self, 
        event_name: str, 
        date: str, 
        start_time: str, 
        end_time: str, 
        user_timezone: str = "America/Los_Angeles"
    ) -> Dict[str, Any]:
        """ Use whenever you want to create an event in your Google Calendar."""

        SCOPES = ['https://www.googleapis.com/auth/calendar.events']

        credentials_file = f"{CREDENTIALS_PATH}/credentials.json"
        write_token_file = f"{CREDENTIALS_PATH}/write_token.pickle"

        creds = None
        if os.path.exists(write_token_file):
            with open(write_token_file, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(write_token_file, 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        tz = pytz.timezone(user_timezone)

        try:
            start_time = datetime.datetime.strptime(start_time, '%H:%M:%S').time()
        except ValueError:
            start_time = datetime.datetime.strptime(start_time, '%H:%M').time()

        try:
            end_time = datetime.datetime.strptime(end_time, '%H:%M:%S').time()
        except ValueError:
            end_time = datetime.datetime.strptime(end_time, '%H:%M').time()

        start_date = tz.localize(datetime.datetime.combine(datetime.datetime.strptime(date, '%Y-%m-%d').date(), start_time))
        end_date = tz.localize(datetime.datetime.combine(datetime.datetime.strptime(date, '%Y-%m-%d').date(), end_time))

        event_body = {
            'summary': event_name,
            'start': {
                'dateTime': start_date.isoformat(),
                'timeZone': user_timezone,
            },
            'end': {
                'dateTime': end_date.isoformat(),
                'timeZone': user_timezone,
            }
        }

        event = service.events().insert(calendarId=self.calendar_id, body=event_body, conferenceDataVersion=1).execute()
        
        return event
    
    def update_event(
        self,
        event_id: str, 
        event_name: str, 
        date_str: str, 
        start_time_str: str, 
        end_time_str: str, 
        user_timezone: str = "America/Los_Angeles"
    ) -> Dict[str, Any]:
        """ Use whenever you want to update an event in your Google Calendar. You can you this tool to update one or all the fields of an event. If you want to update only one field, only pass that field."""
        SCOPES = ['https://www.googleapis.com/auth/calendar.events']

        credentials_file = f"{CREDENTIALS_PATH}/credentials.json"
        write_token_file = f"{CREDENTIALS_PATH}/write_token.pickle"

        creds = None
        if os.path.exists(write_token_file):
            with open(write_token_file, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(write_token_file, 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        # Fetch the original event
        original_event = service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()

        # Prepare changes based on the inputs provided
        if event_name:
            original_event['summary'] = event_name

        if date_str:
            if start_time_str:
                try:
                    start_time = datetime.datetime.strptime(start_time_str, '%H:%M:%S').time()
                except ValueError:
                    start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
            else:
                start_time = datetime.datetime.fromisoformat(original_event['start']['dateTime']).time()

            if end_time_str:
                try:
                    end_time = datetime.datetime.strptime(end_time_str, '%H:%M:%S').time()
                except ValueError:
                    end_time = datetime.datetime.strptime(end_time_str, '%H:%M').time()
            else:
                end_time = datetime.datetime.fromisoformat(original_event['end']['dateTime']).time()

            tz = pytz.timezone(user_timezone) if user_timezone else pytz.timezone(original_event['start']['timeZone'])
            
            start_date = tz.localize(datetime.datetime.combine(datetime.datetime.strptime(date_str, '%Y-%m-%d').date(), start_time))
            end_date = tz.localize(datetime.datetime.combine(datetime.datetime.strptime(date_str, '%Y-%m-%d').date(), end_time))

            original_event['start']['dateTime'] = start_date.isoformat()
            original_event['end']['dateTime'] = end_date.isoformat()

        if user_timezone:
            original_event['start']['timeZone'] = user_timezone
            original_event['end']['timeZone'] = user_timezone

        # Update the event
        updated_event = service.events().update(calendarId=self.calendar_id, eventId=event_id, body=original_event, conferenceDataVersion=1).execute()

        return updated_event
    
    def delete_event(
        self, 
        event_id: str
    ) -> bool:
        """ Use whenever you want to delete an event in your Google Calendar. Use this tool with caution."""

        credentials_file = f"{CREDENTIALS_PATH}/credentials.json"
        write_token_file = f"{CREDENTIALS_PATH}/write_token.pickle"

        SCOPES = ['https://www.googleapis.com/auth/calendar.events']

        creds = None
        if os.path.exists(write_token_file):
            with open(write_token_file, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(write_token_file, 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        try:
            service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
        

    def search_events(
        self, 
        event_name_filter: str, 
        start_date: str, 
        start_time: str, 
        end_date: str, 
        end_time: str, 
        user_timezone="America/Los_Angeles"
    ) -> List[Dict[str, Any]]:
        """ Use whenever you want to search for events in your Google Calendar by name and/or time period. You can use the information to calculate the number of events, the average duration of events, and more. """

        # May need to take this out in case reauthentication is required
        credentials_file = f"{CREDENTIALS_PATH}/credentials.json"
        read_token_file = f"{CREDENTIALS_PATH}/read_token.pickle"

        # If modifying these SCOPES, delete the file token.pickle.
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

        creds = None
        if os.path.exists(read_token_file):
            with open(read_token_file, 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, prompt the user to log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(read_token_file, 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        tz = pytz.timezone(user_timezone)
        now_in_user_tz = datetime.datetime.now(tz)

        default_start_time = datetime.time(0, 0)
        default_end_time = datetime.time(23, 59, 59)

        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = now_in_user_tz.date()

        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = start_date

        if start_time:
            try:
                start_time = datetime.datetime.strptime(start_time, '%H:%M:%S').time()
            except ValueError:
                start_time = datetime.datetime.strptime(start_time, '%H:%M').time()
        else:
            start_time = default_start_time

        if end_time:
            try:
                end_time = datetime.datetime.strptime(end_time, '%H:%M:%S').time()
            except ValueError:
                end_time = datetime.datetime.strptime(end_time, '%H:%M').time()
        else:
            end_time = default_end_time

        start_datetime = tz.localize(datetime.datetime.combine(start_date, start_time))
        end_datetime = tz.localize(datetime.datetime.combine(end_date, end_time))

        start_datetime_iso = start_datetime.isoformat()
        end_datetime_iso = end_datetime.isoformat()
            
        if start_datetime_iso > end_datetime_iso:
            raise ValueError("Start date should be on or before the end date.")
            
        #print("Searching for events between {} and {} with query: \'{}\'".format(start_datetime_iso, end_datetime_iso, event_name_filter))

        events_result = service.events().list(calendarId=self.calendar_id, timeMin=start_datetime_iso, timeMax=end_datetime_iso,
                                            singleEvents=True, orderBy='startTime').execute()
        
        events = events_result.get('items', [])
        #pprint.pprint(events)

        filtered_events = [event for event in events if event_name_filter.lower() in event['summary'].lower()]
        #pprint.pprint(filtered_events)

        return filtered_events
    
    def get_event(
        self,
        event_id: str
    ) -> Dict[str, Any]:
        # May need to take this out in case reauthentication is required
        credentials_file = f"{CREDENTIALS_PATH}/credentials.json"
        read_token_file = f"{CREDENTIALS_PATH}/read_token.pickle"

        # If modifying these SCOPES, delete the file token.pickle.
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

        creds = None
        if os.path.exists(read_token_file):
            with open(read_token_file, 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, prompt the user to log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(read_token_file, 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        event_result = service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()

        return event_result
    

    def _get_calendars_list(
        self
    ) -> List[Dict]:
        # May need to take this out in case reauthentication is required
        credentials_file = f"{CREDENTIALS_PATH}/credentials.json"
        read_token_file = f"{CREDENTIALS_PATH}/read_token.pickle"

        # If modifying these SCOPES, delete the file token.pickle.
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

        creds = None
        if os.path.exists(read_token_file):
            with open(read_token_file, 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, prompt the user to log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(read_token_file, 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        event_result = service.calendarList().list().execute()

        return event_result
    
    def _get_calendar_id(
        self
    ) -> str:
        for cal in self._calendar_list:
            if cal['name'] == self.calendar_name:
                return cal['id']
        raise ValueError(f"Calendar with name {self.calendar_name} not found.")
    

#google_calendar = GoogleCalendar(calendar_name="Audio Agent")
#print(google_calendar.calendar_id)