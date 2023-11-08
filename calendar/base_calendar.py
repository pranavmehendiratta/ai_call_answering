from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union, Optional
from pydantic import BaseModel, Field, root_validator

class BaseCalendar(ABC):
    def __init__(self, calendar_name) -> None:
        self.calendar_name: str = calendar_name
        self._initialize_calendar_list()
        self.calendar_id: str = self._get_calendar_id()

    def _initialize_calendar_list(self) -> None:
        self._calendar_list = [{"id": calendar['id'], "name": calendar['summary']} for calendar in self._get_calendars_list()['items']]

    @abstractmethod
    def create_event(
        self,
        event_name: str, 
        date: str,
        start_time: str,
        end_time: str,
        user_timezone: str = "America/Los_Angeles"
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_event(
        self,
        event_id: str, 
        event_name: str, 
        date_str: str, 
        start_time_str: str, 
        end_time_str: str, 
        user_timezone: str = "America/Los_Angeles"
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def delete_event(
        self, 
        event_id: str
    ) -> str:
        pass

    @abstractmethod
    def search_events(
        self, 
        event_name_filter: str, 
        start_date: str, 
        start_time: str,
        end_date: str, 
        end_time: str,
        user_timezone = "America/Los_Angeles"
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_event(
        self, 
        event_id: str
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _get_calendars_list(
        self
    ) -> List[Dict]:
        pass

    @abstractmethod
    def _get_calendar_id(
        self
    ) -> str:
        pass