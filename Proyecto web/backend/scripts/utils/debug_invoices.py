#!/usr/bin/env python3
"""
Script para diagnosticar el problema de servicios duplicados en facturas
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

def main():
    app = create_app()
    with app.app_context():
        print("=== DIAGNÓSTICO DE FACTURAS Y SERVICIOS ===\n")
        
        # Obtener las últimas 5 facturas
        recent_invoices = Invoice.query.order_by(Invoice.id.desc()).limit(5).all()
        
        if not recent_invoices:
            print("No se encontraron facturas.")
            return
        
        for invoice in recent_invoices:
            print(f"Factura: {invoice.invoice_number}")
            print(f"Paciente: {invoice.patient.full_name if invoice.patient else 'N/A'}")
            print(f"Estado: {invoice.status}")
            print(f"Subtotal: S/ {invoice.subtotal}")
            print(f"Total: S/ {invoice.total_amount}")
            print(f"Método de pago: {invoice.payment_method}")
            print(f"Cita ID: {invoice.appointment_id}")
            
            if invoice.appointment_id:
                appointment = Appointment.query.get(invoice.appointment_id)
                if appointment:
                    specialty = Specialty.query.get(appointment.specialty_id)
                    print(f"Especialidad: {specialty.name if specialty else 'N/A'}")
                    print(f"Precio base especialidad: S/ {specialty.base_price if specialty else 'N/A'}")
            
            print("\nServicios:")
            for service in invoice.services:
                print(f"  - {service.description}")
                print(f"    Cantidad: {service.quantity}")
                print(f"    Precio unitario: S/ {service.unit_price}")
                print(f"    Total: S/ {service.get_total()}")
                print(f"    Notas: {service.notes}")
            
            print(f"\nTotal calculado desde servicios: S/ {sum(service.get_total() for service in invoice.services)}")
            print("-" * 50)
        
        # Verificar precios de especialidades
        print("\n=== PRECIOS DE ESPECIALIDADES ===")
        specialties = Specialty.query.all()
        for specialty in specialties:
            print(f"{specialty.name}: S/ {specialty.base_price}")
        
        print("\n=== VERIFICACIÓN COMPLETA ===")

if __name__ == "__main__":
    main()
