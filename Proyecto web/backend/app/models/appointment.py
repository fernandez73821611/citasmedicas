from datetime import datetime
from app import db

class Appointment(db.Model):
    """Modelo de cita médica"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.id'), nullable=False)
    
    # Información de la cita
    date_time = db.Column(db.DateTime, nullable=False, index=True)
    duration = db.Column(db.Integer, default=30)  # duración en minutos
    
    # Estado: 'scheduled', 'in_triage', 'ready_for_doctor', 'in_consultation', 'completed', 'cancelled', 'no_show'
    status = db.Column(db.String(20), default='scheduled', nullable=False)
    
    # Información adicional
    reason = db.Column(db.Text)  # motivo de la consulta
    notes = db.Column(db.Text)   # observaciones de la cita
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='appointments')
    medical_record = db.relationship('MedicalRecord', uselist=False, backref='appointment')
    
    @property
    def is_completed(self):
        """Verificar si la cita está completada"""
        return self.status == 'completed'
    
    @property
    def can_be_cancelled(self):
        """Verificar si la cita puede ser cancelada"""
        return self.status in ['scheduled'] and self.date_time > datetime.utcnow()
    
    @property
    def is_paid(self):
        """Verificar si la cita tiene pago confirmado"""
        # Buscar factura asociada a esta cita
        from app.models.invoice import Invoice
        invoice = Invoice.query.filter_by(appointment_id=self.id).first()
        
        if not invoice:
            return False
        
        # Verificar si la factura está marcada como pagada
        return invoice.status == 'paid'
    
    @property
    def payment_status(self):
        """Obtener estado de pago legible"""
        from app.models.invoice import Invoice
        invoice = Invoice.query.filter_by(appointment_id=self.id).first()
        
        if not invoice:
            return 'Sin factura'
        
        if invoice.status == 'paid':
            return 'Pagado'
        elif invoice.status == 'pending':
            return 'Pendiente'
        elif invoice.status == 'overdue':
            return 'Vencido'
        else:
            return 'Cancelado'
    
    def can_start_triage(self):
        """Verificar si se puede iniciar triage para esta cita"""
        from datetime import date
        
        # Debe estar programada, tener pago confirmado y ser del día de hoy
        is_today = self.date_time.date() == date.today()
        return self.status == 'scheduled' and self.is_paid and is_today

    @property
    def status_label(self):
        """Etiqueta legible del estado de la cita"""
        labels = {
            'scheduled': 'Programada',
            'in_triage': 'En Triage',
            'ready_for_doctor': 'Lista para Doctor',
            'in_consultation': 'En Consulta',
            'completed': 'Completada',
            'cancelled': 'Cancelada',
            'no_show': 'No asistió'
        }
        return labels.get(self.status, 'Estado desconocido')

    @property
    def status_color(self):
        """Color para mostrar el estado en la interfaz"""
        colors = {
            'scheduled': 'secondary',
            'in_triage': 'warning',
            'ready_for_doctor': 'info',
            'in_consultation': 'primary',
            'completed': 'success',
            'cancelled': 'danger',
            'no_show': 'dark'
        }
        return colors.get(self.status, 'secondary')

    def start_triage(self):
        """Iniciar el proceso de triage"""
        if self.can_start_triage():
            self.status = 'in_triage'
            return True
        return False

    def has_triage(self):
        """Verificar si la cita tiene triage asociado"""
        from app.models.triage import Triage
        return Triage.query.filter_by(appointment_id=self.id).first() is not None

    def get_triage(self):
        """Obtener el triage asociado a esta cita"""
        from app.models.triage import Triage
        return Triage.query.filter_by(appointment_id=self.id).first()

    def __repr__(self):
        return f'<Appointment {self.patient.full_name} - {self.doctor.full_name} - {self.date_time}>'
