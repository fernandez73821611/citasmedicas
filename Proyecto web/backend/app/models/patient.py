from datetime import datetime, date
from app import db

class Patient(db.Model):
    """Modelo de paciente"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Información personal
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    dni = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Información de contacto
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)    # Información médica básica
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10))  # 'M', 'F', 'Other'
    blood_type = db.Column(db.String(5))  # 'A+', 'B-', etc.
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Contacto de emergencia
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relationship = db.Column(db.String(50))
    
    # Apoderado/Tutor Legal (para menores de edad)
    guardian_name = db.Column(db.String(100))
    guardian_dni = db.Column(db.String(20))
    guardian_phone = db.Column(db.String(20))
    guardian_relationship = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    
    # === MÉTODOS PARA HISTORIA CLÍNICA LÓGICA ===
    
    def has_medical_history(self):
        """Verificar si el paciente tiene historia clínica (al menos un registro médico)"""
        return self.medical_records.count() > 0
    
    def is_new_patient(self):
        """Verificar si es un paciente nuevo (sin historia clínica)"""
        return not self.has_medical_history()
    
    def get_medical_history(self):
        """Obtener la historia clínica lógica del paciente"""
        from app.models.medical_history import MedicalHistory
        return MedicalHistory.get_for_patient(self)
    
    def get_or_create_medical_history(self):
        """Obtener o crear historia clínica lógica del paciente"""
        from app.models.medical_history import MedicalHistory
        return MedicalHistory.create_for_patient(self)
    
    def get_patient_status_for_doctor(self):
        """Obtener el estado del paciente para el dashboard del doctor"""
        if self.is_new_patient():
            return {
                'status': 'new',
                'label': 'Paciente Nuevo',
                'action': 'Crear Historia + Consulta',
                'button_class': 'btn-primary',
                'button_text': 'Crear Historia + Consulta',
                'icon': 'fas fa-plus-circle',
                'color': 'primary'
            }
        else:
            return {
                'status': 'existing',
                'label': 'Tiene Historia',
                'action': 'Ver Historia + Consulta',
                'button_class': 'btn-success',
                'button_text': 'Ver Historia + Consulta',
                'icon': 'fas fa-eye',
                'color': 'success'
            }
    
    def get_medical_records_count(self):
        """Obtener el número total de registros médicos del paciente"""
        return self.medical_records.count()
    
    def get_consultation_count(self):
        """Obtener el número total de consultas/registros médicos del paciente
        
        Returns:
            int: Número total de consultas del paciente
        """
        return self.medical_records.count()
    
    def get_last_consultation(self):
        """Obtener la última consulta"""
        from app.models.medical_record import MedicalRecord
        return self.medical_records.order_by(MedicalRecord.consultation_date.desc()).first()
    
    def get_first_consultation(self):
        """Obtener la primera consulta (base para historia clínica)"""
        from app.models.medical_record import MedicalRecord
        return self.medical_records.order_by(MedicalRecord.created_at.asc()).first()
    
    def get_consultations_by_doctor(self, doctor_id):
        """Obtener consultas realizadas por un doctor específico"""
        return self.medical_records.filter_by(doctor_id=doctor_id).all()
    
    def has_been_seen_by_doctor(self, doctor_id):
        """Verificar si el paciente ha sido atendido por un doctor"""
        return self.medical_records.filter_by(doctor_id=doctor_id).count() > 0
    
    def get_complete_medical_summary(self):
        """Obtener resumen médico completo del paciente"""
        history = self.get_medical_history()
        last_consultation = self.get_last_consultation()
        
        return {
            'patient_info': {
                'full_name': self.full_name,
                'dni': self.dni,
                'age': self.age,
                'gender': self.gender,
                'blood_type': self.blood_type,
                'phone': self.phone,
                'address': self.address,
                'emergency_contact': {
                    'name': self.emergency_contact_name,
                    'phone': self.emergency_contact_phone,
                    'relationship': self.emergency_contact_relationship
                }
            },
            'medical_history': history.get_summary() if history else None,
            'consultation_summary': {
                'total_consultations': self.get_medical_records_count(),
                'last_consultation': last_consultation.consultation_date if last_consultation else None,
                'last_diagnosis': last_consultation.diagnosis if last_consultation else None,
                'last_doctor': last_consultation.doctor.full_name if last_consultation and last_consultation.doctor else None
            },
            'status': self.get_patient_status_for_doctor()
        }
    
    @property
    def full_name(self):
        """Nombre completo del paciente"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calcular edad del paciente"""
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    @property
    def is_minor(self):
        """Verificar si el paciente es menor de edad"""
        return self.age < 18
    
    @property
    def age_group(self):
        """Clasificar paciente por grupo etario para triage"""
        age = self.age
        if age < 2:
            return 'lactante'  # 0-2 años
        elif age < 6:
            return 'preescolar'  # 2-6 años
        elif age < 12:
            return 'escolar'  # 6-12 años
        elif age < 18:
            return 'adolescente'  # 12-18 años
        elif age < 65:
            return 'adulto'  # 18-65 años
        else:
            return 'adulto_mayor'  # 65+ años
    
    @property
    def age_group_label(self):
        """Etiqueta legible del grupo etario"""
        labels = {
            'lactante': 'Lactante (0-2 años)',
            'preescolar': 'Preescolar (2-6 años)',
            'escolar': 'Escolar (6-12 años)',
            'adolescente': 'Adolescente (12-18 años)',
            'adulto': 'Adulto (18-65 años)',
            'adulto_mayor': 'Adulto Mayor (65+ años)'
        }
        return labels.get(self.age_group, 'Sin clasificar')
    
    def needs_guardian_consent(self):
        """Verificar si necesita consentimiento del tutor"""
        return self.is_minor
    
    # === MÉTODOS PARA VERIFICACIÓN DE HISTORIA CLÍNICA ===
    
    def get_history_creation_date(self):
        """Obtener fecha de creación de historia clínica
        
        Returns:
            date: Fecha de creación o None si no existe
        """
        history = self.get_medical_history()
        return history.opening_date if history else None
    
    def get_unique_history_number(self):
        """Obtener número único de historia clínica
        
        Returns:
            str: Número de historia o None si no existe
        """
        history = self.get_medical_history()
        return history.medical_history_number if history else None
    
    def can_create_medical_history(self):
        """Verificar si se puede crear historia clínica
        
        Returns:
            tuple: (bool, str) - (puede_crear, mensaje)
        """
        if self.has_medical_history():
            return False, "El paciente ya tiene historia clínica"
        
        if not self.is_active:
            return False, "Paciente inactivo"
            
        if not self.dni:
            return False, "Paciente sin DNI válido"
            
        return True, "Puede crear historia clínica"
    
    def get_patient_status_for_doctor(self):
        """Obtener estado del paciente para el flujo del doctor
        
        Returns:
            dict: Estado completo del paciente
        """
        has_history = self.has_medical_history()
        total_consultations = self.get_consultation_count()
        
        status = {
            'has_medical_history': has_history,
            'is_new_patient': not has_history,
            'total_consultations': total_consultations,
            'needs_guardian': self.needs_guardian_consent(),
            'is_minor': self.is_minor,
            'age_group': self.age_group,
            'can_create_history': self.can_create_medical_history()[0]
        }
        
        if has_history:
            history = self.get_medical_history()
            status.update({
                'history_number': history.medical_history_number,
                'history_creation_date': history.opening_date,
                'expected_action': 'new_consultation'
            })
        else:
            status.update({
                'history_number': None,
                'history_creation_date': None,
                'expected_action': 'create_medical_history'
            })
        
        return status

    def __repr__(self):
        return f'<Patient {self.full_name} - DNI: {self.dni}>'
