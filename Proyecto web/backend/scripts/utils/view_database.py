#!/usr/bin/env python3
"""
Script para ver el contenido de las tablas de la base de datos
"""
import os
from app import create_app, db
from app.models import User, Patient, Appointment, MedicalRecord, Specialty
from app.models.invoice import Invoice, InvoiceService

def view_database():
    # Crear la aplicación
    app = create_app(os.getenv('FLASK_ENV') or 'default')
    
    with app.app_context():
        print("=" * 60)
        print("CONTENIDO DE LA BASE DE DATOS")
        print("=" * 60)
        
        # USUARIOS
        print("\n=== USUARIOS ===")
        users = User.query.all()
        if users:
            for user in users:
                print(f"ID: {user.id}, Nombre: {user.first_name} {user.last_name}, "
                      f"Email: {user.email}, Rol: {user.role}, Activo: {user.is_active}")
        else:
            print("No hay usuarios registrados")
        
        # PACIENTES
        print("\n=== PACIENTES ===")
        patients = Patient.query.all()
        if patients:
            for patient in patients:
                print(f"ID: {patient.id}, Nombre: {patient.first_name} {patient.last_name}, "
                      f"DNI: {patient.dni}, Email: {patient.email}, Activo: {patient.is_active}")
        else:
            print("No hay pacientes registrados")
        
        # ESPECIALIDADES
        print("\n=== ESPECIALIDADES ===")
        specialties = Specialty.query.all()
        if specialties:
            for specialty in specialties:
                print(f"ID: {specialty.id}, Nombre: {specialty.name}")
        else:
            print("No hay especialidades registradas")
        
        # CITAS
        print("\n=== CITAS ===")
        appointments = Appointment.query.all()
        if appointments:
            for apt in appointments:
                patient_name = f"{apt.patient.first_name} {apt.patient.last_name}" if apt.patient else "N/A"
                doctor_name = f"{apt.doctor.first_name} {apt.doctor.last_name}" if apt.doctor else "N/A"
                print(f"ID: {apt.id}, Paciente: {patient_name}, Doctor: Dr. {doctor_name}, "
                      f"Fecha: {apt.date_time}, Estado: {apt.status}")
        else:
            print("No hay citas registradas")
        
        # FACTURAS
        print("\n=== FACTURAS ===")
        invoices = Invoice.query.all()
        if invoices:
            for invoice in invoices:
                patient_name = f"{invoice.patient.first_name} {invoice.patient.last_name}" if invoice.patient else "N/A"
                print(f"ID: {invoice.id}, Paciente: {patient_name}, Total: S/ {invoice.total_amount}, "
                      f"Estado: {invoice.payment_status}, Fecha: {invoice.issue_date}")
        else:
            print("No hay facturas registradas")
        
        # SERVICIOS DE FACTURAS
        print("\n=== SERVICIOS DE FACTURAS ===")
        services = InvoiceService.query.all()
        if services:
            for service in services:
                print(f"ID: {service.id}, Factura: {service.invoice_id}, "
                      f"Descripción: {service.description}, Cantidad: {service.quantity}, "
                      f"Precio: S/ {service.unit_price}, Total: S/ {service.total_price}")
        else:
            print("No hay servicios de facturas registrados")
          # HISTORIALES MÉDICOS
        print("\n=== HISTORIALES MÉDICOS ===")
        records = MedicalRecord.query.all()
        if records:
            for record in records:
                patient_name = f"{record.patient.first_name} {record.patient.last_name}" if record.patient else "N/A"
                doctor_name = f"{record.doctor.first_name} {record.doctor.last_name}" if record.doctor else "N/A"
                diagnosis_preview = record.diagnosis[:50] + "..." if record.diagnosis and len(record.diagnosis) > 50 else record.diagnosis or "N/A"
                print(f"ID: {record.id}, Paciente: {patient_name}, Doctor: Dr. {doctor_name}, "
                      f"Fecha: {record.consultation_date}, Diagnóstico: {diagnosis_preview}")
        else:
            print("No hay historiales médicos registrados")
        
        print("\n" + "=" * 60)
        print("FIN DEL REPORTE")
        print("=" * 60)

if __name__ == '__main__':
    view_database()
