from datetime import datetime
from app import db

class SalaryConfiguration(db.Model):
    """Configuración de salarios por porcentaje para doctores"""
    __tablename__ = 'salary_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación con doctor
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Porcentaje de comisión (ej: 40.00 para 40%)
    commission_percentage = db.Column(db.Numeric(5, 2), nullable=False, default=0.00)
    
    # Estado y fechas
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    effective_from = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relaciones
    doctor = db.relationship('User', backref='salary_configuration', lazy=True)
    
    def __repr__(self):
        return f'<SalaryConfiguration Doctor:{self.doctor_id} {self.commission_percentage}%>'
    
    def calculate_commission(self, specialty_price):
        """Calcular comisión basada en el precio de la especialidad"""
        if not self.is_active or self.commission_percentage <= 0:
            return 0.00
        
        commission = (specialty_price * self.commission_percentage) / 100
        return round(commission, 2)
    
    @staticmethod
    def get_doctor_commission_rate(doctor_id):
        """Obtener porcentaje de comisión de un doctor"""
        config = SalaryConfiguration.query.filter_by(
            doctor_id=doctor_id, 
            is_active=True
        ).first()
        
        return config.commission_percentage if config else 0.00
    
    @staticmethod
    def calculate_doctor_commission(doctor_id, specialty_price):
        """Calcular comisión de un doctor para un precio dado"""
        config = SalaryConfiguration.query.filter_by(
            doctor_id=doctor_id, 
            is_active=True
        ).first()
        
        if config:
            return config.calculate_commission(specialty_price)
        return 0.00


class CommissionRecord(db.Model):
    """Registro de comisiones generadas"""
    __tablename__ = 'commission_records'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    
    # Datos de la comisión
    specialty_price = db.Column(db.Numeric(10, 2), nullable=False)  # Precio base de la especialidad
    commission_percentage = db.Column(db.Numeric(5, 2), nullable=False)  # % aplicado en ese momento
    commission_amount = db.Column(db.Numeric(10, 2), nullable=False)  # Monto calculado
    
    # Fechas
    generated_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    payment_date = db.Column(db.Date, nullable=True)  # Cuando se pagó la factura
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Estado del pago de comisión
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'paid'
    
    # Relaciones
    doctor = db.relationship('User', backref='commission_records', lazy=True)
    invoice = db.relationship('Invoice', backref='commission_record', uselist=False, lazy=True)
    appointment = db.relationship('Appointment', backref='commission_record', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<CommissionRecord Doctor:{self.doctor_id} Amount:{self.commission_amount}>'
    
    @staticmethod
    def generate_commission_for_invoice(invoice):
        """Generar registro de comisión cuando se paga una factura"""
        try:
            # Verificar que la factura esté pagada
            if invoice.status != 'paid':
                return None
            
            # Verificar que no exista ya un registro de comisión
            existing = CommissionRecord.query.filter_by(invoice_id=invoice.id).first()
            if existing:
                return existing
            
            # Obtener precio de la especialidad del doctor
            if invoice.appointment and invoice.appointment.specialty:
                specialty_price = invoice.appointment.specialty.base_price
            else:
                # Si no hay cita asociada, usar el total de la factura como base
                specialty_price = invoice.total_amount
            
            # Obtener configuración del doctor
            config = SalaryConfiguration.query.filter_by(
                doctor_id=invoice.doctor_id,
                is_active=True
            ).first()
            
            if not config or config.commission_percentage <= 0:
                return None
            
            # Calcular comisión
            commission_amount = config.calculate_commission(specialty_price)
            
            # Crear registro de comisión
            commission = CommissionRecord(
                doctor_id=invoice.doctor_id,
                invoice_id=invoice.id,
                appointment_id=invoice.appointment_id,
                specialty_price=specialty_price,
                commission_percentage=config.commission_percentage,
                commission_amount=commission_amount,
                payment_date=invoice.payment_date,
                status='pending'
            )
            
            db.session.add(commission)
            db.session.commit()
            
            return commission
            
        except Exception as e:
            db.session.rollback()
            raise e
