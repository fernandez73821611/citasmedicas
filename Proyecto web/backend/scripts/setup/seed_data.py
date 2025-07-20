#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos de prueba
Sistema de Gestión Médica - Proyecto Académico
"""

from datetime import datetime, date, timedelta
from app import create_app, db
from app.models.user import User
from app.models.patient import Patient
from app.models.specialty import Specialty
from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord

def create_sample_data():
    """Crear datos de prueba para el sistema"""
    
    print("🏥 Creando datos de prueba para el Sistema de Gestión Médica...")
    
    # 1. CREAR ESPECIALIDADES
    print("📋 Creando especialidades médicas...")
    
    specialties_data = [
        {
            'name': 'Medicina General',
            'description': 'Atención médica integral y preventiva',
            'consultation_duration': 30,
            'base_price': 50.00
        },
        {
            'name': 'Cardiología',
            'description': 'Especialidad en enfermedades del corazón',
            'consultation_duration': 45,
            'base_price': 120.00
        },
        {
            'name': 'Neurología',
            'description': 'Especialidad en enfermedades del sistema nervioso',
            'consultation_duration': 60,
            'base_price': 150.00
        },
        {
            'name': 'Pediatría',
            'description': 'Atención médica especializada en niños y adolescentes',
            'consultation_duration': 30,
            'base_price': 80.00
        },
        {
            'name': 'Dermatología',
            'description': 'Especialidad en enfermedades de la piel',
            'consultation_duration': 25,
            'base_price': 90.00
        }
    ]
    
    specialties = {}
    for spec_data in specialties_data:
        specialty = Specialty(**spec_data)
        db.session.add(specialty)
        specialties[spec_data['name']] = specialty
    
    db.session.commit()
    print(f"   ✅ {len(specialties_data)} especialidades creadas")
    
    # 2. CREAR USUARIOS (TRABAJADORES)
    print("👥 Creando usuarios del sistema...")
    
    users_data = [
        # ADMINISTRADOR
        {
            'username': 'admin',
            'email': 'admin@clinica.com',
            'password': 'admin123',
            'first_name': 'Carlos',
            'last_name': 'Mendoza',
            'phone': '987654321',
            'role': 'admin'
        },
        # MÉDICOS
        {
            'username': 'dr.garcia',
            'email': 'garcia@clinica.com',
            'password': 'doc123',
            'first_name': 'Ana',
            'last_name': 'García',
            'phone': '987654322',
            'role': 'doctor'
        },
        {
            'username': 'dr.rodriguez',
            'email': 'rodriguez@clinica.com',
            'password': 'doc123',
            'first_name': 'Miguel',
            'last_name': 'Rodríguez',
            'phone': '987654323',
            'role': 'doctor'
        },
        {
            'username': 'dr.lopez',
            'email': 'lopez@clinica.com',
            'password': 'doc123',
            'first_name': 'Laura',
            'last_name': 'López',
            'phone': '987654324',
            'role': 'doctor'
        },
        # RECEPCIONISTAS
        {
            'username': 'recep.maria',
            'email': 'maria@clinica.com',
            'password': 'recep123',
            'first_name': 'María',
            'last_name': 'Fernández',
            'phone': '987654325',
            'role': 'receptionist'
        },
        {
            'username': 'recep.sofia',
            'email': 'sofia@clinica.com',
            'password': 'recep123',
            'first_name': 'Sofía',
            'last_name': 'Vargas',
            'phone': '987654326',
            'role': 'receptionist'
        },
        {
            'username': 'enf.carmen',
            'email': 'carmen.enfermera@clinica.com',
            'password': 'enf123',
            'first_name': 'Carmen',
            'last_name': 'Ruiz',
            'phone': '987654327',
            'role': 'nurse'
        }
    ]
    
    users = {}
    for user_data in users_data:
        password = user_data.pop('password')
        user = User(**user_data)
        user.set_password(password)
        db.session.add(user)
        users[user_data['username']] = user
    
    db.session.commit()
    print(f"   ✅ {len(users_data)} usuarios creados")
    
    # 3. CREAR PACIENTES
    print("🧑‍⚕️ Creando pacientes...")
    
    patients_data = [
        {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'dni': '12345678',
            'phone': '987123456',
            'email': 'juan.perez@email.com',
            'address': 'Av. Principal 123, Lima',
            'birth_date': date(1985, 3, 15),
            'gender': 'M',
            'blood_type': 'O+',
            'emergency_contact_name': 'Ana Pérez',
            'emergency_contact_phone': '987123457',
            'emergency_contact_relationship': 'Esposa'
        },
        {
            'first_name': 'María',
            'last_name': 'González',
            'dni': '87654321',
            'phone': '987234567',
            'email': 'maria.gonzalez@email.com',
            'address': 'Jr. Libertad 456, Lima',
            'birth_date': date(1990, 7, 22),
            'gender': 'F',
            'blood_type': 'A+',
            'emergency_contact_name': 'Pedro González',
            'emergency_contact_phone': '987234568',
            'emergency_contact_relationship': 'Hermano'
        },
        {
            'first_name': 'Carlos',
            'last_name': 'Sánchez',
            'dni': '11223344',
            'phone': '987345678',
            'email': 'carlos.sanchez@email.com',
            'address': 'Calle Lima 789, Callao',
            'birth_date': date(1978, 12, 3),
            'gender': 'M',
            'blood_type': 'B+',
            'emergency_contact_name': 'Rosa Sánchez',
            'emergency_contact_phone': '987345679',
            'emergency_contact_relationship': 'Madre'
        },
        {
            'first_name': 'Ana',
            'last_name': 'Torres',
            'dni': '44332211',
            'phone': '987456789',
            'email': 'ana.torres@email.com',
            'address': 'Av. Universitaria 321, San Miguel',
            'birth_date': date(1995, 5, 18),
            'gender': 'F',
            'blood_type': 'AB+',
            'emergency_contact_name': 'Luis Torres',
            'emergency_contact_phone': '987456790',
            'emergency_contact_relationship': 'Padre'
        },
        {
            'first_name': 'Luis',
            'last_name': 'Morales',
            'dni': '55667788',
            'phone': '987567890',
            'email': 'luis.morales@email.com',
            'address': 'Jr. Junín 654, Miraflores',
            'birth_date': date(1982, 9, 10),
            'gender': 'M',
            'blood_type': 'O-',
            'emergency_contact_name': 'Carmen Morales',
            'emergency_contact_phone': '987567891',
            'emergency_contact_relationship': 'Esposa'
        },
        {
            'first_name': 'Carmen',
            'last_name': 'Vega',
            'dni': '99887766',
            'phone': '987678901',
            'email': 'carmen.vega@email.com',
            'address': 'Calle Real 987, San Isidro',
            'birth_date': date(1988, 11, 25),
            'gender': 'F',
            'blood_type': 'A-',
            'emergency_contact_name': 'Roberto Vega',
            'emergency_contact_phone': '987678902',
            'emergency_contact_relationship': 'Hermano'
        }
    ]
    
    patients = {}
    for patient_data in patients_data:
        patient = Patient(**patient_data)
        db.session.add(patient)
        patients[patient_data['dni']] = patient
    
    db.session.commit()
    print(f"   ✅ {len(patients_data)} pacientes creados")
    
    # 4. CREAR CITAS
    print("📅 Creando citas médicas...")
    
    # Obtener usuarios y pacientes para crear citas
    dr_garcia = users['dr.garcia']
    dr_rodriguez = users['dr.rodriguez']
    dr_lopez = users['dr.lopez']
    
    patient_juan = patients['12345678']
    patient_maria = patients['87654321']
    patient_carlos = patients['11223344']
    patient_ana = patients['44332211']
    
    # Crear citas variadas
    appointments_data = [
        # Citas de hoy
        {
            'patient': patient_juan,
            'doctor': dr_garcia,
            'specialty': specialties['Medicina General'],
            'date_time': datetime.now().replace(hour=9, minute=0, second=0, microsecond=0),
            'duration': 30,
            'status': 'scheduled',
            'reason': 'Consulta de rutina y chequeo general'
        },
        {
            'patient': patient_maria,
            'doctor': dr_rodriguez,
            'specialty': specialties['Cardiología'],
            'date_time': datetime.now().replace(hour=10, minute=30, second=0, microsecond=0),
            'duration': 45,
            'status': 'scheduled',
            'reason': 'Dolor en el pecho, palpitaciones'
        },
        {
            'patient': patient_carlos,
            'doctor': dr_lopez,
            'specialty': specialties['Neurología'],
            'date_time': datetime.now().replace(hour=14, minute=0, second=0, microsecond=0),
            'duration': 60,
            'status': 'scheduled',
            'reason': 'Dolores de cabeza frecuentes'
        },
        # Citas completadas (ayer)
        {
            'patient': patient_ana,
            'doctor': dr_garcia,
            'specialty': specialties['Medicina General'],
            'date_time': datetime.now() - timedelta(days=1),
            'duration': 30,
            'status': 'completed',
            'reason': 'Control mensual'
        },
        # Citas futuras
        {
            'patient': patient_juan,
            'doctor': dr_rodriguez,
            'specialty': specialties['Cardiología'],
            'date_time': datetime.now() + timedelta(days=3),
            'duration': 45,
            'status': 'scheduled',
            'reason': 'Seguimiento cardiológico'
        },
        {
            'patient': patient_maria,
            'doctor': dr_lopez,
            'specialty': specialties['Dermatología'],
            'date_time': datetime.now() + timedelta(days=7),
            'duration': 25,
            'status': 'scheduled',
            'reason': 'Revisión de lunares'
        }
    ]
    
    appointments = []
    for apt_data in appointments_data:
        appointment = Appointment(
            patient_id=apt_data['patient'].id,
            doctor_id=apt_data['doctor'].id,
            specialty_id=apt_data['specialty'].id,
            date_time=apt_data['date_time'],
            duration=apt_data['duration'],
            status=apt_data['status'],
            reason=apt_data['reason']
        )
        db.session.add(appointment)
        appointments.append(appointment)
    
    db.session.commit()
    print(f"   ✅ {len(appointments_data)} citas creadas")
    
    # 5. CREAR HISTORIALES MÉDICOS
    print("📋 Creando historiales médicos...")
    
    # Crear historial para la cita completada
    completed_appointment = [apt for apt in appointments if apt.status == 'completed'][0]
    
    medical_record = MedicalRecord(
        patient_id=completed_appointment.patient_id,
        doctor_id=completed_appointment.doctor_id,
        appointment_id=completed_appointment.id,
        symptoms='Fatiga leve, dolor de espalda ocasional',
        diagnosis='Estado general bueno. Tensión muscular por trabajo sedentario.',
        treatment='Ejercicios de estiramiento, caminar 30 min diarios',
        prescriptions='Paracetamol 500mg - 1 tableta cada 8 horas si hay dolor',
        blood_pressure='120/80',
        heart_rate=72,
        temperature=36.5,
        weight=70.5,
        height=175.0,
        observations='Paciente en buen estado general. Recomendar actividad física regular.',
        next_appointment_notes='Control en 3 meses. Seguimiento de actividad física.',
        consultation_date=completed_appointment.date_time
    )
    
    db.session.add(medical_record)
    db.session.commit()
    print("   ✅ 1 historial médico creado")
    
    print("\n🎉 ¡Datos de prueba creados exitosamente!")
    print("\n📊 RESUMEN DE DATOS CREADOS:")
    print(f"   👥 Usuarios: {len(users_data)} (1 admin, 3 médicos, 2 recepcionistas)")
    print(f"   🏥 Especialidades: {len(specialties_data)}")
    print(f"   🧑‍⚕️ Pacientes: {len(patients_data)}")
    print(f"   📅 Citas: {len(appointments_data)}")
    print(f"   📋 Historiales: 1")
    
    print("\n🔑 CREDENCIALES DE ACCESO:")
    print("   👨‍💼 ADMINISTRADOR:")
    print("      Usuario: admin")
    print("      Contraseña: admin123")
    print("\n   🩺 MÉDICOS:")
    print("      Usuario: dr.garcia / Contraseña: doc123")
    print("      Usuario: dr.rodriguez / Contraseña: doc123")
    print("      Usuario: dr.lopez / Contraseña: doc123")
    print("\n   📋 RECEPCIONISTAS:")
    print("      Usuario: recep.maria / Contraseña: recep123")
    print("      Usuario: recep.sofia / Contraseña: recep123")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        create_sample_data()
