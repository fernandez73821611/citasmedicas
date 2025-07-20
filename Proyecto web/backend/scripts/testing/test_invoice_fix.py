#!/usr/bin/env python3
"""
Script para probar la creación de una nueva factura y verificar la corrección
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.invoice import Invoice, InvoiceService
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.specialty import Specialty
from app.models.user import User
from decimal import Decimal
from datetime import date

def test_invoice_creation():
    app = create_app()
    with app.app_context():
        print("=== PRUEBA DE CREACIÓN DE FACTURA ===\n")
        
        # Buscar una cita de Cardiología
        cardiology_appointment = Appointment.query.join(Specialty).filter(
            Specialty.name == 'Cardiología'
        ).first()
        
        if not cardiology_appointment:
            print("No se encontró cita de Cardiología para probar")
            return
        
        patient = cardiology_appointment.patient
        specialty = Specialty.query.get(cardiology_appointment.specialty_id)
        
        print(f"Probando con:")
        print(f"- Paciente: {patient.full_name}")
        print(f"- Especialidad: {specialty.name}")
        print(f"- Precio base especialidad: S/ {specialty.base_price}")
        print(f"- Cita ID: {cardiology_appointment.id}")
        
        # Simular la creación de factura como hace el código corregido
        from app.models.invoice import Invoice, InvoiceService
        
        # Crear nueva factura
        invoice = Invoice(
            patient_id=patient.id,
            appointment_id=cardiology_appointment.id,
            doctor_id=cardiology_appointment.doctor_id,
            invoice_number=Invoice.get_next_invoice_number(),
            issue_date=date.today(),
            due_date=date.today(),
            subtotal=Decimal('0.00'),
            total_amount=Decimal('0.00'),
            discount_percentage=0.0,
            tax_percentage=0.0,
            status='paid',
            payment_date=date.today(),
            payment_method='efectivo',
            notes=f"Pago por consulta médica - {patient.full_name}",
            created_by=1  # Assumir ID de usuario admin
        )
        
        # Agregar a la base de datos
        from app import db
        db.session.add(invoice)
        db.session.flush()
        
        # Limpiar cualquier servicio existente
        existing_services = InvoiceService.query.filter_by(invoice_id=invoice.id).all()
        for existing_service in existing_services:
            db.session.delete(existing_service)
        db.session.flush()
        
        # Crear UN SOLO servicio con el precio correcto
        service_description = f"Consulta médica - {specialty.name}"
        service_price = specialty.base_price
        
        service = InvoiceService(
            invoice_id=invoice.id,
            description=service_description,
            quantity=1,
            unit_price=service_price,
            notes=cardiology_appointment.notes
        )
        
        db.session.add(service)
        
        # Recalcular totales
        invoice.calculate_totals()
        
        # Marcar como pagada
        invoice.mark_as_paid('efectivo', date.today())
        
        # Guardar cambios
        db.session.commit()
        
        print(f"\n=== FACTURA CREADA ===")
        print(f"Número: {invoice.invoice_number}")
        print(f"Subtotal: S/ {invoice.subtotal}")
        print(f"Total: S/ {invoice.total_amount}")
        print(f"Servicios:")
        for service in invoice.services:
            print(f"  - {service.description}")
            print(f"    Precio: S/ {service.unit_price}")
            print(f"    Total: S/ {service.get_total()}")
        
        print(f"\nTotal calculado desde servicios: S/ {sum(service.get_total() for service in invoice.services)}")
        
        # Verificar que coincida con el precio de la especialidad
        if invoice.total_amount == specialty.base_price:
            print("✅ ¡CORRECTO! El precio coincide con la especialidad")
        else:
            print("❌ ERROR: El precio no coincide")
            
        # Verificar que solo hay un servicio
        if len(invoice.services) == 1:
            print("✅ ¡CORRECTO! Solo hay un servicio")
        else:
            print(f"❌ ERROR: Hay {len(invoice.services)} servicios en lugar de 1")

if __name__ == "__main__":
    test_invoice_creation()
