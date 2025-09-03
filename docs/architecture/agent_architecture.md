# Agent Architecture

## Overview
The hospital assistant system uses a 3-agent architecture to handle different interaction channels while sharing a common appointment scheduling system.

## Agent Definitions

### 1. Chat Agent (`agents/chat/`)
**Purpose**: Handle text-based patient interactions
**Channels**: WhatsApp, Messenger, Website Chat

**Responsibilities**:
- Process incoming text messages
- Extract patient symptoms and preferences
- Suggest appropriate doctors based on symptoms
- Handle appointment booking flow
- Provide confirmation and pre-visit instructions
- Maintain conversation context

**Key Files**:
- `chat_agent.py` - Main chat processing logic
- `message_handler.py` - Parse and route messages
- `context_manager.py` - Maintain conversation state
- `response_generator.py` - Generate appropriate responses

### 2. Voice Agent (`agents/voice/`)
**Purpose**: Handle phone call interactions
**Channels**: Phone calls via hospital number

**Responsibilities**:
- Convert speech to text using Whisper API
- Process voice commands and natural speech
- Generate natural voice responses via ElevenLabs
- Handle real-time conversation flow
- Manage call state and interruptions
- Book appointments through voice interface

**Key Files**:
- `voice_agent.py` - Main voice processing logic
- `speech_processor.py` - Handle STT/TTS integration
- `call_manager.py` - Manage call state and flow
- `voice_response_generator.py` - Generate voice responses

### 3. Scheduler Agent (`agents/scheduler/`)
**Purpose**: Centralized appointment management
**Channels**: Shared by Chat and Voice agents

**Responsibilities**:
- Check doctor availability in real-time
- Prevent double-booking across all channels
- Update appointment slots immediately
- Generate appointment confirmations
- Send pre-visit instructions
- Handle appointment modifications/cancellations

**Key Files**:
- `scheduler_agent.py` - Main scheduling logic
- `availability_checker.py` - Real-time slot checking
- `booking_manager.py` - Handle booking operations
- `conflict_resolver.py` - Prevent scheduling conflicts

## Communication Flow

```
Patient Input → Chat/Voice Agent → Scheduler Agent → Database
                      ↓                    ↓
              Response Generator ← Appointment Confirmation
                      ↓
              Patient Response
```

## Shared Components

### RAG System (`services/rag/`)
- Real-time database queries
- Doctor information retrieval
- Patient history access
- Available slot checking

### Symptom Mapping (`utils/symptom_mapper.py`)
- Map symptoms to specialties
- Suggest appropriate doctors
- Handle complex symptom combinations

### Conflict Prevention
- Real-time slot locking
- Immediate database updates
- Cross-agent synchronization

## Agent Interaction Protocol

1. **Initialization**: All agents connect to shared database
2. **Patient Contact**: Chat/Voice agent receives patient input
3. **Processing**: Agent processes request and extracts intent
4. **Scheduling**: If appointment needed, route to Scheduler Agent
5. **Confirmation**: Scheduler Agent books and confirms
6. **Response**: Original agent sends confirmation to patient
7. **Instructions**: Pre-visit guidance sent automatically

## Error Handling

- **Database Conflicts**: Scheduler Agent handles with retry logic
- **API Failures**: Graceful degradation with fallback responses
- **Connection Issues**: Queue messages for retry
- **Double Booking**: Real-time conflict detection and resolution

## Scalability Considerations

- **Load Balancing**: Multiple instances of each agent type
- **Database Pooling**: Connection management for concurrent access
- **Message Queuing**: Handle high-volume patient interactions
- **Caching**: Frequent queries cached for performance