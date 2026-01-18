let chatSocket;
let typingTimer;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function updateConnectionStatus(status) {
    const statusEl = document.getElementById('connectionStatus');
    const sendBtn = document.getElementById('sendBtn');
    const input = document.getElementById('messageInput');

    statusEl.className = `connection-status ${status}`;

    if (status === 'connected') {
        statusEl.style.display = 'none';
        sendBtn.disabled = false;
        input.disabled = false;
        reconnectAttempts = 0;
    } else {
        statusEl.style.display = 'block';
        sendBtn.disabled = true;
        input.disabled = true;
    }
}

function initWebSocket() {
    updateConnectionStatus('connecting');

    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    chatSocket = new WebSocket(`${protocol}://${location.host}/ws/chat/${chatId}/`);

    chatSocket.onopen = () => updateConnectionStatus('connected');

    chatSocket.onmessage = e => {
        const data = JSON.parse(e.data);

        if (data.type === 'chat_message') {
            addMessage(data.message, data.sender_id === currentUserId);
        }

        if (data.type === 'typing_indicator') {
            toggleTyping(data.is_typing, data.user);
        }
    };

    chatSocket.onclose = () => {
        updateConnectionStatus('disconnected');
        if (reconnectAttempts++ < maxReconnectAttempts) {
            setTimeout(initWebSocket, reconnectAttempts * 3000);
        }
    };
}

function addMessage(text, isOwn) {
    const container = document.getElementById('messagesContainer');
    const msg = document.createElement('div');
    msg.className = `message ${isOwn ? 'sent' : 'received'}`;
    msg.innerHTML = `
        <div class="message-text">${escapeHtml(text)}</div>
        <div class="message-time">${new Date().toLocaleTimeString([], {
            hour: 'numeric',
            minute: '2-digit'
        })}</div>
    `;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

function toggleTyping(show, user = '') {
    const el = document.getElementById('typingIndicator');
    if (show) {
        el.textContent = `${user} is typing...`;
        el.style.display = 'block';
    } else {
        el.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    initMessageSearch();

    document.getElementById('sendBtn').onclick = sendMessage;

    document.getElementById('messageInput').addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    document.getElementById('messageInput').addEventListener('input', () => {
        chatSocket.send(JSON.stringify({ type: 'typing', is_typing: true }));
        clearTimeout(typingTimer);
        typingTimer = setTimeout(() => {
            chatSocket.send(JSON.stringify({ type: 'typing', is_typing: false }));
        }, 1000);
    });
});

function sendMessage() {
    const input = document.getElementById('messageInput');
    const msg = input.value.trim();
    if (!msg || chatSocket.readyState !== WebSocket.OPEN) return;

    chatSocket.send(JSON.stringify({
        type: 'chat_message',
        message: msg
    }));

    input.value = '';
}

function initMessageSearch() {
    const searchInput = document.getElementById('chatSearchInput');
    const messagesContainer = document.getElementById('messagesContainer');

    if (!searchInput) return;

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase().trim();
        const messages = messagesContainer.querySelectorAll('.message');

        messages.forEach(msg => {
            const text = msg.querySelector('.message-text').textContent.toLowerCase();
            if (text.includes(query)) {
                msg.style.display = 'block';
                // Remove highlighting if it exists
                msg.querySelector('.message-text').innerHTML = escapeHtml(msg.querySelector('.message-text').textContent);

                if (query !== '') {
                    // Simple highlighting
                    const originalText = msg.querySelector('.message-text').textContent;
                    const regex = new RegExp(`(${query})`, 'gi');
                    msg.querySelector('.message-text').innerHTML = originalText.replace(regex, '<mark>$1</mark>');
                }
            } else {
                msg.style.display = 'none';
            }
        });
    });
}
