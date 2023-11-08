from typing import Dict, Union
from flask import Flask, request
import logging
from flask_sock import Sock
import asyncio
import json
import uuid
import base64
from settings import shared_connections
from TwilioIncomingModels import TwilioIncomingCall
from dotenv import load_dotenv

app = Flask(__name__)
sock = Sock(app)
load_dotenv()

@sock.route('/twilio/incoming')
def incoming(ws: Sock) -> None:
    connectionId = "test" #str(uuid.uuid4())  # Generating unique identifier for the connection
    try:
        while True:
            data: Dict[str, Union[str, object]] = json.loads(ws.receive())
            eventName: str = data["event"]

            if eventName == "connected":
                print(f"Call connected: {connectionId}")

            elif eventName == "start":
                print(f"Call started: {connectionId}")
                shared_connections[connectionId] = TwilioIncomingCall.fromStartEvent(data, ws)
                print(f"shared_connections: {shared_connections}")
                shared_connections[connectionId].send_intro_audio()
                print("Send Intro audio")

            elif eventName == "media":
                media = data["media"]
                chunkNumber = media["chunk"]
                payload = data["media"]["payload"]
                chunk = base64.b64decode(payload)
                message_handler: TwilioIncomingCall = shared_connections[connectionId]
                message_handler.handleMediaBytes(chunk)
            
            elif eventName == "stop":
                message_handler: TwilioIncomingCall = shared_connections.pop(connectionId, None)
                if message_handler:
                    print(f"Call ended: {message_handler}")
                else:
                    print(f"No active call found for this connection")
            elif eventName == "mark":
                markName = data["mark"]["name"]
                print(f"Mark event: {connectionId}, name = {markName}")
            else:
                print(f"Unhandled event: {eventName}")

    except ConnectionError:
        if connectionId in shared_connections:
            del shared_connections[connectionId]
        print("Connection dropped")
    except Exception as e:
        print(f"Unhandled exception: {e}")

if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', debug=True, port=8000)
    
