from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class BookingChannel(str, Enum):
    CHAT = "chat"
    VOICE = "voice"
    WEB = "web"

class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class InstructionType(str, Enum):
    DOCUMENTS = "documents"
    PREPARATION = "preparation"
    FASTING = "fasting"

# Doctor Models
class DoctorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    specialty: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)

class DoctorCreate(DoctorBase):
    pass

class Doctor(DoctorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Doctor Schedule Models
class DoctorScheduleBase(BaseModel):
    doctor_id: int
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Sunday, 6=Saturday
    start_time: time
    end_time: time
    is_active: bool = True

class DoctorScheduleCreate(DoctorScheduleBase):
    pass

class DoctorSchedule(DoctorScheduleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Patient Models
class PatientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Appointment Models
class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: date
    appointment_time: time
    duration_minutes: int = 30
    symptoms: Optional[str] = None
    notes: Optional[str] = None
    booking_channel: BookingChannel

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None

class Appointment(AppointmentBase):
    id: int
    status: AppointmentStatus
    serial_number: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Specialty Models
class SpecialtyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    pre_visit_instructions: Optional[str] = None

class SpecialtyCreate(SpecialtyBase):
    pass

class Specialty(SpecialtyBase):
    id: int

    class Config:
        from_attributes = True

# Symptom Mapping Models
class SymptomMappingBase(BaseModel):
    symptom_keywords: str  # JSON array string
    specialty_id: int
    priority: int = 1

class SymptomMappingCreate(SymptomMappingBase):
    pass

class SymptomMapping(SymptomMappingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Conversation History Models
class ConversationHistoryBase(BaseModel):
    patient_phone: str = Field(..., max_length=15)
    channel: BookingChannel
    message_type: MessageType
    message_content: str
    session_id: Optional[str] = Field(None, max_length=50)

class ConversationHistoryCreate(ConversationHistoryBase):
    pass

class ConversationHistory(ConversationHistoryBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Time Slot Models
class TimeSlotBase(BaseModel):
    doctor_id: int
    slot_date: date
    slot_time: time
    is_available: bool = True
    is_blocked: bool = False

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlot(TimeSlotBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Chat Request/Response Models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    phone_number: str = Field(..., min_length=10, max_length=15)
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    suggested_actions: Optional[List[str]] = None

# Voice Request/Response Models
class VoiceRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    phone_number: str = Field(..., min_length=10, max_length=15)
    session_id: Optional[str] = None

class VoiceResponse(BaseModel):
    response_text: str
    audio_response: str  # Base64 encoded audio
    session_id: str
    emotion_context: Optional[dict] = None  # Detected emotion information

# Appointment Booking Request
class AppointmentBookingRequest(BaseModel):
    patient_name: str = Field(..., min_length=1)
    patient_phone: str = Field(..., min_length=10, max_length=15)
    symptoms: str = Field(..., min_length=1)
    preferred_date: Optional[date] = None
    preferred_time: Optional[time] = None
    booking_channel: BookingChannel

class AppointmentBookingResponse(BaseModel):
    success: bool
    appointment: Optional[Appointment] = None
    message: str
    suggested_doctors: Optional[List[Doctor]] = None
    available_slots: Optional[List[dict]] = None

# Doctor Availability Request
class DoctorAvailabilityRequest(BaseModel):
    doctor_id: Optional[int] = None
    specialty: Optional[str] = None
    date: Optional[date] = None

class DoctorAvailabilityResponse(BaseModel):
    doctors: List[Doctor]
    available_slots: List[dict]

# Symptom Analysis Request
class SymptomAnalysisRequest(BaseModel):
    symptoms: str = Field(..., min_length=1)

class SymptomAnalysisResponse(BaseModel):
    recommended_specialties: List[Specialty]
    suggested_doctors: List[Doctor]
    urgency_level: str = Field(..., description="low, medium, high")
    explanation: str