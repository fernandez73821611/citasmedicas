#!/usr/bin/env python3
"""
Script para verificar y corregir las métricas de horarios de trabajo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models.user import User
from app.models.work_schedule import WorkSchedule
from app.models.specialty import Specialty
from datetime import datetime, date, time

def analyze_work_schedules():
    """Analizar métricas de horarios de trabajo"""
    
    print("🔍 Analizando métricas de horarios de trabajo...")
    print("=" * 60)
    
    # 1. Obtener doctores activos
    doctors = User.query.filter_by(role='doctor', is_active=True).all()
    print(f"👨‍⚕️  Doctores Activos: {len(doctors)}")
    
    for doctor in doctors:
        print(f"   • {doctor.full_name} ({doctor.specialty.name if doctor.specialty else 'Sin especialidad'})")
    
    # 2. Obtener horarios configurados
    total_schedules = WorkSchedule.query.filter_by(is_active=True).count()
    print(f"\n📅 Horarios Configurados: {total_schedules}")
    
    # Agrupar por doctor
    doctor_schedules = {}
    for doctor in doctors:
        schedules = WorkSchedule.query.filter_by(doctor_id=doctor.id, is_active=True).all()
        doctor_schedules[doctor.id] = schedules
        
        if schedules:
            print(f"   • {doctor.full_name}: {len(schedules)} horario(s)")
            for schedule in schedules:
                start_date = schedule.start_date if schedule.start_date else "Sin fecha"
                end_date = schedule.end_date if schedule.end_date else "Sin límite"
                print(f"     - {schedule.day_name}: {schedule.start_time} - {schedule.end_time} (Vigencia: {start_date} a {end_date})")
        else:
            print(f"   • {doctor.full_name}: 0 horarios")
    
    # 3. Doctores sin horarios
    doctors_without_schedule = 0
    doctors_with_no_schedules = []
    
    for doctor in doctors:
        if not doctor_schedules.get(doctor.id):
            doctors_without_schedule += 1
            doctors_with_no_schedules.append(doctor.full_name)
    
    print(f"\n⚠️  Doctores Sin Horarios: {doctors_without_schedule}")
    for doctor_name in doctors_with_no_schedules:
        print(f"   • {doctor_name}")
    
    # 4. Especialidades
    specialties = Specialty.query.filter_by(is_active=True).all()
    print(f"\n🏥 Especialidades Activas: {len(specialties)}")
    for specialty in specialties:
        print(f"   • {specialty.name}")
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE MÉTRICAS:")
    print(f"   • Doctores Activos: {len(doctors)}")
    print(f"   • Horarios Configurados: {total_schedules}")
    print(f"   • Sin Horarios: {doctors_without_schedule}")
    print(f"   • Especialidades: {len(specialties)}")
    
    return {
        'doctors_count': len(doctors),
        'total_schedules': total_schedules,
        'doctors_without_schedule': doctors_without_schedule,
        'specialties_count': len(specialties),
        'doctor_schedules': doctor_schedules
    }

def create_sample_schedules():
    """Crear horarios de ejemplo para verificar las métricas"""
    
    print("\n🔧 ¿Desea crear horarios de ejemplo para los doctores sin horarios? (s/n): ", end="")
    response = input().strip().lower()
    
    if response != 's':
        print("No se crearon horarios de ejemplo")
        return
    
    # Obtener doctores sin horarios
    doctors = User.query.filter_by(role='doctor', is_active=True).all()
    doctors_without_schedule = []
    
    for doctor in doctors:
        schedules = WorkSchedule.query.filter_by(doctor_id=doctor.id, is_active=True).count()
        if schedules == 0:
            doctors_without_schedule.append(doctor)
    
    if not doctors_without_schedule:
        print("✅ Todos los doctores ya tienen horarios configurados")
        return
    
    print(f"\n📝 Creando horarios para {len(doctors_without_schedule)} doctor(es)...")
    
    try:
        for doctor in doctors_without_schedule:
            # Crear horarios básicos de Lunes a Viernes
            for day in range(5):  # 0=Lunes a 4=Viernes
                schedule = WorkSchedule(
                    doctor_id=doctor.id,
                    specialty_id=doctor.specialty_id,
                    day_of_week=day,
                    start_time=time(9, 0),  # 09:00
                    end_time=time(17, 0),   # 17:00
                    appointment_duration=30,
                    start_date=date(2025, 7, 1),
                    end_date=date(2025, 12, 31),
                    is_active=True
                )
                db.session.add(schedule)
            
            print(f"   ✅ Horarios creados para {doctor.full_name}")
        
        db.session.commit()
        print(f"\n✅ Se crearon horarios exitosamente para {len(doctors_without_schedule)} doctor(es)")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al crear horarios: {str(e)}")

if __name__ == "__main__":
    # Crear aplicación Flask
    app = create_app()
    
    with app.app_context():
        metrics = analyze_work_schedules()
        
        if metrics['doctors_without_schedule'] > 0:
            create_sample_schedules()
            
            # Analizar nuevamente después de crear horarios
            print("\n🔄 Analizando métricas después de crear horarios...")
            analyze_work_schedules()
