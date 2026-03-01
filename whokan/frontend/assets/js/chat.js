// assets/js/chat.js

const params = new URLSearchParams(window.location.search);
const SKILL_ID = params.get('skill_id');
const SKILL_NAME = params.get('skill_name') || 'Skill Chat';

const HISTORY_PAGE = 50;
let ws = null;
let historyOffset = 0;
let allHistoryLoaded = false;

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;

    if (!SKILL_ID) {
        showConnectionStatus('disconnected', 'No skill specified.');
        return;
    }

    document.getElementById('chat-skill-name').textContent = SKILL_NAME + ' Chat';
    document.title = 'WhoKan – ' + SKILL_NAME + ' Chat';

    const forumUrl = `/forum.html?skill_id=${encodeURIComponent(SKILL_ID)}&skill_name=${encodeURIComponent(SKILL_NAME)}`;
    document.getElementById('forum-link').href = forumUrl;

    document.getElementById('chat-form').addEventListener('submit', handleSend);

    // Load earlier messages button
    const loadEarlierBtn = document.getElementById('load-earlier-btn');
    if (loadEarlierBtn) {
        loadEarlierBtn.addEventListener('click', loadEarlierMessages);
    }

    connect();
});

// ---------------------------------------------------------------------------
// WebSocket connection
// ---------------------------------------------------------------------------

function connect() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }

    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const apiBase = api.baseUrl.startsWith('http')
        ? api.baseUrl.replace(/^https?/, proto)
        : `${proto}://${window.location.host}${api.baseUrl}`;
    const wsUrl = `${apiBase}/skills/${SKILL_ID}/chat/ws?token=${encodeURIComponent(token)}`;

    showConnectionStatus('connecting', 'Connecting…');

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        showConnectionStatus('connected', 'Connected');
        document.getElementById('send-btn').disabled = false;
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        appendMessage(data);
    };

    ws.onclose = () => {
        showConnectionStatus('disconnected', 'Disconnected — reload to reconnect');
        document.getElementById('send-btn').disabled = true;
    };

    ws.onerror = () => {
        showConnectionStatus('disconnected', 'Connection error');
        document.getElementById('send-btn').disabled = true;
    };
}

// ---------------------------------------------------------------------------
// Send message
// ---------------------------------------------------------------------------

function handleSend(event) {
    event.preventDefault();
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(text);
    input.value = '';
}

// ---------------------------------------------------------------------------
// Load earlier messages (history pagination)
// ---------------------------------------------------------------------------

async function loadEarlierMessages() {
    if (allHistoryLoaded) return;
    historyOffset += HISTORY_PAGE;
    try {
        const data = await api.getChatHistory(SKILL_ID, historyOffset);
        const msgs = data.messages || [];
        if (msgs.length < HISTORY_PAGE) {
            allHistoryLoaded = true;
            const btn = document.getElementById('load-earlier-btn');
            if (btn) btn.classList.add('hidden');
        }
        const container = document.getElementById('messages-container');
        const firstChild = container.firstChild;
        msgs.reverse().forEach(msg => {
            const div = _createMessageDiv({ ...msg, type: 'history' });
            container.insertBefore(div, firstChild);
        });
    } catch (err) {
        console.error('Error loading earlier messages:', err);
    }
}

// ---------------------------------------------------------------------------
// Render messages
// ---------------------------------------------------------------------------

function _createMessageDiv(data) {
    const div = document.createElement('div');
    div.className = data.type === 'history'
        ? 'flex flex-col opacity-70'
        : 'flex flex-col';
    div.innerHTML = `
        <div class="flex items-baseline gap-2">
            <span class="text-xs font-semibold text-indigo-700">${escapeHtml(data.author_name)}</span>
            <span class="text-xs text-gray-400">${formatDate(data.created_at)}</span>
        </div>
        <p class="text-sm text-gray-800 mt-0.5">${escapeHtml(data.content)}</p>
    `;
    return div;
}

function appendMessage(data) {
    const container = document.getElementById('messages-container');
    const placeholder = document.getElementById('messages-placeholder');
    if (placeholder) placeholder.remove();

    container.appendChild(_createMessageDiv(data));
    container.scrollTop = container.scrollHeight;
}

// ---------------------------------------------------------------------------
// Connection status indicator
// ---------------------------------------------------------------------------

function showConnectionStatus(state, text) {
    const dot = document.getElementById('status-dot');
    const label = document.getElementById('status-text');
    label.textContent = text;
    dot.className = 'inline-block w-2 h-2 rounded-full ' + {
        connecting: 'bg-yellow-400',
        connected: 'bg-green-400',
        disconnected: 'bg-red-400',
    }[state];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
