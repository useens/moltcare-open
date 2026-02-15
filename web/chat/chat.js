/**
 * 森森·安全聊天室客户端
 * 实时双向通信，端到端加密
 */

// 配置
const CONFIG = {
    WS_HOST: window.location.hostname || 'localhost',
    WS_PORT: window.location.port || (window.location.protocol === 'https:' ? 443 : 80),
    WS_PATH: '/ws',
    RECONNECT_INTERVAL: 3000,
    MAX_RECONNECT_ATTEMPTS: 5,
    TOKEN_KEY: 'sensen_chat_token',
    USER_KEY: 'sensen_chat_user'
};

// 全局状态
let ws = null;
let currentUser = null;
let reconnectAttempts = 0;
let isReconnecting = false;
let messageQueue = [];
let settings = {
    notifications: true,
    sound: true,
    autoscroll: true,
    fontsize: 'medium',
    theme: 'dark'
};

// DOM元素
const elements = {
    loginScreen: document.getElementById('login-screen'),
    chatScreen: document.getElementById('chat-screen'),
    loginForm: document.getElementById('login-form'),
    usernameInput: document.getElementById('username'),
    passwordInput: document.getElementById('password'),
    togglePassword: document.getElementById('toggle-password'),
    rememberMe: document.getElementById('remember-me'),
    loginError: document.getElementById('login-error'),
    btnLogin: document.getElementById('btn-login'),
    currentUser: document.getElementById('current-user'),
    connectionStatus: document.getElementById('connection-status'),
    messages: document.getElementById('messages'),
    messageInput: document.getElementById('message-input'),
    btnSend: document.getElementById('btn-send'),
    charCount: document.getElementById('char-count'),
    typingIndicator: document.getElementById('typing-indicator'),
    scrollBottom: document.getElementById('scroll-bottom'),
    settingsModal: document.getElementById('settings-modal'),
    btnSettings: document.getElementById('btn-settings'),
    btnCloseSettings: document.getElementById('btn-close-settings'),
    btnSaveSettings: document.getElementById('btn-save-settings'),
    btnClearHistory: document.getElementById('btn-clear-history'),
    btnLogout: document.getElementById('btn-logout'),
    emojiPicker: document.getElementById('emoji-picker'),
    btnEmoji: document.querySelector('.btn-emoji'),
    emojiList: document.getElementById('emoji-list'),
    notification: document.getElementById('notification')
};

// 表情数据
const EMOJIS = {
    smileys: ['😀', '😃', '😄', '😁', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩', '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣', '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥', '😓', '🤗', '🤔', '🤭', '🤫', '🤥', '😶', '😐', '😑', '😬', '🙄', '😯', '😦', '😧', '😮', '😲', '🥱', '😴', '🤤', '😪', '😵', '🤐', '🥴', '🤢', '🤮', '🤧', '😷', '🤒', '🤕', '🤑', '🤠', '😈', '👿', '👹', '👺', '🤡', '💩', '👻', '💀', '☠️', '👽', '👾', '🤖', '🎃', '😺', '😸', '😹', '😻', '😼', '😽', '🙀', '😿', '😾'],
    nature: ['🌲', '🌳', '🌴', '🌵', '🌷', '🌸', '🌹', '🌺', '🌻', '🌼', '🌽', '🌾', '🌿', '🍀', '🍁', '🍂', '🍃', '🍄', '🌰', '🦀', '🦞', '🦐', '🦑', '🌍', '🌎', '🌏', '🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘', '🌙', '🌚', '🌛', '🌜', '☀️', '🌝', '🌞', '⭐', '🌟', '🌠', '☁️', '⛅', '⛈️', '🌤️', '🌥️', '🌦️', '🌧️', '🌨️', '🌩️', '🌪️', '🌫️', '🌬️', '💨', '💧', '💦', '☔', '☂️', '🌊', '🌫️'],
    food: ['🍏', '🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍈', '🍒', '🍑', '🍍', '🥝', '🥑', '🍅', '🍆', '🥒', '🥕', '🌽', '🌶️', '🥔', '🍠', '🥐', '🍞', '🥖', '🧀', '🥚', '🍳', '🥞', '🥓', '🍔', '🍟', '🍕', '🌭', '🍿', '🥗', '🥙', '🥪', '🌮', '🌯', '🥫', '🍖', '🍗', '🥩', '🍠', '🍢', '🍣', '🍤', '🍥', '🍡', '🍦', '🍧', '🍨', '🍩', '🍪', '🎂', '🍰', '🧁', '🥧', '🍫', '🍬', '🍭', '🍮', '🍯', '🍼', '🥛', '☕', '🍵', '🍶', '🍾', '🍷', '🍸', '🍹', '🍺', '🍻', '🥂', '🥃'],
    activity: ['⚽', '🏀', '🏈', '⚾', '🥎', '🎾', '🏐', '🏉', '🥏', '🎱', '🏓', '🏸', '🏒', '🏑', '🥍', '🏏', '🥅', '⛳', '🏹', '🎣', '🤿', '🥊', '🥋', '⛸️', '🎿', '🛷', '🥌', '🎯', '🎱', '🎮', '🎲', '🎰', '🎳', '🎨', '🎤', '🎧', '🎼', '🎹', '🥁', '🎷', '🎺', '🎸', '🎻', '🎬', '🏹', '🎪', '🎭', '🎫']
};

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
    init();
});

function init() {
    loadSettings();
    loadSavedAuth();
    setupEventListeners();
    setupEmojiPicker();
}

// ========== 设置 ==========
function loadSettings() {
    const saved = localStorage.getItem('sensen_chat_settings');
    if (saved) {
        settings = { ...settings, ...JSON.parse(saved) };
    }
    applySettings();
}

function saveSettings() {
    localStorage.setItem('sensen_chat_settings', JSON.stringify(settings));
}

function applySettings() {
    document.body.setAttribute('data-fontsize', settings.fontsize);
    document.body.setAttribute('data-theme', settings.theme);
    
    document.getElementById('setting-notifications').checked = settings.notifications;
    document.getElementById('setting-sound').checked = settings.sound;
    document.getElementById('setting-autoscroll').checked = settings.autoscroll;
    document.getElementById('setting-fontsize').value = settings.fontsize;
    document.getElementById('setting-theme').value = settings.theme;
}

// ========== 认证 ==========
function loadSavedAuth() {
    const token = localStorage.getItem(CONFIG.TOKEN_KEY);
    const username = localStorage.getItem(CONFIG.USER_KEY);
    
    if (token && username) {
        connectWithToken(token, username);
    }
}

function saveAuth(token, username, remember = false) {
    if (remember) {
        localStorage.setItem(CONFIG.TOKEN_KEY, token);
        localStorage.setItem(CONFIG.USER_KEY, username);
    } else {
        sessionStorage.setItem(CONFIG.TOKEN_KEY, token);
        sessionStorage.setItem(CONFIG.USER_KEY, username);
    }
}

function clearAuth() {
    localStorage.removeItem(CONFIG.TOKEN_KEY);
    localStorage.removeItem(CONFIG.USER_KEY);
    sessionStorage.removeItem(CONFIG.TOKEN_KEY);
    sessionStorage.removeItem(CONFIG.USER_KEY);
}

// ========== WebSocket连接 ==========
function connect(username, password) {
    showLoginLoading(true);
    hideLoginError();
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${CONFIG.WS_HOST}:${CONFIG.WS_PORT}${CONFIG.WS_PATH}`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket连接成功');
        reconnectAttempts = 0;
        
        // 发送认证
        ws.send(JSON.stringify({
            type: 'auth',
            username: username,
            password: password
        }));
    };
    
    ws.onmessage = (event) => {
        handleMessage(JSON.parse(event.data));
    };
    
    ws.onclose = () => {
        console.log('WebSocket连接关闭');
        updateConnectionStatus('disconnected');
        
        if (currentUser && !isReconnecting) {
            attemptReconnect();
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        showLoginError('连接失败，请检查网络');
        showLoginLoading(false);
    };
}

function connectWithToken(token, username) {
    currentUser = username;
    elements.currentUser.textContent = username;
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${CONFIG.WS_HOST}:${CONFIG.WS_PORT}${CONFIG.WS_PATH}`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        reconnectAttempts = 0;
        ws.send(JSON.stringify({
            type: 'token_auth',
            token: token
        }));
    };
    
    ws.onmessage = (event) => {
        handleMessage(JSON.parse(event.data));
    };
    
    ws.onclose = () => {
        updateConnectionStatus('disconnected');
        if (currentUser && !isReconnecting) {
            attemptReconnect();
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        clearAuth();
        switchToLoginScreen();
    };
}

function attemptReconnect() {
    if (reconnectAttempts >= CONFIG.MAX_RECONNECT_ATTEMPTS) {
        showNotification('连接已断开，请刷新页面重试', 'error');
        return;
    }
    
    isReconnecting = true;
    reconnectAttempts++;
    updateConnectionStatus('connecting');
    
    showNotification(`正在重新连接... (${reconnectAttempts}/${CONFIG.MAX_RECONNECT_ATTEMPTS})`, 'warning');
    
    setTimeout(() => {
        const token = localStorage.getItem(CONFIG.TOKEN_KEY) || sessionStorage.getItem(CONFIG.TOKEN_KEY);
        const username = localStorage.getItem(CONFIG.USER_KEY) || sessionStorage.getItem(CONFIG.USER_KEY);
        
        if (token && username) {
            connectWithToken(token, username);
        }
        isReconnecting = false;
    }, CONFIG.RECONNECT_INTERVAL);
}

// ========== 消息处理 ==========
function handleMessage(data) {
    switch (data.type) {
        case 'auth_result':
            handleAuthResult(data);
            break;
        case 'history':
            loadHistory(data.messages);
            break;
        case 'message':
            addMessage(data);
            break;
        case 'system':
            addSystemMessage(data.content);
            break;
        case 'error':
            handleError(data);
            break;
        case 'pong':
            // 心跳响应
            break;
    }
}

function handleAuthResult(data) {
    showLoginLoading(false);
    
    if (data.success) {
        currentUser = data.username;
        elements.currentUser.textContent = currentUser;
        
        const remember = elements.rememberMe.checked;
        saveAuth(data.token, currentUser, remember);
        
        switchToChatScreen();
        updateConnectionStatus('connected');
        showNotification('登录成功', 'success');
        
        // 发送队列中的消息
        while (messageQueue.length > 0) {
            const msg = messageQueue.shift();
            sendMessage(msg);
        }
    } else {
        showLoginError(data.error || '认证失败');
        clearAuth();
    }
}

function handleError(data) {
    showNotification(data.content, 'error');
}

// ========== UI更新 ==========
function switchToChatScreen() {
    elements.loginScreen.classList.remove('active');
    elements.chatScreen.classList.add('active');
    elements.messageInput.focus();
}

function switchToLoginScreen() {
    elements.chatScreen.classList.remove('active');
    elements.loginScreen.classList.add('active');
    currentUser = null;
}

function updateConnectionStatus(status) {
    const dot = elements.connectionStatus.querySelector('.status-dot');
    const text = elements.connectionStatus.querySelector('.status-text');
    
    dot.className = 'status-dot ' + status;
    
    switch (status) {
        case 'connected':
            text.textContent = '已连接';
            break;
        case 'connecting':
            text.textContent = '连接中...';
            break;
        case 'disconnected':
            text.textContent = '已断开';
            break;
    }
}

function showLoginLoading(show) {
    elements.btnLogin.disabled = show;
    elements.btnLogin.querySelector('.btn-text').style.display = show ? 'none' : 'inline';
    elements.btnLogin.querySelector('.btn-loading').style.display = show ? 'inline' : 'none';
}

function showLoginError(message) {
    elements.loginError.textContent = message;
    elements.loginError.classList.add('show');
}

function hideLoginError() {
    elements.loginError.classList.remove('show');
}

// ========== 消息操作 ==========
function sendMessage(content) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        messageQueue.push(content);
        showNotification('消息已保存，连接恢复后发送', 'warning');
        return;
    }
    
    // 立即在界面上显示自己的消息（乐观更新）
    const tempMsg = {
        id: 'temp-' + Date.now(),
        sender: currentUser,
        content: content,
        timestamp: Date.now() / 1000,
        type: 'text'
    };
    addMessage(tempMsg);
    
    // 发送到服务器
    ws.send(JSON.stringify({
        type: 'message',
        content: content
    }));
}

function addMessage(msg) {
    const isOwn = msg.sender === currentUser;  // 自己的消息
    const isAssistant = msg.type === 'assistant' || msg.sender === '森森';
    
    // 布局：自己的消息在左边，对方的消息在右边
    // 所以对方的消息添加 'own' 类
    const isOther = !isOwn;
    
    const messageEl = document.createElement('div');
    messageEl.className = `message ${isOther ? 'own' : ''} ${isAssistant ? 'assistant' : ''}`;
    messageEl.dataset.id = msg.id;
    
    const time = new Date(msg.timestamp * 1000).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // 头像配置：人类头像 vs 机器人头像
    const avatar = isAssistant ? '🤖' : '👨‍💻';
    
    messageEl.innerHTML = `
        <div class="message-avatar" title="${isAssistant ? '森森 AI助手' : '我'}">${avatar}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-author">${msg.sender}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-bubble">${escapeHtml(msg.content)}</div>
        </div>
    `;
    
    elements.messages.appendChild(messageEl);
    
    if (settings.autoscroll) {
        scrollToBottom();
    } else {
        showScrollButton();
    }
    
    if (isOther && settings.sound) {
        playNotificationSound();
    }
    
    if (isOther && settings.notifications && document.hidden) {
        showBrowserNotification(msg.sender, msg.content);
    }
}

function addSystemMessage(content) {
    const messageEl = document.createElement('div');
    messageEl.className = 'message system';
    messageEl.innerHTML = `
        <div class="message-content">
            <div class="message-bubble">${escapeHtml(content)}</div>
        </div>
    `;
    elements.messages.appendChild(messageEl);
    scrollToBottom();
}

function loadHistory(messages) {
    elements.messages.innerHTML = '';
    
    // 添加欢迎消息
    const welcomeEl = document.createElement('div');
    welcomeEl.className = 'welcome-message';
    welcomeEl.innerHTML = `
        <div class="welcome-icon">🤖</div>
        <h3>欢迎来到森森安全聊天室</h3>
        <p>您的消息将被安全加密传输，不会存储在任何服务器上。</p>
        <p class="hint">提示: 直接在下方输入消息即可与森森对话</p>
    `;
    elements.messages.appendChild(welcomeEl);
    
    // 加载历史消息
    messages.forEach(msg => addMessage(msg));
}

// ========== 事件监听 ==========
function setupEventListeners() {
    // 登录表单
    elements.loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const username = elements.usernameInput.value.trim();
        const password = elements.passwordInput.value;
        
        if (username && password) {
            connect(username, password);
        }
    });
    
    // 密码显示切换
    elements.togglePassword.addEventListener('click', () => {
        const type = elements.passwordInput.type === 'password' ? 'text' : 'password';
        elements.passwordInput.type = type;
        elements.togglePassword.textContent = type === 'password' ? '👁️' : '🙈';
    });
    
    // 发送消息
    elements.btnSend.addEventListener('click', () => {
        sendCurrentMessage();
    });
    
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendCurrentMessage();
        }
    });
    
    // 输入统计
    elements.messageInput.addEventListener('input', () => {
        const len = elements.messageInput.value.length;
        elements.charCount.textContent = `${len}/2000`;
        elements.charCount.style.color = len > 1800 ? '#f85149' : '#6e7681';
        
        // 自动调整高度
        elements.messageInput.style.height = 'auto';
        elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 120) + 'px';
    });
    
    // 滚动监听
    elements.messages.addEventListener('scroll', () => {
        const scrollBottom = elements.messages.scrollHeight - elements.messages.scrollTop - elements.messages.clientHeight;
        if (scrollBottom < 50) {
            elements.scrollBottom.style.display = 'none';
        }
    });
    
    elements.scrollBottom.addEventListener('click', scrollToBottom);
    
    // 设置
    elements.btnSettings.addEventListener('click', () => {
        elements.settingsModal.classList.add('show');
    });
    
    elements.btnCloseSettings.addEventListener('click', closeSettings);
    
    elements.settingsModal.addEventListener('click', (e) => {
        if (e.target === elements.settingsModal) {
            closeSettings();
        }
    });
    
    elements.btnSaveSettings.addEventListener('click', () => {
        settings.notifications = document.getElementById('setting-notifications').checked;
        settings.sound = document.getElementById('setting-sound').checked;
        settings.autoscroll = document.getElementById('setting-autoscroll').checked;
        settings.fontsize = document.getElementById('setting-fontsize').value;
        settings.theme = document.getElementById('setting-theme').value;
        
        saveSettings();
        applySettings();
        closeSettings();
        showNotification('设置已保存', 'success');
    });
    
    elements.btnClearHistory.addEventListener('click', () => {
        if (confirm('确定要清空本地消息历史吗？')) {
            elements.messages.innerHTML = '';
            showNotification('消息历史已清空', 'success');
        }
    });
    
    // 退出
    elements.btnLogout.addEventListener('click', () => {
        if (confirm('确定要退出登录吗？')) {
            clearAuth();
            if (ws) {
                ws.close();
            }
            switchToLoginScreen();
        }
    });
    
    // 表情
    elements.btnEmoji.addEventListener('click', (e) => {
        e.stopPropagation();
        elements.emojiPicker.classList.toggle('show');
    });
    
    document.addEventListener('click', (e) => {
        if (!elements.emojiPicker.contains(e.target) && e.target !== elements.btnEmoji) {
            elements.emojiPicker.classList.remove('show');
        }
    });
    
    // 定期心跳
    setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
        }
    }, 30000);
    
    // 移动端键盘处理
    setupMobileKeyboardHandling();
}

function setupMobileKeyboardHandling() {
    // 处理输入法收起时的滚动问题
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    
    if (isMobile) {
        // 输入框获得焦点时滚动到底部
        elements.messageInput.addEventListener('focus', () => {
            setTimeout(() => {
                scrollToBottom();
                // 确保输入框可见
                elements.messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);
        });
        
        // 处理窗口大小变化（输入法收起/展开）
        let initialHeight = window.innerHeight;
        
        window.addEventListener('resize', () => {
            const currentHeight = window.innerHeight;
            const heightDiff = initialHeight - currentHeight;
            
            // 如果高度变化大于200px，可能是输入法收起/展开
            if (heightDiff > 200) {
                // 输入法展开，滚动到底部
                setTimeout(scrollToBottom, 100);
            } else if (heightDiff < -100) {
                // 输入法收起，确保输入框可见
                setTimeout(() => {
                    elements.messageInput.style.height = '32px';
                    scrollToBottom();
                }, 100);
            }
        });
        
        // 处理页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                setTimeout(() => {
                    elements.messageInput.style.height = '32px';
                }, 100);
            }
        });
    }
}

function closeSettings() {
    elements.settingsModal.classList.remove('show');
}

function sendCurrentMessage() {
    const content = elements.messageInput.value.trim();
    if (!content) return;
    
    sendMessage(content);
    elements.messageInput.value = '';
    elements.charCount.textContent = '0/2000';
    // 重置高度
    elements.messageInput.style.height = '32px';
    elements.emojiPicker.classList.remove('show');
    // 保持焦点但不立即滚动（让输入法保持打开）
    setTimeout(() => {
        elements.messageInput.focus();
    }, 100);
}

function scrollToBottom() {
    elements.messages.scrollTop = elements.messages.scrollHeight;
    elements.scrollBottom.style.display = 'none';
}

function showScrollButton() {
    elements.scrollBottom.style.display = 'block';
}

// ========== 表情选择器 ==========
function setupEmojiPicker() {
    const tabs = document.querySelectorAll('.emoji-tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            loadEmojis(tab.dataset.category);
        });
    });
    
    loadEmojis('smileys');
}

function loadEmojis(category) {
    elements.emojiList.innerHTML = '';
    
    const emojis = EMOJIS[category] || [];
    emojis.forEach(emoji => {
        const btn = document.createElement('button');
        btn.className = 'emoji-item';
        btn.textContent = emoji;
        btn.addEventListener('click', () => {
            insertEmoji(emoji);
        });
        elements.emojiList.appendChild(btn);
    });
}

function insertEmoji(emoji) {
    const start = elements.messageInput.selectionStart;
    const end = elements.messageInput.selectionEnd;
    const text = elements.messageInput.value;
    
    elements.messageInput.value = text.substring(0, start) + emoji + text.substring(end);
    elements.messageInput.focus();
    elements.messageInput.setSelectionRange(start + emoji.length, start + emoji.length);
    
    // 触发输入事件
    elements.messageInput.dispatchEvent(new Event('input'));
}

// ========== 通知 ==========
function showNotification(message, type = 'info') {
    elements.notification.textContent = message;
    elements.notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        elements.notification.classList.remove('show');
    }, 3000);
}

function showBrowserNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: body,
            icon: '🌲'
        });
    }
}

function playNotificationSound() {
    // 使用Web Audio API播放简单提示音
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    } catch (e) {
        // 忽略音频错误
    }
}

// 请求通知权限
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

// ========== 工具函数 ==========
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 暴露到全局（用于调试）
window.chatApp = {
    sendMessage,
    reconnect: attemptReconnect,
    clearHistory: () => {
        elements.messages.innerHTML = '';
    }
};
