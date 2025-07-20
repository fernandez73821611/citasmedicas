#!/usr/bin/env python3
"""
Script para establecer fecha de vigencia de horarios para todos los doctores
Establece una fecha de vigencia de 15 días a partir de hoy
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User

def main():
    """Función principal"""
    app = create_app()
    
    with app.app_context():
        # Calcular fecha de vigencia (15 días desde hoy)
        today = datetime.now().date()
        validity_date = today + timedelta(days=15)
        
        print(f"🗓️  Estableciendo fecha de vigencia para todos los doctores:")
        print(f"   Fecha actual: {today.strftime('%d/%m/%Y')}")
        print(f"   Fecha de vigencia: {validity_date.strftime('%d/%m/%Y')}")
        print("-" * 50)
        
        # Obtener todos los doctores
        doctors = User.query.filter_by(role='doctor', is_active=True).all()
        
        if not doctors:
            print("❌ No se encontraron doctores activos en el sistema")
            return
        
        # Actualizar fecha de vigencia para cada doctor
        updated_count = 0
        for doctor in doctors:
            try:
                doctor.schedule_validity_date = validity_date
                db.session.add(doctor)
                updated_count += 1
                
                print(f"✅ Dr. {doctor.full_name} - Fecha de vigencia actualizada")
                
            except Exception as e:
                print(f"❌ Error actualizando Dr. {doctor.full_name}: {str(e)}")
        
        # Guardar cambios
        try:
            db.session.commit()
            print("-" * 50)
            print(f"🎉 ¡Proceso completado exitosamente!")
            print(f"   Doctores actualizados: {updated_count}")
            print(f"   Fecha de vigencia: {validity_date.strftime('%d/%m/%Y')}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al guardar cambios: {str(e)}")

if __name__ == '__main__':
    main()
