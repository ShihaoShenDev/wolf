// State
let socket = null;
let username = '';
let roomId = '';
let myPlayerId = '';
let gameState = {
    public: {},
    private: {}
};

// DOM Elements
const app = document.getElementById('app');
const loginScreen = document.getElementById('login-screen');
const gameScreen = document.getElementById('game-screen');
const loginForm = document.getElementById('login-form');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatLog = document.getElementById('chat-log');
const playerGrid = document.getElementById('player-grid');
const phaseDisplay = document.getElementById('phase-display');
const roundDisplay = document.getElementById('round-display');
const roleDisplay = document.getElementById('role-display');
const btnStartGame = document.getElementById('btn-start-game');

// Constants
const PHASE = {
    WAITING: 'WAITING',
    NIGHT: 'NIGHT',
    DAY: 'DAY',
    ENDED: 'ENDED'
};

// Login Handler
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    username = document.getElementById('username').value.trim();
    roomId = document.getElementById('room-id').value.trim();

    if (!username || !roomId) return;

    connectWebSocket();
});

// WebSocket Connection
function connectWebSocket() {
    // Construct WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/${username}`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log('Connected to server');
        // Send join action
        sendAction('join', { room_id: roomId });
    };

    socket.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            handleMessage(msg);
        } catch (err) {
            console.error('Error parsing message:', err);
        }
    };

    socket.onclose = () => {
        console.log('Disconnected from server');
        alert('Disconnected from server. Please refresh.');
    };

    socket.onerror = (error) => {
        console.error('WebSocket Error:', error);
    };
}

function sendAction(action, data = {}) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        const payload = {
            action: action,
            room_id: roomId,
            ...data
        };
        // For 'action' and 'vote' types, nested data is required by backend
        if (action === 'action' || action === 'vote' || action === 'chat') {
            payload.data = data; // Wrap data in 'data' field
        }
        
        // Special case handling to match backend expectations exactly
        if (action === 'join' || action === 'start_game') {
            // These are top-level fields in backend
            Object.assign(payload, data);
        }

        socket.send(JSON.stringify(payload));
    }
}

// Message Handler
function handleMessage(msg) {
    console.log('Received:', msg);

    if (msg.event === 'joined_room') {
        myPlayerId = username; // Assuming username is client_id
        showGameScreen();
        appendChat({ sender: 'System', message: `Joined room ${msg.room_id}` });
        // Initial state might be empty or waiting
        if (msg.game_state) {
            // Handle initial game state if provided
        }
    } else if (msg.event === 'player_joined') {
        appendChat({ sender: 'System', message: `${msg.player_id} joined the room.` });
    } else if (msg.event === 'game_started') {
        appendChat({ sender: 'System', message: 'Game Started!' });
    } else if (msg.type === 'state_update') {
        gameState = msg.data;
        renderGame();
    } else if (msg.type === 'chat') {
        appendChat({ sender: msg.player_id, message: msg.message });
    } else if (msg.type === 'action_result' || msg.type === 'vote_result') {
        appendChat({ sender: 'System', message: `${msg.success ? 'Success' : 'Failed'}: ${msg.message}` });
    } else if (msg.error) {
        alert('Error: ' + msg.error);
    }
}

// UI Functions
function showGameScreen() {
    loginScreen.classList.remove('active');
    loginScreen.classList.add('hidden');
    gameScreen.classList.remove('hidden');
    gameScreen.classList.add('active');
}

function renderGame() {
    if (!gameState.public) return;

    const publicState = gameState.public;
    const privateState = gameState.private || {};
    const myRole = privateState.role || {};
    const mySkills = myRole.skills || [];
    const amIAlive = privateState.is_alive;

    // Update Header
    phaseDisplay.textContent = publicState.phase;
    roundDisplay.textContent = publicState.round;
    roleDisplay.textContent = myRole.name || 'Unknown';

    // Update Body Class for Theme
    document.body.classList.remove('day-mode', 'night-mode');
    if (publicState.phase === 'DAY') {
        document.body.classList.add('day-mode');
    } else if (publicState.phase === 'NIGHT') {
        document.body.classList.add('night-mode');
    }

    // Show/Hide Start Game Button
    if (publicState.phase === 'WAITING') {
        btnStartGame.classList.remove('hidden');
    } else {
        btnStartGame.classList.add('hidden');
    }

    // Render Players
    playerGrid.innerHTML = '';
    const players = publicState.players || {};

    // Need to handle teammates visibility for Wolves
    const teammates = privateState.teammates || [];

    Object.keys(players).forEach(pid => {
        const pInfo = players[pid];
        const card = document.createElement('div');
        card.className = `player-card ${pInfo.is_alive ? 'alive' : 'dead'}`;
        
        // Status Indicator
        const indicator = document.createElement('div');
        indicator.className = 'player-status-indicator';
        card.appendChild(indicator);

        // Name
        const nameDiv = document.createElement('div');
        nameDiv.className = 'player-name';
        nameDiv.textContent = pid;
        if (pid === myPlayerId) nameDiv.textContent += ' (Me)';
        if (teammates.includes(pid)) nameDiv.textContent += ' (Wolf)';
        card.appendChild(nameDiv);

        // ID (hidden or small)
        // const idDiv = document.createElement('div');
        // idDiv.className = 'player-id';
        // idDiv.textContent = pid;
        // card.appendChild(idDiv);

        // Actions
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'player-actions';

        if (amIAlive && pInfo.is_alive && pid !== myPlayerId) {
            // Day Actions
            if (publicState.phase === 'DAY') {
                // Vote
                const btnVote = createActionButton('Vote', 'vote', () => {
                    sendAction('vote', { target_id: pid });
                });
                actionsDiv.appendChild(btnVote);

                // Hunter Shoot
                if (mySkills.includes('SHOOT')) {
                    const btnShoot = createActionButton('Shoot', 'shoot', () => {
                        sendAction('action', { target_id: pid, skill_type: 'SHOOT' });
                    });
                    actionsDiv.appendChild(btnShoot);
                }

                // Knight Duel
                if (mySkills.includes('DUEL')) {
                    const btnDuel = createActionButton('Duel', 'shoot', () => { // styling similar to shoot
                        sendAction('action', { target_id: pid, skill_type: 'DUEL' });
                    });
                    actionsDiv.appendChild(btnDuel);
                }
            }

            // Night Actions
            if (publicState.phase === 'NIGHT') {
                // Wolf Kill
                if (mySkills.includes('KILL')) {
                    const btnKill = createActionButton('Kill', 'kill', () => {
                        sendAction('action', { target_id: pid, skill_type: 'KILL' });
                    });
                    actionsDiv.appendChild(btnKill);
                }

                // Seer Check
                if (mySkills.includes('CHECK')) {
                    const btnCheck = createActionButton('Check', 'save', () => { // styling green
                        sendAction('action', { target_id: pid, skill_type: 'CHECK' });
                    });
                    actionsDiv.appendChild(btnCheck);
                }

                // Witch Save/Poison
                if (mySkills.includes('POISON')) {
                    const btnPoison = createActionButton('Poison', 'poison', () => {
                        sendAction('action', { target_id: pid, skill_type: 'POISON' });
                    });
                    actionsDiv.appendChild(btnPoison);
                }
                 // Witch Save is tricky, usually target is predefined by server (who died), 
                 // but here we can just target anyone if we want to save them?
                 // Usually Save is "Save the person who died". 
                 // The backend logic `process_night_action` just takes a target_id.
                 // So we can technically target anyone? Or only the dead one?
                 // Standard rules: Save only the victim.
                 // But UI-wise, if we don't know who died (Server doesn't tell us yet), 
                 // we might not be able to use Save effectively unless the server sends "This person died" to the Witch.
                 // Looking at backend `resolve_night`: it calculates deaths AFTER actions.
                 // Wait, standard Witch logic requires knowing who died.
                 // Does backend send who died to Witch?
                 // `get_private_state` does not seem to include "who died tonight".
                 // So Witch implementation might be incomplete in backend or relies on blind save (unlikely) or I missed something.
                 // For now, I'll add the Save button to everyone just in case.
                if (mySkills.includes('SAVE')) {
                     const btnSave = createActionButton('Save', 'save', () => {
                         sendAction('action', { target_id: pid, skill_type: 'SAVE' });
                     });
                     actionsDiv.appendChild(btnSave);
                }

                // Guard Protect
                if (mySkills.includes('PROTECT')) {
                    const btnProtect = createActionButton('Guard', 'save', () => {
                        sendAction('action', { target_id: pid, skill_type: 'PROTECT' });
                    });
                    actionsDiv.appendChild(btnProtect);
                }
            }
        }
        
        // Self Actions (e.g. Guard self)
        if (amIAlive && pid === myPlayerId) {
             if (publicState.phase === 'NIGHT' && mySkills.includes('PROTECT')) {
                const btnProtect = createActionButton('Guard Self', 'save', () => {
                    sendAction('action', { target_id: pid, skill_type: 'PROTECT' });
                });
                actionsDiv.appendChild(btnProtect);
             }
        }

        card.appendChild(actionsDiv);
        playerGrid.appendChild(card);
    });
}

function createActionButton(text, className, onClick) {
    const btn = document.createElement('button');
    btn.textContent = text;
    btn.className = `action-btn ${className}`;
    btn.onclick = onClick;
    return btn;
}

function appendChat(data) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-msg';
    
    const senderSpan = document.createElement('span');
    senderSpan.className = 'sender';
    senderSpan.textContent = data.sender + ': ';
    
    const textSpan = document.createElement('span');
    textSpan.textContent = data.message;
    
    msgDiv.appendChild(senderSpan);
    msgDiv.appendChild(textSpan);
    
    chatLog.appendChild(msgDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

// Chat Send
chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    sendAction('chat', { message: text });
    chatInput.value = '';
});

// Start Game
btnStartGame.addEventListener('click', () => {
    // Force start for testing if needed, but standard button shouldn't force.
    // However, for 1-player testing we might want force_start.
    // Let's assume standard behavior first.
    // But since I might be testing alone, I'll add a way to force start?
    // No, let's stick to normal.
    // Wait, prompt says "Start Game" button.
    sendAction('start_game', {}); 
});
