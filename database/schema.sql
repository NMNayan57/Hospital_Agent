-- X Hospital Database Schema

-- Doctors table
CREATE TABLE doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Doctor schedules table
CREATE TABLE doctor_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL, -- 0=Sunday, 1=Monday, etc.
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

-- Patients table
CREATE TABLE patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(10),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Appointments table
CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, completed, cancelled, no_show
    symptoms TEXT,
    notes TEXT,
    serial_number VARCHAR(10) NOT NULL UNIQUE,
    booking_channel VARCHAR(20) NOT NULL, -- chat, voice, web
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

-- Specialties table
CREATE TABLE specialties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    pre_visit_instructions TEXT
);

-- Symptom mappings table
CREATE TABLE symptom_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symptom_keywords TEXT NOT NULL, -- JSON array of keywords
    specialty_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 1, -- Higher number = higher priority
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (specialty_id) REFERENCES specialties(id)
);

-- Time slots table (for tracking availability)
CREATE TABLE time_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    slot_date DATE NOT NULL,
    slot_time TIME NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    is_blocked BOOLEAN DEFAULT FALSE, -- Manual blocking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id),
    UNIQUE(doctor_id, slot_date, slot_time)
);

-- Conversation history table
CREATE TABLE conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_phone VARCHAR(15) NOT NULL,
    channel VARCHAR(20) NOT NULL, -- chat, voice
    message_type VARCHAR(10) NOT NULL, -- user, assistant
    message_content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(50)
);

-- Pre-visit instructions table
CREATE TABLE pre_visit_instructions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    specialty_id INTEGER NOT NULL,
    instruction_text TEXT NOT NULL,
    instruction_type VARCHAR(50), -- fasting, preparation, documents
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (specialty_id) REFERENCES specialties(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_appointments_date_doctor ON appointments(appointment_date, doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_time_slots_doctor_date ON time_slots(doctor_id, slot_date);
CREATE INDEX IF NOT EXISTS idx_conversation_patient_time ON conversation_history(patient_phone, timestamp);
CREATE INDEX IF NOT EXISTS idx_doctor_schedules_doctor ON doctor_schedules(doctor_id, day_of_week);

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_doctors_timestamp 
    AFTER UPDATE ON doctors
    BEGIN
        UPDATE doctors SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER update_patients_timestamp 
    AFTER UPDATE ON patients
    BEGIN
        UPDATE patients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER update_appointments_timestamp 
    AFTER UPDATE ON appointments
    BEGIN
        UPDATE appointments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER update_time_slots_timestamp 
    AFTER UPDATE ON time_slots
    BEGIN
        UPDATE time_slots SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;