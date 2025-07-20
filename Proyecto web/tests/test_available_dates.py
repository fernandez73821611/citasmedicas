#!/usr/bin/env python3
"""
Script para verificar las fechas disponibles de un doctor específico
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.work_schedule import WorkSchedule

def main():
    """Función principal"""
    app = create_app()
    
    with app.app_context():
        # Obtener un doctor específico
        doctor_id = 2  # Dr. Ana García
        doctor = User.query.filter_by(id=doctor_id, role='doctor', is_active=True).first()
        
        if not doctor:
            print(f"❌ Doctor con ID {doctor_id} no encontrado")
            return
        
        print(f"🔍 Verificando fechas disponibles para Dr. {doctor.full_name}")
        print("-" * 60)
        
        # Obtener todos los horarios del doctor
        schedules = WorkSchedule.query.filter_by(
            doctor_id=doctor_id,
            is_active=True
        ).all()
        
        print(f"📋 Horarios configurados: {len(schedules)}")
        for schedule in schedules:
            print(f"   - {schedule.day_name}: {schedule.time_range}")
            print(f"     Vigencia: {schedule.start_date} - {schedule.end_date or 'Sin límite'}")
        
        print("\n" + "=" * 60)
        
        # Obtener días de la semana disponibles
        available_weekdays = set()
        for schedule in schedules:
            if (schedule.start_date and schedule.start_date <= datetime.now().date() + timedelta(days=365) and
                (not schedule.end_date or schedule.end_date >= datetime.now().date())):
                available_weekdays.add(schedule.day_of_week)
        
        print(f"📅 Días de la semana disponibles: {available_weekdays}")
        days_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        for day in available_weekdays:
            print(f"   - {days_names[day]} ({day})")
        
        print("\n" + "=" * 60)
        
        # Generar fechas disponibles (próximos 14 días)
        print("📆 Fechas disponibles (próximos 14 días):")
        current_date = datetime.now().date()
        end_date = current_date + timedelta(days=14)
        
        available_dates = []
        
        while current_date <= end_date:
            weekday = current_date.weekday()
            
            print(f"\n   {current_date.strftime('%Y-%m-%d')} ({days_names[weekday]}):")
            
            # Verificar si el día de la semana tiene horarios
            if weekday in available_weekdays:
                print(f"     ✅ Día de la semana disponible")
                
                # Verificar si hay horarios válidos para esta fecha
                valid_schedules = [s for s in schedules if 
                                 s.day_of_week == weekday and
                                 s.start_date <= current_date and
                                 (not s.end_date or s.end_date >= current_date)]
                
                if valid_schedules:
                    print(f"     ✅ Horarios válidos: {len(valid_schedules)}")
                    for schedule in valid_schedules:
                        print(f"        - {schedule.time_range} (ID: {schedule.id})")
                    available_dates.append(current_date.strftime('%Y-%m-%d'))
                else:
                    print(f"     ❌ Sin horarios válidos para esta fecha")
            else:
                print(f"     ❌ Día de la semana no disponible")
            
            current_date += timedelta(days=1)
        
        print("\n" + "=" * 60)
        print(f"📊 Resumen:")
        print(f"   Doctor: Dr. {doctor.full_name}")
        print(f"   Horarios configurados: {len(schedules)}")
        print(f"   Días de la semana disponibles: {len(available_weekdays)}")
        print(f"   Fechas disponibles (próximos 14 días): {len(available_dates)}")
        print(f"   Fechas: {', '.join(available_dates)}")

if __name__ == '__main__':
    main()
