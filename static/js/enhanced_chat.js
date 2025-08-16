/**
 * Enhanced Chat Widget with WebSocket Support
 * Integrates with existing chat system while adding real-time messaging
 * and admin takeover functionality (transparent to customers)
 */

class EnhancedChatWidget {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.conversationId = null;
        this.isConnected = false;
        this.isTyping = false;
        this.typingTimeout = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // Maintain compatibility with existing chat widget
        this.isOpen = false;
        this.isMinimized = false;
        this.messageHistory = [];
        this.currentUser = null;
        
        // Chat mode state
        this.currentMode = 'message'; // 'message' or 'reply'
        this.lastCustomerMessage = null;
        this.isAdmin = this.checkIfAdmin();
        
        this.initializeSocket();
        this.bindEvents();
        this.initializeModeSwitch();
    }
    
    /**
     * Initialize Socket.IO connection
     */
    initializeSocket() {
        try {
            // Check if Socket.IO is available
            if (typeof io === 'undefined') {
                console.warn('Socket.IO not available, falling back to HTTP-only chat');
                this.fallbackToHttpChat();
                return;
            }
            
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true
            });
            
            this.setupSocketEvents();
            
        } catch (error) {
            console.error('Failed to initialize socket:', error);
            this.fallbackToHttpChat();
        }
    }
    
    /**
     * Setup Socket.IO event handlers
     */
    setupSocketEvents() {
        // Connection events
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.joinCustomerSession();
        });
        
        this.socket.on('disconnect', (reason) => {
            this.isConnected = false;
            
            if (reason === 'io server disconnect') {
                // Server disconnected, try to reconnect
                this.attemptReconnect();
            }
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.attemptReconnect();
        });
        
        // Chat events
        this.socket.on('conversation_created', (data) => {
            this.conversationId = data.conversation_id;
            this.sessionId = data.session_id;
        });
        
        this.socket.on('message_received', (data) => {
            this.handleIncomingMessage(data);
        });
        
        this.socket.on('ai_response', (data) => {
            this.handleAIResponse(data);
        });
        
        this.socket.on('admin_message', (data) => {
            // Admin messages appear as AI to customer
            this.handleAdminMessage(data);
        });
        
        this.socket.on('typing_indicator', (data) => {
            if (data.is_typing) {
                this.showTypingIndicator();
            } else {
                this.hideTypingIndicator();
            }
        });
        
        this.socket.on('conversation_history', (data) => {
            this.loadConversationHistory(data.messages);
        });
        
        this.socket.on('error', (data) => {
            console.error('Chat error:', data.message);
            this.showErrorMessage(data.message);
        });
    }
    
    /**
     * Join customer session
     */
    joinCustomerSession() {
        if (!this.socket || !this.isConnected) return;
        
        // Generate session ID if not exists
        if (!this.sessionId) {
            this.sessionId = this.generateSessionId();
        }
        
        this.socket.emit('customer_join', {
            session_id: this.sessionId,
            user_id: this.getCurrentUserId(),
            language: this.detectLanguage()
        });
    }
    
    /**
     * Send message through WebSocket
     */
    sendMessageWS(message) {
        if (!this.socket || !this.isConnected) {
            // Fallback to HTTP
            return this.sendMessageHTTP(message);
        }
        
        this.socket.emit('customer_message', {
            conversation_id: this.conversationId,
            session_id: this.sessionId,
            message: message,
            timestamp: new Date().toISOString(),
            mode: this.currentMode,
            reply_to_message: this.currentMode === 'reply' ? this.lastCustomerMessage?.message : null
        });
        
        // Add message to UI immediately
        this.addMessageToChat(message, 'user');
        
        // Show typing indicator
        this.showTypingIndicator();
    }
    
    /**
     * Handle incoming messages from other users or system
     */
    handleIncomingMessage(data) {
        if (data.message_type === 'user' && data.session_id !== this.sessionId) {
            // Message from another user, ignore
            return;
        }
        
        this.addMessageToChat(data.content, data.message_type);
        
        // Update last customer message for reply mode only if it's from AI or admin
        if (data.message_type === 'ai' || data.message_type === 'admin') {
            this.lastCustomerMessage = {
                message: data.content,
                sender: data.message_type,
                timestamp: new Date().toISOString()
            };
            this.updateModeUI();
        }
    }
    
    /**
     * Handle AI responses
     */
    handleAIResponse(data) {
        this.hideTypingIndicator();
        this.addMessageToChat(data.content, 'ai');
        
        // After AI responds, this becomes something we can reply to
        this.lastCustomerMessage = {
            message: data.content,
            sender: 'ai',
            timestamp: new Date().toISOString()
        };
        this.updateModeUI();
    }
    
    /**
     * Handle admin messages (appears as AI to customer)
     */
    handleAdminMessage(data) {
        this.hideTypingIndicator();
        
        // Admin messages appear as AI responses to customers
        const messageType = data.appears_as_ai ? 'ai' : 'admin';
        this.addMessageToChat(data.content, messageType);
    }
    
    /**
     * Load conversation history
     */
    loadConversationHistory(messages) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        // Clear existing messages except welcome
        const welcomeMessage = chatMessages.querySelector('.bot-message');
        chatMessages.innerHTML = '';
        
        // Re-add welcome message
        if (welcomeMessage) {
            chatMessages.appendChild(welcomeMessage);
        }
        
        // Add history messages - filter out empty/invalid messages
        messages.forEach(msg => {
            // Skip messages with empty or invalid content
            if (!msg.content || typeof msg.content !== 'string' || msg.content.trim() === '') {
                console.warn('Skipping empty message in history:', msg);
                return;
            }
            
            const messageType = msg.message_type === 'admin' && msg.appears_as_ai ? 'ai' : msg.message_type;
            this.addMessageToChat(msg.content, messageType, new Date(msg.timestamp));
        });
        
        this.scrollToBottom();
    }
    
    /**
     * Send typing indicator
     */
    sendTypingIndicator(isTyping) {
        if (!this.socket || !this.isConnected) return;
        
        this.socket.emit('customer_typing', {
            session_id: this.sessionId,
            conversation_id: this.conversationId,
            is_typing: isTyping
        });
    }
    
    /**
     * Fallback to HTTP-only chat when WebSocket is not available
     */
    fallbackToHttpChat() {
        // Using HTTP-only chat mode
        // Use existing HTTP chat functionality
        this.sendMessage = this.sendMessageHTTP;
    }
    
    /**
     * HTTP fallback for sending messages
     */
    async sendMessageHTTP(message) {
        try {
            const requestData = { 
                message: message,
                session_id: this.sessionId,
                mode: this.currentMode,
                reply_to_message: this.currentMode === 'reply' ? this.lastCustomerMessage?.message : null
            };
            
            // Include conversation_id if available for enhanced chat tracking
            if (this.conversationId) {
                requestData.conversation_id = this.conversationId;
            }
            
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            this.hideTypingIndicator();
            
            if (response.ok && data.reply) {
                // Update conversation_id if provided in response
                if (data.conversation_id) {
                    this.conversationId = data.conversation_id;
                }
                
                this.addMessageToChat(data.reply, 'ai');
            } else {
                const errorMsg = data.error || 'Sorry, I encountered an error. Please try again.';
                this.addMessageToChat(errorMsg, 'ai');
            }
            
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessageToChat('Sorry, I\'m having trouble connecting. Please check your internet connection and try again.', 'ai');
            console.error('Chat request failed:', error);
        }
    }
    
    /**
     * Attempt to reconnect to WebSocket
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            // Max reconnection attempts reached, falling back to HTTP
            this.fallbackToHttpChat();
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        // Attempting to reconnect
        
        setTimeout(() => {
            if (this.socket) {
                this.socket.connect();
            }
        }, delay);
    }
    
    /**
     * Bind events to existing chat widget elements
     */
    bindEvents() {
        // Override existing chat widget initialization
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeChatWidget();
        });
        
        // Typing indicator for customer
        const chatInput = document.getElementById('chatMessageInput');
        if (chatInput) {
            let typingTimer;
            
            chatInput.addEventListener('input', () => {
                if (!this.isTyping) {
                    this.isTyping = true;
                    this.sendTypingIndicator(true);
                }
                
                clearTimeout(typingTimer);
                typingTimer = setTimeout(() => {
                    this.isTyping = false;
                    this.sendTypingIndicator(false);
                }, 1000);
            });
            
            chatInput.addEventListener('blur', () => {
                if (this.isTyping) {
                    this.isTyping = false;
                    this.sendTypingIndicator(false);
                }
            });
        }
    }
    
    /**
     * Initialize chat widget (enhanced version)
     */
    initializeChatWidget() {
        // Get DOM elements
        const chatToggle = document.getElementById('chatToggle');
        const chatBox = document.getElementById('chatBox');
        
        // Chat widget initialization
        
        if (!chatToggle || !chatBox) {
            console.error('Chat widget elements not found!', { chatToggle, chatBox });
            return;
        }
        
        const chatClose = document.getElementById('chatClose');
        const chatMinimize = document.getElementById('chatMinimize');
        const chatSendBtn = document.getElementById('chatSendBtn');
        const chatMessageInput = document.getElementById('chatMessageInput');
        const quickBtns = document.querySelectorAll('.quick-btn');
        
        // Initialize welcome message timestamp
        this.updateMessageTime();
        
        // Event listeners
        chatToggle.addEventListener('click', () => this.toggleChatBox());
        chatClose.addEventListener('click', () => this.closeChatBox());
        chatMinimize.addEventListener('click', () => this.minimizeChatBox());
        chatSendBtn.addEventListener('click', () => this.sendMessage());
        chatMessageInput.addEventListener('keypress', (e) => this.handleInputKeypress(e));
        
        // Quick action buttons
        quickBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const message = this.getAttribute('data-message');
                if (message) {
                    chatMessageInput.value = message;
                    enhancedChat.sendMessage();
                }
            });
        });
        
        // Load chat history
        this.loadChatHistory();
        
        // Auto-scroll to bottom
        this.scrollToBottom();
    }
    
    /**
     * Send message (enhanced version)
     */
    sendMessage() {
        const input = document.getElementById('chatMessageInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Check mode restrictions
        if (this.currentMode === 'reply' && !this.lastCustomerMessage) {
            this.showErrorMessage('No message to reply to. Switch to Message mode to start a new conversation.');
            return;
        }
        
        // Clear input
        input.value = '';
        
        // Send via WebSocket or HTTP
        if (this.socket && this.isConnected) {
            this.sendMessageWS(message);
        } else {
            this.addMessageToChat(message, 'user');
            this.showTypingIndicator();
            this.sendMessageHTTP(message);
        }
        
        // Don't automatically enable reply mode - let admin choose
    }
    
    /**
     * Add message to chat interface (enhanced version)
     */
    addMessageToChat(message, sender, timestamp = null) {
        // Validate message content - don't create empty divs
        if (!message || typeof message !== 'string' || message.trim() === '') {
            console.warn('Attempted to add empty message, skipping');
            return;
        }
        
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) {
            console.error('Chat messages container not found');
            return;
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const messageTime = timestamp ? 
            new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) :
            new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const avatarIcon = this.getAvatarIcon(sender);
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${avatarIcon}"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(message.trim())}</div>
                <div class="message-time">${messageTime}</div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        
        // Store in history
        const messageData = {
            message: message.trim(),
            sender: sender,
            timestamp: timestamp || new Date().toISOString()
        };
        this.messageHistory.push(messageData);
        
        // Update last customer message for reply mode
        // Only set lastCustomerMessage when it's an AI or admin response (something to reply to)
        if (sender === 'ai' || sender === 'admin') {
            this.lastCustomerMessage = messageData;
            this.updateModeUI();
        }
        
        // Scroll to bottom
        this.scrollToBottom();
        
        // Show notification if chat is closed
        if (!this.isOpen && (sender === 'ai' || sender === 'admin')) {
            this.showChatNotification('!');
        }
    }
    
    /**
     * Get avatar icon for message sender
     */
    getAvatarIcon(sender) {
        switch (sender) {
            case 'user':
                return 'fa-user';
            case 'admin':
                return 'fa-user-shield';
            case 'ai':
            default:
                return 'fa-robot';
        }
    }
    
    /**
     * Show error message in chat
     */
    showErrorMessage(message) {
        this.addMessageToChat(`Error: ${message}`, 'ai');
    }
    
    /**
     * Generate unique session ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Get current user ID if logged in
     */
    getCurrentUserId() {
        // Try to get user ID from meta tag or global variable
        const userMeta = document.querySelector('meta[name="user-id"]');
        if (userMeta) {
            return userMeta.getAttribute('content');
        }
        
        // Check if user info is available globally
        if (window.currentUser && window.currentUser.id) {
            return window.currentUser.id;
        }
        
        return null;
    }
    
    /**
     * Detect user language preference
     */
    detectLanguage() {
        // Try to detect from HTML lang attribute
        const htmlLang = document.documentElement.lang;
        if (htmlLang) {
            return htmlLang;
        }
        
        // Try to detect from browser language
        const browserLang = navigator.language || navigator.userLanguage;
        if (browserLang) {
            return browserLang.split('-')[0]; // Get language code only
        }
        
        return 'en'; // Default to English
    }
    
    /**
     * Get CSRF token for requests
     */
    getCsrfToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Compatibility methods with existing chat widget
    toggleChatBox() {
        // Toggle chat box
        if (this.isOpen) {
            this.closeChatBox();
        } else {
            this.openChatBox();
        }
    }
    
    openChatBox() {
        // Opening chat box
        const chatBox = document.getElementById('chatBox');
        const chatToggle = document.getElementById('chatToggle');
        
        // Chat elements ready for opening
        
        if (!chatBox || !chatToggle) {
            console.error('Cannot open chat - elements not found');
            return;
        }
        
        chatBox.classList.add('show');
        chatToggle.style.transform = 'scale(0.9)';
        this.isOpen = true;
        this.isMinimized = false;
        
        // Chat box opened successfully
        
        // Focus on input
        setTimeout(() => {
            const input = document.getElementById('chatMessageInput');
            if (input) input.focus();
        }, 300);
        
        // Clear notification
        this.clearChatNotification();
    }
    
    closeChatBox() {
        const chatBox = document.getElementById('chatBox');
        const chatToggle = document.getElementById('chatToggle');
        
        chatBox.classList.remove('show');
        chatToggle.style.transform = 'scale(1)';
        this.isOpen = false;
        this.isMinimized = false;
    }
    
    minimizeChatBox() {
        this.closeChatBox();
        this.isMinimized = true;
        this.showChatNotification('−');
    }
    
    handleInputKeypress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }
    
    showTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'flex';
            this.scrollToBottom();
        }
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
    }
    
    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            setTimeout(() => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 100);
        }
    }
    
    showChatNotification(text = '!') {
        const notification = document.getElementById('chatNotification');
        if (notification) {
            notification.textContent = text;
            notification.classList.add('show');
        }
    }
    
    clearChatNotification() {
        const notification = document.getElementById('chatNotification');
        if (notification) {
            notification.classList.remove('show');
        }
    }
    
    async loadChatHistory() {
        if (this.socket && this.isConnected) {
            // Request history via WebSocket
            this.socket.emit('get_conversation_history', {
                session_id: this.sessionId
            });
        } else {
            // Fallback to HTTP
            try {
                const response = await fetch('/api/chat/history', {
                    method: 'GET',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken()
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.history && data.history.length > 0) {
                        this.loadConversationHistory(data.history);
                    }
                }
            } catch (error) {
                console.warn('Could not load chat history:', error);
            }
        }
    }
    
    updateMessageTime() {
        const timeElements = document.querySelectorAll('.message-time');
        const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        timeElements.forEach(element => {
            if (!element.textContent) {
                element.textContent = currentTime;
            }
        });
    }
    
    /**
     * Check if current user is admin
     */
    checkIfAdmin() {
        // Check for admin role in meta tag
        const userRole = document.querySelector('meta[name="user-role"]');
        if (userRole && userRole.getAttribute('content') === 'admin') {
            return true;
        }
        
        // Check for admin indicator in URL or global variable
        if (window.location.pathname.includes('/admin') || 
            (window.currentUser && window.currentUser.role === 'admin')) {
            return true;
        }
        
        // For testing purposes, temporarily return true
        // Remove this line in production
        return true;
    }
    
    /**
     * Initialize mode switching functionality
     */
    initializeModeSwitch() {
        const chatModeSwitch = document.getElementById('chatModeSwitch');
        const messageModeBtn = document.getElementById('messageModeBtn');
        const replyModeBtn = document.getElementById('replyModeBtn');
        const modeDescription = document.getElementById('modeDescription');
        
        if (!messageModeBtn || !replyModeBtn || !modeDescription || !chatModeSwitch) {
            console.warn('Mode switch elements not found');
            return;
        }
        
        // Show mode switch only for admins
        if (this.isAdmin) {
            chatModeSwitch.style.display = 'block';
        }
        
        // Event listeners for mode buttons
        messageModeBtn.addEventListener('click', () => {
            this.switchToMessageMode();
            this.updateModeUI();
        });
        
        replyModeBtn.addEventListener('click', () => {
            this.switchToReplyMode();
            this.updateModeUI();
        });
        
        // Initialize UI
        this.updateModeUI();
    }
    

    
    /**
     * Switch to message mode
     */
    switchToMessageMode() {
        this.currentMode = 'message';
        // Don't clear lastCustomerMessage - keep it for potential reply mode switch
        // Switched to message mode
    }
    
    /**
     * Switch to reply mode
     */
    switchToReplyMode() {
        if (!this.lastCustomerMessage) {
            this.showErrorMessage('No message to reply to. Please wait for a message or switch to Message mode.');
            return;
        }
        this.currentMode = 'reply';
        // Switched to reply mode
    }
    
    /**
     * Update mode UI based on current state
     */
    updateModeUI() {
        const messageModeBtn = document.getElementById('messageModeBtn');
        const replyModeBtn = document.getElementById('replyModeBtn');
        const modeDescription = document.getElementById('modeDescription');
        const chatMessageInput = document.getElementById('chatMessageInput');
        
        if (!messageModeBtn || !replyModeBtn || !modeDescription || !chatMessageInput) {
            return;
        }
        
        // Update button states
        messageModeBtn.classList.toggle('active', this.currentMode === 'message');
        replyModeBtn.classList.toggle('active', this.currentMode === 'reply');
        
        // Update description and input placeholder
        if (this.currentMode === 'message') {
            modeDescription.textContent = 'Send a new message to start conversation';
            chatMessageInput.placeholder = 'Type your message... (नेपाली वा English)';
        } else {
            if (this.lastCustomerMessage) {
                modeDescription.textContent = `Reply to: "${this.lastCustomerMessage.message.substring(0, 50)}${this.lastCustomerMessage.message.length > 50 ? '...' : ''}"`;
                chatMessageInput.placeholder = 'Type your reply... (नेपाली वा English)';
            } else {
                modeDescription.textContent = 'No message to reply to - switch to Message mode';
                chatMessageInput.placeholder = 'Switch to Message mode to start conversation';
            }
        }
    }
}

// Initialize enhanced chat widget
let enhancedChat;

// Wait for DOM and Socket.IO to be ready
function initializeEnhancedChat() {
    if (typeof io !== 'undefined' || document.readyState === 'complete') {
        enhancedChat = new EnhancedChatWidget();
        
        // Export to global scope for compatibility
        window.ChatWidget = {
            open: () => enhancedChat.openChatBox(),
            close: () => enhancedChat.closeChatBox(),
            minimize: () => enhancedChat.minimizeChatBox(),
            sendMessage: () => enhancedChat.sendMessage(),
            addMessage: (message, sender) => enhancedChat.addMessageToChat(message, sender),
            showNotification: (text) => enhancedChat.showChatNotification(text),
            clearNotification: () => enhancedChat.clearChatNotification()
        };
        
        // Override global chat functions for backward compatibility
        window.initializeChatWidget = () => enhancedChat.initializeChatWidget();
        window.sendMessage = () => enhancedChat.sendMessage();
        window.addMessageToChat = (message, sender) => enhancedChat.addMessageToChat(message, sender);
        
    } else {
        // Retry after a short delay
        setTimeout(initializeEnhancedChat, 100);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEnhancedChat);
} else {
    initializeEnhancedChat();
}

// Handle window resize for mobile responsiveness
window.addEventListener('resize', function() {
    if (enhancedChat && enhancedChat.isOpen) {
        const chatBox = document.getElementById('chatBox');
        if (window.innerWidth <= 768 && chatBox) {
            chatBox.style.width = `${window.innerWidth - 30}px`;
        }
    }
});

// Enhanced Chat Widget loaded successfully