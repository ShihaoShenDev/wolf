# Wolf - 狼人杀游戏系统 (Werewolf Game System)

**Wolf** 是一个基于 Python (FastAPI + WebSocket) 开发的狼人杀游戏后端服务，提供 **命令行 (CLI)** 和 **网页 (Web)** 两种客户端，支持多人实时在线对战。

## 🌟 特性

*   **标准板子**：支持经典的 12 人局配置（4 狼人、4 平民、4 神职：预言家、女巫、猎人、守卫）。
*   **双端互通**：CLI 客户端和 Web 客户端无缝互通，玩家可自由选择喜欢的界面。
*   **实时通信**：基于 WebSocket 实现低延迟的游戏状态同步和聊天功能。
*   **完整流程**：
    *   **夜晚**：狼人刀人、预言家验人、女巫毒/救、守卫守护。
    *   **白天**：死亡名单公布、自由讨论、投票放逐。
    *   **技能**：支持骑士决斗、猎人开枪、白痴翻牌等特殊技能。
    *   **胜利判定**：自动判定屠边（神职全灭或平民全灭）或屠狼。
*   **AI 友好**：提供详细的协议文档，方便接入 AI Agent 进行训练或对战。

## 🛠️ 安装

本项目使用 `poetry` 进行依赖管理。

1.  **克隆项目**
    ```bash
    git clone https://github.com/your-repo/wolf.git
    cd wolf
    ```

2.  **安装依赖**
    ```bash
    poetry install
    ```
    或者使用 pip:
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 快速开始

### 1. 启动服务端
服务端负责维护游戏状态和处理所有连接。

```bash
# 使用 poetry
poetry run wolf server

# 或直接运行模块
python -m wolf.cli server
```
*服务默认运行在 `http://0.0.0.0:8000`*

### 2. 启动 Web 客户端
启动服务端后，打开浏览器访问：

**[http://localhost:8000](http://localhost:8000)**

*   输入昵称和房间号（例如 `room1`）即可加入。
*   界面提供直观的玩家状态卡片和操作按钮。

### 3. 启动 CLI 客户端
如果你喜欢极客风格的终端界面：

```bash
# 打开一个新的终端窗口
poetry run wolf client

# 或
python -m wolf.cli client
```
*   根据提示输入服务器地址（默认 `ws://localhost:8000`）、昵称和房间号。

## 🎮 游戏指令 (CLI)

在 CLI 客户端中，支持以下指令：

| 指令 | 描述 | 示例 |
| :--- | :--- | :--- |
| `/join <room_id>` | 加入房间 | `/join room1` |
| `/start` | 开始游戏 (需满12人，测试可强开) | `/start` |
| `/vote <id>` | 投票给指定玩家 | `/vote P2` |
| `/kill <id>` | [狼人] 击杀目标 | `/kill P5` |
| `/check <id>` | [预言家] 查验身份 | `/check P3` |
| `/save <id>` | [女巫] 使用解药 | `/save P5` |
| `/poison <id>` | [女巫] 使用毒药 | `/poison P6` |
| `/protect <id>` | [守卫] 守护目标 | `/protect P1` |
| `/duel <id>` | [骑士] 发起决斗 | `/duel P4` |
| `/shoot <id>` | [猎人] 开枪带人 | `/shoot P8` |
| `<text>` | 发送聊天消息 | `我是好人！` |

## 🤖 AI 接入

本项目非常适合用于 AI 狼人杀 Agent 的开发与测试。详细的通信协议和接入指南请参考：

👉 **[AI_INTEGRATION.md](AI_INTEGRATION.md)**

## 📂 项目结构

```text
wolf/
├── server/          # 后端核心代码
│   ├── app.py       # FastAPI 应用入口 & WebSocket 处理
│   ├── models.py    # 数据模型 (Player, Room)
│   ├── game/        # 游戏逻辑引擎
│   │   ├── engine.py # 状态机与流程控制
│   │   └── roles.py  # 角色技能定义
│   └── ...
├── client/          # CLI 客户端实现
├── web/             # Web 前端静态资源 (HTML/JS/CSS)
└── cli.py           # 命令行入口工具
```

## 📝 规则说明

**12人标准局**：
*   **狼人 (4人)**：每晚杀一人。屠边胜利（杀光所有神或杀光所有民）。
*   **平民 (4人)**：无特殊技能。放逐所有狼人胜利。
*   **神职 (4人)**：
    *   **预言家**：每晚查验一人身份（好人/狼人）。
    *   **女巫**：一瓶解药（救人），一瓶毒药（杀人）。全场各只能用一次，不可同一晚使用。
    *   **猎人**：死亡时可开枪带走一人（被毒死除外）。
    *   **守卫**：每晚守护一人免受狼刀。不可连续守同一人。
    *   *(可选支持)* **白痴**：被投出翻牌免死。**骑士**：白天决斗查杀狼人。

## License

MIT License
