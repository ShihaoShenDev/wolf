# 狼人杀游戏后端系统 (Werewolf Game Backend System) Spec

## Why
用户希望开发一个狼人杀游戏的后端服务，名为 `wolf`。该服务需管理多玩家的前端状态，支持标准的 12 人局，包含狼人、平民、神职等角色，并实现完整的游戏流程。项目需使用中文，并提供 **命令行 (CLI)** 和 **网页 (Web)** 两种客户端界面。

## What Changes
我们将构建一个基于 **Python (FastAPI + WebSockets)** 的狼人杀后端服务，并附带 CLI 和 Web 两个客户端。

### 核心架构
- **Backend Server (`wolf server`)**: 
    - 提供 WebSocket 接口供多人实时连接。
    - 管理房间 (Room) 和游戏状态 (Game State)。
    - 处理客户端请求（加入、准备、行动、聊天）。
    - 广播游戏事件（天亮、死亡、发言）。
    - 托管静态网页文件 (Web UI)。
- **CLI Client (`wolf client`)**:
    - 终端界面，通过 WebSocket 连接服务端。
    - 支持指令输入和即时消息显示。
- **Web Client (Browser)**:
    - 网页界面，通过 WebSocket 连接服务端。
    - 可视化操作和游戏状态展示。

### 新增模块
- **Server Module**: FastAPI 应用，WebSocket 路由，Static Files Mount。
- **Game Engine**: 核心逻辑，独立于网络层。
- **CLI Module**: 基于 `typer` 和 `websockets` 的终端客户端。
- **Web Module**: HTML/JS/CSS 前端资源。

### 核心功能点
- **服务启动**: `wolf server` 启动后端及 Web 服务。
- **CLI 启动**: `wolf client` 启动终端客户端连接。
- **Web 访问**: 浏览器访问 `http://localhost:8000` 进入游戏。
- **游戏流程**: 无论使用哪种客户端，均可加入同一房间进行游戏。

## Impact
- **Affected specs**: None.
- **Affected code**: New project structure.

## ADDED Requirements

### Requirement: 多端支持 (Multi-Client Support)
- **CLI Client**: 提供纯文本终端界面，支持输入指令（如 `/join`, `/vote`）和查看游戏日志。
- **Web Client**: 提供图形化或文本化网页界面，通过按钮或表单进行交互。
- **互通性**: CLI 玩家和 Web 玩家必须能在同一个房间内进行游戏。

### Requirement: 统一入口 (Unified Entry Point)
- `wolf server`: 启动服务端（默认端口 8000）。
- `wolf client`: 启动客户端（默认连接 localhost:8000）。

### Requirement: 角色与逻辑 (Roles & Logic)
- **Roles**: Werewolf, Villager, Seer, Witch, Hunter, Guard, Idiot, Knight。
- **Flow**: Night (Action) -> Day (Discuss/Vote) -> Night。
- **Win**: 屠边规则。

### Requirement: 中文支持 (Chinese Language)
- 代码注释、日志输出、API 响应消息、游戏提示文本均需使用 **中文**。

#### Scenario: 混合游戏
- **WHEN** 玩家 A 使用 `wolf client` 连接，玩家 B 使用浏览器访问 Web 连接。
- **THEN** 两人进入同一房间，能够互相看到发言和状态更新。

## Reference: 游戏规则 (Game Rules)

### 1. 游戏概述 (Game Overview)
- **玩家人数**：12 人（4狼，4民，4神）。
- **阵营划分**：
    1.  **狼人阵营 (Werewolf Team)**：隐藏在好人中，夜间击杀好人。
    2.  **好人阵营 (Good Team)**：
        *   **神职 (Gods)**：预言家、女巫、猎人、守卫、白痴、骑士。
        *   **平民 (Villagers)**：无特殊技能。
- **胜利条件**：
    *   **狼人胜**：屠边规则 —— 杀死所有神职 **或** 杀死所有平民。
    *   **好人胜**：放逐所有狼人。

### 2. 游戏流程 (Game Flow)
#### 2.1 夜晚阶段 (Night Phase)
1.  **狼人行动**：共同商量并选择一名玩家击杀（`kill_target`）。
2.  **守卫行动**：选择一名玩家守护（`protect_target`），不可连续两晚守护同一人。
3.  **女巫行动**：知晓当晚被击杀者。可选择使用解药（`save_target`）或毒药（`poison_target`）。同一晚不能同时使用两瓶药。
4.  **预言家行动**：查验一名玩家的身份（返回 `Werewolf` 或 `Good`）。
5.  **其他神职行动**：如猎人、白痴、骑士等（视具体板子而定）。
*   **结算逻辑**：
    *   若 `kill_target` == `protect_target`，则无人死亡（平安夜）。
    *   若 `kill_target` 被 `save_target` 救赎，则无人死亡。
    *   若 `poison_target` 存在，该玩家死亡。
    *   死亡信息在白天公布。

#### 2.2 白天阶段 (Day Phase)
1.  **公布昨夜情况**：法官宣布死亡玩家名单（或宣布平安夜）。
2.  **遗言 (Last Words)**：首夜死亡玩家有遗言。
3.  **公聊讨论 (Discussion)**：玩家轮流发言，分析局势。
4.  **放逐投票 (Voting)**：
    *   所有存活玩家投票选出一名玩家放逐。
    *   得票最多者出局（若平票，通常进入 PK 发言后再投）。
    *   被放逐者可留遗言。
5.  **进入夜晚**：重复上述流程。

### 3. 角色定义与技能 (Roles & Abilities)
#### 3.1 狼人阵营
*   **狼人 (Werewolf)**
    *   **技能**：每晚共同击杀一名玩家。
    *   **限制**：不能自刀（除非战术需要，规则允许），必须达成一致。

#### 3.2 好人阵营 - 神职
*   **预言家 (Seer)**
    *   **技能**：每晚查验一名玩家的具体身份（通常返回“狼人”或“好人”）。
*   **女巫 (Witch)**
    *   **技能**：拥有一瓶解药（救活当晚死者）和一瓶毒药（毒死任意存活玩家）。
    *   **限制**：全程每瓶药只能用一次；同一晚不能双用；通常首夜可自救。
*   **猎人 (Hunter)**
    *   **技能**：死亡时（除被毒杀外）可开枪带走一名玩家。
*   **守卫 (Guard)**
    *   **技能**：每晚守护一名玩家免受狼人击杀。
    *   **限制**：不能连续两晚守护同一人；守护与女巫解药同时作用于同一人导致死亡（奶穿）。
*   **白痴 (Idiot)**
    *   **技能**：被放逐时翻牌免疫死亡，但失去投票权。
*   **骑士 (Knight)**
    *   **技能**：白天发言阶段可随时翻牌决斗一名玩家。若对方是狼人，对方死亡；若对方是好人，骑士死亡。

#### 3.3 好人阵营 - 平民
*   **平民 (Villager)**
    *   **技能**：无。

### 4. 技能优先级与冲突解决
1.  **死亡判定顺序**：骑士决斗 > 女巫毒杀 > 狼人击杀 vs 守卫守护。
2.  **守护与解药冲突**：若 `Guard` 守护了 `X`，且 `Witch` 救了 `X`（针对狼刀），`X` 死亡（奶穿规则）。
3.  **猎人触发**：若 `death_cause == Poison`，则禁用猎人技能。
