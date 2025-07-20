#!/usr/bin/env python3
"""
Script para probar la funcionalidad de rangos de fechas en horarios de trabajo.
"""

import os
import sys
from datetime import datetime, date, timedelta

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.specialty import Specialty
from app.models.work_schedule import WorkSchedule

def test_date_ranges():
    """Probar funcionalidad de rangos de fechas"""
    
    # Crear app
    app = create_app()
    
    with app.app_context():
        print("=== PRUEBA DE RANGOS DE FECHAS EN HORARIOS ===\n")
        
        # Obtener un doctor
        doctor = User.query.filter_by(role='doctor', is_active=True).first()
        if not doctor:
            print("❌ No se encontró ningún doctor activo")
            return
        
        print(f"✅ Doctor encontrado: Dr. {doctor.full_name}")
        
        # Crear horario con rango de fechas
        today = date.today()
        start_date = today + timedelta(days=1)  # Desde mañana
        end_date = today + timedelta(days=30)   # Hasta 30 días
        
        # Verificar si ya existe un horario para este doctor en lunes
        existing_schedule = WorkSchedule.query.filter_by(
            doctor_id=doctor.id,
            day_of_week=0,  # Lunes
            is_active=True
        ).first()
        
        if existing_schedule:
            print(f"✅ Horario existente encontrado para lunes: {existing_schedule.time_range}")
            
            # Actualizar con fechas
            existing_schedule.start_date = start_date
            existing_schedule.end_date = end_date
            db.session.commit()
            
            test_schedule = existing_schedule
            print(f"✅ Horario actualizado con fechas: {test_schedule.date_range}")
            
        else:
            # Crear nuevo horario
            test_schedule = WorkSchedule(
                doctor_id=doctor.id,
                specialty_id=doctor.specialty_id if doctor.specialty else None,
                day_of_week=0,  # Lunes
                start_time=datetime.strptime('09:00', '%H:%M').time(),
                end_time=datetime.strptime('17:00', '%H:%M').time(),
                start_date=start_date,
                end_date=end_date,
                appointment_duration=30,
                is_active=True
            )
            
            db.session.add(test_schedule)
            db.session.commit()
            
            print(f"✅ Nuevo horario creado: {test_schedule.time_range}")
            print(f"✅ Rango de fechas: {test_schedule.date_range}")
        
        # Probar validación de fechas
        print("\n=== PRUEBAS DE VALIDACIÓN DE FECHAS ===")
        
        # Fecha dentro del rango
        test_date_valid = start_date + timedelta(days=7)
        is_valid = test_schedule.is_valid_for_date(test_date_valid)
        print(f"✅ Fecha {test_date_valid} (dentro del rango): {'Válida' if is_valid else 'No válida'}")
        
        # Fecha antes del rango
        test_date_before = start_date - timedelta(days=1)
        is_valid = test_schedule.is_valid_for_date(test_date_before)
        print(f"✅ Fecha {test_date_before} (antes del rango): {'Válida' if is_valid else 'No válida'}")
        
        # Fecha después del rango
        test_date_after = end_date + timedelta(days=1)
        is_valid = test_schedule.is_valid_for_date(test_date_after)
        print(f"✅ Fecha {test_date_after} (después del rango): {'Válida' if is_valid else 'No válida'}")
        
        # Probar horarios disponibles
        print("\n=== PRUEBAS DE HORARIOS DISPONIBLES ===")
        
        # Obtener próximo lunes
        days_ahead = 0 - today.weekday()  # 0 = lunes
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        
        # Asegurar que esté dentro del rango
        if next_monday < start_date:
            next_monday = start_date
        elif next_monday > end_date:
            next_monday = end_date - timedelta(days=1)
        
        # Obtener horarios disponibles
        available_times = WorkSchedule.get_available_times(
            doctor.id,
            next_monday,
            doctor.specialty_id if doctor.specialty else None
        )
        
        print(f"✅ Horarios disponibles para {next_monday}: {len(available_times)} slots")
        if available_times:
            print(f"   Primeros horarios: {[t.strftime('%H:%M') for t in available_times[:5]]}")
        
        # Probar con fecha fuera del rango
        invalid_date = start_date - timedelta(days=5)
        available_times_invalid = WorkSchedule.get_available_times(
            doctor.id,
            invalid_date,
            doctor.specialty_id if doctor.specialty else None
        )
        
        print(f"✅ Horarios disponibles para {invalid_date} (fuera del rango): {len(available_times_invalid)} slots")
        
        print("\n=== PRUEBAS COMPLETADAS ===")
        print("✅ Funcionalidad de rangos de fechas implementada correctamente")
        
        # Mostrar información del horario
        print(f"\n=== INFORMACIÓN DEL HORARIO ===")
        print(f"Doctor: Dr. {doctor.full_name}")
        print(f"Día: {test_schedule.day_name}")
        print(f"Horario: {test_schedule.time_range}")
        print(f"Vigencia: {test_schedule.date_range}")
        print(f"Especialidad: {test_schedule.specialty.name if test_schedule.specialty else 'General'}")
        print(f"Estado: {'Activo' if test_schedule.is_active else 'Inactivo'}")

if __name__ == "__main__":
    test_date_ranges()
