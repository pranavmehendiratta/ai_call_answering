from typing import Dict, Union
from TwilioIncomingModels import TwilioIncomingCall

shared_connections: Dict[str, TwilioIncomingCall] = {}