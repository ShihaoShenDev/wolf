# 狼人杀 AI 接入指南 (Werewolf AI Integration Guide)

本文档旨在帮助开发者将 AI Agent 接入 `wolf` 狼人杀游戏服务器。

## 1. 连接方式 (Connection)

服务器使用 WebSocket 协议进行通信。

*   **URL**: `ws://<server_host>:<port>/ws/<client_id>`
*   **示例**: `ws://localhost:8000/ws/ai_agent_001`
*   **Client ID**: 任意唯一字符串，用于标识玩家身份。

## 2. 通信协议 (Protocol)

所有消息均为 JSON 格式。

### 2.1 客户端发送消息 (Client -> Server)

AI 需要根据当前状态发送以下指令：

#### 加入房间
```json
{
  "action": "join",
  "room_id": "room_1"
}
```

#### 开始游戏 (仅限房主或测试用)
```json
{
  "action": "start_game",
  "room_id": "room_1",
  "force_start": true  // 可选，强制在不满12人时开始
}
```

#### 执行行动 (夜间/白天技能)
适用于：狼人杀人、预言家验人、女巫毒/救、守卫守护、猎人开枪、骑士决斗。
```json
{
  "action": "action",
  "room_id": "room_1",
  "data": {
    "target_id": "target_player_id",
    "skill_type": "KILL" // 可选值: KILL, CHECK, SAVE, POISON, PROTECT, SHOOT, DUEL
  }
}
```

#### 投票 (白天)
```json
{
  "action": "vote",
  "room_id": "room_1",
  "data": {
    "target_id": "target_player_id"
  }
}
```

#### 聊天 (公聊)
```json
{
  "action": "chat",
  "room_id": "room_1",
  "data": {
    "message": "我是预言家，昨晚验了 Player 2 是金水！"
  }
}
```

---

### 2.2 服务器推送消息 (Server -> Client)

AI 需监听并处理以下消息：

#### 状态更新 (State Update)
这是最核心的消息，包含游戏的所有公开和私有信息。每次状态变更（如阶段切换、行动结算）都会发送。
```json
{
  "type": "state_update",
  "data": {
    "public": {
      "phase": "NIGHT", // 阶段: WAITING, NIGHT, DAY, ENDED
      "round": 1,
      "players": {
        "player_1": { "is_alive": true },
        "player_2": { "is_alive": false },
        ...
      }
    },
    "private": {
      "player_id": "my_id",
      "is_alive": true,
      "role": {
        "name": "Seer", // 角色名: Werewolf, Villager, Seer, Witch, Hunter, Guard, Idiot, Knight
        "team": "GOOD", // 阵营: GOOD, WEREWOLF
        "skills": ["CHECK"] // 当前可用技能
      },
      "teammates": [] // 如果是狼人，这里包含队友 ID 列表
    }
  }
}
```

#### 操作结果反馈
```json
{
  "type": "action_result", // 或 "vote_result"
  "success": true,
  "message": "Action recorded"
}
```

#### 聊天消息
```json
{
  "type": "chat",
  "player_id": "player_2",
  "message": "我是好人，别出我！"
}
```

#### 事件通知
```json
{
  "event": "player_joined", // 或 "game_started", "player_left"
  "player_id": "new_player",
  "room_id": "room_1"
}
```

## 3. AI 决策逻辑建议 (AI Strategy Guide)

为了让 AI 表现得更像人类玩家，建议实现以下逻辑：

### 3.1 状态解析
1.  **存活判断**: 检查 `private.is_alive`。若已死亡，除猎人发动技能外，不应发送任何行动指令。
2.  **阶段判断**:
    *   `NIGHT`: 检查 `role.skills`。
        *   **狼人**: 必须与队友协商（通过私有逻辑或默认策略），发送 `KILL` 指令。
        *   **预言家**: 发送 `CHECK` 指令获取一名玩家身份。
        *   **女巫**: 决定是否 `SAVE`（如果有死讯提示，目前协议暂未包含夜间死讯，通常首夜盲救）或 `POISON`。
        *   **守卫**: 发送 `PROTECT`。
    *   `DAY`:
        *   **发言**: 分析 `chat` 历史，生成自然语言回复。
        *   **投票**: 在投票阶段（通常在发言结束后，服务器端暂未严格区分发言/投票子阶段，AI 可自行延时）发送 `vote`。
        *   **技能**: 骑士可随时 `DUEL`；猎人死后可 `SHOOT`。

### 3.2 记忆管理
AI 应当维护一个内部状态（Memory）：
*   **已知身份**: 预言家需记录查验过的 `GOOD`/`WEREWOLF` 名单。
*   **发言历史**: 记录谁跳了什么身份，寻找逻辑漏洞。
*   **行为模式**: 记录谁投了谁的票。

### 3.3 角色扮演 (Role Play)
*   **伪装**: 狼人 AI 不应暴露自己身份，应在聊天中伪装成平民或神职。
*   **欺骗**: 狼人可以“悍跳”预言家，给队友发金水或给好人发查杀。
*   **协作**: 狼人队友之间应有某种隐式或显式的配合（目前系统未提供狼人专属频道，建议狼人 AI 内部通过算法默认刀号最小的非狼玩家，或随机刀）。

## 4. 示例代码 (Python)

```python
import asyncio
import websockets
import json

async def ai_agent():
    uri = "ws://localhost:8000/ws/ai_player_1"
    async with websockets.connect(uri) as websocket:
        # Join Room
        await websocket.send(json.dumps({"action": "join", "room_id": "test_room"}))
        
        while True:
            msg = await websocket.recv()
            data = json.loads(msg)
            
            if data.get("type") == "state_update":
                state = data["data"]
                phase = state["public"]["phase"]
                my_role = state["private"]["role"]["name"]
                
                if phase == "NIGHT" and "CHECK" in state["private"]["role"]["skills"]:
                    # Seer Logic: Check a random unknown player
                    await websocket.send(json.dumps({
                        "action": "action",
                        "room_id": "test_room",
                        "data": {"skill_type": "CHECK", "target_id": "player_2"}
                    }))
                    
            elif data.get("type") == "chat":
                print(f"[{data['player_id']}]: {data['message']}")

if __name__ == "__main__":
    asyncio.run(ai_agent())
```
