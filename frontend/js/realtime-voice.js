/**
 * Real-time Voice Assistant - Hospital AI
 * Inspired by GPT Voice Assistant, Siri, and modern voice interfaces
 * Features: VAD, continuous conversation, real-time processing
 */

class HospitalVoiceAssistant {
    constructor() {
        this.isListening = false;
        this.isProcessing = false;
        this.isSpeaking = false;
        this.stream = null;
        this.audioContext = null;
        this.processor = null;
        this.websocket = null;
        this.vadThreshold = 0.01;
        this.silenceDuration = 0;
        this.maxSilence = 1500; // 1.5 seconds of silence to trigger processing
        this.minRecordingTime = 500; // Minimum 0.5 seconds before processing
        this.recordingStartTime = 0;
        this.audioChunks = [];
        this.conversationHistory = [];
        
        // Voice Activity Detection
        this.vadAnalyzer = null;
        this.vadDataArray = null;
        
        // Audio playback
        this.audioQueue = [];
        this.isPlayingAudio = false;
        
        // UI elements
        this.statusElement = null;
        this.transcriptElement = null;
        this.connectionElement = null;
        this.visualizer = null;
        
        // Configuration
        this.phoneNumber = null;
        this.sessionId = null;
        
        this.initializeAudio();
        this.setupEventListeners();
    }
    
    async initializeAudio() {
        try {
            // Initialize audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Request microphone access
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            console.log('🎤 Microphone access granted');
            this.setupAudioProcessing();
            this.setupVoiceActivityDetection();
            
        } catch (error) {
            console.error('❌ Error initializing audio:', error);
            this.updateStatus('Microphone access denied', 'error');
        }
    }
    
    setupAudioProcessing() {
        // Create audio processing nodes
        const source = this.audioContext.createMediaStreamSource(this.stream);
        this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
        
        // Connect nodes
        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);
        
        // Process audio chunks
        this.processor.onaudioprocess = (e) => {
            if (!this.isListening || this.isSpeaking) return;
            
            const inputData = e.inputBuffer.getChannelData(0);
            this.processAudioChunk(inputData);
        };
    }
    
    setupVoiceActivityDetection() {
        // Create analyzer for VAD
        const source = this.audioContext.createMediaStreamSource(this.stream);
        this.vadAnalyzer = this.audioContext.createAnalyser();
        this.vadAnalyzer.fftSize = 256;
        this.vadDataArray = new Uint8Array(this.vadAnalyzer.frequencyBinCount);
        
        source.connect(this.vadAnalyzer);
        
        // Start VAD loop
        this.vadLoop();
    }
    
    vadLoop() {
        if (!this.vadAnalyzer) return;
        
        this.vadAnalyzer.getByteFrequencyData(this.vadDataArray);
        
        // Calculate audio level
        let sum = 0;
        for (let i = 0; i < this.vadDataArray.length; i++) {
            sum += this.vadDataArray[i];
        }\n        const average = sum / this.vadDataArray.length / 255;\n        \n        this.updateVisualizer(average);\n        \n        if (this.isListening && !this.isSpeaking) {\n            this.detectVoiceActivity(average);\n        }\n        \n        requestAnimationFrame(() => this.vadLoop());\n    }\n    \n    detectVoiceActivity(level) {\n        const now = Date.now();\n        \n        if (level > this.vadThreshold) {\n            // Voice detected\n            if (this.silenceDuration > 0) {\n                console.log('🗣️ Voice activity detected');\n                this.updateStatus('Listening...', 'listening');\n            }\n            \n            this.silenceDuration = 0;\n            \n            if (!this.recordingStartTime) {\n                this.recordingStartTime = now;\n                this.audioChunks = [];\n            }\n        } else {\n            // Silence detected\n            if (this.recordingStartTime && !this.isProcessing) {\n                this.silenceDuration += 16; // ~16ms per frame\n                \n                // Check if we should process the audio\n                const recordingDuration = now - this.recordingStartTime;\n                \n                if (this.silenceDuration >= this.maxSilence && \n                    recordingDuration >= this.minRecordingTime && \n                    this.audioChunks.length > 0) {\n                    \n                    console.log('🔇 Silence detected, processing audio');\n                    this.processRecordedAudio();\n                }\n            }\n        }\n    }\n    \n    processAudioChunk(audioData) {\n        if (this.recordingStartTime) {\n            // Convert to 16-bit PCM\n            const buffer = new ArrayBuffer(audioData.length * 2);\n            const view = new DataView(buffer);\n            \n            for (let i = 0; i < audioData.length; i++) {\n                const sample = Math.max(-1, Math.min(1, audioData[i]));\n                view.setInt16(i * 2, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);\n            }\n            \n            this.audioChunks.push(new Uint8Array(buffer));\n        }\n    }\n    \n    async processRecordedAudio() {\n        if (this.isProcessing || this.audioChunks.length === 0) return;\n        \n        this.isProcessing = true;\n        this.updateStatus('Processing...', 'processing');\n        \n        try {\n            // Combine audio chunks\n            const totalLength = this.audioChunks.reduce((sum, chunk) => sum + chunk.length, 0);\n            const combinedAudio = new Uint8Array(totalLength);\n            let offset = 0;\n            \n            for (const chunk of this.audioChunks) {\n                combinedAudio.set(chunk, offset);\n                offset += chunk.length;\n            }\n            \n            // Convert to base64\n            const audioBase64 = btoa(String.fromCharCode(...combinedAudio));\n            \n            // Send to backend for processing\n            await this.sendAudioToBackend(audioBase64);\n            \n        } catch (error) {\n            console.error('❌ Error processing audio:', error);\n            this.updateStatus('Processing error', 'error');\n        } finally {\n            // Reset for next recording\n            this.recordingStartTime = 0;\n            this.audioChunks = [];\n            this.silenceDuration = 0;\n            this.isProcessing = false;\n        }\n    }\n    \n    async sendAudioToBackend(audioBase64) {\n        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {\n            await this.connectWebSocket();\n        }\n        \n        const message = {\n            type: 'voice_input',\n            audio_data: audioBase64,\n            phone_number: this.phoneNumber,\n            session_id: this.sessionId,\n            timestamp: Date.now()\n        };\n        \n        this.websocket.send(JSON.stringify(message));\n        console.log('📤 Sent audio to backend');\n    }\n    \n    async connectWebSocket() {\n        return new Promise((resolve, reject) => {\n            const wsUrl = `ws://localhost:8000/ws/voice?phone_number=${encodeURIComponent(this.phoneNumber || '+8801742957256')}`;\n            \n            this.websocket = new WebSocket(wsUrl);\n            \n            this.websocket.onopen = () => {\n                console.log('🔌 Voice WebSocket connected');\n                this.updateConnectionStatus('Connected', 'connected');\n                resolve();\n            };\n            \n            this.websocket.onmessage = (event) => {\n                this.handleWebSocketMessage(JSON.parse(event.data));\n            };\n            \n            this.websocket.onerror = (error) => {\n                console.error('❌ WebSocket error:', error);\n                this.updateConnectionStatus('Connection error', 'error');\n                reject(error);\n            };\n            \n            this.websocket.onclose = () => {\n                console.log('🔌 WebSocket disconnected');\n                this.updateConnectionStatus('Disconnected', 'disconnected');\n                \n                // Auto-reconnect after 3 seconds\n                setTimeout(() => {\n                    if (this.isListening) {\n                        this.connectWebSocket();\n                    }\n                }, 3000);\n            };\n        });\n    }\n    \n    handleWebSocketMessage(message) {\n        console.log('📥 Received message:', message);\n        \n        switch (message.type) {\n            case 'transcription':\n                this.displayTranscription(message.text);\n                break;\n                \n            case 'voice_response':\n                this.handleVoiceResponse(message);\n                break;\n                \n            case 'error':\n                this.updateStatus(`Error: ${message.message}`, 'error');\n                break;\n                \n            case 'system':\n                console.log('ℹ️ System message:', message.message);\n                break;\n                \n            default:\n                console.log('❓ Unknown message type:', message.type);\n        }\n    }\n    \n    displayTranscription(text) {\n        if (this.transcriptElement) {\n            this.transcriptElement.textContent = `You: ${text}`;\n        }\n        console.log('📝 Transcription:', text);\n    }\n    \n    async handleVoiceResponse(message) {\n        console.log('🤖 AI Response:', message.text);\n        \n        if (this.transcriptElement) {\n            this.transcriptElement.innerHTML += `<br><strong>AI:</strong> ${message.text}`;\n        }\n        \n        // Add to conversation history\n        this.conversationHistory.push({\n            type: 'ai_response',\n            text: message.text,\n            timestamp: Date.now(),\n            emotion: message.emotion_context\n        });\n        \n        // Play audio response if available\n        if (message.audio_data) {\n            await this.playAudioResponse(message.audio_data);\n        }\n        \n        // Resume listening after response\n        setTimeout(() => {\n            if (this.isListening) {\n                this.updateStatus('Listening...', 'listening');\n            }\n        }, 500);\n    }\n    \n    async playAudioResponse(audioBase64) {\n        try {\n            this.isSpeaking = true;\n            this.updateStatus('AI Speaking...', 'speaking');\n            \n            // Convert base64 to audio buffer\n            const audioData = atob(audioBase64);\n            const arrayBuffer = new ArrayBuffer(audioData.length);\n            const uint8Array = new Uint8Array(arrayBuffer);\n            \n            for (let i = 0; i < audioData.length; i++) {\n                uint8Array[i] = audioData.charCodeAt(i);\n            }\n            \n            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);\n            const source = this.audioContext.createBufferSource();\n            source.buffer = audioBuffer;\n            source.connect(this.audioContext.destination);\n            \n            // Play audio\n            source.start();\n            \n            source.onended = () => {\n                this.isSpeaking = false;\n                console.log('🔊 Audio playback finished');\n            };\n            \n        } catch (error) {\n            console.error('❌ Error playing audio:', error);\n            this.isSpeaking = false;\n        }\n    }\n    \n    // Public methods\n    async startListening(phoneNumber = null) {\n        if (this.isListening) return;\n        \n        this.phoneNumber = phoneNumber || this.phoneNumber || '+8801742957256';\n        this.sessionId = this.generateSessionId();\n        \n        try {\n            await this.connectWebSocket();\n            \n            this.isListening = true;\n            this.updateStatus('Listening... Speak naturally', 'listening');\n            \n            console.log('👂 Started continuous listening');\n            \n        } catch (error) {\n            console.error('❌ Error starting voice assistant:', error);\n            this.updateStatus('Failed to start', 'error');\n        }\n    }\n    \n    stopListening() {\n        this.isListening = false;\n        this.isProcessing = false;\n        this.isSpeaking = false;\n        \n        if (this.websocket) {\n            this.websocket.close();\n        }\n        \n        this.updateStatus('Stopped', 'stopped');\n        console.log('🛑 Stopped listening');\n    }\n    \n    // UI Updates\n    setUIElements(statusElement, transcriptElement, connectionElement, visualizer) {\n        this.statusElement = statusElement;\n        this.transcriptElement = transcriptElement;\n        this.connectionElement = connectionElement;\n        this.visualizer = visualizer;\n    }\n    \n    updateStatus(message, type = 'info') {\n        if (this.statusElement) {\n            this.statusElement.textContent = message;\n            this.statusElement.className = `status ${type}`;\n        }\n        console.log(`📊 Status: ${message} (${type})`);\n    }\n    \n    updateConnectionStatus(message, type = 'info') {\n        if (this.connectionElement) {\n            this.connectionElement.textContent = message;\n            this.connectionElement.className = `connection-status ${type}`;\n        }\n    }\n    \n    updateVisualizer(level) {\n        if (this.visualizer) {\n            const intensity = Math.min(100, level * 200);\n            this.visualizer.style.width = `${intensity}%`;\n            this.visualizer.style.backgroundColor = level > this.vadThreshold ? '#4CAF50' : '#ddd';\n        }\n    }\n    \n    // Utilities\n    generateSessionId() {\n        return 'voice_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);\n    }\n    \n    // Configuration\n    setVADThreshold(threshold) {\n        this.vadThreshold = threshold;\n    }\n    \n    setSilenceTimeout(timeout) {\n        this.maxSilence = timeout;\n    }\n    \n    // Cleanup\n    destroy() {\n        this.stopListening();\n        \n        if (this.stream) {\n            this.stream.getTracks().forEach(track => track.stop());\n        }\n        \n        if (this.audioContext) {\n            this.audioContext.close();\n        }\n    }\n    \n    setupEventListeners() {\n        // Handle page visibility changes\n        document.addEventListener('visibilitychange', () => {\n            if (document.hidden && this.isListening) {\n                console.log('📱 Page hidden, maintaining connection');\n            }\n        });\n        \n        // Handle beforeunload\n        window.addEventListener('beforeunload', () => {\n            this.destroy();\n        });\n    }\n}\n\n// Export for global use\nif (typeof window !== 'undefined') {\n    window.HospitalVoiceAssistant = HospitalVoiceAssistant;\n}"