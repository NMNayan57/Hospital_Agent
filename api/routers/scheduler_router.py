from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from models.database import get_db
from models.schemas import (
    AppointmentBookingRequest, AppointmentBookingResponse,
    DoctorAvailabilityRequest, DoctorAvailabilityResponse,
    SymptomAnalysisRequest, SymptomAnalysisResponse
)
from agents.scheduler.scheduler_agent import SchedulerAgent
from services.rag.rag_service import RAGService

router = APIRouter()

@router.post("/book", response_model=AppointmentBookingResponse)
async def book_appointment(
    request: AppointmentBookingRequest,
    db: Session = Depends(get_db)
):
    """Book a new appointment"""
    try:
        scheduler_agent = SchedulerAgent(db)
        response = await scheduler_agent.book_appointment(request)
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error booking appointment: {str(e)}"
        )

@router.get("/availability/{doctor_id}")
async def get_doctor_availability(
    doctor_id: int,
    start_date: Optional[date] = Query(None, description="Start date for availability check"),
    days: int = Query(7, description="Number of days to check"),
    db: Session = Depends(get_db)
):
    """Get availability for a specific doctor"""
    try:
        rag_service = RAGService(db)
        available_slots = rag_service.get_doctor_availability(
            doctor_id=doctor_id,
            start_date=start_date,
            days=days
        )
        
        # Get doctor info
        from models.database import Doctor as DoctorModel
        doctor = db.query(DoctorModel).filter(DoctorModel.id == doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found"
            )
        
        return {
            "doctor": {
                "id": doctor.id,
                "name": doctor.name,
                "specialty": doctor.specialty,
                "phone": doctor.phone,
                "email": doctor.email
            },
            "available_slots": available_slots,
            "search_period": {
                "start_date": start_date.isoformat() if start_date else date.today().isoformat(),
                "days": days
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving availability: {str(e)}"
        )

@router.post("/analyze-symptoms", response_model=SymptomAnalysisResponse)
async def analyze_symptoms(
    request: SymptomAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze symptoms and recommend doctors"""
    try:
        rag_service = RAGService(db)
        
        # Get doctor recommendations based on symptoms
        recommended_doctors = rag_service.search_doctors_by_symptoms(request.symptoms)
        
        # Get urgency assessment
        urgency_check = rag_service.get_urgent_symptoms_check(request.symptoms)
        
        # Get specialties
        recommended_specialties = []
        seen_specialties = set()
        
        for doctor_info in recommended_doctors:
            specialty_name = doctor_info.get('specialty_info', {}).get('name')
            if specialty_name and specialty_name not in seen_specialties:
                specialty = db.query(Specialty).filter(
                    Specialty.name == specialty_name
                ).first()
                if specialty:
                    recommended_specialties.append(specialty)
                    seen_specialties.add(specialty_name)
        
        # Convert doctors
        doctors = []
        for doctor_info in recommended_doctors:
            from models.database import Doctor as DoctorModel  
            doctor = db.query(DoctorModel).filter(DoctorModel.id == doctor_info['id']).first()
            if doctor:
                doctors.append(doctor)
        
        return SymptomAnalysisResponse(
            recommended_specialties=recommended_specialties,
            suggested_doctors=doctors,
            urgency_level=urgency_check['urgency_level'],
            explanation=urgency_check['recommendation']
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing symptoms: {str(e)}"
        )

@router.get("/appointments/{phone_number}")
async def get_patient_appointments(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Get all appointments for a patient by phone number"""
    try:
        scheduler_agent = SchedulerAgent(db)
        appointments = await scheduler_agent.get_patient_appointments(phone_number)
        
        return {
            "phone_number": phone_number,
            "appointments": appointments,
            "count": len(appointments)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving appointments: {str(e)}"
        )

@router.put("/appointments/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: int,
    reason: str = "",
    db: Session = Depends(get_db)
):
    """Cancel an appointment"""
    try:
        scheduler_agent = SchedulerAgent(db)
        result = await scheduler_agent.cancel_appointment(appointment_id, reason)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling appointment: {str(e)}"
        )

@router.put("/appointments/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: int,
    new_date: date,
    new_time: str,  # Format: "HH:MM"
    db: Session = Depends(get_db)
):
    """Reschedule an appointment"""
    try:
        from datetime import time
        
        # Parse time
        try:
            time_parts = new_time.split(":")
            new_time_obj = time(int(time_parts[0]), int(time_parts[1]))
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid time format. Use HH:MM"
            )
        
        scheduler_agent = SchedulerAgent(db)
        result = await scheduler_agent.reschedule_appointment(
            appointment_id, new_date, new_time_obj
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rescheduling appointment: {str(e)}"
        )

@router.get("/doctors")
async def get_all_doctors(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    db: Session = Depends(get_db)
):
    """Get list of all doctors"""
    try:
        from models.database import Doctor as DoctorModel
        query = db.query(DoctorModel)
        
        if specialty:
            query = query.filter(DoctorModel.specialty.ilike(f"%{specialty}%"))
        
        doctors = query.all()
        
        return {
            "doctors": [
                {
                    "id": doctor.id,
                    "name": doctor.name,
                    "specialty": doctor.specialty,
                    "phone": doctor.phone,
                    "email": doctor.email
                }
                for doctor in doctors
            ],
            "count": len(doctors),
            "specialty_filter": specialty
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving doctors: {str(e)}"
        )

@router.get("/specialties")
async def get_all_specialties(
    db: Session = Depends(get_db)
):
    """Get list of all medical specialties"""
    try:
        specialties = db.query(Specialty).all()
        
        return {
            "specialties": [
                {
                    "id": specialty.id,
                    "name": specialty.name,
                    "description": specialty.description,
                    "pre_visit_instructions": specialty.pre_visit_instructions
                }
                for specialty in specialties
            ],
            "count": len(specialties)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving specialties: {str(e)}"
        )

@router.get("/appointments/today")
async def get_todays_appointments(
    db: Session = Depends(get_db)
):
    """Get all appointments scheduled for today"""
    try:
        from models.database import Appointment
        
        today = date.today()
        appointments = db.query(Appointment).filter(
            Appointment.appointment_date == today,
            Appointment.status == "scheduled"
        ).all()
        
        appointments_data = []
        for apt in appointments:
            appointments_data.append({
                "id": apt.id,
                "serial_number": apt.serial_number,
                "patient_name": apt.patient.name,
                "patient_phone": apt.patient.phone,
                "doctor_name": apt.doctor.name,
                "specialty": apt.doctor.specialty,
                "appointment_time": apt.appointment_time.strftime("%H:%M"),
                "symptoms": apt.symptoms,
                "status": apt.status,
                "booking_channel": apt.booking_channel
            })
        
        return {
            "date": today.isoformat(),
            "appointments": appointments_data,
            "count": len(appointments_data)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving today's appointments: {str(e)}"
        )

@router.get("/statistics")
async def get_appointment_statistics(
    days: int = Query(7, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get appointment statistics"""
    try:
        from models.database import Appointment
        from datetime import timedelta
        
        start_date = date.today() - timedelta(days=days)
        
        # Total appointments
        total = db.query(Appointment).filter(
            Appointment.appointment_date >= start_date
        ).count()
        
        # By status
        scheduled = db.query(Appointment).filter(
            Appointment.appointment_date >= start_date,
            Appointment.status == "scheduled"
        ).count()
        
        completed = db.query(Appointment).filter(
            Appointment.appointment_date >= start_date,
            Appointment.status == "completed"
        ).count()
        
        cancelled = db.query(Appointment).filter(
            Appointment.appointment_date >= start_date,
            Appointment.status == "cancelled"
        ).count()
        
        # By channel
        chat_bookings = db.query(Appointment).filter(
            Appointment.appointment_date >= start_date,
            Appointment.booking_channel == "chat"
        ).count()
        
        voice_bookings = db.query(Appointment).filter(
            Appointment.appointment_date >= start_date,
            Appointment.booking_channel == "voice"
        ).count()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": date.today().isoformat(),
                "days": days
            },
            "total_appointments": total,
            "by_status": {
                "scheduled": scheduled,
                "completed": completed,
                "cancelled": cancelled
            },
            "by_channel": {
                "chat": chat_bookings,
                "voice": voice_bookings
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )

@router.get("/appointments")
async def get_all_appointments(
    limit: Optional[int] = Query(50, description="Maximum number of appointments to return"),
    db: Session = Depends(get_db)
):
    """Get all recent appointments for admin dashboard"""
    try:
        from models.database import Appointment, Doctor, Patient
        
        appointments = db.query(Appointment).join(Doctor).join(Patient).order_by(
            Appointment.created_at.desc()
        ).limit(limit).all()
        
        appointments_data = []
        for apt in appointments:
            appointments_data.append({
                'id': apt.id,
                'patient_name': apt.patient.name,
                'patient_phone': apt.patient.phone,
                'doctor_name': apt.doctor.name,
                'doctor_specialty': apt.doctor.specialty,
                'appointment_date': apt.appointment_date.isoformat(),
                'appointment_time': apt.appointment_time.strftime('%H:%M'),
                'symptoms': apt.symptoms,
                'status': apt.status,
                'serial_number': apt.serial_number,
                'booking_channel': apt.booking_channel,
                'created_at': apt.created_at.isoformat(),
                'booking_timestamp': apt.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return {
            "appointments": appointments_data,
            "total_count": len(appointments_data),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching appointments: {str(e)}"
        )

@router.get("/appointments/live/recent")
async def get_live_recent_appointments(db: Session = Depends(get_db)):
    """Get live recent appointments for real-time display"""
    try:
        from models.database import Appointment, Doctor, Patient
        from datetime import timedelta
        
        # Get appointments from last 24 hours
        yesterday = datetime.now() - timedelta(days=1)
        
        recent_appointments = db.query(Appointment).join(Doctor).join(Patient).filter(
            Appointment.created_at >= yesterday
        ).order_by(
            Appointment.created_at.desc()
        ).limit(20).all()
        
        appointments_data = []
        for apt in recent_appointments:
            # Calculate time since booking
            time_diff = datetime.now() - apt.created_at
            if time_diff.days > 0:
                time_since = f"{time_diff.days} days ago"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                time_since = f"{hours} hours ago"
            elif time_diff.seconds > 60:
                minutes = time_diff.seconds // 60
                time_since = f"{minutes} minutes ago"
            else:
                time_since = "Just now"
            
            appointments_data.append({
                'id': apt.id,
                'patient_name': apt.patient.name,
                'patient_phone': apt.patient.phone,
                'doctor_name': apt.doctor.name,
                'doctor_specialty': apt.doctor.specialty,
                'appointment_date': apt.appointment_date.strftime('%Y-%m-%d'),
                'appointment_time': apt.appointment_time.strftime('%H:%M'),
                'formatted_datetime': f"{apt.appointment_date.strftime('%b %d')} at {apt.appointment_time.strftime('%I:%M %p')}",
                'symptoms': apt.symptoms[:100] + "..." if len(apt.symptoms) > 100 else apt.symptoms,
                'status': apt.status,
                'serial_number': apt.serial_number,
                'booking_channel': apt.booking_channel,
                'booking_channel_icon': '💬' if apt.booking_channel == 'chat' else '🎤' if apt.booking_channel == 'voice' else '🌐',
                'created_at': apt.created_at.isoformat(),
                'time_since_booking': time_since,
                'is_recent': time_diff.seconds < 300  # Last 5 minutes
            })
        
        return {
            "appointments": appointments_data,
            "total_count": len(appointments_data),
            "last_updated": datetime.now().isoformat(),
            "update_time": datetime.now().strftime('%H:%M:%S')
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching live appointments: {str(e)}"
        )

@router.get("/health")
async def scheduler_health_check():
    """Health check endpoint for scheduler service"""
    return {
        "service": "scheduler_agent",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }