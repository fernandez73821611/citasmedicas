from datetime import datetime
from app import db

class Triage(db.Model):
    """Modelo de triage - evaluación inicial del paciente por enfermera"""
    __tablename__ = 'triages'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    nurse_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Signos vitales básicos
    blood_pressure_systolic = db.Column(db.Integer)  # presión sistólica
    blood_pressure_diastolic = db.Column(db.Integer)  # presión diastólica
    heart_rate = db.Column(db.Integer)  # frecuencia cardíaca (bpm)
    temperature = db.Column(db.Numeric(4, 1))  # temperatura corporal (°C)
    respiratory_rate = db.Column(db.Integer)  # frecuencia respiratoria
    oxygen_saturation = db.Column(db.Integer)  # saturación de oxígeno (%)
    weight = db.Column(db.Numeric(5, 2))  # peso en kg
    height = db.Column(db.Numeric(5, 2))  # altura en cm
    
    # Información clínica inicial
    chief_complaint = db.Column(db.Text, nullable=False)  # motivo principal de consulta
    pain_scale = db.Column(db.Integer)  # escala de dolor (0-10)
    
    # Clasificación de prioridad
    # 'alta': Urgente - requiere atención inmediata
    # 'media': Moderada - puede esperar un poco
    # 'baja': No urgente - consulta de rutina
    priority_level = db.Column(db.String(10), nullable=False, default='media')
    
    # Información médica importante
    allergies = db.Column(db.Text)  # alergias conocidas
    current_medications = db.Column(db.Text)  # medicamentos actuales
    blood_type = db.Column(db.String(10))  # tipo de sangre (A+, B-, O+, etc.)
    
    # Estado del triage
    # 'pending': Pendiente de completar
    # 'completed': Completado, listo para doctor
    # 'in_consultation': Paciente con doctor
    status = db.Column(db.String(20), default='pending', nullable=False)
    
    # Observaciones adicionales de la enfermera
    nurse_observations = db.Column(db.Text)
    
    # Campos específicos por edad - Lactantes (0-2 años)
    feeding_status = db.Column(db.String(20))  # normal, poor, vomiting, refusing
    sleep_pattern = db.Column(db.String(20))  # normal, restless, excessive, poor
    irritability = db.Column(db.String(20))  # calm, mild_irritable, inconsolable
    fontanel = db.Column(db.String(20))  # normal, bulging, sunken, closed
    
    # Campos específicos por edad - Preescolares (2-6 años)
    psychomotor_development = db.Column(db.String(20))  # appropriate, delayed, advanced
    social_behavior = db.Column(db.String(20))  # cooperative, anxious, aggressive, withdrawn
    toilet_training = db.Column(db.String(20))  # independent, partial, not_started
    
    # Campos específicos por edad - Escolares (6-12 años)
    school_performance = db.Column(db.String(20))  # good, average, poor
    physical_activity = db.Column(db.String(20))  # active, sedentary, limited
    mood_state = db.Column(db.String(20))  # happy, sad, anxious, irritable
    
    # Campos específicos por edad - Adolescentes (12-18 años)
    pubertal_development = db.Column(db.String(20))  # appropriate, early, delayed
    menstruation_status = db.Column(db.String(20))  # not_applicable, regular, irregular, not_started
    risk_behaviors = db.Column(db.String(50))  # none, smoking, alcohol, drugs, multiple
    
    # Campos específicos por edad - Adultos Mayores (65+ años)
    mobility_status = db.Column(db.String(20))  # independent, walker, wheelchair, assisted, bedridden
    cognitive_status = db.Column(db.String(20))  # alert, confused, forgetful, disoriented, dementia
    fall_risk = db.Column(db.String(20))  # low, moderate, high, previous_falls
    functional_status = db.Column(db.String(20))  # independent, partial_assistance, total_assistance, deteriorated
    chronic_conditions = db.Column(db.Text)  # condiciones crónicas conocidas
    medication_polypharmacy = db.Column(db.Text)  # medicamentos actuales (polifarmacia)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)  # cuando se completó el triage
    
    # Relaciones
    patient = db.relationship('Patient', foreign_keys=[patient_id], backref='triages')
    appointment = db.relationship('Appointment', foreign_keys=[appointment_id], backref='triage')
    nurse = db.relationship('User', foreign_keys=[nurse_id], backref='triages')

    def get_age_specific_validations(self):
        """Validaciones específicas por grupo etario"""
        if not hasattr(self, 'patient') or not self.patient:
            return self._original_vital_signs_check()
        
        age_group = self.patient.age_group
        abnormal = []
        
        if age_group == 'lactante':
            # Lactantes: No presión arterial, validaciones específicas
            if self.heart_rate:
                if self.heart_rate > 160 or self.heart_rate < 100:
                    abnormal.append('frecuencia cardíaca (lactantes: 100-160 bpm)')
            
            if self.temperature:
                temp = float(self.temperature)
                if temp > 37.8 or temp < 36.5:
                    abnormal.append('temperatura (lactantes: 36.5-37.8°C)')
                    
        elif age_group == 'preescolar':
            # Preescolares: validaciones según sub-edad
            if self.patient.age >= 3:
                # Mayores de 3 años: evaluar presión arterial
                if self.blood_pressure_systolic:
                    if self.blood_pressure_systolic > 110 or self.blood_pressure_systolic < 85:
                        abnormal.append('presión sistólica (preescolar: 85-110 mmHg)')
                        
                if self.blood_pressure_diastolic:
                    if self.blood_pressure_diastolic > 75 or self.blood_pressure_diastolic < 55:
                        abnormal.append('presión diastólica (preescolar: 55-75 mmHg)')
            
            if self.heart_rate:
                if self.heart_rate > 130 or self.heart_rate < 90:
                    abnormal.append('frecuencia cardíaca (preescolar: 90-130 bpm)')
                    
        elif age_group == 'escolar':
            # Escolares: evaluación más completa
            if self.blood_pressure_systolic:
                if self.blood_pressure_systolic > 120 or self.blood_pressure_systolic < 90:
                    abnormal.append('presión sistólica (escolar: 90-120 mmHg)')
                    
            if self.blood_pressure_diastolic:
                if self.blood_pressure_diastolic > 80 or self.blood_pressure_diastolic < 60:
                    abnormal.append('presión diastólica (escolar: 60-80 mmHg)')
                    
            if self.heart_rate:
                if self.heart_rate > 110 or self.heart_rate < 70:
                    abnormal.append('frecuencia cardíaca (escolar: 70-110 bpm)')
                    
        elif age_group in ['adolescente', 'adulto']:
            # Adolescentes y adultos: validación estándar
            return self._original_vital_signs_check()
            
        elif age_group == 'adulto_mayor':
            # Adultos mayores: tolerancias especiales
            if self.blood_pressure_systolic:
                if self.blood_pressure_systolic > 140 or self.blood_pressure_systolic < 90:
                    abnormal.append('presión sistólica (adulto mayor: 90-140 mmHg)')
                    
            if self.blood_pressure_diastolic:
                if self.blood_pressure_diastolic > 90 or self.blood_pressure_diastolic < 60:
                    abnormal.append('presión diastólica (adulto mayor: 60-90 mmHg)')
                    
            if self.heart_rate:
                if self.heart_rate > 90 or self.heart_rate < 50:
                    abnormal.append('frecuencia cardíaca (adulto mayor: 50-90 bpm)')
                    
            # Tolerancia especial en temperatura
            if self.temperature:
                temp = float(self.temperature)
                if temp > 37.0 or temp < 35.5:
                    abnormal.append('temperatura (adulto mayor: 35.5-37.0°C)')
                    
            # Tolerancia menor en saturación de oxígeno
            if self.oxygen_saturation and self.oxygen_saturation < 90:
                abnormal.append('saturación de oxígeno (adulto mayor: ≥90%)')
        
        else:
            # Validación estándar para otros grupos
            return self._original_vital_signs_check()
        
        # Validaciones comunes para todos los grupos (excepto adulto mayor que tiene sus propias validaciones)
        if age_group != 'adulto_mayor':
            if self.temperature:
                temp = float(self.temperature)
                if temp > 37.5 or temp < 36.0:
                    abnormal.append('temperatura')
                    
            if self.oxygen_saturation and self.oxygen_saturation < 95:
                abnormal.append('saturación de oxígeno')
        
        return abnormal
    
    @property
    def blood_pressure(self):
        """Presión arterial en formato "120/80" """
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None
    
    @property
    def bmi(self):
        """Calcular índice de masa corporal"""
        if self.weight and self.height:
            height_m = float(self.height) / 100  # convertir cm a metros
            return round(float(self.weight) / (height_m ** 2), 2)
        return None
    
    @property
    def priority_color(self):
        """Color para mostrar la prioridad en la interfaz"""
        colors = {
            'alta': 'danger',
            'media': 'warning', 
            'baja': 'success'
        }
        return colors.get(self.priority_level, 'secondary')
    
    @property
    def priority_label(self):
        """Etiqueta legible para la prioridad"""
        labels = {
            'alta': 'Prioridad Alta',
            'media': 'Prioridad Media',
            'baja': 'Prioridad Baja'
        }
        return labels.get(self.priority_level, 'Sin Clasificar')
    
    def is_vital_signs_abnormal(self):
        """Verificar signos vitales anormales usando validaciones específicas por edad"""
        if hasattr(self, 'get_age_specific_validations'):
            return self.get_age_specific_validations()
        else:
            # Fallback al método original si no hay paciente asignado
            return self._original_vital_signs_check()
    
    def _original_vital_signs_check(self):
        """Verificación original de signos vitales (para adultos o fallback)"""
        abnormal = []
        
        # Presión arterial
        if self.blood_pressure_systolic:
            if self.blood_pressure_systolic > 140 or self.blood_pressure_systolic < 90:
                abnormal.append('presión sistólica')
        
        if self.blood_pressure_diastolic:
            if self.blood_pressure_diastolic > 90 or self.blood_pressure_diastolic < 60:
                abnormal.append('presión diastólica')
        
        # Frecuencia cardíaca
        if self.heart_rate:
            if self.heart_rate > 100 or self.heart_rate < 60:
                abnormal.append('frecuencia cardíaca')
        
        # Temperatura
        if self.temperature:
            if float(self.temperature) > 37.5 or float(self.temperature) < 36.0:
                abnormal.append('temperatura')
        
        # Saturación de oxígeno
        if self.oxygen_saturation:
            if self.oxygen_saturation < 95:
                abnormal.append('saturación de oxígeno')
        
        return abnormal
    
    def mark_completed(self):
        """Marcar el triage como completado"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        
        # Si hay cita asociada, actualizar su estado
        if self.appointment:
            self.appointment.status = 'ready_for_doctor'
    
    def __repr__(self):
        return f'<Triage {self.patient.full_name} - {self.priority_level} - {self.created_at}>'
