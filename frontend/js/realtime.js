// Real-time WebSocket functionality for X Hospital AI Assistant

class HospitalWebSocketManager {
    constructor() {
        this.chatSocket = null;
        this.voiceSocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;
    }

    // Chat WebSocket Management
    async connectChatWebSocket(phoneNumber) {
        const wsUrl = `ws://localhost:8000/ws/chat?phone_number=${encodeURIComponent(phoneNumber)}`;
        
        try {
            this.chatSocket = new WebSocket(wsUrl);
            
            this.chatSocket.onopen = () => {
                console.log('Chat WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('chat', 'connected');
            };
            
            this.chatSocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleChatMessage(data);
            };
            
            this.chatSocket.onclose = () => {
                console.log('Chat WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus('chat', 'disconnected');
                this.attemptReconnect('chat', phoneNumber);
            };
            
            this.chatSocket.onerror = (error) => {
                console.error('Chat WebSocket error:', error);
                this.updateConnectionStatus('chat', 'error');
            };
            
        } catch (error) {
            console.error('Failed to connect chat WebSocket:', error);
            this.updateConnectionStatus('chat', 'error');
        }
    }

    async connectVoiceWebSocket(phoneNumber) {
        const wsUrl = `ws://localhost:8000/ws/voice?phone_number=${encodeURIComponent(phoneNumber)}`;
        
        try {
            this.voiceSocket = new WebSocket(wsUrl);
            
            this.voiceSocket.onopen = () => {
                console.log('Voice WebSocket connected');
                this.updateConnectionStatus('voice', 'connected');
                
                // Request voice capabilities
                this.sendVoiceMessage({
                    type: 'get_capabilities'
                });
            };
            
            this.voiceSocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleVoiceMessage(data);
            };
            
            this.voiceSocket.onclose = () => {
                console.log('Voice WebSocket disconnected');
                this.updateConnectionStatus('voice', 'disconnected');
                this.attemptReconnect('voice', phoneNumber);
            };
            
            this.voiceSocket.onerror = (error) => {
                console.error('Voice WebSocket error:', error);
                this.updateConnectionStatus('voice', 'error');
            };
            
        } catch (error) {
            console.error('Failed to connect voice WebSocket:', error);
            this.updateConnectionStatus('voice', 'error');
        }
    }

    sendChatMessage(message) {
        if (this.chatSocket && this.chatSocket.readyState === WebSocket.OPEN) {
            this.chatSocket.send(JSON.stringify({
                type: 'chat_message',
                message: message,
                timestamp: new Date().toISOString()
            }));
            return true;
        }
        return false;
    }

    sendVoiceMessage(data) {
        if (this.voiceSocket && this.voiceSocket.readyState === WebSocket.OPEN) {
            this.voiceSocket.send(JSON.stringify({
                ...data,
                timestamp: new Date().toISOString()
            }));
            return true;
        }
        return false;
    }

    handleChatMessage(data) {
        switch (data.type) {
            case 'system':
                console.log('System message:', data.message);
                break;
                
            case 'typing':
                this.showTypingIndicator();
                break;
                
            case 'chat_response':
                this.hideTypingIndicator();
                this.displayChatResponse(data.message, data.suggested_actions);
                break;
                
            case 'error':
                this.displayChatError(data.message);
                break;
                
            case 'pong':
                // Keep-alive response
                break;
                
            default:
                console.log('Unknown chat message type:', data.type);
        }
    }

    handleVoiceMessage(data) {
        switch (data.type) {
            case 'voice_capabilities':
                this.updateVoiceCapabilities(data.capabilities);
                break;
                
            case 'voice_processing':
                this.showVoiceProcessing(data.message);
                break;
                
            case 'voice_response':
                this.displayVoiceResponse(data.transcript, data.audio_response);
                break;
                
            case 'real_time_ready':
                this.enableRealTimeVoice();
                break;
                
            case 'error':
                this.displayVoiceError(data.message);
                break;
                
            default:
                console.log('Unknown voice message type:', data.type);
        }
    }

    attemptReconnect(type, phoneNumber) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * this.reconnectAttempts;
            
            console.log(`Attempting to reconnect ${type} in ${delay}ms (attempt ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                if (type === 'chat') {
                    this.connectChatWebSocket(phoneNumber);
                } else if (type === 'voice') {
                    this.connectVoiceWebSocket(phoneNumber);
                }
            }, delay);
        } else {
            console.error(`Max reconnection attempts reached for ${type}`);
            this.updateConnectionStatus(type, 'failed');
        }
    }

    updateConnectionStatus(type, status) {
        const statusElement = document.getElementById(`${type}ConnectionStatus`);
        if (statusElement) {
            const statusMessages = {
                connected: 'Connected and ready',
                disconnected: 'Disconnected',
                error: 'Connection error',
                failed: 'Connection failed'
            };
            
            statusElement.textContent = statusMessages[status] || status;
            
            // Update visual indicators
            const indicator = statusElement.parentElement?.querySelector('.status-dot');
            if (indicator) {
                indicator.className = `status-dot ${status}`;
            }
        }
    }

    // UI Update Methods
    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        
        // Remove existing typing indicator
        this.hideTypingIndicator();
        
        // Add new typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-animation">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        typingDiv.id = 'typingIndicator';
        
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    displayChatResponse(message, suggestedActions) {
        const messagesContainer = document.getElementById('chatMessages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.textContent = message;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Show suggested actions if available
        if (suggestedActions && suggestedActions.length > 0) {
            this.showSuggestedActions(suggestedActions);
        }
    }

    displayChatError(message) {
        const messagesContainer = document.getElementById('chatMessages');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message assistant error';
        errorDiv.textContent = `Error: ${message}`;
        errorDiv.style.borderLeft = '4px solid #f44336';
        
        messagesContainer.appendChild(errorDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showSuggestedActions(actions) {
        // Create or update suggested actions container
        let actionsContainer = document.getElementById('suggestedActions');
        
        if (!actionsContainer) {
            actionsContainer = document.createElement('div');
            actionsContainer.id = 'suggestedActions';
            actionsContainer.className = 'suggested-actions';
            
            const chatContainer = document.querySelector('.chat-container');
            chatContainer.insertBefore(actionsContainer, chatContainer.lastElementChild);
        }
        
        actionsContainer.innerHTML = '';
        
        actions.forEach(action => {
            const actionBtn = document.createElement('button');
            actionBtn.className = 'suggested-action-btn';
            actionBtn.textContent = action;
            actionBtn.onclick = () => {
                this.sendChatMessage(action);
                actionsContainer.style.display = 'none';
            };
            
            actionsContainer.appendChild(actionBtn);
        });
        
        actionsContainer.style.display = 'flex';
    }

    // Voice UI Methods
    updateVoiceCapabilities(capabilities) {
        console.log('Voice capabilities:', capabilities);
        
        const voiceStatus = document.getElementById('voiceStatus');
        const hasSpeechmatics = capabilities.speech_to_text?.speechmatics?.available;
        
        if (hasSpeechmatics) {
            voiceStatus.textContent = 'Enhanced voice processing available - Click to start';
        } else {
            voiceStatus.textContent = 'Basic voice processing - Click to start';
        }
    }

    showVoiceProcessing(message) {
        const voiceStatus = document.getElementById('voiceStatus');
        const voiceConnectionStatus = document.getElementById('voiceConnectionStatus');
        
        if (voiceStatus) voiceStatus.textContent = message;
        if (voiceConnectionStatus) voiceConnectionStatus.textContent = 'Processing...';
    }

    displayVoiceResponse(transcript, audioResponse) {
        const voiceTranscript = document.getElementById('voiceTranscript');
        
        if (voiceTranscript) {
            voiceTranscript.innerHTML = `
                <div style="margin-bottom: 15px;">
                    <strong>Assistant Response:</strong>
                    <div style="background: #f0f8ff; padding: 10px; border-radius: 8px; margin-top: 5px;">
                        ${transcript}
                    </div>
                </div>
            `;
        }
        
        // Play audio response
        if (audioResponse) {
            this.playAudioResponse(audioResponse);
        }
        
        // Reset UI
        this.resetVoiceUI();
    }

    displayVoiceError(message) {
        const voiceTranscript = document.getElementById('voiceTranscript');
        
        if (voiceTranscript) {
            voiceTranscript.innerHTML = `
                <div style="color: #f44336; padding: 15px; text-align: center;">
                    <strong>Error:</strong> ${message}
                </div>
            `;
        }
        
        this.resetVoiceUI();
    }

    playAudioResponse(base64Audio) {
        try {
            const audio = new Audio(`data:audio/mpeg;base64,${base64Audio}`);
            audio.play();
            
            const voiceConnectionStatus = document.getElementById('voiceConnectionStatus');
            if (voiceConnectionStatus) {
                voiceConnectionStatus.textContent = 'Playing response';
            }
            
            audio.onended = () => {
                if (voiceConnectionStatus) {
                    voiceConnectionStatus.textContent = 'Ready to listen';
                }
            };
        } catch (error) {
            console.error('Audio playback error:', error);
        }
    }

    resetVoiceUI() {
        const voiceButton = document.getElementById('voiceButton');
        const voiceStatus = document.getElementById('voiceStatus');
        const voiceConnectionStatus = document.getElementById('voiceConnectionStatus');
        
        if (voiceButton) {
            voiceButton.className = 'voice-button idle';
            voiceButton.textContent = '🎤';
        }
        
        if (voiceStatus) {
            voiceStatus.textContent = 'Click the microphone to start speaking';
        }
        
        if (voiceConnectionStatus) {
            voiceConnectionStatus.textContent = 'Ready to listen';
        }
    }

    // Keep-alive ping
    startKeepAlive() {
        setInterval(() => {
            if (this.chatSocket && this.chatSocket.readyState === WebSocket.OPEN) {
                this.chatSocket.send(JSON.stringify({ type: 'ping' }));
            }
            
            if (this.voiceSocket && this.voiceSocket.readyState === WebSocket.OPEN) {
                this.voiceSocket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000); // Ping every 30 seconds
    }

    // Cleanup
    disconnect() {
        if (this.chatSocket) {
            this.chatSocket.close();
            this.chatSocket = null;
        }
        
        if (this.voiceSocket) {
            this.voiceSocket.close();
            this.voiceSocket = null;
        }
        
        this.isConnected = false;
    }
}

// Export for use in main application
window.HospitalWebSocketManager = HospitalWebSocketManager;