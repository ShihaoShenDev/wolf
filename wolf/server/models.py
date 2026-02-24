from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, PrivateAttr
from fastapi import WebSocket

class Role(str, Enum):
    VILLAGER = "villager"
    WEREWOLF = "werewolf"
    SEER = "seer"
    WITCH = "witch"
    HUNTER = "hunter"

class GameState(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    ENDED = "ended"

class Player(BaseModel):
    id: str
    name: str
    role: Optional[Role] = None
    is_alive: bool = True
    
    # WebSocket object is not serializable, so we exclude it from Pydantic model
    _websocket: Optional[WebSocket] = PrivateAttr(default=None)

    def set_websocket(self, ws: WebSocket):
        self._websocket = ws

    @property
    def websocket(self) -> Optional[WebSocket]:
        return self._websocket

class Room(BaseModel):
    id: str
    players: Dict[str, Player] = {}
    game_state: GameState = GameState.WAITING
    
    _game: Optional[Any] = PrivateAttr(default=None)

    @property
    def game(self) -> Optional[Any]:
        return self._game

    @game.setter
    def game(self, value: Any):
        self._game = value
