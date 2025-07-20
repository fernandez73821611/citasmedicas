from datetime import datetime
from app import db

class MedicalRecord(db.Model):
    """Modelo de Registro Médico/Consulta - Anamnesis por cada consulta
    
    NOTA: Mantiene compatibilidad total con la estructura actual de la base de datos.
    Los nuevos campos son lógicos y se mapean a los campos existentes.
    """
    __tablename__ = 'medical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    
    # Información médica (campos existentes - NO SE MODIFICAN)
    symptoms = db.Column(db.Text)           # síntomas reportados
    diagnosis = db.Column(db.Text)          # diagnóstico
    treatment = db.Column(db.Text)          # tratamiento prescrito
    prescriptions = db.Column(db.Text)      # medicamentos recetados
    
    # Signos vitales (campos existentes - NO SE MODIFICAN)
    blood_pressure = db.Column(db.String(20))    # presión arterial
    heart_rate = db.Column(db.Integer)           # frecuencia cardíaca
    temperature = db.Column(db.Numeric(4, 1))    # temperatura corporal
    weight = db.Column(db.Numeric(5, 2))         # peso en kg
    height = db.Column(db.Numeric(5, 2))         # altura en cm
    
    # Observaciones y notas (campos existentes - NO SE MODIFICAN)
    observations = db.Column(db.Text)       # observaciones del médico
    next_appointment_notes = db.Column(db.Text)  # notas para próxima cita
    
    # Timestamps (campos existentes - NO SE MODIFICAN)
    consultation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='medical_records')
    
    # === PROPIEDADES LÓGICAS PARA ANAMNESIS (mapean a campos existentes) ===
    
    @property
    def chief_complaint(self):
        """Motivo de consulta (mapea a symptoms)"""
        return self.symptoms or ""
    
    @chief_complaint.setter
    def chief_complaint(self, value):
        """Establecer motivo de consulta"""
        self.symptoms = value
    
    @property
    def current_illness(self):
        """Enfermedad actual (extraída de observations)"""
        if self.observations:
            obs = self.observations.lower()
            if 'enfermedad actual:' in obs:
                parts = obs.split('enfermedad actual:')
                if len(parts) > 1:
                    content = parts[1]
                    # Múltiples delimitadores de fin para ser más robusto
                    for delimiter in ['---fin enfermedad actual---', 'examen físico general:', 'examen físico:', 'examen por sistemas:', 'examen regional:', 'exámenes auxiliares:', 'diagnóstico:', 'tratamiento:', 'recomendaciones:', 'observaciones adicionales:']:
                        if delimiter in content:
                            content = content.split(delimiter)[0]
                            break
                    return content.strip()
        return ""

    @current_illness.setter
    def current_illness(self, value):
        """Establecer enfermedad actual"""
        if not self.observations:
            self.observations = ""
        
        # Agregar delimitador de fin para evitar mezcla de datos
        value_with_delimiter = f"{value}\n---fin enfermedad actual---" if value else ""
        
        if 'enfermedad actual:' not in self.observations.lower():
            self.observations += f"\n\nEnfermedad actual: {value_with_delimiter}"
        else:
            # Reemplazar la sección existente usando el delimitador
            obs_lower = self.observations.lower()
            start_marker = 'enfermedad actual:'
            
            start_idx = obs_lower.find(start_marker)
            if start_idx != -1:
                before = self.observations[:start_idx]
                
                # Buscar el final de la sección
                remaining = self.observations[start_idx + len(start_marker):]
                remaining_lower = remaining.lower()
                
                end_idx = len(remaining)
                for delimiter in ['---fin enfermedad actual---', 'examen físico general:', 'examen físico:', 'examen por sistemas:', 'examen regional:', 'exámenes auxiliares:', 'diagnóstico:', 'tratamiento:', 'recomendaciones:', 'observaciones adicionales:']:
                    idx = remaining_lower.find(delimiter)
                    if idx != -1:
                        end_idx = idx
                        break
                
                after = remaining[end_idx:]
                # Limpiar delimitador viejo si existe
                if after.lower().startswith('---fin enfermedad actual---'):
                    after = after[len('---fin enfermedad actual---'):].lstrip()
                
                self.observations = f"{before}{start_marker} {value_with_delimiter}\n{after}".strip()
    
    @property
    def respiratory_rate(self):
        """Frecuencia respiratoria (lógica - no existe en BD)"""
        # Extraer de observations si existe
        if self.observations:
            obs = self.observations.lower()
            if 'fr:' in obs or 'frecuencia respiratoria:' in obs:
                import re
                match = re.search(r'fr?:?\s*(\d+)', obs)
                if match:
                    return int(match.group(1))
        return None

    @respiratory_rate.setter
    def respiratory_rate(self, value):
        """Establecer frecuencia respiratoria"""
        if not self.observations:
            self.observations = ""
        if value:
            self.observations += f"\nFR: {value} rpm"
    
    @property
    def general_examination(self):
        """Examen físico general (extraído de observations)"""
        if self.observations:
            obs = self.observations.lower()
            # Buscar tanto "examen físico general:" como "examen físico:"
            for marker in ['examen físico general:', 'examen físico:']:
                if marker in obs:
                    parts = obs.split(marker)
                    if len(parts) > 1:
                        content = parts[1]
                        # Múltiples delimitadores de fin - incluir variantes
                        for delimiter in ['---fin examen físico general---', 'examen por sistemas:', 'examen sistémico:', 'examen sistemico:', 'examen regional:', 'exámenes auxiliares:', 'examenes auxiliares:', 'diagnóstico:', 'diagnostico:', 'tratamiento:', 'recomendaciones:', 'observaciones adicionales:']:
                            if delimiter in content:
                                content = content.split(delimiter)[0]
                                break
                        return content.strip()
        return ""

    @general_examination.setter
    def general_examination(self, value):
        """Establecer examen físico general"""
        if not self.observations:
            self.observations = ""
        
        # Agregar delimitador de fin para evitar mezcla de datos
        value_with_delimiter = f"{value}\n---fin examen físico general---" if value else ""
        
        # Buscar si ya existe alguna variante
        obs_lower = self.observations.lower()
        existing_marker = None
        for marker in ['examen físico general:', 'examen físico:']:
            if marker in obs_lower:
                existing_marker = marker
                break
        
        if not existing_marker:
            self.observations += f"\n\nExamen físico general: {value_with_delimiter}"
        else:
            # Reemplazar la sección existente
            start_idx = obs_lower.find(existing_marker)
            if start_idx != -1:
                before = self.observations[:start_idx]
                
                # Buscar el final de la sección
                remaining = self.observations[start_idx + len(existing_marker):]
                remaining_lower = remaining.lower()
                
                end_idx = len(remaining)
                for delimiter in ['---fin examen físico general---', 'examen por sistemas:', 'examen sistémico:', 'examen sistemico:', 'examen regional:', 'exámenes auxiliares:', 'examenes auxiliares:', 'diagnóstico:', 'diagnostico:', 'tratamiento:', 'recomendaciones:', 'observaciones adicionales:']:
                    idx = remaining_lower.find(delimiter)
                    if idx != -1:
                        end_idx = idx
                        break
                
                after = remaining[end_idx:]
                # Limpiar delimitador viejo si existe
                if after.lower().startswith('---fin examen físico general---'):
                    after = after[len('---fin examen físico general---'):].lstrip()
                
                self.observations = f"{before}Examen físico general: {value_with_delimiter}\n{after}".strip()
    
    @property
    def systemic_examination(self):
        """Examen por sistemas (extraído de observations)"""
        if self.observations:
            obs = self.observations.lower()
            # Buscar variantes del nombre
            for marker in ['examen por sistemas:', 'examen sistémico:', 'examen sistemico:']:
                if marker in obs:
                    parts = obs.split(marker)
                    if len(parts) > 1:
                        content = parts[1]
                        # Múltiples delimitadores de fin
                        for delimiter in ['---fin examen por sistemas---', '---fin examen sistémico---', 'examen regional:', 'exámenes auxiliares:', 'examenes auxiliares:', 'diagnóstico:', 'diagnostico:', 'tratamiento:', 'recomendaciones:', 'observaciones adicionales:']:
                            if delimiter in content:
                                content = content.split(delimiter)[0]
                                break
                        return content.strip()
        return ""

    @systemic_examination.setter
    def systemic_examination(self, value):
        """Establecer examen por sistemas"""
        if not self.observations:
            self.observations = ""
        
        # Agregar delimitador de fin para evitar mezcla de datos
        value_with_delimiter = f"{value}\n---fin examen por sistemas---" if value else ""
        
        # Buscar si ya existe alguna variante
        obs_lower = self.observations.lower()
        existing_marker = None
        for marker in ['examen por sistemas:', 'examen sistémico:', 'examen sistemico:']:
            if marker in obs_lower:
                existing_marker = marker
                break
        
        if not existing_marker:
            self.observations += f"\n\nExamen por sistemas: {value_with_delimiter}"
        else:
            # Reemplazar la sección existente
            start_idx = obs_lower.find(existing_marker)
            if start_idx != -1:
                before = self.observations[:start_idx]
                
                # Buscar el final de la sección
                remaining = self.observations[start_idx + len(existing_marker):]
                remaining_lower = remaining.lower()
                
                end_idx = len(remaining)
                for delimiter in ['---fin examen por sistemas---', '---fin examen sistémico---', 'examen regional:', 'exámenes auxiliares:', 'examenes auxiliares:', 'diagnóstico:', 'diagnostico:', 'tratamiento:', 'recomendaciones:', 'observaciones adicionales:']:
                    idx = remaining_lower.find(delimiter)
                    if idx != -1:
                        end_idx = idx
                        break
                
                after = remaining[end_idx:]
                # Limpiar delimitadores viejos si existen
                for old_delimiter in ['---fin examen por sistemas---', '---fin examen sistémico---']:
                    if after.lower().startswith(old_delimiter):
                        after = after[len(old_delimiter):].lstrip()
                        break
                
                self.observations = f"{before}Examen por sistemas: {value_with_delimiter}\n{after}".strip()
    
    @property
    def regional_examination(self):
        """Examen regional (extraído de observations)"""
        if self.observations:
            obs = self.observations.lower()
            if 'examen regional:' in obs:
                parts = obs.split('examen regional:')
                if len(parts) > 1:
                    content = parts[1]
                    # Múltiples delimitadores de fin
                    for delimiter in ['---fin examen regional---', 'exámenes auxiliares:', 'diagnóstico:', 'tratamiento:', 'recomendaciones:', 'observaciones adicionales:']:
                        if delimiter in content:
                            content = content.split(delimiter)[0]
                            break
                    return content.strip()
        return ""

    @regional_examination.setter
    def regional_examination(self, value):
        """Establecer examen regional"""
        if not self.observations:
            self.observations = ""
        
        # Agregar delimitador de fin para evitar mezcla de datos
        value_with_delimiter = f"{value}\n---fin examen regional---" if value else ""
        
        if 'examen regional:' not in self.observations.lower():
            self.observations += f"\n\nExamen regional: {value_with_delimiter}"
        else:
            # Reemplazar la sección existente
            obs_lower = self.observations.lower()
            start_marker = 'examen regional:'
            
            start_idx = obs_lower.find(start_marker)
            if start_idx != -1:
                before = self.observations[:start_idx]
                
                # Buscar el final de la sección
                remaining = self.observations[start_idx + len(start_marker):]
                remaining_lower = remaining.lower()
                
                end_idx = len(remaining)
                for delimiter in ['---fin examen regional---', 'exámenes auxiliares:', 'diagnóstico:', 'tratamiento:', 'recomendaciones:', 'observaciones adicionales:']:
                    idx = remaining_lower.find(delimiter)
                    if idx != -1:
                        end_idx = idx
                        break
                
                after = remaining[end_idx:]
                # Limpiar delimitador viejo si existe
                if after.lower().startswith('---fin examen regional---'):
                    after = after[len('---fin examen regional---'):].lstrip()
                
                self.observations = f"{before}{start_marker} {value_with_delimiter}\n{after}".strip()
    
    @property
    def auxiliary_exams(self):
        """Exámenes auxiliares (extraído de observations)"""
        if self.observations:
            obs = self.observations.lower()
            if 'exámenes auxiliares:' in obs:
                parts = obs.split('exámenes auxiliares:')
                if len(parts) > 1:
                    content = parts[1]
                    # Múltiples delimitadores de fin
                    for delimiter in ['---fin exámenes auxiliares---', 'diagnóstico:', 'tratamiento:', 'recomendaciones:', 'observaciones adicionales:']:
                        if delimiter in content:
                            content = content.split(delimiter)[0]
                            break
                    return content.strip()
        return ""

    @auxiliary_exams.setter
    def auxiliary_exams(self, value):
        """Establecer exámenes auxiliares"""
        if not self.observations:
            self.observations = ""
        
        # Agregar delimitador de fin para evitar mezcla de datos
        value_with_delimiter = f"{value}\n---fin exámenes auxiliares---" if value else ""
        
        if 'exámenes auxiliares:' not in self.observations.lower():
            self.observations += f"\n\nExámenes auxiliares: {value_with_delimiter}"
        else:
            # Reemplazar la sección existente
            obs_lower = self.observations.lower()
            start_marker = 'exámenes auxiliares:'
            
            start_idx = obs_lower.find(start_marker)
            if start_idx != -1:
                before = self.observations[:start_idx]
                
                # Buscar el final de la sección
                remaining = self.observations[start_idx + len(start_marker):]
                remaining_lower = remaining.lower()
                
                end_idx = len(remaining)
                for delimiter in ['---fin exámenes auxiliares---', 'diagnóstico:', 'tratamiento:', 'recomendaciones:', 'observaciones adicionales:']:
                    idx = remaining_lower.find(delimiter)
                    if idx != -1:
                        end_idx = idx
                        break
                
                after = remaining[end_idx:]
                # Limpiar delimitador viejo si existe
                if after.lower().startswith('---fin exámenes auxiliares---'):
                    after = after[len('---fin exámenes auxiliares---'):].lstrip()
                
                self.observations = f"{before}{start_marker} {value_with_delimiter}\n{after}".strip()
    
    @property
    def recommendations(self):
        """Recomendaciones (extraída de observations)"""
        if self.observations:
            obs = self.observations.lower()
            if 'recomendaciones:' in obs:
                parts = obs.split('recomendaciones:')
                if len(parts) > 1:
                    content = parts[1]
                    # Múltiples delimitadores de fin
                    for delimiter in ['---fin recomendaciones---', 'observaciones adicionales:', 'próxima cita:', 'proxima cita:']:
                        if delimiter in content:
                            content = content.split(delimiter)[0]
                            break
                    return content.strip()
        return ""

    @recommendations.setter
    def recommendations(self, value):
        """Establecer recomendaciones"""
        if not self.observations:
            self.observations = ""
        
        # Agregar delimitador de fin para evitar mezcla de datos
        value_with_delimiter = f"{value}\n---fin recomendaciones---" if value else ""
        
        if 'recomendaciones:' not in self.observations.lower():
            self.observations += f"\n\nRecomendaciones: {value_with_delimiter}"
        else:
            # Reemplazar la sección existente
            obs_lower = self.observations.lower()
            start_marker = 'recomendaciones:'
            
            start_idx = obs_lower.find(start_marker)
            if start_idx != -1:
                before = self.observations[:start_idx]
                
                # Buscar el final de la sección
                remaining = self.observations[start_idx + len(start_marker):]
                remaining_lower = remaining.lower()
                
                end_idx = len(remaining)
                for delimiter in ['---fin recomendaciones---', 'observaciones adicionales:', 'próxima cita:', 'proxima cita:']:
                    idx = remaining_lower.find(delimiter)
                    if idx != -1:
                        end_idx = idx
                        break
                
                after = remaining[end_idx:]
                # Limpiar delimitador viejo si existe
                if after.lower().startswith('---fin recomendaciones---'):
                    after = after[len('---fin recomendaciones---'):].lstrip()
                
                self.observations = f"{before}{start_marker} {value_with_delimiter}\n{after}".strip()
    
    @property
    def next_appointment_date(self):
        """Fecha de próxima cita (lógica - no existe en BD)"""
        # Extraer de next_appointment_notes si existe
        if self.next_appointment_notes:
            print(f"DEBUG: next_appointment_notes content: '{self.next_appointment_notes}'")
            import re
            from datetime import datetime
            
            # Buscar patrón más flexible
            patterns = [
                r'próxima cita:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
                r'proxima cita:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
                r'cita:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, self.next_appointment_notes.lower())
                if match:
                    print(f"DEBUG: Pattern matched: {pattern}, groups: {match.groups()}")
                    try:
                        date_str = match.group(1)
                        print(f"DEBUG: Date string found: {date_str}")
                        # Normalizar el separador
                        if '/' in date_str:
                            parsed_date = datetime.strptime(date_str, '%d/%m/%Y').date()
                            print(f"DEBUG: Parsed date: {parsed_date}")
                            return parsed_date
                        elif '-' in date_str:
                            parsed_date = datetime.strptime(date_str, '%d-%m-%Y').date()
                            print(f"DEBUG: Parsed date: {parsed_date}")
                            return parsed_date
                    except Exception as e:
                        print(f"DEBUG: Error parsing date: {e}")
                        continue
            print("DEBUG: No date pattern found")
        else:
            print("DEBUG: next_appointment_notes is empty or None")
        return None

    @next_appointment_date.setter
    def next_appointment_date(self, value):
        """Establecer fecha de próxima cita"""
        if not self.next_appointment_notes:
            self.next_appointment_notes = ""
        if value:
            self.next_appointment_notes += f"\nPróxima cita: {value.strftime('%d/%m/%Y')}"
    
    # === PROPIEDADES Y MÉTODOS ADICIONALES ===
    
    @property
    def bmi(self):
        """Calcular índice de masa corporal"""
        if self.weight and self.height:
            height_m = float(self.height) / 100  # convertir cm a metros
            return round(float(self.weight) / (height_m ** 2), 2)
        return None
    
    @property
    def bmi_category(self):
        """Categoría del IMC"""
        bmi = self.bmi
        if not bmi:
            return "N/A"
        
        if bmi < 18.5:
            return "Bajo peso"
        elif bmi < 25:
            return "Normal"
        elif bmi < 30:
            return "Sobrepeso"
        else:
            return "Obesidad"
    
    def has_complete_vitals(self):
        """Verificar si tiene signos vitales completos"""
        return all([
            self.blood_pressure,
            self.heart_rate,
            self.temperature,
            self.weight,
            self.height
        ])
    
    def has_complete_anamnesis(self):
        """Verificar si tiene anamnesis completa"""
        return all([
            self.chief_complaint,
            self.current_illness or self.symptoms  # fallback a symptoms
        ])
    
    def has_complete_examination(self):
        """Verificar si tiene examen físico completo"""
        return bool(self.general_examination or self.observations)
    
    def has_complete_diagnosis(self):
        """Verificar si tiene diagnóstico completo"""
        return bool(self.diagnosis)
    
    def is_complete_consultation(self):
        """Verificar si es una consulta completa"""
        return all([
            self.has_complete_anamnesis(),
            self.has_complete_vitals(),
            self.has_complete_examination(),
            self.has_complete_diagnosis()
        ])
    
    def get_patient_medical_history(self):
        """Obtener la historia clínica del paciente"""
        if self.patient:
            from app.models.medical_history import MedicalHistory
            return MedicalHistory.get_for_patient(self.patient)
        return None
    
    def get_doctor_specialty(self):
        """Obtener especialidad del médico"""
        return self.doctor.specialty.name if self.doctor and self.doctor.specialty else "General"
    
    def get_consultation_summary(self):
        """Obtener resumen de la consulta"""
        return {
            'id': self.id,
            'date': self.consultation_date,
            'patient': self.patient.full_name if self.patient else 'N/A',
            'patient_dni': self.patient.dni if self.patient else 'N/A',
            'doctor': self.doctor.full_name if self.doctor else 'N/A',
            'doctor_specialty': self.get_doctor_specialty(),
            'chief_complaint': self.chief_complaint,
            'diagnosis': self.diagnosis,
            'treatment': self.treatment,
            'is_complete': self.is_complete_consultation(),
            'has_vitals': self.has_complete_vitals()
        }
    
    def is_first_consultation_for_patient(self):
        """Verificar si es la primera consulta del paciente"""
        if not self.patient:
            return False
        
        first_record = self.patient.medical_records.order_by(
            MedicalRecord.created_at.asc()
        ).first()
        
        return first_record and first_record.id == self.id
    
    def get_all_patient_consultations(self):
        """Obtener todas las consultas del paciente"""
        if self.patient:
            return self.patient.medical_records.order_by(
                MedicalRecord.consultation_date.desc()
            ).all()
        return []
    
    # === COMPATIBILIDAD CON DATOS EXISTENTES ===
    
    def migrate_to_new_format(self):
        """Migrar datos existentes al nuevo formato lógico"""
        # Esta función no modifica la BD, solo actualiza los campos lógicos
        # para que funcionen con los datos actuales
        
        # Si symptoms existe pero chief_complaint no, usar symptoms
        if self.symptoms and not self.chief_complaint:
            # No se modifica BD, solo se lee lógicamente
            pass
        
        # Si next_appointment_notes existe pero recommendations no, usar next_appointment_notes
        if self.next_appointment_notes and not self.recommendations:
            # No se modifica BD, solo se lee lógicamente
            pass
        
        return True

    def __repr__(self):
        return f'<MedicalRecord {self.patient.full_name if self.patient else "N/A"} - {self.consultation_date}>'
    
    @property
    def additional_observations(self):
        """Extraer solo las observaciones adicionales del campo observations"""
        if not self.observations:
            return ""
        
        obs_lower = self.observations.lower()
        
        # Buscar diferentes variantes del marcador de observaciones adicionales
        patterns = ['observaciones adicionales:', 'observaciones del médico:', 'notas adicionales:']
        
        for pattern in patterns:
            if pattern in obs_lower:
                parts = obs_lower.split(pattern)
                if len(parts) > 1:
                    content = parts[1]
                    # Buscar delimitadores de fin o inicio de otras secciones
                    end_delimiters = [
                        '---fin observaciones---',
                        'enfermedad actual:',
                        'examen físico general:',
                        'examen sistémico:',
                        'examen regional:',
                        'exámenes auxiliares:',
                        'recomendaciones:',
                        'próxima cita:',
                        'proxima cita:'
                    ]
                    
                    for delimiter in end_delimiters:
                        if delimiter in content:
                            content = content.split(delimiter)[0]
                            break
                    
                    # Obtener el contenido original (con mayúsculas/minúsculas preservadas)
                    original_start_idx = self.observations.lower().find(pattern) + len(pattern)
                    original_content = self.observations[original_start_idx:]
                    
                    for delimiter in end_delimiters:
                        if delimiter in original_content.lower():
                            original_content = original_content[:original_content.lower().find(delimiter)]
                            break
                    
                    return original_content.strip()
        
        # Si no se encuentra el patrón específico, ver si todo el campo es observaciones adicionales
        # (sin otros marcadores de secciones)
        section_markers = [
            'enfermedad actual:',
            'examen físico general:',
            'examen sistémico:',
            'examen regional:',
            'exámenes auxiliares:',
            'recomendaciones:'
        ]
        
        has_sections = any(marker in obs_lower for marker in section_markers)
        if not has_sections:
            # Si no hay otros marcadores, todo el campo son observaciones adicionales
            return self.observations.strip()
        
        return ""

    @additional_observations.setter
    def additional_observations(self, value):
        """Establecer observaciones adicionales"""
        if not self.observations:
            self.observations = ""
        
        # Agregar delimitador de fin para evitar mezcla de datos
        value_with_delimiter = f"{value}\n---fin observaciones---" if value else ""
        
        if 'observaciones adicionales:' not in self.observations.lower():
            self.observations += f"\n\nObservaciones adicionales: {value_with_delimiter}"
        else:
            # Reemplazar la sección existente
            obs_lower = self.observations.lower()
            start_marker = 'observaciones adicionales:'
            
            start_idx = obs_lower.find(start_marker)
            if start_idx != -1:
                before = self.observations[:start_idx]
                
                # Buscar el final de la sección
                remaining = self.observations[start_idx + len(start_marker):]
                remaining_lower = remaining.lower()
                
                end_idx = len(remaining)
                for delimiter in ['---fin observaciones---', 'enfermedad actual:', 'examen físico general:', 'próxima cita:']:
                    idx = remaining_lower.find(delimiter)
                    if idx != -1:
                        end_idx = idx
                        break
                
                after = remaining[end_idx:]
                # Limpiar delimitador viejo si existe
                if after.lower().startswith('---fin observaciones---'):
                    after = after[len('---fin observaciones---'):].lstrip()
                
                self.observations = f"{before}{start_marker} {value_with_delimiter}\n{after}".strip()
    
    def can_be_edited_by(self, doctor_id):
        """Verificar si la consulta puede ser editada por el doctor especificado
        
        Restricciones:
        1. Solo el doctor que creó la consulta puede editarla
        2. Solo se puede editar dentro de 1 hora desde su creación
        """
        from datetime import datetime, timedelta
        
        # Solo el doctor que creó la consulta puede editarla
        if self.doctor_id != doctor_id:
            return False, "Solo el doctor que realizó la consulta puede editarla"
        
        # Verificar tiempo límite (1 hora desde creación)
        time_limit = self.created_at + timedelta(hours=1)
        current_time = datetime.utcnow()
        
        if current_time > time_limit:
            return False, "El tiempo límite para editar la consulta ha expirado (1 hora)"
        
        return True, "Consulta editable"
    
    @property
    def is_editable_by_current_doctor(self):
        """Helper property para templates - requiere contexto de flask_login"""
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            can_edit, _ = self.can_be_edited_by(current_user.id)
            return can_edit
        return False
    
    def get_edit_status_for_doctor(self, doctor_id):
        """Obtener estado detallado de edición para el doctor"""
        from datetime import datetime, timedelta
        
        can_edit, message = self.can_be_edited_by(doctor_id)
        
        # Calcular tiempo restante si es editable
        time_remaining = None
        if can_edit:
            time_limit = self.created_at + timedelta(hours=1)
            time_remaining = time_limit - datetime.utcnow()
            minutes_remaining = int(time_remaining.total_seconds() / 60)
        
        return {
            'can_edit': can_edit,
            'message': message,
            'time_remaining_minutes': minutes_remaining if can_edit else 0,
            'is_own_consultation': self.doctor_id == doctor_id
        }
