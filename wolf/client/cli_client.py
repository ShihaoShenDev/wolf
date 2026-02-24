import asyncio
import json
import sys
import uuid
import websockets
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import HTML

class WolfClient:
    def __init__(self, host="localhost", port=8000):
        self.host = host
        self.port = port
        self.client_id = str(uuid.uuid4())[:8]  # Generate a short unique ID
        self.websocket = None
        self.room_id = None
        self.session = PromptSession()
        self.game_state = None
        self.running = True

    async def connect(self):
        uri = f"ws://{self.host}:{self.port}/ws/{self.client_id}"
        print(f"Connecting to {uri}...")
        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                print(f"Connected! Your Client ID is: {self.client_id}")
                print("Type '/join <room_id>' to join a room.")
                
                # Run input and receive loops concurrently
                await asyncio.gather(
                    self.receive_messages(),
                    self.handle_input()
                )
        except ConnectionRefusedError:
            print(f"Failed to connect to {uri}. Is the server running?")
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.running = False

    async def receive_messages(self):
        try:
            async for message in self.websocket:
                await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("\nDisconnected from server.")
            self.running = False

    async def handle_message(self, message_str):
        try:
            data = json.loads(message_str)
            
            # Handle different message types
            msg_type = data.get("type")
            event = data.get("event")
            error = data.get("error")

            with patch_stdout():
                if error:
                    print(f"\n[ERROR] {error}")
                
                elif msg_type == "state_update":
                    self.print_game_state(data.get("data"))
                
                elif msg_type == "chat":
                    player = data.get("player_id")
                    content = data.get("message")
                    print(f"\n[CHAT] {player}: {content}")
                
                elif msg_type in ["action_result", "vote_result"]:
                    success = data.get("success")
                    msg = data.get("message")
                    status = "SUCCESS" if success else "FAILED"
                    print(f"\n[{status}] {msg}")
                
                elif event == "joined_room":
                    self.room_id = data.get("room_id")
                    print(f"\nJoined room: {self.room_id}")
                
                elif event == "player_joined":
                    print(f"\nPlayer {data.get('player_id')} joined the room.")
                
                elif event == "player_left":
                    print(f"\nPlayer {data.get('player_id')} left the room.")
                
                elif event == "game_started":
                    print(f"\nGame started in room {data.get('room_id')}!")
                
                else:
                    # Generic print for other messages
                    print(f"\n[SERVER] {message_str}")

        except json.JSONDecodeError:
            print(f"\n[RAW] {message_str}")
        except Exception as e:
            print(f"\nError handling message: {e}")

    def print_game_state(self, state):
        if not state:
            return

        public = state.get("public", {})
        private = state.get("private", {})
        
        phase = public.get("phase", "UNKNOWN")
        round_num = public.get("round", 0)
        players = public.get("players", {})
        
        role_info = private.get("role", {})
        role_name = role_info.get("name", "Unknown")
        team = role_info.get("team", "Unknown")
        is_alive = private.get("is_alive", True)
        
        print("\n" + "="*40)
        print(f"GAME STATE - Phase: {phase} | Round: {round_num}")
        print(f"You are: {role_name} ({team}) | Status: {'ALIVE' if is_alive else 'DEAD'}")
        
        print("\nPlayers:")
        for pid, p_data in players.items():
            status = "Alive" if p_data.get("is_alive") else "Dead"
            marker = " (YOU)" if pid == self.client_id else ""
            print(f"  - {pid}: {status}{marker}")
            
        teammates = private.get("teammates", [])
        if teammates:
            print(f"\nTeammates (Werewolves): {', '.join(teammates)}")
            
        print("="*40 + "\n")

    async def handle_input(self):
        while self.running:
            try:
                with patch_stdout():
                    user_input = await self.session.prompt_async(f"[{self.client_id}] > ")
                
                if not user_input.strip():
                    continue
                
                if user_input.lower() == "/quit":
                    self.running = False
                    if self.websocket:
                        await self.websocket.close()
                    break
                
                await self.process_command(user_input)
                
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break
            except Exception as e:
                print(f"Input error: {e}")

    async def process_command(self, user_input):
        parts = user_input.strip().split()
        command = parts[0].lower()
        args = parts[1:]
        
        payload = {}
        
        if command == "/join":
            if not args:
                print("Usage: /join <room_id>")
                return
            payload = {
                "action": "join",
                "room_id": args[0]
            }
        
        elif command == "/start":
            if not self.room_id:
                print("You must join a room first.")
                return
            
            force = False
            if args and args[0].lower() == "force":
                force = True
                
            payload = {
                "action": "start_game",
                "room_id": self.room_id,
                "force_start": force
            }
            
        elif command == "/vote":
            if not self.room_id or not args:
                print("Usage: /vote <target_id>")
                return
            payload = {
                "action": "vote",
                "room_id": self.room_id,
                "data": {"target_id": args[0]}
            }
            
        elif command in ["/kill", "/check", "/save", "/poison", "/protect", "/shoot", "/duel"]:
            if not self.room_id or not args:
                print(f"Usage: {command} <target_id>")
                return
            
            skill_map = {
                "/kill": "KILL",
                "/check": "CHECK",
                "/save": "SAVE",
                "/poison": "POISON",
                "/protect": "PROTECT",
                "/shoot": "SHOOT",
                "/duel": "DUEL"
            }
            
            payload = {
                "action": "action",
                "room_id": self.room_id,
                "data": {
                    "skill_type": skill_map[command],
                    "target_id": args[0]
                }
            }
            
        else:
            # Chat message
            if not self.room_id:
                print("Join a room to chat.")
                return
            payload = {
                "action": "chat",
                "room_id": self.room_id,
                "data": {"message": user_input}
            }

        if self.websocket and payload:
            await self.websocket.send(json.dumps(payload))

def run():
    client = WolfClient()
    try:
        asyncio.run(client.connect())
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    run()
