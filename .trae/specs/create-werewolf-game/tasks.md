# Tasks

- [x] Task 1: 项目初始化与基础架构
    - [x] SubTask 1.1: 创建项目结构，配置 `poetry` 或 `requirements.txt` (FastAPI, Uvicorn, Typer, Websockets)。
    - [x] SubTask 1.2: 创建 `wolf` 命令行入口，支持 `wolf server` 和 `wolf client` 子命令。
    - [x] SubTask 1.3: 搭建 FastAPI + WebSocket 基础框架，并配置静态文件服务 (Static Files)。

- [x] Task 2: 核心数据模型与房间管理 (Backend)
    - [x] SubTask 2.1: 定义 `Player` (玩家) 和 `Room` (房间) 类。
    - [x] SubTask 2.2: 实现 WebSocket 连接管理器 (ConnectionManager)，处理玩家加入、离开。
    - [x] SubTask 2.3: 定义前后端通信协议 (Protocol) 的基础消息结构 (JSON)。

- [x] Task 3: 游戏逻辑引擎 (Backend)
    - [x] SubTask 3.1: 定义 `Role` 基类及 `Werewolf`, `Villager` 等具体角色类。
    - [x] SubTask 3.2: 实现 `Game` 类，处理发牌 (分配角色) 和 游戏状态流转 (State Machine)。
    - [x] SubTask 3.3: 实现 **夜晚阶段** 逻辑 (接收并处理 `action` 请求)。
    - [x] SubTask 3.4: 实现 **白天阶段** 逻辑 (发言队列、投票结算)。
    - [x] SubTask 3.5: 实现 **胜利判定** 逻辑。

- [x] Task 4: 业务逻辑整合 (Backend Integration)
    - [x] SubTask 4.1: 将 WebSocket 消息路由到 Game Engine。
    - [x] SubTask 4.2: 实现 **私有信息推送** (如：狼人同伴信息，预言家验人结果)。
    - [x] SubTask 4.3: 实现 **广播信息推送** (如：游戏开始，天亮，死亡名单)。

- [x] Task 5: Web 客户端开发 (Frontend - Web)
    - [x] SubTask 5.1: 创建基础 HTML/CSS 页面 (`index.html`)。
    - [x] SubTask 5.2: 编写 JavaScript 逻辑连接 WebSocket，处理登录/入房。
    - [x] SubTask 5.3: 实现游戏状态渲染 (显示身份、日志、操作按钮)。

- [x] Task 6: CLI 客户端开发 (Frontend - CLI)
    - [x] SubTask 6.1: 使用 `websockets` 库实现异步连接客户端。
    - [x] SubTask 6.2: 使用 `prompt_toolkit` 或类似库实现命令行交互 (输入+输出分离)。
    - [x] SubTask 6.3: 解析服务端消息并格式化输出到终端。

- [x] Task 7: 完善与测试
    - [x] SubTask 7.1: 验证 Web 和 CLI 客户端的互通性。
    - [x] SubTask 7.2: 确保所有日志和提示信息均为 **中文**。

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 3]
- [Task 5] depends on [Task 4]
- [Task 6] depends on [Task 4]
- [Task 7] depends on [Task 5], [Task 6]
