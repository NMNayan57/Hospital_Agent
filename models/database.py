from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Time, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hospital.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False)
    phone = Column(String(15))
    email = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    schedules = relationship("DoctorSchedule", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")
    time_slots = relationship("TimeSlot", back_populates="doctor")

class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Sunday, 6=Saturday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    doctor = relationship("Doctor", back_populates="schedules")

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False, unique=True, index=True)
    email = Column(String(100))
    date_of_birth = Column(Date)
    gender = Column(String(10))
    address = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    appointments = relationship("Appointment", back_populates="patient")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(String(20), default="scheduled")
    symptoms = Column(Text)
    notes = Column(Text)
    serial_number = Column(String(10), nullable=False, unique=True)
    booking_channel = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")

class Specialty(Base):
    __tablename__ = "specialties"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    pre_visit_instructions = Column(Text)
    
    # Relationships
    symptom_mappings = relationship("SymptomMapping", back_populates="specialty")
    pre_visit_instructions_rel = relationship("PreVisitInstruction", back_populates="specialty")

class SymptomMapping(Base):
    __tablename__ = "symptom_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    symptom_keywords = Column(Text, nullable=False)  # JSON array
    specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=False)
    priority = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    specialty = relationship("Specialty", back_populates="symptom_mappings")

class TimeSlot(Base):
    __tablename__ = "time_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    slot_date = Column(Date, nullable=False)
    slot_time = Column(Time, nullable=False)
    is_available = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    doctor = relationship("Doctor", back_populates="time_slots")

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_phone = Column(String(15), nullable=False, index=True)
    channel = Column(String(20), nullable=False)
    message_type = Column(String(10), nullable=False)
    message_content = Column(Text, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    session_id = Column(String(50), index=True)

class PreVisitInstruction(Base):
    __tablename__ = "pre_visit_instructions"
    
    id = Column(Integer, primary_key=True, index=True)
    specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=False)
    instruction_text = Column(Text, nullable=False)
    instruction_type = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    specialty = relationship("Specialty", back_populates="pre_visit_instructions_rel")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)