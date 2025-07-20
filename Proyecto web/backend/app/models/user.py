from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """Modelo de usuario - Administrador, Médico, Recepcionista"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Información personal
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
      # Role: 'admin', 'doctor', 'receptionist', 'nurse'
    role = db.Column(db.String(20), nullable=False, index=True)
    
    # Especialidad para doctores
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.id'), nullable=True)
    
    # Estado y timestamps
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
      # Relaciones
    # appointments = relación con Appointment (doctor)
    # medical_records = relación con MedicalRecord (doctor)
    specialty = db.relationship('Specialty', backref='doctors')
    
    def set_password(self, password):
        """Encriptar y guardar contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar contraseña"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}"
    
    def has_role(self, role):
        """Verificar si el usuario tiene un rol específico"""
        return self.role == role
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
