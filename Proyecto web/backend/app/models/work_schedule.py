from datetime import datetime, time
from app import db
from sqlalchemy import Enum

class WorkSchedule(db.Model):
    """Modelo para configuración de horarios de trabajo de médicos"""
    __tablename__ = 'work_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.id'), nullable=True)  # Opcional, para horarios específicos por especialidad
    
    # Configuración de días
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Lunes, 1=Martes, ..., 6=Domingo
    
    # Horarios
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Configuración de intervalos
    appointment_duration = db.Column(db.Integer, default=30)  # Duración en minutos por cita
    break_start_time = db.Column(db.Time, nullable=True)  # Hora inicio de almuerzo/descanso
    break_end_time = db.Column(db.Time, nullable=True)    # Hora fin de almuerzo/descanso
    
    # Estado y configuración
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    max_patients_per_day = db.Column(db.Integer, default=None)  # Límite de pacientes por día
    
    # Rango de fechas de validez
    start_date = db.Column(db.Date, nullable=True)  # Fecha de inicio de validez
    end_date = db.Column(db.Date, nullable=True)    # Fecha de fin de validez
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='work_schedules')
    specialty = db.relationship('Specialty', foreign_keys=[specialty_id], backref='work_schedules')
    
    @property
    def day_name(self):
        """Nombre del día de la semana"""
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return days[self.day_of_week]
    
    @property
    def day_name_short(self):
        """Nombre corto del día"""
        days = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        return days[self.day_of_week]
    
    @property
    def time_range(self):
        """Rango de horario formateado"""
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    @property
    def break_time_range(self):
        """Rango de descanso formateado"""
        if self.break_start_time and self.break_end_time:
            return f"{self.break_start_time.strftime('%H:%M')} - {self.break_end_time.strftime('%H:%M')}"
        return None
    
    @property
    def date_range(self):
        """Rango de fechas de validez formateado"""
        if self.start_date and self.end_date:
            return f"{self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')}"
        elif self.start_date:
            return f"Desde {self.start_date.strftime('%d/%m/%Y')}"
        elif self.end_date:
            return f"Hasta {self.end_date.strftime('%d/%m/%Y')}"
        else:
            return "Sin límite de fechas"
    
    def get_available_slots(self, date=None):
        """Obtener slots disponibles para una fecha específica"""
        from datetime import datetime, timedelta
        
        if not date:
            date = datetime.now().date()
        
        # Verificar si es el día correcto de la semana
        if date.weekday() != self.day_of_week:
            return []
        
        # Verificar si la fecha está dentro del rango de vigencia
        if self.start_date and date < self.start_date:
            return []
        
        if self.end_date and date > self.end_date:
            return []
        
        slots = []
        current_time = datetime.combine(date, self.start_time)
        end_time = datetime.combine(date, self.end_time)
        
        while current_time < end_time:
            # Verificar si está en horario de descanso
            if (self.break_start_time and self.break_end_time and
                self.break_start_time <= current_time.time() < self.break_end_time):
                current_time += timedelta(minutes=self.appointment_duration)
                continue
            
            # Verificar si el slot está disponible (no tiene cita programada)
            from app.models.appointment import Appointment
            existing_appointment = Appointment.query.filter(
                Appointment.doctor_id == self.doctor_id,
                Appointment.date_time == current_time,
                Appointment.status.in_(['scheduled', 'in_triage', 'ready_for_doctor', 'in_consultation'])
            ).first()
            
            if not existing_appointment:
                slots.append(current_time.time())
            
            current_time += timedelta(minutes=self.appointment_duration)
        
        return slots
    
    def is_available_at(self, date_time):
        """Verificar si el doctor está disponible en una fecha/hora específica"""
        # Verificar día de la semana
        if date_time.weekday() != self.day_of_week:
            return False
        
        # Verificar horario de trabajo
        if not (self.start_time <= date_time.time() <= self.end_time):
            return False
        
        # Verificar horario de descanso
        if (self.break_start_time and self.break_end_time and
            self.break_start_time <= date_time.time() < self.break_end_time):
            return False
        
        # Verificar excepciones
        if (self.exception_date == date_time.date() and 
            self.exception_type == 'unavailable'):
            return False
        
        return True
    
    @classmethod
    def get_doctor_schedule(cls, doctor_id, day_of_week=None, specialty_id=None, for_date=None):
        """Obtener horario de un doctor específico"""
        query = cls.query.filter_by(doctor_id=doctor_id, is_active=True)
        
        if day_of_week is not None:
            query = query.filter_by(day_of_week=day_of_week)
        
        if specialty_id:
            query = query.filter_by(specialty_id=specialty_id)
        
        schedules = query.all()
        
        # Filtrar por fecha de validez si se proporciona
        if for_date:
            valid_schedules = []
            for schedule in schedules:
                if schedule.is_valid_for_date(for_date):
                    valid_schedules.append(schedule)
            return valid_schedules
        
        return schedules
    
    @classmethod
    def get_available_times(cls, doctor_id, date, specialty_id=None):
        """Obtener horarios disponibles para un doctor en una fecha específica"""
        day_of_week = date.weekday()
        
        # Primero buscar horarios específicos de la especialidad
        schedules = cls.get_doctor_schedule(doctor_id, day_of_week, specialty_id, for_date=date)
        
        # Si no hay horarios específicos de la especialidad, buscar horarios generales
        if not schedules and specialty_id:
            schedules = cls.get_doctor_schedule(doctor_id, day_of_week, None, for_date=date)
        
        available_times = []
        for schedule in schedules:
            if schedule.is_active:
                slots = schedule.get_available_slots(date)
                available_times.extend(slots)
        
        # Eliminar duplicados y ordenar
        available_times = list(set(available_times))
        available_times.sort()
        
        return available_times
    
    def is_valid_for_date(self, date):
        """Verificar si el horario es válido para una fecha específica"""
        # Verificar si es el día correcto de la semana
        if date.weekday() != self.day_of_week:
            return False
        
        # Verificar si la fecha está dentro del rango de vigencia
        if self.start_date and date < self.start_date:
            return False
        
        if self.end_date and date > self.end_date:
            return False
        
        return True
    
    def __repr__(self):
        specialty_name = self.specialty.name if self.specialty else "General"
        return f'<WorkSchedule Dr.{self.doctor.full_name} {self.day_name} {self.time_range} ({specialty_name})>'
