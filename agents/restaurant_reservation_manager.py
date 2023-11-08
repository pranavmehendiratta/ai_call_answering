from enum import Enum
from typing import Union, Dict, Any, List, Optional, Tuple
from ..calendar.google_calendar import GoogleCalendar
from ..calendar.base_calendar import BaseCalendar
from datetime import datetime, timedelta
import json
import copy
from dateutil.parser import parse

class RestaurantReservationManager:

    class ReservationType(Enum):
        TABLE = "TABLE"
        BALLROOM = "BALLROOM"

    DURATION_IN_MINUTES_FOR_INDIVIDUALS = 60  # This could be a configurable setting
    RESTAURANT_OPEN_TIME = "14:00:00" # 2 PM
    RESTAURANT_CLOSE_TIME = "22:00:00" # 10 PM

    def __init__(self, calendar_instance: BaseCalendar):
        self.calendar_instance = calendar_instance
        with open('audio/structured_chat/table_config.json') as f:
            self.config_data = json.load(f)

        # Available tables
        self.table_availability: Dict[str, Dict] = {}
        for table_type, table in self.config_data['TABLES'].items():
            self.table_availability[table_type] = {
                'seats_up_to': table['seats_up_to'],
                'open_tables': table['num_of_tables']
            }

        self.ballroom_availability: Dict[str, Dict] = {}
        for ballroom_type, ballroom in self.config_data['BALLROOMS'].items():
            self.ballroom_availability[ballroom_type] = {
                'min_capacity': ballroom['min_capacity'],
                'max_capacity': ballroom['max_capacity'],
                'open_ballrooms': 1
            }

        # Pre-sort table information based on seating capacity for quick look-up
        self.sorted_tables = sorted(self.table_availability.items(), key=lambda x: x[1]['seats_up_to'])

    def _add_duration(self, time_str, duration_mins):
        # Convert the string to a datetime object
        time_obj = datetime.strptime(time_str, '%H:%M:%S')
        
        # Add the duration
        new_time_obj = time_obj + timedelta(minutes=duration_mins)
        
        # Convert back to string in desired format
        return new_time_obj.strftime('%H:%M:%S')

    def _subtract_duration(self, time_str, duration_mins):
        # Convert the string to a datetime object
        time_obj = datetime.strptime(time_str, '%H:%M:%S')
        
        # Add the duration
        new_time_obj = time_obj - timedelta(minutes=duration_mins)
        
        # Convert back to string in desired format
        return new_time_obj.strftime('%H:%M:%S')
    
    def _to_24_hour_format(self, time_str):
        # Handling AM/PM cases
        if "AM" in time_str or "PM" in time_str:
            # If there's no space, add one before 'AM' or 'PM' for consistency
            time_str = time_str.replace("AM", " AM").replace("PM", " PM")

            # Splitting the string on space to get the time part and the meridiem (AM/PM)
            time_part, meridiem = time_str.split() if ":" not in time_str.split()[1] else (time_str[:-2], time_str[-2:])

            # Parsing hours, minutes and seconds
            time_components = time_part.split(':')
            hours = int(time_components[0].strip())
            minutes = time_components[1] if len(time_components) > 1 else "00"
            seconds = time_components[2] if len(time_components) > 2 else "00"
            
            # Check if AM or PM
            if 'PM' in meridiem and hours != 12:
                hours += 12
            if 'AM' in meridiem and hours == 12:
                hours = 0

            return f"{hours:02d}:{minutes}:{seconds}"
        
        # Handling 24-hour format cases
        time_components = time_str.split(':')
        hours = int(time_components[0].strip())
        minutes = time_components[1] if len(time_components) > 1 else "00"
        seconds = time_components[2] if len(time_components) > 2 else "00"

        return f"{hours:02d}:{minutes}:{seconds}"
    
    def _encode_partial_event_name(
        self, 
        name: str, 
        phone_number: str,
    ) -> str:
        return f"_{name}_{phone_number}_"

    def _encode_event_name(
        self, 
        reservation_type: str, 
        name: str, 
        phone_number: str,
        party_size: int,
        type: str,
        duration: int
    ) -> str:
        return f"[{reservation_type}]_{name}_{phone_number}_{party_size}_{type}_{duration}"

    def _decode_event_name(
        self, 
        event_name: str
    ) -> Dict[str, str]:
        components = event_name.split('_')
        if len(components) != 6:
            raise Exception(f"Invalid event name: {event_name}")
        reservation_type = components[0][1:-1]  # Remove square brackets
        name = components[1]
        phone_number = components[2]
        party_size = components[3]
        type = components[4]
        duration = components[5]
        return {
            'reservation_type': reservation_type,
            'name': name,
            'phone_number': phone_number,
            'party_size': party_size,
            'type': type,
            'duration': duration
        }
    
    def _find_suitable_table(self, party_size: int) -> Optional[str]:
        for table_type, table_info in self.sorted_tables:
            if table_info['seats_up_to'] >= party_size and table_info['open_tables'] > 0:
                return table_type
        return None
    
    def _find_suitable_ballroom(self, party_size: int) -> Optional[str]:
        for ballroom_type, ballroom_info in self.ballroom_availability.items():
            if ballroom_info['min_capacity'] <= party_size <= ballroom_info['max_capacity'] and ballroom_info['open_ballrooms'] > 0:
                return ballroom_type
        return None
    
    def _initialize_table_availablility(self, date: str):
        if date not in self.date_based_table_availability:
            self.date_based_table_availability[date] = dict(self.table_availability)
        
        all_events_for_date = self.calendar_instance.search_events(
            event_name_filter="",
            start_date=date,
            start_time="00:00:00",
            end_date=date,
            end_time="23:59:59",
            user_timezone="America/Los_Angeles"
        )

        for event in all_events_for_date:
            event_name = event['event_name']
            event_info = self._decode_event_name(event_name)
            if event_info['reservation_type'] == self.ReservationType.TABLE.value:
                table_type = event_info['type']
                self.date_based_table_availability[date][table_type]['open_tables'] -= 1

    def _initialize_ballroom_availablility(self, date: str):
        if date not in self.date_based_ballroom_availability:
            self.date_based_ballroom_availability[date] = dict(self.ballroom_availability)
        
        all_events_for_date = self.calendar_instance.search_events(
            event_name_filter="",
            start_date=date,
            start_time=self.RESTAURANT_OPEN_TIME,
            end_date=date,
            end_time=self.RESTAURANT_CLOSE_TIME,
            user_timezone="America/Los_Angeles"
        )

        for event in all_events_for_date:
            event_name = event['event_name']
            event_info = self._decode_event_name(event_name)
            if event_info['reservation_type'] == self.ReservationType.BALLROOM.value:
                ballroom_type = event_info['type']
                self.date_based_ballroom_availability[date][ballroom_type]['open_ballrooms'] -= 1

    def _extract_time_from_event(event) -> Tuple[str, str]:
        start_time_str = event['start']['dateTime']
        end_time_str = event['end']['dateTime']

        # Parsing the datetime string
        start_time_dt = parse(start_time_str)
        end_time_dt = parse(end_time_str)

        # Formatting to time part only in HH:mm:ss format
        start_time = start_time_dt.strftime("%H:%M:%S")
        end_time = end_time_dt.strftime("%H:%M:%S")

        return (start_time, end_time)


    def make_reservation_for_individuals(
        self,
        name: str,
        phone_number: str,
        date: str,
        start_time: str,
        party_size: int
    ) -> Union[Dict[str, Any], str]:
        if party_size > 6:
            return "Sorry, we only take reservations for up to 6 people. If you have a party size larger than 25, we can help you book a ballroom."

        # Step 1: Convert Start Time to 24-Hour Format
        start_time_24hr = self._to_24_hour_format(start_time)
        
        # Step 2: Generate Event Name
        reservation_type = self.ReservationType.TABLE.value
        table_type = self._find_suitable_table(party_size)
        event_name = self._encode_event_name(reservation_type, name, phone_number, party_size, table_type, self.DURATION_IN_MINUTES_FOR_INDIVIDUALS)

        # Step 3: Calculate End Time
        end_time = self._add_duration(start_time_24hr, self.DURATION_IN_MINUTES_FOR_INDIVIDUALS)

        try:
            created_event = self.calendar_instance.create_event(
                event_name=event_name,
                date=date,
                start_time=start_time_24hr,
                end_time=end_time
            )

            return {
                'id': created_event['id'],
                'name': name,
                'phone_number': phone_number,
                'party_size': party_size,
                'duration_in_mins': self.DURATION_IN_MINUTES_FOR_INDIVIDUALS,
                'status': created_event['status'],
                'date': date,
                'start_time': start_time_24hr,
                'end_time': end_time
            }
        except Exception:
            return "Sorry, I'm having trouble accessing out system at the moment. Can I make a note and will send you a confirmation text message as soon as your table is booked?"
    
    def _find_overlapping_events(
        self, 
        events: List[Dict], 
        start_time_str: str, 
        end_time_str: str,
        reservation_type: ReservationType
    ) -> List[Dict]:
        overlapping_events = {}
        
        # Convert input start and end times to datetime.time objects
        start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
        end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()

        for event in events:
            # Extract start and end times from the event and convert to datetime.time
            event_start_time_str = event['start']['dateTime'].split('T')[1].split('-')[0]
            event_end_time_str = event['end']['dateTime'].split('T')[1].split('-')[0]
            
            event_start_time = datetime.strptime(event_start_time_str, '%H:%M:%S').time()
            event_end_time = datetime.strptime(event_end_time_str, '%H:%M:%S').time()

            # Check for overlapping conditions
            if event_start_time < end_time and event_end_time > start_time:
                decoded_event = self._decode_event_name(event["summary"])
                decoded_reservation_type = decoded_event["reservation_type"]
                decoded_event_type = decoded_event["type"]
                if reservation_type == self.ReservationType.TABLE and decoded_reservation_type == self.ReservationType.TABLE.value:
                    overlapping_events[decoded_event_type] = overlapping_events.get(decoded_event_type, 0) + 1
                elif reservation_type == self.ReservationType.BALLROOM and decoded_reservation_type == self.ReservationType.BALLROOM.value:
                    overlapping_events[decoded_event_type] = overlapping_events.get(decoded_event_type, 0) + 1
                    
        return overlapping_events

    def find_tables_for_individuals(
        self, 
        date: str, 
        time: str
    ) -> List[str]:
        """
        Find available tables for individuals for the given date and time.
        """
        # Convert time to 24-hour format
        time_24hr = self._to_24_hour_format(time)
        end_time_24hr = self._add_duration(time_24hr, self.DURATION_IN_MINUTES_FOR_INDIVIDUALS)
        
        # Get all the events for the date
        try:
            events = self.calendar_instance.search_events(
                event_name_filter="",
                start_date=date,
                start_time=self.RESTAURANT_OPEN_TIME,
                end_date=date,
                end_time=self.RESTAURANT_CLOSE_TIME,
                user_timezone="America/Los_Angeles"
            )
            
            available_tables = copy.deepcopy(self.table_availability)
            overlapping_events = self._find_overlapping_events(events, time_24hr, end_time_24hr, self.ReservationType.TABLE)

            keys_to_remove = []
            for key in available_tables.keys():
                available_tables[key]['open_tables'] -= overlapping_events.get(key, 0)
                if available_tables[key]['open_tables'] == 0:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del available_tables[key]

            return available_tables
        except Exception:
            return "Sorry, I'm having trouble accessing out system at the moment. Ask for phone number, name and time for scheduling a call back."
    
    def search_booked_reservations(
        self, 
        name: str, 
        date: str, 
        phone_number: str
    ) -> List[dict]:
        # Step 1: Convert Start Time to 24-Hour Format
        start_time_24hr = self.RESTAURANT_OPEN_TIME
        end_time_24hr = self.RESTAURANT_CLOSE_TIME

        # Step 2: Generate Event Name
        event_name = self._encode_partial_event_name(name, phone_number)

        try:
            raw_reservations = self.calendar_instance.search_events(
                event_name_filter=event_name,
                start_date=date,
                start_time=start_time_24hr,
                end_date=date,
                end_time=end_time_24hr,
                user_timezone="America/Los_Angeles"
            )
            
            # 2. Decode the event names.
            decoded_reservations = [self._decode_event_name(reservation['summary']) for reservation in raw_reservations]
            
            # 3. Apply filters based on the provided search criteria.
            filtered_reservations = []

            for decoded_info, raw_reservation in zip(decoded_reservations, raw_reservations):
                if name and decoded_info['name'] != name:
                    continue
                if phone_number and decoded_info['phone_number'] != phone_number:
                    continue
                # TODO: Maybe add additional checks for date and time but for now its good enough

                start_time_str = raw_reservation['start']['dateTime']
                end_time_str = raw_reservation['end']['dateTime']

                # Parsing the datetime string
                start_time_dt = parse(start_time_str)
                end_time_dt = parse(end_time_str)

                # Formatting to time part only in HH:mm:ss format
                start_time = start_time_dt.strftime("%H:%M:%S")
                end_time = end_time_dt.strftime("%H:%M:%S")

                filtered_reservations.append(
                    {
                        'id': raw_reservation['id'],
                        'name': decoded_info['name'],
                        'phone_number': decoded_info['phone_number'],
                        'party_size': decoded_info['party_size'],
                        'duration_in_mins': decoded_info['duration'],
                        'status': raw_reservation['status'], 
                        'date': date,
                        'start_time': start_time,
                        'end_time': end_time
                    }
                )
            
            return filtered_reservations
        except Exception:
            return "Sorry, I'm having trouble accessing out system at the moment. Ask for time for scheduling a call back."
    
    def find_ballrooms_availability(
        self,
        date: str,
        start_time: str,
        duration: int
    ) -> Union[Dict[str, Any], str]:
        try:
            start_time24hr = self._to_24_hour_format(start_time)
            duration_in_mins = duration * 60
            end_time24hr = self._add_duration(start_time24hr, duration_in_mins)

            events = self.calendar_instance.search_events(
                event_name_filter="",
                start_date=date,
                start_time=self.RESTAURANT_OPEN_TIME,
                end_date=date,
                end_time=self.RESTAURANT_CLOSE_TIME,
                user_timezone="America/Los_Angeles"
            )

            available_ballrooms = copy.deepcopy(self.ballroom_availability)
            overlapping_events = self._find_overlapping_events(events, start_time24hr, end_time24hr, self.ReservationType.BALLROOM)

            keys_to_remove = []
            for key in available_ballrooms.keys():
                available_ballrooms[key]['open_ballrooms'] -= overlapping_events.get(key, 0)
                if available_ballrooms[key]['open_ballrooms'] == 0:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del available_ballrooms[key]

            return available_ballrooms
        
        except Exception:
            return "Sorry, I'm having trouble accessing out system at the moment. Ask for time for scheduling a call back."
        

    def make_reservation_for_ballrooms(
        self,
        name: str,
        phone_number: str,
        date: str,
        start_time: str,
        party_size: int,
        duration_in_hours: int
    ) -> Union[Dict[str, Any], str]:
        if party_size < 25:
            return "Sorry, we only take ballroom reservations for parties of 25 or more people. If you have a party size of 6 or less, we can help you book a table."

        # Step 1: Convert Start Time to 24-Hour Format
        start_time_24hr = self._to_24_hour_format(start_time)
        
        duration_in_mins = duration_in_hours * 60

        # Step 2: Generate Event Name
        reservation_type = self.ReservationType.BALLROOM.value
        ballroom_type = self._find_suitable_ballroom(party_size)
        event_name = self._encode_event_name(reservation_type, name, phone_number, party_size, ballroom_type, duration_in_mins)
        
        # Step 3: Calculate End Time
        end_time = self._add_duration(start_time_24hr, duration_in_mins)

        try:
            created_event = self.calendar_instance.create_event(
                event_name=event_name,
                date=date,
                start_time=start_time_24hr,
                end_time=end_time
            )

            return {
                'id': created_event['id'],
                'name': name,
                'phone_number': phone_number,
                'party_size': party_size,
                'duration_in_mins':duration_in_mins,
                'status': created_event['status'],
                'date': date,
                'start_time': start_time_24hr,
                'end_time': end_time
            }
        except Exception:
            return "Sorry, I'm having trouble accessing out system at the moment. Can I make a note and will send you a confirmation text message as soon as your table is booked?"  

    def update_reservation(
        self, 
        event_id: str,
        name: str,
        phone_number: str,
        date: str,
        start_time: str,
        party_size: int,
        duration_in_hours: int = 1
    ) -> Union[Dict[str, Any], str]:
        prev_event_name = self.calendar_instance.get_event(event_id)['summary']
        prev_event_info = self._decode_event_name(prev_event_name)

        start_time_24hr = self._to_24_hour_format(start_time)
        duration_in_mins = duration_in_hours * 60
        end_time_24hr = self._add_duration(start_time_24hr, duration_in_mins)

        event_name = self._encode_event_name(
            prev_event_info["reservation_type"],
            name, 
            phone_number, 
            party_size,
            prev_event_info["type"],
            duration_in_mins
        )
        
        try:
            updated_event = self.calendar_instance.update_event(
                event_id=event_id,
                event_name=event_name,
                date_str=date,
                start_time_str=start_time_24hr,
                end_time_str=end_time_24hr
            )

            return {
                'id': updated_event['id'],
                'name': name,
                'phone_number': phone_number,
                'party_size': party_size,
                'duration_in_mins': duration_in_mins,
                'status': updated_event['status'],
                'date': date,
                'start_time': start_time_24hr,
                'end_time': end_time_24hr
            }
        except Exception:
            return "Sorry, I'm having trouble accessing out system at the moment. Can I make a note and will send you a confirmation text message as soon as your table is booked?"
        

    def cancel_reservation(
        self,
        event_id: str
    ) -> str:
        if self.calendar_instance.delete_event(event_id):
            "Your reservation has been cancelled."
        else:
            "Sorry I'm having trouble accessing our systems at the momemt. Rest assured I have noted down your request and will send you a confirmation text message as soon as your reservation is cancelled."
        
google_calendar = GoogleCalendar("Audio Agent")
reservation_manager = RestaurantReservationManager(google_calendar)
#reservation_manager.find_tables_for_individuals(
#    date="2023-09-11",
#    time="15:50:00"    
#)

#result = reservation_manager.search_booked_reservations(
#    name="Reddington",
#    date="2023-09-11",
#    phone_number="1234567890"
#)

#print(result)

#result = reservation_manager.make_reservation_for_ballrooms(
#    name="Harold Cooper",
#    phone_number="1234567890",
#    date="2023-09-12",
#    start_time="17:45:00",
#    party_size=25,
#    duration_in_hours=5
#)

#result = reservation_manager.find_ballrooms_availability(
#    date="2023-09-12",
#    start_time="17:45:00",
#    duration=5
#)

#result = reservation_manager.update_reservation(
#    event_id='rbt9frshmbb4ifc0oq6a6tfmhs',
#    name="Harold Cooper Updated",
#    date="2023-09-12",
#    phone_number="0000000000",
#    start_time="17:45:00",
#    party_size=25,
#)

#print(f"result = {result}")
