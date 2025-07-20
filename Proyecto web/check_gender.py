import os
from app import create_app, db
from app.models.patient import Patient

# Crear la aplicación
app = create_app()

# Crear un contexto de aplicación
with app.app_context():
    # Consultar los valores únicos de género en la base de datos
    unique_genders = db.session.query(Patient.gender).distinct().all()
    print("Valores únicos de género en la base de datos:")
    for gender in unique_genders:
        print(f"- '{gender[0]}'")
    
    # Contar pacientes por género
    print("\nConteo de pacientes por género:")
    gender_counts = db.session.query(Patient.gender, db.func.count(Patient.id)).group_by(Patient.gender).all()
    for gender, count in gender_counts:
        print(f"- {gender}: {count} pacientes")
