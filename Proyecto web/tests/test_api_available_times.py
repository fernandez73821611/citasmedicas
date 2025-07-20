#!/usr/bin/env python3
"""Test script para debug del API available-times"""

from datetime import datetime
from app import create_app
from app.models.user import User
from app.models.work_schedule import WorkSchedule

app = create_app()

with app.app_context():
    # Testear la función con datos específicos
    doctor_id = 2
    date_str = '2025-07-07'
    
    print(f"Testing API available-times with doctor_id={doctor_id}, date={date_str}")
    
    # Probar diferentes fechas - incluir algunas fuera de vigencia y días sin horario
    test_dates = ['2025-07-07', '2025-07-08', '2025-07-10', '2025-07-14', '2025-07-15', '2025-07-04', '2025-07-25', '2025-07-13']  # Domingo
    
    for date_str in test_dates:
        print(f"\n=== Testing date: {date_str} ===")
        try:
            # Parsear fecha
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            print(f"Date parsed: {date_obj}, weekday: {date_obj.weekday()}")
            
            # Obtener doctor
            doctor = User.query.get(doctor_id)
            if not doctor:
                print("Doctor not found")
                continue
            
            print(f"Doctor: {doctor.full_name}")
            print(f"Doctor specialty: {doctor.specialty.name if doctor.specialty else 'None'}")
            
            # Buscar horarios para este doctor y día de la semana
            schedules = WorkSchedule.query.filter_by(
                doctor_id=doctor_id,
                day_of_week=date_obj.weekday(),
                is_active=True
            ).all()
            
            print(f"Found {len(schedules)} schedules for weekday {date_obj.weekday()}")
            
            for schedule in schedules:
                print(f"Schedule: {schedule}")
                print(f"  Start date: {schedule.start_date}")
                print(f"  End date: {schedule.end_date}")
                print(f"  Valid for date: {schedule.is_valid_for_date(date_obj)}")
                if schedule.is_valid_for_date(date_obj):
                    slots = schedule.get_available_slots(date_obj)
                    print(f"  Available slots: {len(slots)} slots")
                    if slots:
                        print(f"    First slot: {slots[0]}")
                        print(f"    Last slot: {slots[-1]}")
                print()
            
            # Filtrar por vigencia
            valid_schedules = []
            for schedule in schedules:
                if (schedule.start_date <= date_obj and 
                    (not schedule.end_date or schedule.end_date >= date_obj)):
                    valid_schedules.append(schedule)
            
            print(f"Valid schedules: {len(valid_schedules)}")
            
            if not valid_schedules:
                print("No valid schedules found")
                continue
            
            # Obtener horarios disponibles usando el método del modelo
            available_times = WorkSchedule.get_available_times(
                doctor_id, 
                date_obj, 
                doctor.specialty_id if doctor.specialty else None
            )
            
            print(f"Available times: {len(available_times)} slots")
            
            # Formatear horarios para respuesta
            formatted_times = [time.strftime('%H:%M') for time in available_times]
            
            print(f"Formatted times: {formatted_times[:5]}{'...' if len(formatted_times) > 5 else ''}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
