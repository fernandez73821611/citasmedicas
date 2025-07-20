#!/usr/bin/env python3
"""
Script para limpiar las facturas problemáticas de la base de datos
"""

from app import create_app, db
from app.models.invoice import Invoice, InvoiceService

def clean_invoices():
    """Eliminar todas las facturas con monto 0 o problemáticas"""
    
    # Obtener todas las facturas problemáticas
    problematic_invoices = Invoice.query.filter(
        db.or_(
            Invoice.total_amount == 0,
            Invoice.subtotal == 0,
            Invoice.issue_date == Invoice.due_date
        )
    ).all()
    
    print(f"Encontradas {len(problematic_invoices)} facturas problemáticas")
    
    if not problematic_invoices:
        print("No hay facturas problemáticas para eliminar")
        return
    
    # Mostrar detalles de las facturas a eliminar
    for invoice in problematic_invoices:
        print(f"Factura {invoice.invoice_number}: Monto={invoice.total_amount}, "
              f"Fecha={invoice.issue_date}, Vencimiento={invoice.due_date}")
    
    # Confirmar eliminación
    confirm = input("¿Desea eliminar estas facturas? (y/N): ")
    if confirm.lower() != 'y':
        print("Operación cancelada")
        return
    
    # Eliminar facturas (los servicios se eliminan automáticamente por CASCADE)
    for invoice in problematic_invoices:
        try:
            print(f"Eliminando factura {invoice.invoice_number}...")
            db.session.delete(invoice)
        except Exception as e:
            print(f"Error al eliminar factura {invoice.invoice_number}: {e}")
    
    # Confirmar cambios
    try:
        db.session.commit()
        print(f"Se eliminaron {len(problematic_invoices)} facturas exitosamente")
    except Exception as e:
        db.session.rollback()
        print(f"Error al confirmar cambios: {e}")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        clean_invoices()
