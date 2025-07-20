from datetime import datetime
from app import db

class MedicalHistory:
    """Modelo Lógico de Historia Clínica - Datos completos del MINSA
    
    NOTA: Este es un modelo lógico que NO crea tabla en la base de datos.
    Se basa en el primer registro médico del paciente para simular la historia clínica.
    """
    
    def __init__(self, patient):
        """Inicializar historia clínica lógica para un paciente"""
        self.patient = patient
        self._first_record = None
        self._load_first_record()
    
    def _load_first_record(self):
        """Cargar el primer registro médico del paciente"""
        if self.patient and self.patient.medical_records:
            from app.models.medical_record import MedicalRecord
            self._first_record = self.patient.medical_records.order_by(
                MedicalRecord.created_at.asc()
            ).first()
    
    # === PROPIEDADES LÓGICAS ===
    
    @property
    def id(self):
        """ID lógico basado en el paciente"""
        return self.patient.id if self.patient else None
    
    @property
    def medical_history_number(self):
        """Número único de historia clínica usando el método estático"""
        return self.generate_unique_number(self.patient)
    
    @property
    def medical_record_number(self):
        """Alias para compatibilidad con templates existentes"""
        return self.medical_history_number
    
    @property
    def opening_date(self):
        """Fecha de apertura (fecha del primer registro)"""
        if self._first_record:
            return self._first_record.created_at.date()
        return self.patient.created_at.date() if self.patient else None
    
    @property
    def patient_id(self):
        """ID del paciente"""
        return self.patient.id if self.patient else None
    
    # === DATOS EXTRAÍDOS DE REGISTROS MÉDICOS ===
    
    @property
    def personal_history(self):
        """Antecedentes personales (extraídos de observaciones)"""
        if self._first_record and self._first_record.observations:
            obs = self._first_record.observations
            # Buscar sección de antecedentes personales
            patterns = ['antecedentes personales:', 'ANTECEDENTES PERSONALES:']
            for pattern in patterns:
                if pattern in obs:
                    parts = obs.split(pattern)
                    if len(parts) > 1:
                        # Buscar el final de esta sección
                        next_section = parts[1]
                        for end_pattern in ['ANTECEDENTES FAMILIARES:', 'antecedentes familiares:', 
                                          'ALERGIAS:', 'alergias:', '\n\n']:
                            if end_pattern in next_section:
                                next_section = next_section.split(end_pattern)[0]
                                break
                        return next_section.strip()
        return ""
    
    @property
    def family_history(self):
        """Antecedentes familiares (extraídos de observaciones)"""
        if self._first_record and self._first_record.observations:
            obs = self._first_record.observations
            patterns = ['antecedentes familiares:', 'ANTECEDENTES FAMILIARES:']
            for pattern in patterns:
                if pattern in obs:
                    parts = obs.split(pattern)
                    if len(parts) > 1:
                        # Buscar el final de esta sección
                        next_section = parts[1]
                        for end_pattern in ['ALERGIAS:', 'alergias:', 'MEDICAMENTOS:', 'medicamentos:', 
                                          'HÁBITOS:', 'hábitos:', '\n\n']:
                            if end_pattern in next_section:
                                next_section = next_section.split(end_pattern)[0]
                                break
                        return next_section.strip()
        return ""
    
    @property
    def smoking_habits(self):
        """Hábitos de tabaco (extraídos de observaciones)"""
        if self._first_record and self._first_record.observations:
            obs = self._first_record.observations
            patterns = ['hábitos de tabaco:', 'HÁBITOS DE TABACO:', 'tabaco:', 'TABACO:']
            for pattern in patterns:
                if pattern in obs:
                    parts = obs.split(pattern)
                    if len(parts) > 1:
                        # Buscar el final de esta sección
                        next_section = parts[1]
                        for end_pattern in ['HÁBITOS DE ALCOHOL:', 'hábitos de alcohol:', 'alcohol:', 'ALCOHOL:',
                                          'ACTIVIDAD:', 'actividad:', '\n\n']:
                            if end_pattern in next_section:
                                next_section = next_section.split(end_pattern)[0]
                                break
                        return next_section.strip()
        return ""
    
    @property
    def alcohol_habits(self):
        """Hábitos de alcohol (extraídos de observaciones)"""
        if self._first_record and self._first_record.observations:
            obs = self._first_record.observations
            patterns = ['hábitos de alcohol:', 'HÁBITOS DE ALCOHOL:', 'alcohol:', 'ALCOHOL:']
            for pattern in patterns:
                if pattern in obs:
                    parts = obs.split(pattern)
                    if len(parts) > 1:
                        # Buscar el final de esta sección
                        next_section = parts[1]
                        for end_pattern in ['USO DE DROGAS:', 'uso de drogas:', 'ACTIVIDAD FÍSICA:', 'actividad física:', 
                                          'ACTIVIDAD:', 'actividad:', 'OBSERVACIONES:', 'observaciones:', '\n\n']:
                            if end_pattern in next_section:
                                next_section = next_section.split(end_pattern)[0]
                                break
                        return next_section.strip()
        return ""
    
    @property
    def drug_habits(self):
        """Hábitos de drogas (extraídos de observaciones)"""
        if self._first_record and self._first_record.observations:
            obs = self._first_record.observations
            patterns = ['hábitos de drogas:', 'HÁBITOS DE DROGAS:', 'drogas:', 'DROGAS:', 'uso de drogas:', 'USO DE DROGAS:']
            for pattern in patterns:
                if pattern in obs:
                    parts = obs.split(pattern)
                    if len(parts) > 1:
                        # Buscar el final de esta sección
                        next_section = parts[1]
                        for end_pattern in ['ACTIVIDAD FÍSICA:', 'actividad física:', 'ACTIVIDAD:', 'actividad:',
                                          'OBSERVACIONES:', 'observaciones:', '\n\n']:
                            if end_pattern in next_section:
                                next_section = next_section.split(end_pattern)[0]
                                break
                        return next_section.strip()
        return ""
    
    @property
    def physical_activity(self):
        """Actividad física (extraídos de observaciones)"""
        if self._first_record and self._first_record.observations:
            obs = self._first_record.observations
            patterns = ['actividad física:', 'ACTIVIDAD FÍSICA:', 'actividad:', 'ACTIVIDAD:']
            for pattern in patterns:
                if pattern in obs:
                    parts = obs.split(pattern)
                    if len(parts) > 1:
                        # Buscar el final de esta sección
                        next_section = parts[1]
                        for end_pattern in ['OBSERVACIONES DE CONSULTA:', 'observaciones de consulta:', 
                                          'OBSERVACIONES:', 'observaciones:', '\n\n']:
                            if end_pattern in next_section:
                                next_section = next_section.split(end_pattern)[0]
                                break
                        return next_section.strip()
        return ""
    
    @property
    def allergies(self):
        """Alergias (extraídas de observaciones)"""
        if self._first_record and self._first_record.observations:
            obs = self._first_record.observations
            patterns = ['alergias:', 'ALERGIAS:']
            for pattern in patterns:
                if pattern in obs:
                    parts = obs.split(pattern)
                    if len(parts) > 1:
                        # Buscar el final de esta sección
                        next_section = parts[1]
                        for end_pattern in ['MEDICAMENTOS CRÓNICOS:', 'medicamentos crónicos:', 'MEDICAMENTOS ACTUALES:', 'medicamentos actuales:', 
                                          'MEDICAMENTOS:', 'medicamentos:', 'HISTORIA QUIRÚRGICA:', 'historia quirúrgica:',
                                          'HÁBITOS:', 'hábitos:', '\n\n']:
                            if end_pattern in next_section:
                                next_section = next_section.split(end_pattern)[0]
                                break
                        return next_section.strip()
        return ""
    
    @property
    def chronic_medications(self):
        """Medicamentos crónicos (extraídos de observaciones o prescripciones)"""
        if self._first_record:
            # Primero buscar en observaciones
            if self._first_record.observations:
                obs = self._first_record.observations
                patterns = ['medicamentos crónicos:', 'MEDICAMENTOS CRÓNICOS:', 'medicamentos actuales:', 'MEDICAMENTOS ACTUALES:',
                          'medicamentos:', 'MEDICAMENTOS:']
                for pattern in patterns:
                    if pattern in obs:
                        parts = obs.split(pattern)
                        if len(parts) > 1:
                            # Buscar el final de esta sección
                            next_section = parts[1]
                            for end_pattern in ['HISTORIA QUIRÚRGICA:', 'historia quirúrgica:', 'HÁBITOS DE TABACO:', 'hábitos de tabaco:',
                                              'HÁBITOS:', 'hábitos:', 'ACTIVIDAD:', 'actividad:', '\n\n']:
                                if end_pattern in next_section:
                                    next_section = next_section.split(end_pattern)[0]
                                    break
                            result = next_section.strip()
                            # Siempre retornar el resultado encontrado, incluso si parece vacío
                            return result
            
            # Si no encontró en observaciones, buscar en prescripciones
            if self._first_record.prescriptions:
                return self._first_record.prescriptions.strip()
        return ""

    @property
    def surgical_history(self):
        """Historia quirúrgica (extraída de observaciones)"""
        if self._first_record and self._first_record.observations:
            obs = self._first_record.observations
            patterns = ['historia quirúrgica:', 'HISTORIA QUIRÚRGICA:', 'cirugías:', 'CIRUGÍAS:', 
                       'antecedentes quirúrgicos:', 'ANTECEDENTES QUIRÚRGICOS:']
            for pattern in patterns:
                if pattern in obs:
                    parts = obs.split(pattern)
                    if len(parts) > 1:
                        # Buscar el final de esta sección
                        next_section = parts[1]
                        for end_pattern in ['ALERGIAS:', 'alergias:', 'MEDICAMENTOS:', 'medicamentos:', '\n\n']:
                            if end_pattern in next_section:
                                next_section = next_section.split(end_pattern)[0]
                                break
                        return next_section.strip()
        return ""
    
    @property
    def created_at(self):
        """Fecha de creación"""
        return self._first_record.created_at if self._first_record else self.patient.created_at
    
    @property
    def updated_at(self):
        """Fecha de actualización"""
        return self._first_record.updated_at if self._first_record else self.patient.updated_at
    
    # === MÉTODOS LÓGICOS ===
    
    @staticmethod
    def generate_unique_number(patient):
        """Generar número único de historia clínica"""
        if patient:
            return f"HC-{patient.dni}-{patient.id:04d}"
        return None
    
    @staticmethod
    def validate_history_number(history_number):
        """Validar formato de número de historia clínica
        
        Args:
            history_number (str): Número de historia a validar
            
        Returns:
            tuple: (is_valid, message)
        """
        if not history_number:
            return False, "Número de historia requerido"
        
        # Formato esperado: HC-DNI-ID
        if not history_number.startswith("HC-"):
            return False, "Formato inválido. Debe comenzar con 'HC-'"
        
        parts = history_number.split("-")
        if len(parts) != 3:
            return False, "Formato inválido. Debe ser HC-DNI-ID"
        
        try:
            # Validar que DNI sea numérico
            dni = int(parts[1])
            if dni < 10000000 or dni > 99999999:
                return False, "DNI inválido en número de historia"
            
            # Validar que ID sea numérico
            patient_id = int(parts[2])
            if patient_id < 1:
                return False, "ID de paciente inválido"
                
        except ValueError:
            return False, "Formato inválido. DNI e ID deben ser numéricos"
        
        return True, "Número de historia válido"
    
    @classmethod
    def create_for_patient(cls, patient):
        """Crear historia clínica lógica para un paciente"""
        return cls(patient)
    
    @classmethod
    def get_for_patient(cls, patient):
        """Obtener historia clínica lógica para un paciente
        
        Returns:
            MedicalHistory: Si el paciente tiene registros médicos con información sustancial
            None: Si el paciente no tiene registros médicos o solo tiene registros vacíos
        """
        # Solo devolver historia clínica si el paciente tiene registros médicos con información sustancial
        if patient and patient.medical_records.count() > 0:
            # Verificar si al menos un registro médico tiene información sustancial
            for record in patient.medical_records:
                # Contar observaciones con información estructurada de historia clínica
                has_substantial_observations = False
                if record.observations and record.observations.strip():
                    # Verificar si las observaciones contienen información de historia clínica
                    obs_upper = record.observations.upper()
                    has_substantial_observations = any([
                        'ANTECEDENTES PERSONALES' in obs_upper,
                        'ANTECEDENTES FAMILIARES' in obs_upper,
                        'ALERGIAS' in obs_upper,
                        'MEDICAMENTOS ACTUALES' in obs_upper,
                        'HÁBITOS' in obs_upper,
                        len(record.observations.strip()) > 50  # Observaciones sustanciales
                    ])
                
                has_substantial_info = any([
                    record.symptoms and record.symptoms.strip(),
                    record.diagnosis and record.diagnosis.strip(),
                    record.treatment and record.treatment.strip(),
                    record.prescriptions and record.prescriptions.strip(),
                    has_substantial_observations,
                    record.blood_pressure,
                    record.heart_rate,
                    record.temperature,
                    record.weight,
                    record.height
                ])
                if has_substantial_info:
                    return cls(patient)
        return None
    
    def has_complete_data(self):
        """Verificar si la historia clínica tiene datos completos"""
        return bool(self.personal_history or self.family_history or self.allergies)
    
    def get_summary(self):
        """Obtener resumen de la historia clínica"""
        return {
            'number': self.medical_history_number,
            'opening_date': self.opening_date,
            'patient_name': self.patient.full_name if self.patient else 'N/A',
            'patient_dni': self.patient.dni if self.patient else 'N/A',
            'patient_age': self.patient.age if self.patient else 'N/A',
            'patient_gender': self.patient.gender if self.patient else 'N/A',
            'has_personal_history': bool(self.personal_history),
            'has_family_history': bool(self.family_history),
            'has_allergies': bool(self.allergies),
            'has_chronic_medications': bool(self.chronic_medications),
            'total_consultations': self.patient.get_medical_records_count() if self.patient else 0,
            'first_consultation': self.opening_date,
            'last_consultation': self.patient.get_last_consultation().consultation_date if self.patient and self.patient.get_last_consultation() else None
        }
    
    def get_complete_history(self):
        """Obtener historia clínica completa con todos los datos"""
        return {
            'identification': {
                'number': self.medical_history_number,
                'opening_date': self.opening_date,
                'patient_name': self.patient.full_name if self.patient else 'N/A',
                'dni': self.patient.dni if self.patient else 'N/A',
                'birth_date': self.patient.birth_date if self.patient else None,
                'age': self.patient.age if self.patient else 'N/A',
                'gender': self.patient.gender if self.patient else 'N/A',
                'address': self.patient.address if self.patient else 'N/A',
                'phone': self.patient.phone if self.patient else 'N/A',
                'emergency_contact': {
                    'name': self.patient.emergency_contact_name if self.patient else 'N/A',
                    'phone': self.patient.emergency_contact_phone if self.patient else 'N/A',
                    'relationship': self.patient.emergency_contact_relationship if self.patient else 'N/A'
                }
            },
            'clinical_history': {
                'personal_history': self.personal_history,
                'family_history': self.family_history,
                'allergies': self.allergies,
                'chronic_medications': self.chronic_medications,
                'surgical_history': self.surgical_history
            },
            'habits': {
                'smoking': self.smoking_habits,
                'alcohol': self.alcohol_habits,
                'drugs': self.drug_habits,
                'physical_activity': self.physical_activity
            },
            'consultations': {
                'total': self.patient.get_medical_records_count() if self.patient else 0,
                'first': self.opening_date,
                'last': self.patient.get_last_consultation().consultation_date if self.patient and self.patient.get_last_consultation() else None
            }
        }
    
    def __repr__(self):
        return f'<MedicalHistory {self.medical_history_number} - {self.patient.full_name if self.patient else "N/A"}>'
