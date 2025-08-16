/**
 * 🍖 Nepal Meat Shop - Enhanced Chat Widget
 * Frontend chat widget with role-based access, admin takeover, and real-time WebSocket integration.
 */

class EnhancedChatWidget {
    constructor(options = {}) {
        this.options = {
            apiBaseUrl: '/api/v2/chat',
            socketIOUrl: window.location.origin,
            containerId: 'enhanced-chat-widget',
            position: 'bottom-left',
            theme: 'light',
            language: 'en',
            autoStart: true,
            enableTypingIndicator: true,
            enableSoundNotifications: false,
            maxMessageLength: 1000,
            reconnectAttempts: 5,
            reconnectDelay: 3000,
            ...options
        };

        this.state = {
            isOpen: false,
            isConnected: false,
            isTyping: false,
            sessionId: null,
            conversationId: null,
            userRole: 'customer',
            adminMode: false,
            messages: [],
            connectionAttempts: 0,
            lastActivity: null
        };

        this.socket = null;
        this.typingTimer = null;
        this.reconnectTimer = null;
        this.messageQueue = [];

        this.init();
    }

    /**
     * Initialize the chat widget
     */
    init() {
        // Remove any old chat elements that might still exist
        const oldChatElements = [
            'enhanced-chat-widget',
            'chatWidget', 
            'chatToggle',
            'chat-widget',
            'chat-toggle'
        ];
        
        oldChatElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                console.log(`Removing old chat element: ${id}`);
                element.remove();
            }
        });
        
        this.detectUserRole();
        this.createWidget();
        this.bindEvents();
        
        if (this.options.autoStart) {
            this.startConversation();
        }

        // Auto-connect WebSocket if user is admin
        if (this.state.adminMode) {
            this.connectWebSocket();
        }

        this.log('Enhanced chat widget initialized', this.state);
    }

    /**
     * Detect user role from meta tags or API
     */
    detectUserRole() {
        try {
            // Check meta tag first
            const userRoleMeta = document.querySelector('meta[name="user-role"]');
            if (userRoleMeta) {
                const role = userRoleMeta.getAttribute('content');
                if (['admin', 'super_admin'].includes(role)) {
                    this.state.userRole = role;
                    this.state.adminMode = true;
                    this.log('Admin role detected from meta tag:', role);
                    return;
                }
            }

            // Check for admin panel link
            const adminLink = document.querySelector('a[href*="/admin"]');
            if (adminLink) {
                this.state.userRole = 'admin';
                this.state.adminMode = true;
                this.log('Admin role detected from admin link');
                return;
            }

            // Check authentication status
            if (window.currentUser && window.currentUser.role) {
                const role = window.currentUser.role;
                if (['admin', 'super_admin'].includes(role)) {
                    this.state.userRole = role;
                    this.state.adminMode = true;
                    this.log('Admin role detected from currentUser:', role);
                    return;
                }
            }

            this.log('Customer role detected (default)');
        } catch (error) {
            this.log('Error detecting user role:', error);
        }
    }

    /**
     * Create the chat widget HTML structure
     */
    createWidget() {
        const container = document.getElementById(this.options.containerId) || document.body;
        
        const widgetHTML = `
            <div id="enhanced-chat-widget" class="enhanced-chat-widget ${this.options.position} ${this.options.theme}">
                <!-- Chat Toggle Button -->
                <div class="chat-toggle" id="chat-toggle">
                    <div class="chat-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 2C6.48 2 2 6.48 2 12c0 1.54.36 3.04.97 4.37L1 23l6.63-1.97C9.96 21.64 11.46 22 13 22h7c1.1 0 2-.9 2-2V12c0-5.52-4.48-10-10-10z" fill="currentColor" opacity="0.9"/>
                            <circle cx="8" cy="12" r="1.5" fill="white"/>
                            <circle cx="12" cy="12" r="1.5" fill="white"/>
                            <circle cx="16" cy="12" r="1.5" fill="white"/>
                        </svg>
                    </div>
                    <div class="notification-badge" id="notification-badge" style="display: none;">0</div>
                    <div class="connection-status" id="connection-status"></div>
                </div>

                <!-- Chat Window -->
                <div class="chat-window" id="chat-window" style="display: none;">
                    <!-- Chat Header -->
                    <div class="chat-header">
                        <div class="chat-title">
                            <h3>Nepal Meat Shop</h3>
                            <span class="chat-subtitle">How can we help you?</span>
                        </div>
                        <div class="chat-controls">
                            ${this.state.adminMode ? this.getAdminControls() : ''}
                            <button class="minimize-btn" id="minimize-btn">
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                    <path d="M12 6L8 10L4 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                            </button>
                        </div>
                    </div>

                    <!-- Admin Panel (if admin) -->
                    ${this.state.adminMode ? this.getAdminPanel() : ''}

                    <!-- Chat Messages -->
                    <div class="chat-messages" id="chat-messages">
                        <div class="welcome-message">
                            <div class="message ai-message">
                                <div class="message-content">
                                    <p>Hello! Welcome to Nepal Meat Shop. I'm here to help you with our fresh meat products and services. How can I assist you today?</p>
                                </div>
                                <div class="message-time">${this.formatTime(new Date())}</div>
                            </div>
                        </div>
                    </div>

                    <!-- Typing Indicator -->
                    <div class="typing-indicator" id="typing-indicator" style="display: none;">
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                        <span class="typing-text">AI is typing...</span>
                    </div>

                    <!-- Chat Input -->
                    <div class="chat-input-container">
                        <div class="chat-input-wrapper">
                            <textarea 
                                id="chat-input" 
                                class="chat-input" 
                                placeholder="Type your message..." 
                                rows="1"
                                maxlength="${this.options.maxMessageLength}"
                            ></textarea>
                            <button class="send-btn" id="send-btn" disabled>
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                                    <path d="M18 2L9 11L6 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                            </button>
                        </div>
                        <div class="input-footer">
                            <span class="char-counter">0/${this.options.maxMessageLength}</span>
                            <div class="connection-indicator" id="connection-indicator">
                                <span class="status-dot"></span>
                                <span class="status-text">Connecting...</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        if (container === document.body) {
            container.insertAdjacentHTML('beforeend', widgetHTML);
        } else {
            container.innerHTML = widgetHTML;
        }

        this.elements = {
            widget: document.getElementById('enhanced-chat-widget'),
            toggle: document.getElementById('chat-toggle'),
            window: document.getElementById('chat-window'),
            messages: document.getElementById('chat-messages'),
            input: document.getElementById('chat-input'),
            sendBtn: document.getElementById('send-btn'),
            minimizeBtn: document.getElementById('minimize-btn'),
            typingIndicator: document.getElementById('typing-indicator'),
            notificationBadge: document.getElementById('notification-badge'),
            connectionStatus: document.getElementById('connection-status'),
            connectionIndicator: document.getElementById('connection-indicator')
        };

        this.loadStyles();
    }

    /**
     * Get admin controls HTML
     */
    getAdminControls() {
        return `
            <div class="admin-controls">
                <button class="admin-btn" id="admin-takeover-btn" title="Take over conversation">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M2 8h8m0 0l-3-3m3 3l-3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M14 2v12a1 1 0 01-1 1H9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <circle cx="3" cy="3" r="1.5" fill="currentColor" opacity="0.6"/>
                    </svg>
                </button>
                <button class="admin-btn" id="admin-internal-btn" title="Send internal message">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M8 2a6 6 0 100 12 6 6 0 000-12z" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M8 5v3l2 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M14 8h1.5M0.5 8H2M8 0.5V2M8 14v1.5" stroke="currentColor" stroke-width="1" stroke-linecap="round"/>
                    </svg>
                </button>
            </div>
        `;
    }

    /**
     * Get admin panel HTML
     */
    getAdminPanel() {
        return `
            <div class="admin-panel" id="admin-panel" style="display: none;">
                <div class="admin-panel-header">
                    <h4>Quick Actions</h4>
                    <button class="close-admin-panel" id="close-admin-panel">×</button>
                </div>
                <div class="admin-panel-content">
                    <div class="quick-actions">
                        <button class="quick-action-btn customer-reply" id="customer-reply-btn">
                            <span class="icon">💬</span>
                            Reply to Customer
                        </button>
                        <button class="quick-action-btn private-note" id="private-note-btn">
                            <span class="icon">📝</span>
                            Add Private Note
                        </button>
                        <button class="quick-action-btn escalate" id="escalate-btn">
                            <span class="icon">⚠️</span>
                            Need Help
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Toggle chat window
        this.elements.toggle.addEventListener('click', () => this.toggleChat());
        this.elements.minimizeBtn.addEventListener('click', () => this.toggleChat());

        // Send message
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Input handling
        this.elements.input.addEventListener('input', () => this.handleInputChange());
        this.elements.input.addEventListener('focus', () => this.markAsRead());

        // Admin controls
        if (this.state.adminMode) {
            this.bindAdminEvents();
        }

        // Window events
        window.addEventListener('beforeunload', () => this.disconnect());
        window.addEventListener('focus', () => this.markAsRead());
    }

    /**
     * Bind admin-specific events
     */
    bindAdminEvents() {
        const takeoverBtn = document.getElementById('admin-takeover-btn');
        const internalBtn = document.getElementById('admin-internal-btn');
        const adminPanel = document.getElementById('admin-panel');
        const closeAdminPanel = document.getElementById('close-admin-panel');

        if (takeoverBtn) {
            takeoverBtn.addEventListener('click', () => this.toggleAdminTakeover());
        }

        if (internalBtn) {
            internalBtn.addEventListener('click', () => this.toggleAdminPanel());
        }

        if (closeAdminPanel) {
            closeAdminPanel.addEventListener('click', () => this.toggleAdminPanel());
        }

        // Simplified admin action buttons
        const customerReplyBtn = document.getElementById('customer-reply-btn');
        const privateNoteBtn = document.getElementById('private-note-btn');
        const escalateBtn = document.getElementById('escalate-btn');

        if (customerReplyBtn) {
            customerReplyBtn.addEventListener('click', () => this.replyToCustomer());
        }

        if (privateNoteBtn) {
            privateNoteBtn.addEventListener('click', () => this.addPrivateNote());
        }

        if (escalateBtn) {
            escalateBtn.addEventListener('click', () => this.requestHelp());
        }
    }

    /**
     * Start a new conversation
     */
    async startConversation() {
        try {
            this.updateConnectionStatus('connecting');

            const response = await fetch(`${this.options.apiBaseUrl}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    language: this.options.language,
                    device_type: this.detectDeviceType(),
                    initial_page: window.location.pathname
                })
            });

            const data = await response.json();

            if (data.success) {
                this.state.sessionId = data.session_id;
                this.state.conversationId = data.conversation_id;
                this.updateConnectionStatus('connected');
                
                if (this.state.adminMode) {
                    this.connectWebSocket();
                }

                this.log('Conversation started:', data);
            } else {
                throw new Error(data.error || 'Failed to start conversation');
            }
        } catch (error) {
            this.log('Error starting conversation:', error);
            this.updateConnectionStatus('error');
            this.showError('Failed to connect to chat service. Please try again.');
        }
    }

    /**
     * Connect to Socket.IO
     */
    connectWebSocket() {
        if (this.socket && this.socket.connected) {
            return;
        }

        try {
            this.socket = io(this.options.socketIOUrl);

            this.socket.on('connect', () => {
                this.log('Socket.IO connected');
                this.state.isConnected = true;
                this.state.connectionAttempts = 0;
                this.updateConnectionStatus('connected');

                // Join conversation if we have session ID
                if (this.state.sessionId) {
                    this.socket.emit('customer_join', {
                        session_id: this.state.sessionId,
                        user_role: this.state.userRole
                    });
                }

                // Process queued messages
                this.processMessageQueue();
            });

            this.socket.on('new_message', (data) => {
                this.handleWebSocketMessage({ type: 'message', message: data.message });
            });

            this.socket.on('disconnect', () => {
                this.log('Socket.IO disconnected');
                this.state.isConnected = false;
                this.updateConnectionStatus('disconnected');
                this.scheduleReconnect();
            });

            this.socket.on('error', (error) => {
                this.log('Socket.IO error:', error);
                this.updateConnectionStatus('error');
            });

        } catch (error) {
            this.log('Error connecting Socket.IO:', error);
            this.updateConnectionStatus('error');
        }
    }

    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(data) {
        this.log('WebSocket message received:', data);

        switch (data.type) {
            case 'message':
                this.addMessage(data.message);
                break;
            case 'typing':
                this.handleTypingIndicator(data);
                break;
            case 'admin_takeover':
                this.handleAdminTakeover(data);
                break;
            case 'admin_release':
                this.handleAdminRelease(data);
                break;
            case 'conversation_update':
                this.handleConversationUpdate(data);
                break;
            case 'error':
                this.showError(data.message);
                break;
            default:
                this.log('Unknown WebSocket message type:', data.type);
        }
    }

    /**
     * Send Socket.IO message
     */
    sendWebSocketMessage(type, data) {
        if (this.socket && this.socket.connected) {
            this.socket.emit(type, data);
        } else {
            // Queue message for later
            this.messageQueue.push({ type, data });
        }
    }

    /**
     * Process queued messages
     */
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.socket.emit(message.type, message.data);
        }
    }

    /**
     * Send a message
     */
    async sendMessage() {
        const message = this.elements.input.value.trim();
        if (!message || !this.state.sessionId) {
            return;
        }

        // Check if this is an admin internal message
        const isInternal = this.state.adminMode && this.isInternalMessageMode();
        
        try {
            // Clear input
            this.elements.input.value = '';
            this.updateSendButton();
            this.updateCharCounter();

            // Add message to UI immediately
            this.addMessage({
                content: message,
                message_type: isInternal ? 'internal' : 'user',
                timestamp: new Date().toISOString(),
                is_internal: isInternal,
                sender_role: this.state.userRole
            });

            // Send via WebSocket if connected, otherwise use HTTP API
            if (this.state.isConnected && this.socket) {
                this.sendWebSocketMessage('customer_message', {
                    session_id: this.state.sessionId,
                    message: message,
                    is_internal: isInternal,
                    message_type: isInternal ? this.getInternalMessageType() : 'user',
                    visibility: isInternal ? this.getInternalVisibility() : 'public',
                    internal_tags: isInternal ? this.getInternalTags() : []
                });
            } else {
                // Fallback to HTTP API
                await this.sendMessageHTTP(message, isInternal);
            }

            // Show typing indicator for AI response (if not internal)
            if (!isInternal) {
                this.showTypingIndicator();
            }

        } catch (error) {
            this.log('Error sending message:', error);
            this.showError('Failed to send message. Please try again.');
        }
    }

    /**
     * Send message via HTTP API
     */
    async sendMessageHTTP(message, isInternal = false) {
        const endpoint = isInternal ? '/admin/internal' : '/send';
        const payload = {
            session_id: this.state.sessionId,
            message: message
        };

        if (isInternal) {
            payload.visibility = this.getInternalVisibility();
            payload.tags = this.getInternalTags();
        }

        const response = await fetch(`${this.options.apiBaseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to send message');
        }

        // Add AI response if provided
        if (data.ai_response && !isInternal) {
            setTimeout(() => {
                this.hideTypingIndicator();
                this.addMessage({
                    content: data.ai_response.content,
                    message_type: 'ai',
                    timestamp: data.ai_response.timestamp,
                    ai_confidence: data.ai_response.confidence
                });
            }, 1000);
        }
    }

    /**
     * Add message to chat
     */
    addMessage(messageData) {
        const message = {
            id: messageData.id || Date.now().toString(),
            content: messageData.content,
            message_type: messageData.message_type || 'user',
            timestamp: new Date(messageData.timestamp || Date.now()),
            is_internal: messageData.is_internal || false,
            sender_role: messageData.sender_role || 'customer',
            sender_name: messageData.sender_name || '',
            appears_as_ai: messageData.appears_as_ai || false,
            ai_confidence: messageData.ai_confidence || null,
            internal_tags: messageData.internal_tags || [],
            escalation_flag: messageData.escalation_flag || false
        };

        // Check if message should be visible to current user
        if (!this.isMessageVisible(message)) {
            return;
        }

        this.state.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
        this.updateNotificationBadge();
        this.state.lastActivity = new Date();
    }

    /**
     * Check if message is visible to current user
     */
    isMessageVisible(message) {
        // Customers can only see public messages
        if (this.state.userRole === 'customer') {
            return !message.is_internal && message.visibility !== 'admin_only';
        }

        // Admins can see most messages
        if (this.state.userRole === 'admin') {
            return message.visibility !== 'super_admin_only';
        }

        // Super admins can see all messages
        if (this.state.userRole === 'super_admin') {
            return true;
        }

        return false;
    }

    /**
     * Render a message in the chat
     */
    renderMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${this.getMessageClass(message)}`;
        messageElement.dataset.messageId = message.id;

        const messageContent = `
            <div class="message-content">
                ${this.formatMessageContent(message)}
                ${this.getMessageMetadata(message)}
            </div>
            <div class="message-time">${this.formatTime(message.timestamp)}</div>
            ${this.getMessageActions(message)}
        `;

        messageElement.innerHTML = messageContent;
        this.elements.messages.appendChild(messageElement);
    }

    /**
     * Get message CSS class
     */
    getMessageClass(message) {
        const classes = [];

        // Message type classes
        if (message.message_type === 'user') {
            classes.push('user-message');
        } else if (message.message_type === 'ai' || message.appears_as_ai) {
            classes.push('ai-message');
        } else if (message.message_type === 'admin') {
            classes.push('admin-message');
        } else if (message.message_type === 'internal') {
            classes.push('internal-message');
        } else if (message.message_type === 'system') {
            classes.push('system-message');
        }

        // Special flags
        if (message.is_internal) {
            classes.push('internal');
        }
        if (message.escalation_flag) {
            classes.push('escalated');
        }
        if (message.ai_confidence && message.ai_confidence < 0.7) {
            classes.push('low-confidence');
        }

        return classes.join(' ');
    }

    /**
     * Format message content
     */
    formatMessageContent(message) {
        let content = this.escapeHtml(message.content);
        
        // Convert URLs to links
        content = content.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        
        // Convert line breaks
        content = content.replace(/\n/g, '<br>');

        return `<p>${content}</p>`;
    }

    /**
     * Get message metadata for admin view
     */
    getMessageMetadata(message) {
        if (!this.state.adminMode) {
            return '';
        }

        const metadata = [];

        if (message.sender_name) {
            metadata.push(`<span class="sender">by ${message.sender_name}</span>`);
        }

        if (message.ai_confidence !== null) {
            const confidence = Math.round(message.ai_confidence * 100);
            metadata.push(`<span class="confidence">AI: ${confidence}%</span>`);
        }

        if (message.internal_tags && message.internal_tags.length > 0) {
            const tags = message.internal_tags.map(tag => `<span class="tag">${tag}</span>`).join('');
            metadata.push(`<span class="tags">${tags}</span>`);
        }

        return metadata.length > 0 ? `<div class="message-metadata">${metadata.join(' ')}</div>` : '';
    }

    /**
     * Get message actions for admin
     */
    getMessageActions(message) {
        if (!this.state.adminMode || message.message_type === 'user') {
            return '';
        }

        const actions = [];

        if (message.message_type === 'ai') {
            actions.push(`<button class="message-action" onclick="enhancedChat.correctAIResponse('${message.id}')">Correct</button>`);
        }

        if (message.is_internal) {
            actions.push(`<button class="message-action" onclick="enhancedChat.editInternalMessage('${message.id}')">Edit</button>`);
        }

        return actions.length > 0 ? `<div class="message-actions">${actions.join('')}</div>` : '';
    }

    /**
     * Handle input changes
     */
    handleInputChange() {
        this.updateSendButton();
        this.updateCharCounter();
        this.handleTyping();
    }

    /**
     * Update send button state
     */
    updateSendButton() {
        const hasText = this.elements.input.value.trim().length > 0;
        this.elements.sendBtn.disabled = !hasText || !this.state.sessionId;
    }

    /**
     * Update character counter
     */
    updateCharCounter() {
        const counter = document.querySelector('.char-counter');
        if (counter) {
            const length = this.elements.input.value.length;
            counter.textContent = `${length}/${this.options.maxMessageLength}`;
            counter.classList.toggle('warning', length > this.options.maxMessageLength * 0.9);
        }
    }

    /**
     * Handle typing indicator
     */
    handleTyping() {
        if (!this.state.isConnected) return;

        // Clear existing timer
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
        }

        // Send typing start
        if (!this.state.isTyping) {
            this.state.isTyping = true;
            this.sendWebSocketMessage('typing', {
                session_id: this.state.sessionId,
                is_typing: true
            });
        }

        // Set timer to stop typing
        this.typingTimer = setTimeout(() => {
            this.state.isTyping = false;
            this.sendWebSocketMessage('typing', {
                session_id: this.state.sessionId,
                is_typing: false
            });
        }, 1000);
    }

    /**
     * Show typing indicator
     */
    showTypingIndicator(text = 'AI is typing...') {
        this.elements.typingIndicator.querySelector('.typing-text').textContent = text;
        this.elements.typingIndicator.style.display = 'block';
        this.scrollToBottom();
    }

    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        this.elements.typingIndicator.style.display = 'none';
    }

    /**
     * Handle typing indicator from WebSocket
     */
    handleTypingIndicator(data) {
        if (data.is_typing) {
            const text = data.user_role === 'admin' ? 'Admin is typing...' : 'AI is typing...';
            this.showTypingIndicator(text);
        } else {
            this.hideTypingIndicator();
        }
    }

    /**
     * Toggle chat window
     */
    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
        this.elements.window.style.display = this.state.isOpen ? 'flex' : 'none';
        
        if (this.state.isOpen) {
            this.elements.input.focus();
            this.markAsRead();
            this.scrollToBottom();
            
            // Connect WebSocket if not connected
            if (!this.state.isConnected && this.state.sessionId) {
                this.connectWebSocket();
            }
        }
    }

    /**
     * Admin takeover functionality
     */
    async toggleAdminTakeover() {
        if (!this.state.conversationId) {
            this.showError('No active conversation to take over.');
            return;
        }

        try {
            const endpoint = this.state.adminTakenOver ? '/admin/release' : '/admin/takeover';
            const response = await fetch(`${this.options.apiBaseUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation_id: this.state.conversationId
                })
            });

            const data = await response.json();

            if (data.success) {
                this.state.adminTakenOver = !this.state.adminTakenOver;
                this.updateAdminControls();
                this.showSuccess(data.message);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.log('Error toggling admin takeover:', error);
            this.showError('Failed to toggle admin takeover.');
        }
    }

    /**
     * Toggle admin panel
     */
    toggleAdminPanel() {
        const panel = document.getElementById('admin-panel');
        if (panel) {
            const isVisible = panel.style.display !== 'none';
            panel.style.display = isVisible ? 'none' : 'block';
        }
    }

    /**
     * Check if in internal message mode
     */
    isInternalMessageMode() {
        const messageType = document.getElementById('admin-message-type');
        return messageType && messageType.value === 'internal';
    }

    /**
     * Get internal message type
     */
    getInternalMessageType() {
        const messageType = document.getElementById('admin-message-type');
        return messageType ? messageType.value : 'internal';
    }

    /**
     * Get internal visibility
     */
    getInternalVisibility() {
        const visibility = document.getElementById('admin-visibility');
        return visibility ? visibility.value : 'admin_only';
    }

    /**
     * Get internal tags
     */
    getInternalTags() {
        const tagsInput = document.getElementById('admin-internal-tags');
        if (!tagsInput || !tagsInput.value.trim()) {
            return [];
        }
        return tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    }

    /**
     * Create custom modal dialog
     */
    createModal(title, inputLabel, inputValue = '', inputType = 'text', options = null) {
        return new Promise((resolve) => {
            // Create modal overlay
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
            `;

            // Create modal content
            const modal = document.createElement('div');
            modal.style.cssText = `
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                max-width: 400px;
                width: 90%;
                font-family: Arial, sans-serif;
            `;

            // Create modal HTML
            let inputHTML;
            if (options) {
                inputHTML = `<select id="modalInput" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin: 10px 0;">
                    ${options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                </select>`;
            } else if (inputType === 'textarea') {
                inputHTML = `<textarea id="modalInput" placeholder="${inputLabel}" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin: 10px 0; box-sizing: border-box; min-height: 100px; resize: vertical;">${inputValue}</textarea>`;
            } else {
                inputHTML = `<input type="${inputType}" id="modalInput" value="${inputValue}" placeholder="${inputLabel}" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin: 10px 0; box-sizing: border-box;" />`;
            }

            modal.innerHTML = `
                <h3 style="margin: 0 0 15px 0; color: #333;">${title}</h3>
                <label style="display: block; margin-bottom: 5px; color: #666;">${inputLabel}</label>
                ${inputHTML}
                <div style="text-align: right; margin-top: 15px;">
                    <button id="modalCancel" style="padding: 8px 16px; margin-right: 10px; border: 1px solid #ddd; background: #f5f5f5; border-radius: 4px; cursor: pointer;">Cancel</button>
                    <button id="modalOk" style="padding: 8px 16px; border: none; background: #007bff; color: white; border-radius: 4px; cursor: pointer;">OK</button>
                </div>
            `;

            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            const input = modal.querySelector('#modalInput');
            const okBtn = modal.querySelector('#modalOk');
            const cancelBtn = modal.querySelector('#modalCancel');

            // Focus input
            setTimeout(() => input.focus(), 100);

            // Handle OK button
            const handleOk = () => {
                const value = input.value.trim();
                document.body.removeChild(overlay);
                resolve(value || null);
            };

            // Handle Cancel button
            const handleCancel = () => {
                document.body.removeChild(overlay);
                resolve(null);
            };

            okBtn.addEventListener('click', handleOk);
            cancelBtn.addEventListener('click', handleCancel);
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') handleOk();
                if (e.key === 'Escape') handleCancel();
            });
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) handleCancel();
            });
        });
    }

    /**
     * Escalate conversation
     */
    async escalateConversation() {
        const reason = await this.createModal('Escalate Conversation', 'Escalation reason:');
        if (!reason) return;

        try {
            const response = await fetch(`${this.options.apiBaseUrl}/admin/conversation/${this.state.conversationId}/escalate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    reason: reason,
                    level: 1
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Conversation escalated successfully.');
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.log('Error escalating conversation:', error);
            this.showError('Failed to escalate conversation.');
        }
    }

    /**
     * Set conversation priority
     */
    async setPriority() {
        const priority = await this.createModal('Set Priority', 'Select priority level:', '', 'text', ['low', 'normal', 'high', 'urgent']);
        if (!priority || !['low', 'normal', 'high', 'urgent'].includes(priority)) {
            if (priority) this.showError('Invalid priority level.');
            return;
        }

        try {
            const response = await fetch(`${this.options.apiBaseUrl}/admin/conversation/${this.state.conversationId}/priority`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    priority: priority
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Priority updated successfully.');
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.log('Error setting priority:', error);
            this.showError('Failed to set priority.');
        }
    }

    /**
     * Add admin note
     */
    async addAdminNote() {
        const note = await this.createModal('Add Admin Note', 'Enter your note:');
        if (!note) return;

        try {
            const response = await fetch(`${this.options.apiBaseUrl}/admin/conversation/${this.state.conversationId}/note`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    note: note,
                    type: 'general'
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Note added successfully.');
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.log('Error adding note:', error);
            this.showError('Failed to add note.');
        }
    }

    /**
     * Simplified: Reply to customer as admin
     */
    async replyToCustomer() {
        this.toggleAdminPanel();
        this.elements.input.focus();
        this.elements.input.placeholder = 'Type your reply to the customer...';
    }

    /**
     * Simplified: Add a private note (only admins can see)
     */
    async addPrivateNote() {
        const note = await this.createModal('Private Note', 'Add a note for other admins:');
        if (!note) return;

        try {
            await this.sendMessageHTTP(note, true); // Send as internal message
            this.showSuccess('Private note added successfully.');
            this.toggleAdminPanel();
        } catch (error) {
            this.showError('Failed to add private note.');
        }
    }

    /**
     * Simplified: Request help from senior admin
     */
    async requestHelp() {
        const reason = await this.createModal('Request Help', 'Why do you need help with this conversation?');
        if (!reason) return;

        try {
            const helpMessage = `🆘 HELP REQUESTED: ${reason}`;
            await this.sendMessageHTTP(helpMessage, true); // Send as internal message
            this.showSuccess('Help request sent to senior admins.');
            this.toggleAdminPanel();
        } catch (error) {
            this.showError('Failed to send help request.');
        }
    }

    /**
     * Correct AI response
     */
    async correctAIResponse(messageId) {
        const message = this.state.messages.find(m => m.id === messageId);
        if (!message) return;

        const correction = await this.createModal('Correct AI Response', 'Provide corrected response:', message.content, 'textarea');
        if (!correction) return;

        const reason = await this.createModal('Correction Reason', 'Why is this correction needed?');
        const category = await this.createModal('Improvement Category', 'Select category:', '', 'text', ['accuracy', 'tone', 'completeness', 'relevance', 'other']);

        try {
            const response = await fetch(`${this.options.apiBaseUrl}/admin/correct`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation_id: this.state.conversationId,
                    original_message_id: messageId,
                    corrected_response: correction,
                    correction_reason: reason,
                    improvement_category: category
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('AI response corrected for learning.');
                // Update message in UI
                const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
                if (messageElement) {
                    messageElement.classList.add('corrected');
                }
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.log('Error correcting AI response:', error);
            this.showError('Failed to correct AI response.');
        }
    }

    /**
     * Update connection status
     */
    updateConnectionStatus(status) {
        const indicator = this.elements.connectionIndicator;
        const statusText = indicator.querySelector('.status-text');
        const statusDot = indicator.querySelector('.status-dot');

        indicator.className = `connection-indicator ${status}`;
        
        switch (status) {
            case 'connected':
                statusText.textContent = 'Connected';
                break;
            case 'connecting':
                statusText.textContent = 'Connecting...';
                break;
            case 'disconnected':
                statusText.textContent = 'Disconnected';
                break;
            case 'error':
                statusText.textContent = 'Connection Error';
                break;
        }
    }

    /**
     * Update notification badge
     */
    updateNotificationBadge() {
        if (!this.state.isOpen) {
            const unreadCount = this.getUnreadMessageCount();
            if (unreadCount > 0) {
                this.elements.notificationBadge.textContent = unreadCount;
                this.elements.notificationBadge.style.display = 'block';
            } else {
                this.elements.notificationBadge.style.display = 'none';
            }
        }
    }

    /**
     * Get unread message count
     */
    getUnreadMessageCount() {
        // This would track unread messages
        return 0;
    }

    /**
     * Mark messages as read
     */
    markAsRead() {
        this.elements.notificationBadge.style.display = 'none';
    }

    /**
     * Scroll to bottom of messages
     */
    scrollToBottom() {
        setTimeout(() => {
            this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
        }, 100);
    }

    /**
     * Schedule WebSocket reconnection
     */
    scheduleReconnect() {
        if (this.state.connectionAttempts >= this.options.reconnectAttempts) {
            this.log('Max reconnection attempts reached');
            return;
        }

        this.state.connectionAttempts++;
        const delay = this.options.reconnectDelay * this.state.connectionAttempts;

        this.log(`Scheduling reconnection attempt ${this.state.connectionAttempts} in ${delay}ms`);

        this.reconnectTimer = setTimeout(() => {
            this.connectWebSocket();
        }, delay);
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        this.state.isConnected = false;
    }

    /**
     * Show error message
     */
    showError(message) {
        this.showNotification(message, 'error');
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `chat-notification ${type}`;
        notification.textContent = message;

        // Add to widget
        this.elements.widget.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    /**
     * Detect device type
     */
    detectDeviceType() {
        const userAgent = navigator.userAgent.toLowerCase();
        if (/mobile|android|iphone|ipad|phone/i.test(userAgent)) {
            return 'mobile';
        } else if (/tablet|ipad/i.test(userAgent)) {
            return 'tablet';
        }
        return 'desktop';
    }

    /**
     * Format time
     */
    formatTime(date) {
        return new Intl.DateTimeFormat('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        }).format(new Date(date));
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Load CSS styles
     */
    loadStyles() {
        if (document.getElementById('enhanced-chat-styles')) {
            return;
        }

        const styles = `
            <style id="enhanced-chat-styles">
                .enhanced-chat-widget {
                    position: fixed;
                    z-index: 10000;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                
                .enhanced-chat-widget.bottom-left {
                    bottom: 20px;
                    left: 20px;
                }
                
                .chat-toggle {
                    width: 60px;
                    height: 60px;
                    background: #e74c3c;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    transition: all 0.3s ease;
                    position: relative;
                }
                
                .chat-toggle:hover {
                    transform: scale(1.1);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.2);
                }
                
                .chat-icon {
                    color: white;
                    font-size: 24px;
                }
                
                .notification-badge {
                    position: absolute;
                    top: -5px;
                    right: -5px;
                    background: #ff4444;
                    color: white;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    font-size: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .connection-status {
                    position: absolute;
                    bottom: -2px;
                    right: -2px;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    border: 2px solid white;
                }
                
                .chat-window {
                    position: absolute;
                    bottom: 80px;
                    left: 0;
                    width: 350px;
                    height: 500px;
                    max-width: calc(100vw - 40px);
                    max-height: calc(100vh - 120px);
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 8px 30px rgba(0,0,0,0.12);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }
                
                .chat-header {
                    background: #e74c3c;
                    color: white;
                    padding: 15px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .chat-title h3 {
                    margin: 0;
                    font-size: 16px;
                }
                
                .chat-subtitle {
                    font-size: 12px;
                    opacity: 0.9;
                }
                
                .chat-controls {
                    display: flex;
                    gap: 8px;
                }
                
                .admin-controls {
                    display: flex;
                    gap: 4px;
                }
                
                .admin-btn, .minimize-btn {
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: white;
                    width: 32px;
                    height: 32px;
                    border-radius: 6px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background 0.2s;
                }
                
                .admin-btn:hover, .minimize-btn:hover {
                    background: rgba(255,255,255,0.3);
                }
                
                .admin-panel {
                    background: #f8f9fa;
                    border-bottom: 1px solid #e9ecef;
                    padding: 12px;
                }
                
                .admin-panel-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 12px;
                }
                
                .admin-panel-header h4 {
                    margin: 0;
                    font-size: 14px;
                    color: #495057;
                }
                
                .close-admin-panel {
                    background: none;
                    border: none;
                    font-size: 18px;
                    cursor: pointer;
                    color: #6c757d;
                }
                
                .quick-actions {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }
                
                .quick-action-btn {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 16px;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    text-align: left;
                }
                
                .quick-action-btn .icon {
                    font-size: 16px;
                }
                
                .quick-action-btn.customer-reply {
                    background: #e3f2fd;
                    color: #1976d2;
                    border: 1px solid #bbdefb;
                }
                
                .quick-action-btn.customer-reply:hover {
                    background: #bbdefb;
                }
                
                .quick-action-btn.private-note {
                    background: #f3e5f5;
                    color: #7b1fa2;
                    border: 1px solid #e1bee7;
                }
                
                .quick-action-btn.private-note:hover {
                    background: #e1bee7;
                }
                
                .quick-action-btn.escalate {
                    background: #fff3e0;
                    color: #f57c00;
                    border: 1px solid #ffcc02;
                }
                
                .quick-action-btn.escalate:hover {
                    background: #ffcc02;
                }
                
                .chat-messages {
                    flex: 1;
                    padding: 15px;
                    overflow-y: auto;
                    background: #f8f9fa;
                }
                
                .message {
                    margin-bottom: 15px;
                    max-width: 80%;
                }
                
                .user-message {
                    margin-left: auto;
                }
                
                .user-message .message-content {
                    background: #007bff;
                    color: white;
                    border-radius: 18px 18px 4px 18px;
                }
                
                .ai-message .message-content,
                .admin-message .message-content {
                    background: white;
                    border-radius: 18px 18px 18px 4px;
                    border: 1px solid #e9ecef;
                }
                
                .internal-message {
                    border-left: 4px solid #ffc107;
                    background: #fff3cd;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 8px 0;
                }
                
                .internal-message .message-content {
                    background: transparent;
                    border: none;
                    border-radius: 0;
                }
                
                .system-message {
                    text-align: center;
                    margin: 8px 0;
                }
                
                .system-message .message-content {
                    background: #e9ecef;
                    color: #6c757d;
                    border-radius: 12px;
                    font-size: 12px;
                    display: inline-block;
                }
                
                .message-content {
                    padding: 12px 16px;
                }
                
                .message-content p {
                    margin: 0;
                    line-height: 1.4;
                }
                
                .message-metadata {
                    margin-top: 6px;
                    font-size: 11px;
                    color: #6c757d;
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                }
                
                .message-metadata .tag {
                    background: #007bff;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 10px;
                    font-size: 10px;
                }
                
                .message-time {
                    font-size: 11px;
                    color: #6c757d;
                    margin-top: 4px;
                    text-align: right;
                }
                
                .user-message .message-time {
                    text-align: left;
                }
                
                .message-actions {
                    margin-top: 6px;
                    display: flex;
                    gap: 6px;
                }
                
                .message-action {
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    color: #495057;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    cursor: pointer;
                }
                
                .message-action:hover {
                    background: #e9ecef;
                }
                
                .message.corrected {
                    opacity: 0.7;
                }
                
                .message.corrected::after {
                    content: '✓ Corrected';
                    position: absolute;
                    top: -8px;
                    right: 8px;
                    background: #28a745;
                    color: white;
                    font-size: 10px;
                    padding: 2px 6px;
                    border-radius: 10px;
                }
                
                .typing-indicator {
                    padding: 15px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    background: #f8f9fa;
                }
                
                .typing-dots {
                    display: flex;
                    gap: 4px;
                }
                
                .typing-dots span {
                    width: 6px;
                    height: 6px;
                    background: #6c757d;
                    border-radius: 50%;
                    animation: typing 1.4s infinite;
                }
                
                .typing-dots span:nth-child(2) {
                    animation-delay: 0.2s;
                }
                
                .typing-dots span:nth-child(3) {
                    animation-delay: 0.4s;
                }
                
                @keyframes typing {
                    0%, 60%, 100% {
                        transform: translateY(0);
                        opacity: 0.5;
                    }
                    30% {
                        transform: translateY(-10px);
                        opacity: 1;
                    }
                }
                
                .typing-text {
                    font-size: 12px;
                    color: #6c757d;
                }
                
                .chat-input-container {
                    border-top: 1px solid #e9ecef;
                    background: white;
                }
                
                .chat-input-wrapper {
                    display: flex;
                    padding: 12px;
                    gap: 8px;
                }
                
                .chat-input {
                    flex: 1;
                    border: 1px solid #ced4da;
                    border-radius: 20px;
                    padding: 8px 16px;
                    resize: none;
                    outline: none;
                    font-family: inherit;
                    font-size: 14px;
                    max-height: 100px;
                }
                
                .chat-input:focus {
                    border-color: #007bff;
                }
                
                .send-btn {
                    width: 40px;
                    height: 40px;
                    background: #007bff;
                    border: none;
                    border-radius: 50%;
                    color: white;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background 0.2s;
                }
                
                .send-btn:hover:not(:disabled) {
                    background: #0056b3;
                }
                
                .send-btn:disabled {
                    background: #6c757d;
                    cursor: not-allowed;
                }
                
                .input-footer {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    font-size: 11px;
                    color: #6c757d;
                    background: #f8f9fa;
                }
                
                .char-counter.warning {
                    color: #dc3545;
                }
                
                .connection-indicator {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }
                
                .status-dot {
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                    background: #6c757d;
                }
                
                .connection-indicator.connected .status-dot {
                    background: #28a745;
                }
                
                .connection-indicator.connecting .status-dot {
                    background: #ffc107;
                    animation: pulse 1s infinite;
                }
                
                .connection-indicator.error .status-dot {
                    background: #dc3545;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                
                .chat-notification {
                    position: absolute;
                    top: -40px;
                    left: 0;
                    right: 0;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    z-index: 1000;
                    animation: slideDown 0.3s ease;
                }
                
                .chat-notification.success {
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
                
                .chat-notification.error {
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }
                
                .chat-notification.info {
                    background: #d1ecf1;
                    color: #0c5460;
                    border: 1px solid #bee5eb;
                }
                
                @keyframes slideDown {
                    from {
                        transform: translateY(-100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
                
                /* Mobile Responsive */
                @media (max-width: 480px) {
                    .chat-window {
                        width: 100vw;
                        height: 100vh;
                        bottom: 0;
                        left: 0;
                        border-radius: 0;
                    }
                    
                    .enhanced-chat-widget.bottom-left {
                        bottom: 10px;
                        left: 10px;
                    }
                }
                
                /* Dark theme */
                .enhanced-chat-widget.dark {
                    /* Dark theme styles would go here */
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
    }

    /**
     * Debug logging
     */
    log(...args) {
        if (window.location.hostname === 'localhost' || window.location.search.includes('debug=true')) {
            console.log('[Enhanced Chat Widget]', ...args);
        }
    }

    /**
     * Destroy the widget
     */
    destroy() {
        this.disconnect();
        
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
        }
        
        if (this.elements.widget) {
            this.elements.widget.remove();
        }
        
        const styles = document.getElementById('enhanced-chat-styles');
        if (styles) {
            styles.remove();
        }
    }
}

// Auto-initialize if not in module environment
if (typeof module === 'undefined') {
    // Prevent multiple instances
    if (!window.enhancedChat) {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                if (!window.enhancedChat) {
                    window.enhancedChat = new EnhancedChatWidget();
                }
            });
        } else {
            window.enhancedChat = new EnhancedChatWidget();
        }
    } else {
        console.log('Enhanced chat widget already initialized');
    }
}

// Export for module environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedChatWidget;
}