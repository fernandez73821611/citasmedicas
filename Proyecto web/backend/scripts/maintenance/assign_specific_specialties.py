#!/usr/bin/env python3
"""Script para asignar especialidades específicas a doctores"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.specialty import Specialty

def main():
    app = create_app()
    with app.app_context():
        # Obtener doctores y especialidades
        doctors = User.query.filter_by(role='doctor').all()
        specialties = Specialty.query.all()
        
        # Asignar especialidades específicas
        specialty_mapping = {
            'dr.garcia': 'Cardiología',
            'dr.rodriguez': 'Neurología', 
            'dr.lopez': 'Pediatría'
        }
        
        for doctor in doctors:
            if doctor.username in specialty_mapping:
                specialty_name = specialty_mapping[doctor.username]
                specialty = Specialty.query.filter_by(name=specialty_name).first()
                if specialty:
                    doctor.specialty_id = specialty.id
                    print(f"Asignada especialidad '{specialty.name}' al doctor {doctor.full_name}")
        
        db.session.commit()
        print("Especialidades específicas asignadas correctamente.")
        
        # Verificar resultado
        print("\nResultado final:")
        for doctor in doctors:
            specialty_name = doctor.specialty.name if doctor.specialty else 'Sin especialidad'
            print(f"Dr. {doctor.full_name} - {specialty_name}")

if __name__ == "__main__":
    main()
