from datetime import datetime
from app import db
from sqlalchemy.sql import func

class Invoice(db.Model):
    """Modelo de factura médica"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Información de la factura
    invoice_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    due_date = db.Column(db.Date, nullable=False)    # Detalles financieros
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    tax_percentage = db.Column(db.Numeric(5, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Estado de pago: 'pending', 'paid', 'overdue', 'cancelled'
    status = db.Column(db.String(20), default='pending', nullable=False)
    payment_date = db.Column(db.Date, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)  # 'efectivo', 'tarjeta', 'transferencia', 'seguro'
    
    # Notas adicionales
    notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
      # Relaciones
    patient = db.relationship('Patient', backref='invoices', lazy=True)
    appointment = db.relationship('Appointment', backref='invoice', uselist=False, lazy=True)
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_invoices', lazy=True)
    created_by_user = db.relationship('User', foreign_keys=[created_by], backref='created_invoices', lazy=True)
    services = db.relationship('InvoiceService', backref='invoice', lazy=True, cascade='all, delete-orphan')    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
    
    def is_overdue(self):
        """Verificar si la factura está vencida"""
        if self.status == 'paid':
            return False
        from datetime import date
        return date.today() > self.due_date
    
    def days_overdue(self):
        """Días de vencimiento"""
        if not self.is_overdue():
            return 0
        from datetime import date
        return (date.today() - self.due_date).days
    
    def status_display(self):
        """Estado para mostrar en la interfaz"""
        if self.status == 'paid':
            return 'Pagada'
        elif self.is_overdue():
            return 'Vencida'
        elif self.status == 'pending':
            return 'Pendiente'
        elif self.status == 'cancelled':
            return 'Cancelada'
        return self.status.title()
    
    def calculate_totals(self):
        """Calcular totales automáticamente"""
        from decimal import Decimal
        
        # Calcular subtotal de servicios
        self.subtotal = sum(service.get_total() for service in self.services)
        
        # Calcular descuento - convertir porcentaje a Decimal
        discount_pct = Decimal(str(self.discount_percentage or 0))
        self.discount_amount = self.subtotal * (discount_pct / 100)
        subtotal_after_discount = self.subtotal - self.discount_amount
        
        # Calcular impuesto - convertir porcentaje a Decimal
        tax_pct = Decimal(str(self.tax_percentage or 0))
        self.tax_amount = subtotal_after_discount * (tax_pct / 100)
        
        # Calcular total
        self.total_amount = subtotal_after_discount + self.tax_amount
        
    def mark_as_paid(self, payment_method='efectivo', payment_date=None):
        """Marcar factura como pagada y generar comisión automáticamente"""
        self.status = 'paid'
        self.payment_method = payment_method
        self.payment_date = payment_date or datetime.utcnow().date()
        self.updated_at = datetime.utcnow()
        
        # Generar registro de comisión automáticamente
        try:
            from app.models.salary_configuration import CommissionRecord
            CommissionRecord.generate_commission_for_invoice(self)
        except Exception as e:
            # Log error but don't fail the payment process
            print(f"Error generating commission for invoice {self.id}: {str(e)}")
    
    @staticmethod
    def get_next_invoice_number():
        """Generar siguiente número de factura"""
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[1])
            return f"FAC-{last_number + 1:06d}"
        return "FAC-000001"


class InvoiceService(db.Model):
    """Modelo para los servicios incluidos en una factura"""
    __tablename__ = 'invoice_services'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    
    # Detalles del servicio
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<InvoiceService {self.description}>'
    
    def get_total(self):
        """Calcular total del servicio"""
        return self.quantity * self.unit_price
