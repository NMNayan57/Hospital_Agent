import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models.database import Doctor, Specialty, SymptomMapping, TimeSlot, Appointment, PreVisitInstruction
from datetime import datetime, date, time, timedelta
import re

class RAGService:
    def __init__(self, db: Session):
        self.db = db
    
    def search_doctors_by_specialty(self, specialty: str) -> List[Dict]:
        """Find doctors by specialty name"""
        doctors = self.db.query(Doctor).filter(
            Doctor.specialty.ilike(f"%{specialty}%")
        ).all()
        
        return [self._doctor_to_dict(doctor) for doctor in doctors]
    
    def search_doctors_by_symptoms(self, symptoms: str) -> List[Dict]:
        """Find appropriate doctors based on symptoms"""
        symptoms_lower = symptoms.lower()
        
        # Get all symptom mappings
        symptom_mappings = self.db.query(SymptomMapping).all()
        
        specialty_scores = {}
        
        for mapping in symptom_mappings:
            keywords = json.loads(mapping.symptom_keywords)
            score = 0
            
            for keyword in keywords:
                if keyword.lower() in symptoms_lower:
                    score += mapping.priority
            
            if score > 0:
                if mapping.specialty_id not in specialty_scores:
                    specialty_scores[mapping.specialty_id] = 0
                specialty_scores[mapping.specialty_id] += score
        
        # Get top specialties
        sorted_specialties = sorted(
            specialty_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        # Find doctors for top specialties
        recommended_doctors = []
        for specialty_id, score in sorted_specialties:
            specialty = self.db.query(Specialty).filter(
                Specialty.id == specialty_id
            ).first()
            
            if specialty:
                doctors = self.db.query(Doctor).filter(
                    Doctor.specialty == specialty.name
                ).all()
                
                for doctor in doctors:
                    doctor_dict = self._doctor_to_dict(doctor)
                    doctor_dict['match_score'] = score
                    doctor_dict['specialty_info'] = {
                        'name': specialty.name,
                        'description': specialty.description,
                        'instructions': specialty.pre_visit_instructions
                    }
                    recommended_doctors.append(doctor_dict)
        
        return recommended_doctors
    
    def get_doctor_availability(self, doctor_id: int, start_date: date = None, days: int = 7) -> List[Dict]:
        """Get available slots for a doctor"""
        if start_date is None:
            start_date = date.today()
        
        end_date = start_date + timedelta(days=days)
        
        # Get doctor's schedule
        doctor = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            return []
        
        schedules = self.db.query(Doctor).filter(Doctor.id == doctor_id).first().schedules
        
        available_slots = []
        current_date = start_date
        
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            # Convert Python weekday (Monday=0) to our format (Sunday=0)
            day_of_week = (day_of_week + 1) % 7
            
            # Find schedule for this day
            day_schedule = None
            for schedule in schedules:
                if schedule.day_of_week == day_of_week and schedule.is_active:
                    day_schedule = schedule
                    break
            
            if day_schedule:
                # Generate time slots
                current_time = datetime.combine(current_date, day_schedule.start_time)
                end_time = datetime.combine(current_date, day_schedule.end_time)
                
                while current_time < end_time:
                    slot_time = current_time.time()
                    
                    # Check if slot is available
                    existing_appointment = self.db.query(Appointment).filter(
                        Appointment.doctor_id == doctor_id,
                        Appointment.appointment_date == current_date,
                        Appointment.appointment_time == slot_time,
                        Appointment.status == "scheduled"
                    ).first()
                    
                    # Check if slot is blocked
                    blocked_slot = self.db.query(TimeSlot).filter(
                        TimeSlot.doctor_id == doctor_id,
                        TimeSlot.slot_date == current_date,
                        TimeSlot.slot_time == slot_time,
                        TimeSlot.is_blocked == True
                    ).first()
                    
                    if not existing_appointment and not blocked_slot:
                        available_slots.append({
                            'date': current_date.isoformat(),
                            'time': slot_time.strftime('%H:%M'),
                            'datetime': current_time.isoformat(),
                            'doctor_id': doctor_id,
                            'doctor_name': doctor.name,
                            'specialty': doctor.specialty
                        })
                    
                    # Move to next 30-minute slot
                    current_time += timedelta(minutes=30)
            
            current_date += timedelta(days=1)
        
        return available_slots
    
    def get_specialty_instructions(self, specialty_name: str) -> Dict:
        """Get pre-visit instructions for a specialty"""
        specialty = self.db.query(Specialty).filter(
            Specialty.name.ilike(f"%{specialty_name}%")
        ).first()
        
        if not specialty:
            return {}
        
        instructions = self.db.query(PreVisitInstruction).filter(
            PreVisitInstruction.specialty_id == specialty.id
        ).all()
        
        instruction_dict = {
            'specialty': specialty.name,
            'description': specialty.description,
            'general_instructions': specialty.pre_visit_instructions,
            'detailed_instructions': []
        }
        
        for instruction in instructions:
            instruction_dict['detailed_instructions'].append({
                'text': instruction.instruction_text,
                'type': instruction.instruction_type
            })
        
        return instruction_dict
    
    def search_patient_history(self, phone_number: str, limit: int = 10) -> List[Dict]:
        """Get patient's appointment history"""
        from models.database import Patient
        
        patient = self.db.query(Patient).filter(
            Patient.phone == phone_number
        ).first()
        
        if not patient:
            return []
        
        appointments = self.db.query(Appointment).filter(
            Appointment.patient_id == patient.id
        ).order_by(Appointment.appointment_date.desc()).limit(limit).all()
        
        history = []
        for appointment in appointments:
            history.append({
                'appointment_id': appointment.id,
                'date': appointment.appointment_date.isoformat(),
                'time': appointment.appointment_time.strftime('%H:%M'),
                'doctor_name': appointment.doctor.name,
                'specialty': appointment.doctor.specialty,
                'symptoms': appointment.symptoms,
                'status': appointment.status,
                'serial_number': appointment.serial_number,
                'notes': appointment.notes
            })
        
        return history
    
    def get_urgent_symptoms_check(self, symptoms: str) -> Dict:
        """Check if symptoms indicate urgent care needed"""
        symptoms_lower = symptoms.lower()
        
        urgent_keywords = [
            'severe chest pain', 'heart attack', 'stroke', 'unconscious',
            'severe bleeding', 'broken bone', 'high fever', 'difficulty breathing',
            'poisoning', 'severe injury', 'emergency', 'urgent'
        ]
        
        medium_keywords = [
            'chest pain', 'severe headache', 'high blood pressure', 
            'persistent fever', 'severe pain', 'kidney stone'
        ]
        
        urgency_level = 'low'
        matched_keywords = []
        
        for keyword in urgent_keywords:
            if keyword in symptoms_lower:
                urgency_level = 'high'
                matched_keywords.append(keyword)
        
        if urgency_level != 'high':
            for keyword in medium_keywords:
                if keyword in symptoms_lower:
                    urgency_level = 'medium'
                    matched_keywords.append(keyword)
        
        return {
            'urgency_level': urgency_level,
            'matched_keywords': matched_keywords,
            'recommendation': self._get_urgency_recommendation(urgency_level)
        }
    
    def _doctor_to_dict(self, doctor: Doctor) -> Dict:
        """Convert Doctor model to dictionary"""
        return {
            'id': doctor.id,
            'name': doctor.name,
            'specialty': doctor.specialty,
            'phone': doctor.phone,
            'email': doctor.email,
            'created_at': doctor.created_at,
            'updated_at': doctor.updated_at
        }
    
    def _get_urgency_recommendation(self, urgency_level: str) -> str:
        """Get recommendation based on urgency level"""
        recommendations = {
            'high': 'Please seek immediate emergency care or call emergency services.',
            'medium': 'You should see a doctor as soon as possible, preferably today.',
            'low': 'You can schedule a regular appointment with the appropriate specialist.'
        }
        return recommendations.get(urgency_level, recommendations['low'])
    
    def generate_serial_number(self) -> str:
        """Generate unique serial number for appointment"""
        last_appointment = self.db.query(Appointment).order_by(
            Appointment.id.desc()
        ).first()
        
        if last_appointment:
            # Extract number from last serial (e.g., XH015 -> 15)
            last_num = int(last_appointment.serial_number[2:])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"XH{new_num:03d}"