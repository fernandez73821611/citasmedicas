from datetime import datetime
from app import db

class Specialty(db.Model):
    """Modelo de especialidad médica"""
    __tablename__ = 'specialties'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Configuración de la especialidad
    consultation_duration = db.Column(db.Integer, default=30)  # duración en minutos
    base_price = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Estado
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    appointments = db.relationship('Appointment', backref='specialty', lazy='dynamic')
    
    def __repr__(self):
        return f'<Specialty {self.name}>'
