#!/usr/bin/env python3
"""
Script para crear datos de prueba de horarios de trabajo
"""

import sys
import os
from datetime import time

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.specialty import Specialty
from app.models.work_schedule import WorkSchedule

def create_sample_work_schedules():
    """Crear horarios de trabajo de ejemplo"""
    
    print("🕐 Creando horarios de trabajo de prueba...")
    
    try:
        # Obtener doctores existentes
        doctors = User.query.filter_by(role='doctor', is_active=True).all()
        
        if not doctors:
            print("❌ No hay doctores registrados. Ejecute primero el script de usuarios.")
            return False
        
        # Obtener especialidades
        specialties = Specialty.query.filter_by(is_active=True).all()
        
        # Horarios típicos para diferentes especialidades
        specialty_schedules = {
            'Medicina General': {
                'duration': 30,
                'schedules': [
                    # Lunes a Viernes: 8:00-12:00, 14:00-18:00
                    (0, time(8, 0), time(12, 0), time(12, 0), time(14, 0)),  # Lunes
                    (1, time(8, 0), time(12, 0), time(12, 0), time(14, 0)),  # Martes
                    (2, time(8, 0), time(12, 0), time(12, 0), time(14, 0)),  # Miércoles
                    (3, time(8, 0), time(12, 0), time(12, 0), time(14, 0)),  # Jueves
                    (4, time(8, 0), time(12, 0), time(12, 0), time(14, 0)),  # Viernes
                ]
            },
            'Pediatría': {
                'duration': 45,
                'schedules': [
                    # Lunes, Miércoles, Viernes: 9:00-13:00, 15:00-18:00
                    (0, time(9, 0), time(13, 0), time(13, 0), time(15, 0)),  # Lunes
                    (2, time(9, 0), time(13, 0), time(13, 0), time(15, 0)),  # Miércoles
                    (4, time(9, 0), time(18, 0), None, None),  # Viernes sin descanso
                ]
            },
            'Cardiología': {
                'duration': 60,
                'schedules': [
                    # Martes y Jueves: 8:00-12:00
                    (1, time(8, 0), time(12, 0), None, None),  # Martes
                    (3, time(8, 0), time(12, 0), None, None),  # Jueves
                    # Sábado: 9:00-13:00
                    (5, time(9, 0), time(13, 0), None, None),  # Sábado
                ]
            },
            'Dermatología': {
                'duration': 30,
                'schedules': [
                    # Lunes a Jueves: 14:00-18:00
                    (0, time(14, 0), time(18, 0), None, None),  # Lunes
                    (1, time(14, 0), time(18, 0), None, None),  # Martes
                    (2, time(14, 0), time(18, 0), None, None),  # Miércoles
                    (3, time(14, 0), time(18, 0), None, None),  # Jueves
                ]
            }
        }
        
        created_count = 0
        
        for doctor in doctors:
            print(f"\n📅 Configurando horarios para Dr. {doctor.full_name}")
            
            # Asignar horarios basados en la especialidad del doctor
            doctor_specialty = doctor.specialty.name if doctor.specialty else 'Medicina General'
            
            # Buscar configuración de horario para la especialidad
            schedule_config = None
            for specialty_name, config in specialty_schedules.items():
                if specialty_name.lower() in doctor_specialty.lower():
                    schedule_config = config
                    break
            
            # Si no encuentra configuración específica, usar Medicina General
            if not schedule_config:
                schedule_config = specialty_schedules['Medicina General']
            
            # Crear horarios para el doctor
            for day_of_week, start_time, end_time, break_start, break_end in schedule_config['schedules']:
                
                # Verificar si ya existe un horario para este día
                existing_schedule = WorkSchedule.query.filter_by(
                    doctor_id=doctor.id,
                    day_of_week=day_of_week,
                    specialty_id=doctor.specialty_id if doctor.specialty else None
                ).first()
                
                if existing_schedule:
                    print(f"   ⚠️  Ya existe horario para {['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][day_of_week]}")
                    continue
                
                # Crear nuevo horario
                new_schedule = WorkSchedule(
                    doctor_id=doctor.id,
                    specialty_id=doctor.specialty_id if doctor.specialty else None,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    appointment_duration=schedule_config['duration'],
                    break_start_time=break_start,
                    break_end_time=break_end,
                    max_patients_per_day=None,  # Sin límite por defecto
                    is_active=True
                )
                
                db.session.add(new_schedule)
                created_count += 1
                
                day_name = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][day_of_week]
                time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                print(f"   ✅ {day_name}: {time_range} ({schedule_config['duration']} min/cita)")
        
        # Crear algunos horarios especiales adicionales
        print("\n🌟 Creando horarios especiales...")
        
        # Horario de emergencias para el primer doctor (si existe)
        if doctors:
            first_doctor = doctors[0]
            
            # Horario especial de emergencias los fines de semana
            emergency_schedules = [
                (5, time(9, 0), time(13, 0)),  # Sábado mañana
                (6, time(9, 0), time(12, 0)),  # Domingo mañana
            ]
            
            for day_of_week, start_time, end_time in emergency_schedules:
                existing = WorkSchedule.query.filter_by(
                    doctor_id=first_doctor.id,
                    day_of_week=day_of_week
                ).first()
                
                if not existing:
                    emergency_schedule = WorkSchedule(
                        doctor_id=first_doctor.id,
                        specialty_id=None,  # Horario general
                        day_of_week=day_of_week,
                        start_time=start_time,
                        end_time=end_time,
                        appointment_duration=20,  # Citas más cortas para emergencias
                        break_start_time=None,
                        break_end_time=None,
                        max_patients_per_day=10,  # Límite para emergencias
                        is_active=True
                    )
                    
                    db.session.add(emergency_schedule)
                    created_count += 1
                    
                    day_name = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][day_of_week]
                    print(f"   🚨 {day_name}: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')} (Emergencias)")
        
        # Confirmar cambios
        db.session.commit()
        
        print(f"\n✅ Horarios de trabajo creados exitosamente!")
        print(f"📊 Total de horarios creados: {created_count}")
        print(f"👨‍⚕️ Doctores configurados: {len(doctors)}")
        
        # Mostrar resumen
        print("\n📋 RESUMEN DE HORARIOS:")
        for doctor in doctors:
            schedules = WorkSchedule.query.filter_by(doctor_id=doctor.id, is_active=True).count()
            print(f"   Dr. {doctor.full_name}: {schedules} horario(s)")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al crear horarios: {str(e)}")
        return False

def show_schedules_summary():
    """Mostrar resumen de horarios existentes"""
    
    print("\n📊 RESUMEN DE HORARIOS EXISTENTES:")
    print("=" * 50)
    
    doctors = User.query.filter_by(role='doctor', is_active=True).all()
    
    for doctor in doctors:
        print(f"\n👨‍⚕️ Dr. {doctor.full_name}")
        if doctor.specialty:
            print(f"   Especialidad: {doctor.specialty.name}")
        
        schedules = WorkSchedule.query.filter_by(doctor_id=doctor.id, is_active=True).order_by(WorkSchedule.day_of_week).all()
        
        if schedules:
            days = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
            for schedule in schedules:
                day_name = days[schedule.day_of_week]
                time_range = f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
                duration = f"{schedule.appointment_duration}min"
                
                specialty_info = ""
                if schedule.specialty:
                    specialty_info = f" ({schedule.specialty.name})"
                
                break_info = ""
                if schedule.break_start_time and schedule.break_end_time:
                    break_info = f" [Descanso: {schedule.break_start_time.strftime('%H:%M')}-{schedule.break_end_time.strftime('%H:%M')}]"
                
                print(f"   {day_name}: {time_range} {duration}{specialty_info}{break_info}")
        else:
            print("   ⚠️  Sin horarios configurados")

def main():
    """Función principal"""
    app = create_app()
    
    with app.app_context():
        print("🏥 CONFIGURACIÓN DE HORARIOS DE TRABAJO")
        print("=" * 50)
        
        # Mostrar horarios existentes
        show_schedules_summary()
        
        print("\n¿Desea crear horarios de prueba? (s/n): ", end="")
        response = input().lower().strip()
        
        if response in ['s', 'si', 'yes', 'y']:
            if create_sample_work_schedules():
                print("\n🎉 ¡Configuración completada exitosamente!")
                show_schedules_summary()
            else:
                print("\n❌ Error en la configuración")
        else:
            print("\n👋 Configuración cancelada")

if __name__ == '__main__':
    main()
