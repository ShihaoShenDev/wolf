import pytest
from fastapi.testclient import TestClient
from wolf.server.app import app
import json

client = TestClient(app)

def test_join_room():
    with client.websocket_connect("/ws/player1") as websocket:
        # Join room
        websocket.send_json({"action": "join", "room_id": "room1"})
        
        # Expect player_joined (broadcast to room, including self)
        # Wait, broadcast_to_room sends to all players in room.
        # So I should receive player_joined.
        # But wait, connection_manager adds connection before room logic?
        # In app.py:
        # await manager.connect(websocket, client_id) -> Adds to active_connections
        # ...
        # room.players[client_id] = player
        # await broadcast_to_room(...) -> Sends to all in room.players
        # So yes, I should receive player_joined.
        
        data = websocket.receive_json()
        if data.get("event") == "player_joined":
            # Then receive joined_room
            data = websocket.receive_json()
        
        assert data["event"] == "joined_room"
        assert data["room_id"] == "room1"

def test_start_game_force():
    with client.websocket_connect("/ws/player1") as websocket:
        websocket.send_json({"action": "join", "room_id": "room3"})
        
        # Consume join messages
        while True:
            data = websocket.receive_json()
            if data.get("event") == "joined_room":
                break
        
        # Force start
        websocket.send_json({"action": "start_game", "room_id": "room3", "force_start": True})
        
        # Expect game_started
        data = websocket.receive_json()
        assert data["event"] == "game_started"
        
        # Expect state_update
        data = websocket.receive_json()
        assert data["type"] == "state_update"
        assert "public" in data["data"]
        assert "private" in data["data"]
        assert data["data"]["public"]["phase"] == "NIGHT"

def test_game_action():
    with client.websocket_connect("/ws/player1") as websocket:
        websocket.send_json({"action": "join", "room_id": "room4"})
        
        # Consume join messages
        while True:
            data = websocket.receive_json()
            if data.get("event") == "joined_room":
                break
        
        # Force start
        websocket.send_json({"action": "start_game", "room_id": "room4", "force_start": True})
        websocket.receive_json() # game_started
        websocket.receive_json() # state_update
        
        # Send action
        websocket.send_json({
            "action": "action", 
            "room_id": "room4",
            "data": {
                "target_id": "player1",
                "skill_type": "KILL"
            }
        })
        
        # Expect action_result
        data = websocket.receive_json()
        assert data["type"] == "action_result"
        
        # Expect state_update broadcast
        data = websocket.receive_json()
        assert data["type"] == "state_update"

def test_chat():
    with client.websocket_connect("/ws/player1") as websocket:
        websocket.send_json({"action": "join", "room_id": "room5"})
        
        # Consume join messages
        while True:
            data = websocket.receive_json()
            if data.get("event") == "joined_room":
                break
        
        websocket.send_json({
            "action": "chat",
            "room_id": "room5",
            "data": {"message": "Hello"}
        })
        
        data = websocket.receive_json()
        assert data["type"] == "chat"
        assert data["message"] == "Hello"
        assert data["player_id"] == "player1"
