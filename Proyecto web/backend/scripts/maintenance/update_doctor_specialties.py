#!/usr/bin/env python3
"""Script para verificar y actualizar datos de especialidades en doctores"""

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
        
        print("Doctores encontrados:")
        for doctor in doctors:
            print(f"ID: {doctor.id}, Usuario: {doctor.username}, Nombre: {doctor.full_name}, Especialidad: {doctor.specialty_id}")
        
        print("\nEspecialidades disponibles:")
        for specialty in specialties:
            print(f"ID: {specialty.id}, Nombre: {specialty.name}")
        
        # Si hay doctores sin especialidad, asignar una por defecto
        if doctors and specialties and any(d.specialty_id is None for d in doctors):
            print("\nAsignando especialidades a doctores...")
            default_specialty = specialties[0]  # Usar la primera especialidad como default
            
            for doctor in doctors:
                if doctor.specialty_id is None:
                    doctor.specialty_id = default_specialty.id
                    print(f"Asignada especialidad '{default_specialty.name}' al doctor {doctor.full_name}")
            
            db.session.commit()
            print("Especialidades asignadas correctamente.")

if __name__ == "__main__":
    main()
