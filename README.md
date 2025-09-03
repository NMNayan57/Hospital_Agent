# X Hospital AI Assistant

AI-powered hospital assistant system for handling patient interactions via chat and phone calls with real-time appointment booking.

## Features

- **Multi-Channel Support**: WhatsApp, Messenger, website chat, and phone calls
- **Smart Doctor Recommendations**: Symptom-based doctor suggestions
- **Real-Time Appointment Booking**: Prevents double-booking across all channels
- **Voice Integration**: Natural phone conversations with ElevenLabs TTS and Whisper STT
- **Pre-Visit Guidance**: Doctor-specific instructions after booking

## Architecture

### 3-Agent System
1. **Chat Agent** - Handles text-based interactions (WhatsApp, Messenger, Web)
2. **Voice Agent** - Manages phone calls with speech-to-text/text-to-speech
3. **Scheduler Agent** - Coordinates appointments and prevents conflicts

### Tech Stack
- **AI/ML**: OpenAI GPT API, Whisper API
- **Voice**: ElevenLabs API for text-to-speech
- **Database**: SQLite for demo data
- **RAG**: Real-time data retrieval system
- **Backend**: Python with FastAPI
- **Frontend**: React (for web chat interface)

## Demo Data

### Doctors
- **Dr. Rahman** (Cardiologist): Mon–Thu, 6:00 PM – 8:00 PM
- **Dr. Ayesha** (Gastroenterologist): Sat–Tue, 4:00 PM – 6:00 PM  
- **Dr. Karim** (General Physician): Every day, 10:00 AM – 2:00 PM

### Symptom Mapping
- Chest pain → Cardiologist
- Fever + cough → General Physician
- Stomach pain → Gastroenterologist

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 16+
- OpenAI API key
- ElevenLabs API key

### Installation
```bash
# Clone repository
git clone <repository-url>
cd hospital-agents

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies (for web interface)
cd frontend
npm install
cd ..

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables
```
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
WHISPER_API_KEY=your_whisper_api_key
DATABASE_URL=sqlite:///./hospital.db
```

### Running the Application
```bash
# Start the backend
python main.py

# Start the frontend (in another terminal)
cd frontend
npm start
```

## Project Structure
```
hospital-agents/
├── agents/           # Chat, Voice, and Scheduler agents
├── database/         # SQLite database and demo data
├── services/         # OpenAI, ElevenLabs, RAG services
├── models/           # Data schemas and models
├── utils/            # Helper functions and utilities
├── config/           # Configuration and settings
├── frontend/         # React web interface
├── tests/            # Unit and integration tests
└── docs/             # Documentation
```

## API Endpoints

- `POST /chat` - Handle chat messages
- `POST /voice/call` - Process voice calls
- `GET /doctors` - Get doctor availability
- `POST /appointments` - Book appointments
- `GET /appointments/{patient_id}` - Get patient bookings

## Development

### Running Tests
```bash
pytest tests/
```

### Database Migration
```bash
python scripts/init_db.py
```

## Demo Usage

1. **Chat Booking**: Send message "I need to see a doctor for chest pain"
2. **Voice Booking**: Call the hospital number and speak naturally
3. **System Response**: AI suggests cardiologist and available slots
4. **Confirmation**: Provides appointment details and pre-visit instructions

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request