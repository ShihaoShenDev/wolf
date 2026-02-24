from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import os
import json
from .models import Player, Room, GameState
from .connection_manager import ConnectionManager
from .game.engine import Game, GamePhase
from .game.roles import SkillType

app = FastAPI()

manager = ConnectionManager()
rooms: dict[str, Room] = {}

async def broadcast_to_room(room_id: str, message: str):
    if room_id in rooms:
        room = rooms[room_id]
        for player_id in room.players:
            await manager.send_personal_message(message, player_id)

async def broadcast_game_state(room_id: str):
    room = rooms.get(room_id)
    if not room or not room.game:
        return
    
    game = room.game
    public_state = game.get_public_state()
    
    for player_id in room.players:
        # Get private state
        private_state = game.get_private_state(player_id)
        
        # Combine
        state = {
            "public": public_state,
            "private": private_state
        }
        
        # Use manager to send message to player
        await manager.send_personal_message(json.dumps({
            "type": "state_update",
            "data": state
        }), player_id)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "join":
                    room_id = message.get("room_id")
                    if room_id:
                        # Create room if not exists
                        if room_id not in rooms:
                            rooms[room_id] = Room(id=room_id)
                        
                        room = rooms[room_id]
                        
                        # Add player to room
                        if client_id not in room.players:
                            player = Player(id=client_id, name=client_id)
                            player.set_websocket(websocket)
                            room.players[client_id] = player
                            
                            # Broadcast join event
                            await manager.broadcast(json.dumps({
                                "event": "player_joined",
                                "player_id": client_id,
                                "room_id": room_id
                            }))
                            
                            # Send success message to the player
                            await manager.send_personal_message(json.dumps({
                                "event": "joined_room",
                                "room_id": room_id,
                                "game_state": room.game_state
                            }), client_id)
                    else:
                        await manager.send_personal_message(json.dumps({"error": "Missing room_id"}), client_id)

                elif action == "start_game":
                    room_id = message.get("room_id")
                    if room_id in rooms:
                        room = rooms[room_id]
                        player_ids = list(room.players.keys())
                        # Allow force_start for testing with < 12 players
                        if len(player_ids) >= 12 or message.get("force_start"):
                            room.game = Game(player_ids)
                            room.game.start()
                            room.game_state = GameState.PLAYING
                            
                            await broadcast_to_room(room_id, json.dumps({
                                "event": "game_started",
                                "room_id": room_id
                            }))
                            await broadcast_game_state(room_id)
                        else:
                            await manager.send_personal_message(json.dumps({"error": "Need 12 players to start"}), client_id)

                elif action == "action":
                    room_id = message.get("room_id")
                    if room_id in rooms:
                        room = rooms[room_id]
                        if room.game:
                            data = message.get("data", {})
                            target_id = data.get("target_id")
                            skill_type_str = data.get("skill_type")
                            
                            success = False
                            msg = "Unknown action"
                            
                            if room.game.phase == GamePhase.NIGHT:
                                try:
                                    skill_type = SkillType(skill_type_str)
                                    success, msg = room.game.process_night_action(client_id, target_id, skill_type)
                                except ValueError:
                                    msg = "Invalid skill type"
                            elif room.game.phase == GamePhase.DAY:
                                # Day actions (shoot, duel)
                                try:
                                    skill_type = SkillType(skill_type_str)
                                    if skill_type in [SkillType.SHOOT, SkillType.DUEL]:
                                        success, msg = room.game.process_day_action(client_id, target_id, action_type=skill_type.value)
                                    else:
                                        msg = "Invalid day action skill"
                                except ValueError:
                                    msg = "Invalid skill type"
                            else:
                                msg = "Game not in action phase"
                                    
                            await manager.send_personal_message(json.dumps({
                                "type": "action_result",
                                "success": success,
                                "message": msg
                            }), client_id)
                            
                            await broadcast_game_state(room_id)

                elif action == "vote":
                    room_id = message.get("room_id")
                    if room_id in rooms:
                        room = rooms[room_id]
                        if room.game and room.game.phase == GamePhase.DAY:
                            data = message.get("data", {})
                            target_id = data.get("target_id")
                            success, msg = room.game.process_day_action(client_id, target_id, action_type="VOTE")
                            
                            await manager.send_personal_message(json.dumps({
                                "type": "vote_result",
                                "success": success,
                                "message": msg
                            }), client_id)
                            
                            await broadcast_game_state(room_id)

                elif action == "chat":
                    room_id = message.get("room_id")
                    if room_id in rooms:
                        content = message.get("data", {}).get("message", "")
                        await manager.broadcast(json.dumps({
                            "type": "chat",
                            "player_id": client_id,
                            "message": content
                        }))
                
                else:
                    await manager.send_personal_message(json.dumps({"error": "Unknown action"}), client_id)

            except json.JSONDecodeError:
                await manager.send_personal_message(f"You wrote: {data}", client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        # Remove player from room logic
        for room_id, room in rooms.items():
            if client_id in room.players:
                del room.players[client_id]
                await broadcast_to_room(room_id, json.dumps({
                    "event": "player_left",
                    "player_id": client_id,
                    "room_id": room_id
                }))

# Mount static files
# Use absolute path to ensure it works regardless of where the app is run from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "web", "static")

if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
