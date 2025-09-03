from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from models.database import Doctor, Patient, Appointment, TimeSlot
from models.schemas import AppointmentCreate, AppointmentBookingRequest, AppointmentBookingResponse
from services.rag.rag_service import RAGService
import uuid
import asyncio
import threading

class SchedulerAgent:
    def __init__(self, db: Session):
        self.db = db
        self.rag_service = RAGService(db)
        self._lock = threading.Lock()  # For thread-safe operations
    
    async def book_appointment(self, request: AppointmentBookingRequest) -> AppointmentBookingResponse:
        """Main appointment booking logic with conflict prevention"""
        try:
            with self._lock:  # Ensure atomic operations
                # Find or create patient
                patient = await self._get_or_create_patient(request.patient_name, request.patient_phone)
                
                # Analyze symptoms to suggest doctors
                recommended_doctors = self.rag_service.search_doctors_by_symptoms(request.symptoms)
                
                if not recommended_doctors:
                    return AppointmentBookingResponse(
                        success=False,
                        message="No suitable doctors found for your symptoms. Please contact hospital directly.",
                        suggested_doctors=[]
                    )
                
                # Check urgency level
                urgency_check = self.rag_service.get_urgent_symptoms_check(request.symptoms)
                
                if urgency_check['urgency_level'] == 'high':
                    return AppointmentBookingResponse(
                        success=False,
                        message=f"URGENT: {urgency_check['recommendation']} Please call emergency services or visit ER immediately.",
                        suggested_doctors=recommended_doctors[:3]
                    )
                
                # Find the best available slot
                best_slot = await self._find_best_available_slot(
                    recommended_doctors,
                    request.preferred_date,
                    request.preferred_time
                )
                
                if not best_slot:
                    available_slots = []
                    for doctor_info in recommended_doctors[:3]:
                        slots = self.rag_service.get_doctor_availability(doctor_info['id'], days=14)
                        available_slots.extend(slots[:5])  # Top 5 slots per doctor
                    
                    return AppointmentBookingResponse(
                        success=False,
                        message="No immediate availability found. Here are some available slots:",
                        suggested_doctors=recommended_doctors[:3],
                        available_slots=available_slots[:10]  # Top 10 overall slots
                    )
                
                # Book the appointment
                appointment = await self._create_appointment(
                    patient_id=patient.id,
                    doctor_id=best_slot['doctor_id'],
                    appointment_date=datetime.fromisoformat(best_slot['date']).date(),
                    appointment_time=datetime.strptime(best_slot['time'], '%H:%M').time(),
                    symptoms=request.symptoms,
                    booking_channel=request.booking_channel
                )
                
                # Get specialty instructions
                doctor = self.db.query(Doctor).filter(Doctor.id == best_slot['doctor_id']).first()
                instructions = self.rag_service.get_specialty_instructions(doctor.specialty)
                
                success_message = f"""
Appointment Confirmed!

Date: {appointment.appointment_date.strftime('%A, %B %d, %Y')}
Time: {appointment.appointment_time.strftime('%I:%M %p')}
Doctor: {doctor.name} ({doctor.specialty})
Serial Number: {appointment.serial_number}
Hospital Phone: +8801712345000

Pre-visit Instructions:
{self._format_instructions(instructions)}

Please arrive 15 minutes early. Bring a valid ID and any previous medical reports.
                """.strip()
                
                return AppointmentBookingResponse(
                    success=True,
                    appointment=appointment,
                    message=success_message,
                    suggested_doctors=[self.rag_service._doctor_to_dict(doctor)]
                )
                
        except Exception as e:
            return AppointmentBookingResponse(
                success=False,
                message=f"Booking failed due to system error. Please try again or call hospital directly. Error: {str(e)}",
                suggested_doctors=[]
            )
    
    async def _get_or_create_patient(self, name: str, phone: str) -> Patient:
        """Find existing patient or create new one"""
        patient = self.db.query(Patient).filter(Patient.phone == phone).first()
        
        if not patient:
            patient = Patient(
                name=name,
                phone=phone
            )
            self.db.add(patient)
            self.db.commit()
            self.db.refresh(patient)
        
        return patient
    
    async def _find_best_available_slot(
        self, 
        recommended_doctors: List[Dict], 
        preferred_date: Optional[date] = None,
        preferred_time: Optional[time] = None
    ) -> Optional[Dict]:
        """Find the best available slot from recommended doctors"""
        
        # Priority: preferred date/time > earliest available > highest priority doctor
        search_start_date = preferred_date if preferred_date else date.today()
        
        # Search for next 14 days
        for days_ahead in range(14):
            search_date = search_start_date + timedelta(days=days_ahead)
            
            for doctor_info in recommended_doctors[:5]:  # Check top 5 doctors
                available_slots = self.rag_service.get_doctor_availability(
                    doctor_info['id'], 
                    search_date, 
                    days=1
                )
                
                for slot in available_slots:
                    slot_date = datetime.fromisoformat(slot['date']).date()
                    slot_time = datetime.strptime(slot['time'], '%H:%M').time()
                    
                    # Check if this exact slot is still available (double-check for race conditions)
                    if await self._is_slot_still_available(doctor_info['id'], slot_date, slot_time):
                        # If preferred time specified, prioritize slots close to it
                        if preferred_time:
                            slot_datetime = datetime.combine(slot_date, slot_time)
                            preferred_datetime = datetime.combine(search_date, preferred_time)
                            
                            # Within 2 hours of preferred time
                            if abs((slot_datetime - preferred_datetime).total_seconds()) <= 7200:
                                return slot
                        else:
                            return slot  # Return first available slot
            
            # If preferred date specified and no slots found, continue to next date
            if preferred_date and search_date == preferred_date:
                continue
        
        return None
    
    async def _is_slot_still_available(self, doctor_id: int, slot_date: date, slot_time: time) -> bool:
        """Double-check if slot is still available (prevent race conditions)"""
        existing_appointment = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == slot_date,
            Appointment.appointment_time == slot_time,
            Appointment.status == "scheduled"
        ).first()
        
        blocked_slot = self.db.query(TimeSlot).filter(
            TimeSlot.doctor_id == doctor_id,
            TimeSlot.slot_date == slot_date,
            TimeSlot.slot_time == slot_time,
            TimeSlot.is_blocked == True
        ).first()
        
        return not existing_appointment and not blocked_slot
    
    async def _create_appointment(
        self,
        patient_id: int,
        doctor_id: int,
        appointment_date: date,
        appointment_time: time,
        symptoms: str,
        booking_channel: str
    ) -> Appointment:
        """Create new appointment with unique serial number"""
        
        serial_number = self.rag_service.generate_serial_number()
        
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            symptoms=symptoms,
            booking_channel=booking_channel,
            serial_number=serial_number,
            status="scheduled"
        )
        
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        
        return appointment
    
    def _format_instructions(self, instructions: Dict) -> str:
        """Format pre-visit instructions for display"""
        if not instructions:
            return "No specific instructions."
        
        formatted = []
        
        if instructions.get('general_instructions'):
            formatted.append(f"• {instructions['general_instructions']}")
        
        for instruction in instructions.get('detailed_instructions', []):
            formatted.append(f"• {instruction['text']}")
        
        return '\n'.join(formatted) if formatted else "No specific instructions."
    
    async def cancel_appointment(self, appointment_id: int, reason: str = "") -> Dict:
        """Cancel an appointment"""
        try:
            appointment = self.db.query(Appointment).filter(
                Appointment.id == appointment_id,
                Appointment.status == "scheduled"
            ).first()
            
            if not appointment:
                return {
                    "success": False,
                    "message": "Appointment not found or already cancelled."
                }
            
            appointment.status = "cancelled"
            appointment.notes = f"Cancelled: {reason}" if reason else "Cancelled by patient"
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Appointment {appointment.serial_number} has been cancelled successfully."
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Cancellation failed: {str(e)}"
            }
    
    async def reschedule_appointment(
        self, 
        appointment_id: int, 
        new_date: date, 
        new_time: time
    ) -> Dict:
        """Reschedule an existing appointment"""
        try:
            appointment = self.db.query(Appointment).filter(
                Appointment.id == appointment_id,
                Appointment.status == "scheduled"
            ).first()
            
            if not appointment:
                return {
                    "success": False,
                    "message": "Appointment not found or cannot be rescheduled."
                }
            
            # Check if new slot is available
            if not await self._is_slot_still_available(appointment.doctor_id, new_date, new_time):
                return {
                    "success": False,
                    "message": "The requested time slot is not available."
                }
            
            appointment.appointment_date = new_date
            appointment.appointment_time = new_time
            appointment.notes = f"Rescheduled on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Appointment {appointment.serial_number} rescheduled to {new_date} at {new_time.strftime('%H:%M')}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Rescheduling failed: {str(e)}"
            }
    
    async def get_patient_appointments(self, phone_number: str) -> List[Dict]:
        """Get all appointments for a patient"""
        try:
            patient = self.db.query(Patient).filter(Patient.phone == phone_number).first()
            
            if not patient:
                return []
            
            appointments = self.db.query(Appointment).filter(
                Appointment.patient_id == patient.id
            ).order_by(Appointment.appointment_date.desc()).all()
            
            result = []
            for apt in appointments:
                result.append({
                    'id': apt.id,
                    'serial_number': apt.serial_number,
                    'date': apt.appointment_date.isoformat(),
                    'time': apt.appointment_time.strftime('%H:%M'),
                    'doctor_name': apt.doctor.name,
                    'specialty': apt.doctor.specialty,
                    'symptoms': apt.symptoms,
                    'status': apt.status,
                    'notes': apt.notes
                })
            
            return result
            
        except Exception as e:
            return []