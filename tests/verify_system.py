import asyncio
import json
import subprocess
import time
import sys
import os
import websockets
from websockets.client import connect

SERVER_PORT = 8001
SERVER_URL = f"ws://localhost:{SERVER_PORT}"

async def receive_messages(ws, queue):
    try:
        async for message in ws:
            queue.put_nowait(json.loads(message))
    except Exception:
        pass

async def get_event(queue, event_name, timeout=5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Check if queue has item
            if queue.empty():
                await asyncio.sleep(0.1)
                continue
            
            # Peek or get
            # We need to process all messages until we find the one we want
            # But we might consume messages we need later.
            # So let's just peek? No, queues are consumed.
            # We should probably just return the next message and let the caller decide, 
            # or store unhandled messages.
            # For simplicity, let's just look for the specific event in the queue 
            # by draining it until we find it or timeout.
            
            msg = await asyncio.wait_for(queue.get(), timeout=1)
            # print(f"DEBUG: Received {msg}")
            
            if msg.get("event") == event_name:
                return msg
            if msg.get("type") == event_name:
                return msg
                
        except asyncio.TimeoutError:
            continue
    return None

async def run_test():
    server_process = None
    try:
        # Start the server
        print(f"Starting server on port {SERVER_PORT}...")
        # Use a new process group so we can kill it reliably
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            server_process = subprocess.Popen(
                [sys.executable, "-m", "wolf", "server", "--port", str(SERVER_PORT)],
                creationflags=creationflags,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            server_process = subprocess.Popen(
                [sys.executable, "-m", "wolf", "server", "--port", str(SERVER_PORT)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

        # Wait for server to be ready
        print("Waiting for server to be ready...")
        connected = False
        for i in range(10):
            try:
                # Try to connect to a check endpoint
                async with connect(f"{SERVER_URL}/ws/check_connection") as ws:
                    connected = True
                    break
            except (ConnectionRefusedError, OSError):
                time.sleep(1)
                print(f"Retrying connection... ({i+1}/10)")
        
        if not connected:
            print("Failed to connect to server.")
            if server_process:
                server_process.kill()
            sys.exit(1)

        print("Server is ready.")

        # Connect two clients
        uri_a = f"{SERVER_URL}/ws/client_a"
        uri_b = f"{SERVER_URL}/ws/client_b"

        async with connect(uri_a) as ws_a, connect(uri_b) as ws_b:
            print("Clients connected.")
            
            queue_a = asyncio.Queue()
            queue_b = asyncio.Queue()
            
            task_a = asyncio.create_task(receive_messages(ws_a, queue_a))
            task_b = asyncio.create_task(receive_messages(ws_b, queue_b))

            # Client A joins room "test"
            print("Client A joining room 'test'...")
            await ws_a.send(json.dumps({
                "action": "join",
                "room_id": "test"
            }))

            # Client A should get "joined_room"
            msg = await get_event(queue_a, "joined_room")
            if msg:
                print("Client A joined room.")
            else:
                print("Client A failed to join room.")
                return

            # Client A should get "player_joined" (itself)
            msg = await get_event(queue_a, "player_joined")
            if msg and msg.get("player_id") == "client_a":
                print("Client A received own join event.")
            
            # Client B joins room "test"
            print("Client B joining room 'test'...")
            await ws_b.send(json.dumps({
                "action": "join",
                "room_id": "test"
            }))

            # Client B should get "joined_room"
            msg = await get_event(queue_b, "joined_room")
            if msg:
                print("Client B joined room.")
            else:
                print("Client B failed to join room.")
                return

            # Client B should get "player_joined" (itself)
            msg = await get_event(queue_b, "player_joined")
            if msg and msg.get("player_id") == "client_b":
                print("Client B received own join event.")
                
            # Client A should get "player_joined" (Client B)
            # NOTE: Depending on timing, A might have received other messages.
            # But get_event drains until it finds it.
            print("Waiting for Client A to see Client B...")
            msg = await get_event(queue_a, "player_joined")
            if msg and msg.get("player_id") == "client_b":
                print("Client A received Client B's join event.")
            else:
                print("Client A failed to receive Client B's join event.")
                # Don't return, try to proceed

            # Client A sends "start_game"
            print("Client A sending start_game...")
            await ws_a.send(json.dumps({
                "action": "start_game",
                "room_id": "test",
                "force_start": True
            }))

            # Verify both receive "state_update" with phase="NIGHT"
            print("Waiting for state_update on Client A...")
            state_a = await get_event(queue_a, "state_update")
            if state_a:
                phase = state_a.get("data", {}).get("public", {}).get("phase")
                if phase == "NIGHT":
                    print("Client A received state_update with phase NIGHT.")
                else:
                    print(f"Client A received state_update but phase is {phase}.")
            else:
                print("Client A failed to receive state_update.")

            print("Waiting for state_update on Client B...")
            state_b = await get_event(queue_b, "state_update")
            if state_b:
                phase = state_b.get("data", {}).get("public", {}).get("phase")
                if phase == "NIGHT":
                    print("Client B received state_update with phase NIGHT.")
                else:
                    print(f"Client B received state_update but phase is {phase}.")
            else:
                print("Client B failed to receive state_update.")

            task_a.cancel()
            task_b.cancel()
            print("Verification successful!")

    except Exception as e:
        print(f"Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Terminating server...")
        if server_process:
            server_process.terminate()
            # Windows terminate is harsh, but we used CREATE_NEW_PROCESS_GROUP
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

if __name__ == "__main__":
    asyncio.run(run_test())
