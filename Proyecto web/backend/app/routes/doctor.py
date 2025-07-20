from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.utils.decorators import require_role
from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.user import User
from app.models.medical_history import MedicalHistory
from app import db
from datetime import datetime, date

# Blueprint para médico
bp = Blueprint('doctor', __name__)

def filter_real_consultations(medical_records):
    """
    Filtrar registros médicos para mostrar solo consultas reales,
    excluyendo registros que son solo historia clínica.
    
    Args:
        medical_records: Lista de objetos MedicalRecord
        
    Returns:
        Lista filtrada de consultas reales
    """
    real_consultations = []
    for record in medical_records:
        is_real_consultation = any([
            record.symptoms and record.symptoms.strip(),
            record.diagnosis and record.diagnosis.strip(),
            record.treatment and record.treatment.strip(),
            record.prescriptions and record.prescriptions.strip()
        ])
        if is_real_consultation:
            real_consultations.append(record)
    return real_consultations

def _build_observations_text(form):
    """Construir texto de observaciones desde el formulario"""
    observations = []
    
    # Enfermedad actual
    if form.get('current_illness'):
        observations.append(f"Enfermedad actual: {form.get('current_illness').strip()}")
    
    # Examen físico
    if form.get('general_examination'):
        observations.append(f"Examen físico general: {form.get('general_examination').strip()}")
    
    if form.get('systemic_examination'):
        observations.append(f"Examen sistémico: {form.get('systemic_examination').strip()}")
    
    if form.get('regional_examination'):
        observations.append(f"Examen regional: {form.get('regional_examination').strip()}")
    
    # Exámenes auxiliares
    if form.get('auxiliary_exams'):
        observations.append(f"Exámenes auxiliares: {form.get('auxiliary_exams').strip()}")
    
    # Recomendaciones
    if form.get('recommendations'):
        observations.append(f"Recomendaciones: {form.get('recommendations').strip()}")
    
    # Observaciones adicionales
    if form.get('observations'):
        observations.append(f"Observaciones adicionales: {form.get('observations').strip()}")
    
    return "\n\n".join(observations)

@bp.route('/dashboard')
@login_required
@require_role('doctor')
def dashboard():
    """Dashboard del médico"""
    today = date.today()
    
    # Citas de hoy (excluyendo las ya completadas)
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.date_time >= datetime.combine(today, datetime.min.time()),
        Appointment.date_time < datetime.combine(today, datetime.max.time()),
        Appointment.status != 'completed'  # Excluir citas completadas
    ).order_by(Appointment.date_time).all()
    
    # Citas listas para consulta (con triage completado, pero no completadas)
    ready_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.status == 'ready_for_doctor'
    ).order_by(Appointment.date_time).all()
    
    # Citas en triage actualmente
    in_triage_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.status == 'in_triage'
    ).order_by(Appointment.date_time).all()
    
    # Próximas citas (después de hoy)
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.date_time > datetime.combine(today, datetime.max.time())
    ).order_by(Appointment.date_time).limit(5).all()
    
    # Contar pacientes únicos que he atendido
    my_patients_count = Patient.query.join(Appointment).filter(
        Appointment.doctor_id == current_user.id
    ).distinct().count()
    
    # Consultas del mes actual (filtradas para contar solo consultas reales)
    start_of_month = datetime(today.year, today.month, 1)
    consultations_this_month_all = MedicalRecord.query.filter(
        MedicalRecord.doctor_id == current_user.id,
        MedicalRecord.consultation_date >= start_of_month
    ).all()
    
    # Contar solo consultas reales
    consultations_this_month = len(filter_real_consultations(consultations_this_month_all))
    
    # Últimas consultas (filtradas para mostrar solo consultas reales)
    recent_consultations_all = MedicalRecord.query.filter(
        MedicalRecord.doctor_id == current_user.id
    ).order_by(MedicalRecord.consultation_date.desc()).limit(10).all()
    
    # Filtrar y tomar solo las primeras 5 consultas reales
    recent_consultations = filter_real_consultations(recent_consultations_all)[:5]
    
    # Agregar información completa de estado de historia clínica para cada cita
    for appointment in ready_appointments:
        patient_status = appointment.patient.get_patient_status_for_doctor()
        appointment.patient_has_history = patient_status['has_medical_history']
        appointment.patient_status = patient_status
        appointment.expected_action = patient_status['expected_action']
    
    for appointment in today_appointments:
        patient_status = appointment.patient.get_patient_status_for_doctor()
        appointment.patient_has_history = patient_status['has_medical_history']
        appointment.patient_status = patient_status
        appointment.expected_action = patient_status['expected_action']
    
    return render_template('doctor/dashboard.html', 
                         title='Dashboard Médico',
                         today_appointments=today_appointments,
                         ready_appointments=ready_appointments,
                         in_triage_appointments=in_triage_appointments,
                         upcoming_appointments=upcoming_appointments,
                         my_patients_count=my_patients_count,
                         consultations_this_month=consultations_this_month,
                         recent_consultations=recent_consultations)

@bp.route('/appointments')
@login_required
@require_role('doctor')
def appointments():
    """Mis citas"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    patient_search = request.args.get('patient_search', '')
    
    # Query base - solo citas del doctor actual
    query = Appointment.query.filter_by(doctor_id=current_user.id)
    
    # Filtros
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    
    if patient_search:
        query = query.join(Patient).filter(
            (Patient.first_name.ilike(f'%{patient_search}%')) |
            (Patient.last_name.ilike(f'%{patient_search}%')) |
            (Patient.dni.ilike(f'%{patient_search}%'))
        )
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Appointment.date_time >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.filter(Appointment.date_time <= to_date)
        except ValueError:
            pass
      # Ordenar por fecha
    appointments = query.order_by(Appointment.date_time.desc()).all()
    
    # Agregar información adicional para determinar si se puede consultar
    current_datetime = datetime.now()
    for appointment in appointments:
        # Agregar atributo para saber si se puede consultar (cita de hoy o pasada)
        appointment.can_consult = (
            appointment.status in ['scheduled', 'confirmed'] and 
            appointment.date_time.date() <= current_datetime.date()
        )
    
    # Estadísticas rápidas
    today = date.today()
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.date_time >= datetime.combine(today, datetime.min.time()),
        Appointment.date_time < datetime.combine(today, datetime.max.time())
    ).count()
    
    pending_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.status.in_(['scheduled', 'confirmed']),
        Appointment.date_time > datetime.now()
    ).count()
    
    return render_template('doctor/appointments.html', 
                         title='Mis Citas',
                         appointments=appointments,
                         today_appointments=today_appointments,
                         pending_appointments=pending_appointments,
                         status_filter=status_filter,
                         date_from=date_from,
                         date_to=date_to,
                         patient_search=patient_search)

# RUTA COMENTADA: Funcionalidad redundante con clinical_histories
# La funcionalidad de historiales médicos individuales está disponible
# dentro de cada historia clínica de paciente
"""
@bp.route('/medical-records')
@login_required
@require_role('doctor')
def medical_records():
    \"\"\"Lista de historiales médicos del doctor\"\"\"
    page = request.args.get('page', 1, type=int)
    patient_search = request.args.get('patient_search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Query base
    query = MedicalRecord.query.filter_by(doctor_id=current_user.id)
    
    # Aplicar búsqueda por paciente si se proporciona
    if patient_search:
        query = query.join(Patient).filter(
            (Patient.first_name.ilike(f'%{patient_search}%')) |
            (Patient.last_name.ilike(f'%{patient_search}%')) |
            (Patient.dni.ilike(f'%{patient_search}%'))
        )
    
    # Aplicar filtros de fecha
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(MedicalRecord.consultation_date >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            # Agregar 23:59:59 para incluir todo el día
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.filter(MedicalRecord.consultation_date <= to_date)
        except ValueError:
            pass
    
    # Obtener resultados ordenados (sin paginación por ahora)
    medical_records = query.order_by(MedicalRecord.consultation_date.desc()).all()
    
    return render_template('doctor/medical_records.html',
                         title='Historiales Médicos',
                         medical_records=medical_records,
                         patient_search=patient_search,
                         date_from=date_from,
                         date_to=date_to)
"""

@bp.route('/medical-records/new', methods=['GET', 'POST'])
@login_required
@require_role('doctor')
def new_medical_record():
    """Crear nuevo historial médico"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            patient_id = request.form.get('patient_id')
            appointment_id = request.form.get('appointment_id')  # Opcional
            symptoms = request.form.get('symptoms', '').strip()
            diagnosis = request.form.get('diagnosis', '').strip()
            treatment = request.form.get('treatment', '').strip()
            prescriptions = request.form.get('prescriptions', '').strip()
            next_appointment_date = request.form.get('next_appointment_date', '').strip()
            next_appointment_notes = ""
            
            # DEBUG: Verificar qué viene del formulario
            print(f"DEBUG: next_appointment_date from form: [{next_appointment_date}]")
            print(f"DEBUG: All form data: {dict(request.form)}")
            
            # Procesar fecha de próxima cita si se proporciona
            if next_appointment_date:
                # Convertir fecha para guardarla en next_appointment_notes
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(next_appointment_date, '%Y-%m-%d')
                    date_formatted = date_obj.strftime('%d/%m/%Y')
                    next_appointment_notes = f"Próxima cita: {date_formatted}"
                    print(f"DEBUG: Fecha procesada: {date_formatted}")
                    print(f"DEBUG: next_appointment_notes final: {next_appointment_notes}")
                except ValueError as e:
                    print(f"DEBUG: Error en formato de fecha: {e}")
                    next_appointment_notes = ""
                    # Si hay error en el formato de fecha, ignora silenciosamente
                    pass
            
            # Signos vitales
            blood_pressure = request.form.get('blood_pressure', '').strip()
            heart_rate = request.form.get('heart_rate', '')
            temperature = request.form.get('temperature', '')
            weight = request.form.get('weight', '')
            height = request.form.get('height', '')
            
            # Validaciones básicas
            if not all([patient_id, symptoms, diagnosis]):
                flash('Los campos paciente, síntomas y diagnóstico son obligatorios', 'error')
                return redirect(request.url)
            
            # Verificar que el paciente existe
            patient = db.session.get(Patient, patient_id)
            if not patient:
                flash('Paciente no encontrado', 'error')
                return redirect(request.url)
            
            # Crear historial médico
            medical_record = MedicalRecord(
                patient_id=patient_id,
                doctor_id=current_user.id,
                appointment_id=appointment_id if appointment_id else None,
                symptoms=symptoms,
                diagnosis=diagnosis,
                treatment=treatment,
                prescriptions=prescriptions,
                observations=_build_observations_text(request.form),
                next_appointment_notes=next_appointment_notes,
                blood_pressure=blood_pressure if blood_pressure else None,
                heart_rate=int(heart_rate) if heart_rate and heart_rate.isdigit() else None,
                temperature=float(temperature) if temperature else None,
                weight=float(weight) if weight else None,
                height=float(height) if height else None,
                consultation_date=datetime.now()
            )
            
            from app import db
            db.session.add(medical_record)
            
            # Si viene de una cita, marcarla como completada
            if appointment_id:
                appointment = db.session.get(Appointment, appointment_id)
                if appointment and appointment.doctor_id == current_user.id:
                    appointment.status = 'completed'
            
            db.session.commit()
            
            flash(f'Historial médico creado exitosamente para {patient.full_name}', 'success')
            return redirect(url_for('doctor.clinical_histories'))
            
        except Exception as e:
            from app import db
            db.session.rollback()
            flash(f'Error al crear historial médico: {str(e)}', 'error')
    
    # GET request - mostrar formulario
    appointment_id = request.args.get('appointment_id')
    appointment = None
    
    if appointment_id:
        appointment = Appointment.query.filter_by(
            id=appointment_id,
            doctor_id=current_user.id
        ).first_or_404()
    
    # Obtener pacientes activos
    patients = Patient.query.filter_by(is_active=True).order_by(Patient.first_name).all()
    
    return render_template('doctor/medical_record_form.html',
                         title='Nuevo Historial Médico',
                         patients=patients,
                         appointment=appointment)

@bp.route('/medical-records/<int:id>')
@login_required
@require_role('doctor')
def view_medical_record(id):
    """Ver detalles del historial médico"""
    medical_record = MedicalRecord.query.filter_by(
        id=id,
        doctor_id=current_user.id
    ).first_or_404()
    
    # Obtener otros historiales del mismo paciente
    patient_records = MedicalRecord.query.filter_by(
        patient_id=medical_record.patient_id
    ).order_by(MedicalRecord.consultation_date.desc()).all()
    
    return render_template('doctor/medical_record_detail.html',
                         title=f'Historial: {medical_record.patient.full_name}',
                         medical_record=medical_record,
                         patient_records=patient_records)

@bp.route('/medical-records/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('doctor')
def edit_medical_record(id):
    """Editar historial médico"""
    medical_record = MedicalRecord.query.filter_by(
        id=id,
        doctor_id=current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        try:
            # Actualizar datos
            medical_record.symptoms = request.form.get('symptoms', '').strip()
            medical_record.diagnosis = request.form.get('diagnosis', '').strip()
            medical_record.treatment = request.form.get('treatment', '').strip()
            medical_record.prescriptions = request.form.get('prescriptions', '').strip()
            medical_record.observations = request.form.get('observations', '').strip()
            
            # Procesar fecha de próxima cita
            next_appointment_date = request.form.get('next_appointment_date', '').strip()
            if next_appointment_date:
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(next_appointment_date, '%Y-%m-%d')
                    date_formatted = date_obj.strftime('%d/%m/%Y')
                    medical_record.next_appointment_notes = f"Próxima cita: {date_formatted}"
                    print(f"DEBUG EDIT: Fecha procesada: {date_formatted}")
                except ValueError as e:
                    print(f"DEBUG EDIT: Error en formato de fecha: {e}")
                    medical_record.next_appointment_notes = ""
            else:
                medical_record.next_appointment_notes = ""
            
            # Signos vitales
            medical_record.blood_pressure = request.form.get('blood_pressure', '').strip() or None
            
            heart_rate = request.form.get('heart_rate', '')
            medical_record.heart_rate = int(heart_rate) if heart_rate and heart_rate.isdigit() else None
            
            temperature = request.form.get('temperature', '')
            medical_record.temperature = float(temperature) if temperature else None
            
            weight = request.form.get('weight', '')
            medical_record.weight = float(weight) if weight else None
            
            height = request.form.get('height', '')
            medical_record.height = float(height) if height else None
            
            medical_record.updated_at = datetime.now()
            
            from app import db
            db.session.commit()
            
            flash('Historial médico actualizado exitosamente', 'success')
            return redirect(url_for('doctor.view_medical_record', id=id))
            
        except Exception as e:
            from app import db
            db.session.rollback()
            flash(f'Error al actualizar historial: {str(e)}', 'error')
    
    return render_template('doctor/medical_record_form.html',
                         title='Editar Historial Médico',
                         medical_record=medical_record)

@bp.route('/patient/<int:patient_id>/history')
@login_required
@require_role('doctor')
def patient_history(patient_id):
    """Ver historial completo de un paciente"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Obtener todos los historiales del paciente
    medical_records = MedicalRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(MedicalRecord.consultation_date.desc()).all()
    
    # Obtener citas del paciente
    appointments = Appointment.query.filter_by(
        patient_id=patient_id
    ).order_by(Appointment.date_time.desc()).limit(10).all()
    
    return render_template('doctor/patient_history.html',
                         title=f'Historial: {patient.full_name}',
                         patient=patient,
                         medical_records=medical_records,
                         appointments=appointments)

@bp.route('/appointment/<int:appointment_id>/consult', methods=['GET', 'POST'])
@login_required
@require_role('doctor')
def consult_appointment(appointment_id):
    """Realizar consulta desde una cita programada"""
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=current_user.id
    ).first_or_404()
    
    # Verificar que la cita está lista para consulta (debe haber pasado por triage)
    if appointment.status not in ['ready_for_doctor', 'in_consultation']:
        flash('Esta cita no está lista para consulta. Debe haber completado el triage.', 'error')
        return redirect(url_for('doctor.dashboard'))
    
    # Redirigir al flujo de verificación de historia clínica
    return redirect(url_for('doctor.check_patient_history', 
                           patient_id=appointment.patient_id, 
                           appointment_id=appointment_id))

@bp.route('/view_triage/<int:appointment_id>')
@login_required
@require_role('doctor')
def view_triage(appointment_id):
    """Ver el triage de una cita específica"""
    # Verificar que la cita pertenece al doctor actual
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=current_user.id
    ).first_or_404()
    
    # Obtener el triage asociado
    triage = appointment.get_triage()
    if not triage:
        flash('Esta cita no tiene triage asociado', 'error')
        return redirect(url_for('doctor.dashboard'))
    
    return render_template('doctor/view_triage.html',
                         title=f'Triage - {appointment.patient.full_name}',
                         appointment=appointment,
                         triage=triage,
                         patient=appointment.patient)

@bp.route('/start_consultation/<int:appointment_id>')
@login_required
@require_role('doctor')
def start_consultation(appointment_id):
    """Iniciar consulta médica desde triage"""
    # Verificar que la cita pertenece al doctor actual
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=current_user.id
    ).first_or_404()
    
    # Verificar que la cita está lista para consulta
    if appointment.status != 'ready_for_doctor':
        flash('Esta cita no está lista para consulta', 'error')
        return redirect(url_for('doctor.dashboard'))
    
    # Cambiar estado a "in_consultation"
    appointment.status = 'in_consultation'
    db.session.commit()
    
    # Redirigir al flujo de verificación de historia clínica
    return redirect(url_for('doctor.check_patient_history', 
                           patient_id=appointment.patient_id, 
                           appointment_id=appointment_id))

@bp.route('/medical-history/<int:patient_id>')
@login_required
@require_role('doctor')
def view_medical_history(patient_id):
    """Ver la historia clínica completa de un paciente"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Verificar que el doctor ha atendido a este paciente
    has_attended = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).first()
    
    if not has_attended:
        flash('No tiene permisos para ver la historia clínica de este paciente', 'error')
        return redirect(url_for('doctor.clinical_histories'))
    
    # Obtener la historia clínica del paciente
    medical_history = patient.get_medical_history()
    
    # Obtener todas las consultas del paciente (de todos los doctores)
    all_consultations = MedicalRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(MedicalRecord.consultation_date.desc()).all()
    
    # Filtrar para mostrar solo consultas reales, no historia clínica
    real_consultations = filter_real_consultations(all_consultations)
    
    # Agregar información de edición para cada consulta
    consultations_with_edit_info = []
    for consultation in real_consultations:
        edit_status = consultation.get_edit_status_for_doctor(current_user.id)
        consultations_with_edit_info.append({
            'consultation': consultation,
            'edit_status': edit_status
        })
    
    # Obtener solo las consultas del doctor actual
    my_consultations_all = MedicalRecord.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).order_by(MedicalRecord.consultation_date.desc()).all()
    
    # Filtrar las consultas del doctor actual
    my_consultations = filter_real_consultations(my_consultations_all)
    
    return render_template('doctor/medical_history_view.html',
                         title=f'Historia Clínica - {patient.full_name}',
                         patient=patient,
                         medical_history=medical_history,
                         all_consultations=real_consultations,
                         consultations_with_edit_info=consultations_with_edit_info,
                         my_consultations=my_consultations,
                         has_medical_history=medical_history is not None)

@bp.route('/medical-history/<int:patient_id>/new', methods=['GET', 'POST'])
@login_required
@require_role('doctor')
def new_medical_history(patient_id):
    """Crear nueva historia clínica completa para un paciente"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Verificar que el doctor puede crear la historia (debe tener cita con el paciente)
    has_appointment = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).first()
    
    if not has_appointment:
        flash('No tiene permisos para crear historia clínica para este paciente', 'error')
        return redirect(url_for('doctor.clinical_histories'))
    
    # Verificar que no exista ya una historia clínica y validar que se puede crear
    can_create, validation_message = patient.can_create_medical_history()
    if not can_create:
        flash(f'No se puede crear historia clínica: {validation_message}', 'error')
        return redirect(url_for('doctor.clinical_histories'))
    
    existing_history = patient.get_medical_history()
    if existing_history:
        flash('Este paciente ya tiene una historia clínica. Puede crear una nueva consulta.', 'info')
        return redirect(url_for('doctor.view_medical_history', patient_id=patient_id))
    
    if request.method == 'POST':
        try:
            # Crear la información estructurada de historia clínica en observations
            # SIEMPRE incluir todas las secciones para evitar "No registrado" en la visualización
            history_info = []
            
            # Agregar antecedentes personales (siempre incluir la sección)
            personal_history = request.form.get('personal_history', '').strip()
            history_info.append(f"ANTECEDENTES PERSONALES:\n{personal_history or 'Sin antecedentes registrados'}")
            
            # Agregar antecedentes familiares (siempre incluir la sección)
            family_history = request.form.get('family_history', '').strip()
            history_info.append(f"ANTECEDENTES FAMILIARES:\n{family_history or 'Sin antecedentes registrados'}")
            
            # Agregar alergias (siempre incluir la sección)
            allergies = request.form.get('allergies', '').strip()
            history_info.append(f"ALERGIAS:\n{allergies or 'Sin alergias registradas'}")
            
            # Agregar medicamentos crónicos (siempre incluir la sección)
            chronic_medications = request.form.get('chronic_medications', '').strip()
            history_info.append(f"MEDICAMENTOS CRÓNICOS:\n{chronic_medications or 'Sin medicamentos registrados'}")
            
            # Agregar historia quirúrgica (siempre incluir la sección)
            surgical_history = request.form.get('surgical_history', '').strip()
            history_info.append(f"HISTORIA QUIRÚRGICA:\n{surgical_history or 'Sin cirugías registradas'}")
            
            # Agregar hábitos de tabaco (siempre incluir la sección)
            smoking_habits = request.form.get('smoking_habits', '').strip()
            history_info.append(f"HÁBITOS DE TABACO:\n{smoking_habits or 'No fuma'}")
            
            # Agregar hábitos de alcohol (siempre incluir la sección)
            alcohol_habits = request.form.get('alcohol_habits', '').strip()
            history_info.append(f"HÁBITOS DE ALCOHOL:\n{alcohol_habits or 'No consume alcohol'}")
            
            # Agregar uso de drogas (siempre incluir la sección)
            drug_habits = request.form.get('drug_habits', '').strip()
            history_info.append(f"USO DE DROGAS:\n{drug_habits or 'No consume drogas'}")
            
            # Agregar actividad física (siempre incluir la sección)
            physical_activity = request.form.get('physical_activity', '').strip()
            history_info.append(f"ACTIVIDAD FÍSICA:\n{physical_activity or 'Sin información de actividad física'}")
            
            # Combinar información de historia clínica con observaciones de la consulta
            # Siempre usar la información estructurada de historia clínica
            full_observations = "\n\n".join(history_info)
            
            # Validar que haya información de historia clínica
            has_medical_info = any([
                personal_history,
                family_history,
                allergies,
                chronic_medications,
                surgical_history,
                smoking_habits,
                alcohol_habits,
                drug_habits,
                physical_activity
            ])
            
            if not has_medical_info:
                flash('Debe proporcionar al menos alguna información médica para crear la historia clínica', 'error')
                return redirect(request.url)
            
            # Determinar qué acción realizar según el botón presionado
            action = request.form.get('action', 'save')
            
            if action == 'save':
                # SOLO GUARDAR HISTORIA CLÍNICA - No crear consulta
                # Crear un registro médico mínimo solo para almacenar la historia clínica
                medical_record = MedicalRecord(
                    patient_id=patient_id,
                    doctor_id=current_user.id,
                    observations=full_observations,
                    consultation_date=datetime.now(),
                    # No incluir datos de consulta (symptoms, diagnosis, treatment)
                    # Solo la información de historia clínica en observations
                )
                
                db.session.add(medical_record)
                db.session.commit()
                
                flash(f'Historia clínica guardada exitosamente para {patient.full_name}', 'success')
                return redirect(url_for('doctor.view_medical_history', patient_id=patient_id))
            
            elif action == 'save_and_consult':
                # GUARDAR HISTORIA CLÍNICA Y CONTINUAR A CONSULTA
                # Primero crear el registro base con la historia clínica
                base_record = MedicalRecord(
                    patient_id=patient_id,
                    doctor_id=current_user.id,
                    observations=full_observations,
                    consultation_date=datetime.now(),
                )
                
                db.session.add(base_record)
                db.session.commit()
                
                flash(f'Historia clínica guardada exitosamente para {patient.full_name}', 'success')
                # Redirigir a crear nueva consulta
                return redirect(url_for('doctor.new_consultation', patient_id=patient_id))
            
            else:
                flash('Acción no válida', 'error')
                return redirect(request.url)
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear historia clínica: {str(e)}', 'error')
    
    # GET request - mostrar formulario
    appointment_id = request.args.get('appointment_id')
    appointment = None
    
    if appointment_id:
        appointment = Appointment.query.filter_by(
            id=appointment_id,
            doctor_id=current_user.id,
            patient_id=patient_id
        ).first()
    
    return render_template('doctor/medical_history_form.html',
                         title=f'Nueva Historia Clínica - {patient.full_name}',
                         patient=patient,
                         appointment=appointment,
                         is_new_history=True,
                         current_datetime=datetime.now())

@bp.route('/consultation/<int:patient_id>/new', methods=['GET', 'POST'])
@login_required
@require_role('doctor')
def new_consultation(patient_id):
    """Crear nueva consulta para un paciente que ya tiene historia clínica"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Verificar que el doctor puede crear consulta (debe tener cita con el paciente)
    has_appointment = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).first()
    
    if not has_appointment:
        flash('No tiene permisos para crear consulta para este paciente', 'error')
        return redirect(url_for('doctor.clinical_histories'))
    
    # Verificar que existe historia clínica
    medical_history = patient.get_medical_history()
    if not medical_history:
        flash('Este paciente no tiene historia clínica. Debe crear primero la historia clínica completa.', 'error')
        return redirect(url_for('doctor.new_medical_history', patient_id=patient_id))
    
    if request.method == 'POST':
        try:
            # DEBUG: Mostrar todos los datos del formulario
            print("=== DEBUG: Datos del formulario de consulta ===")
            for key, value in request.form.items():
                print(f"{key}: '{value}'")
            print("=== FIN DEBUG ===")
            
            # Procesar fecha de próxima cita
            next_appointment_notes = request.form.get('next_appointment_notes', '').strip()
            next_appointment_date = request.form.get('next_appointment_date', '').strip()
            
            print(f"DEBUG: next_appointment_notes desde formulario: '{next_appointment_notes}'")
            print(f"DEBUG: next_appointment_date desde formulario: '{next_appointment_date}'")
            
            # Si hay fecha de próxima cita, agregarla a las notas
            if next_appointment_date:
                try:
                    date_obj = datetime.strptime(next_appointment_date, '%Y-%m-%d')
                    date_formatted = date_obj.strftime('%d/%m/%Y')
                    if next_appointment_notes:
                        next_appointment_notes += f"\nPróxima cita: {date_formatted}"
                    else:
                        next_appointment_notes = f"Próxima cita: {date_formatted}"
                    print(f"DEBUG: next_appointment_notes procesado: '{next_appointment_notes}'")
                except ValueError:
                    print(f"DEBUG: Error al procesar fecha: {next_appointment_date}")
                    pass
            
            # Crear nueva consulta
            medical_record = MedicalRecord(
                patient_id=patient_id,
                doctor_id=current_user.id,
                appointment_id=request.form.get('appointment_id') if request.form.get('appointment_id') else None,
                
                # Datos principales de la consulta
                symptoms=request.form.get('chief_complaint', '').strip(),
                diagnosis=request.form.get('diagnosis', '').strip(),
                treatment=request.form.get('treatment', '').strip(),
                prescriptions=request.form.get('prescriptions', '').strip(),
                observations=_build_observations_text(request.form),
                next_appointment_notes=next_appointment_notes,
                
                # Signos vitales
                blood_pressure=request.form.get('blood_pressure', '').strip() or None,
                heart_rate=int(request.form.get('heart_rate', 0)) if request.form.get('heart_rate') else None,
                temperature=float(request.form.get('temperature', 0)) if request.form.get('temperature') else None,
                weight=float(request.form.get('weight', 0)) if request.form.get('weight') else None,
                height=float(request.form.get('height', 0)) if request.form.get('height') else None,
                
                # Datos administrativos
                consultation_date=datetime.now()
            )
            
            # Validaciones básicas
            if not all([medical_record.symptoms, medical_record.diagnosis]):
                flash('Los campos motivo de consulta y diagnóstico son obligatorios', 'error')
                return redirect(request.url)
            
            db.session.add(medical_record)
            
            # Si viene de una cita, marcarla como completada
            if medical_record.appointment_id:
                appointment = db.session.get(Appointment, medical_record.appointment_id)
                if appointment and appointment.doctor_id == current_user.id:
                    appointment.status = 'completed'
            
            db.session.commit()
            
            # Verificar qué acción realizar según el botón presionado
            action = request.form.get('action', 'save')
            
            flash(f'Consulta registrada exitosamente para {patient.full_name}', 'success')
            
            if action == 'save_and_print':
                # Redirigir al ticket de impresión
                return redirect(url_for('doctor.print_consultation_ticket', id=medical_record.id))
            else:
                # Redirigir a la vista normal de consulta
                return redirect(url_for('doctor.view_consultation', id=medical_record.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar consulta: {str(e)}', 'error')
    
    # GET request - mostrar formulario
    appointment_id = request.args.get('appointment_id')
    appointment = None
    triage = None
    
    if appointment_id:
        appointment = Appointment.query.filter_by(
            id=appointment_id,
            doctor_id=current_user.id,
            patient_id=patient_id
        ).first()
        
        # Obtener el triage asociado a la cita si existe
        if appointment:
            from app.models.triage import Triage
            triage = Triage.query.filter_by(appointment_id=appointment_id).first()
    else:
        # Si no hay appointment_id específico, buscar la cita más reciente con triage
        # para prellenar los signos vitales
        from app.models.triage import Triage
        
        # Buscar todas las citas del paciente con este doctor
        all_appointments = Appointment.query.filter_by(
            patient_id=patient_id,
            doctor_id=current_user.id
        ).order_by(Appointment.date_time.desc()).all()
        
        recent_appointment = Appointment.query.filter_by(
            patient_id=patient_id,
            doctor_id=current_user.id
        ).filter(
            Appointment.status.in_(['ready_for_consultation', 'completed'])
        ).order_by(Appointment.date_time.desc()).first()
        
        if recent_appointment:
            appointment = recent_appointment
            triage = Triage.query.filter_by(appointment_id=recent_appointment.id).first()
        else:
            # Fallback: buscar cualquier cita con triage
            for apt in all_appointments:
                triage_check = Triage.query.filter_by(appointment_id=apt.id).first()
                if triage_check:
                    appointment = apt
                    triage = triage_check
                    break
    
    # Obtener las últimas 3 consultas del paciente para referencia
    recent_consultations = MedicalRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(MedicalRecord.consultation_date.desc()).limit(3).all()
    
    return render_template('doctor/consultation_form.html',
                         title=f'Nueva Consulta - {patient.full_name}',
                         patient=patient,
                         medical_record=None,  # Nueva consulta, no edición
                         medical_history=medical_history,
                         recent_consultations=recent_consultations,
                         appointment=appointment,
                         triage=triage,  # Datos del triage para pre-llenar signos vitales
                         current_datetime=datetime.now())

@bp.route('/consultation/<int:id>')
@login_required
@require_role('doctor')
def view_consultation(id):
    """Ver detalles de una consulta específica"""
    consultation = MedicalRecord.query.get_or_404(id)
    
    # Verificar que el doctor puede ver esta consulta
    # (Si es del doctor actual o si el doctor ha atendido al paciente)
    if consultation.doctor_id != current_user.id:
        has_attended = Appointment.query.filter_by(
            patient_id=consultation.patient_id,
            doctor_id=current_user.id
        ).first()
        
        if not has_attended:
            flash('No tiene permisos para ver esta consulta', 'error')
            return redirect(url_for('doctor.clinical_histories'))
    
    # Obtener la historia clínica del paciente
    medical_history = consultation.patient.get_medical_history()
    
    # Obtener otras consultas del mismo paciente
    other_consultations = MedicalRecord.query.filter(
        MedicalRecord.patient_id == consultation.patient_id,
        MedicalRecord.id != consultation.id
    ).order_by(MedicalRecord.consultation_date.desc()).limit(5).all()
    
    return render_template('doctor/consultation_view.html',
                         title=f'Consulta - {consultation.patient.full_name}',
                         consultation=consultation,
                         medical_record=consultation,  # Alias para compatibilidad con template
                         patient=consultation.patient,
                         medical_history=medical_history,
                         other_consultations=other_consultations,
                         can_edit=(consultation.doctor_id == current_user.id))


@bp.route('/consultation/print/<int:id>')
@login_required
@require_role('doctor')
def print_consultation_ticket(id):
    """Imprimir ticket de consulta en formato tiquetera"""
    consultation = MedicalRecord.query.get_or_404(id)
    
    # Verificar que el doctor puede ver esta consulta
    if consultation.doctor_id != current_user.id:
        has_attended = Appointment.query.filter_by(
            patient_id=consultation.patient_id,
            doctor_id=current_user.id
        ).first()
        
        if not has_attended:
            flash('No tiene permisos para imprimir esta consulta', 'error')
            return redirect(url_for('doctor.clinical_histories'))
    
    # Datos de la clínica (genéricos por ahora)
    clinic_info = {
        'name': 'Centro Médico Santa Rosa',
        'address': 'Av. Principal 123, Chachapoyas',
        'ruc': '20123456789',
        'phone': '(041) 477-123',
        'email': 'info@centromedicosantarosa.com'
    }
    
    return render_template('doctor/consultation_ticket.html',
                         consultation=consultation,
                         patient=consultation.patient,
                         doctor=consultation.doctor,
                         clinic_info=clinic_info,
                         now=datetime.now())

@bp.route('/patient/<int:patient_id>/check-history')
@login_required
@require_role('doctor')
def check_patient_history(patient_id):
    """Verificar si el paciente tiene historia clínica y redirigir apropiadamente"""
    patient = Patient.query.get_or_404(patient_id)
    appointment_id = request.args.get('appointment_id')
    
    # Verificar que el doctor puede atender a este paciente
    has_appointment = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).first()
    
    if not has_appointment:
        flash('No tiene permisos para atender a este paciente', 'error')
        return redirect(url_for('doctor.clinical_histories'))
    
    # Usar la nueva lógica de negocio para obtener estado completo
    patient_status = patient.get_patient_status_for_doctor()
    
    # Verificar si puede crear historia clínica (si es necesario)
    if not patient_status['has_medical_history']:
        can_create, message = patient.can_create_medical_history()
        if not can_create:
            flash(f'No se puede crear historia clínica: {message}', 'error')
            return redirect(url_for('doctor.clinical_histories'))
    
    # Redirigir según el estado del paciente
    if patient_status['expected_action'] == 'new_consultation':
        # Paciente tiene historia, crear nueva consulta
        flash(f'Paciente con historia clínica N° {patient_status["history_number"]}', 'info')
        if appointment_id:
            return redirect(url_for('doctor.new_consultation', patient_id=patient_id, appointment_id=appointment_id))
        else:
            return redirect(url_for('doctor.new_consultation', patient_id=patient_id))
    
    elif patient_status['expected_action'] == 'create_medical_history':
        # Paciente nuevo, crear historia clínica completa
        flash(f'Paciente nuevo - se creará historia clínica completa', 'info')
        if appointment_id:
            return redirect(url_for('doctor.new_medical_history', patient_id=patient_id, appointment_id=appointment_id))
        else:
            return redirect(url_for('doctor.new_medical_history', patient_id=patient_id))
    
    else:
        # Caso no contemplado
        flash('Error en la lógica de verificación de historia clínica', 'error')
        return redirect(url_for('doctor.clinical_histories'))

@bp.route('/clinical-histories')
@login_required
@require_role('doctor')
def clinical_histories():
    """Lista de historias clínicas de pacientes que el doctor actual ha atendido"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Query base - pacientes que tienen consultas realizadas por ESTE doctor
    query = Patient.query.join(MedicalRecord).filter(
        MedicalRecord.doctor_id == current_user.id,  # Solo registros del doctor actual
        Patient.is_active == True
    ).distinct()
    
    # Filtro de búsqueda
    if search:
        query = query.filter(
            (Patient.first_name.ilike(f'%{search}%')) |
            (Patient.last_name.ilike(f'%{search}%')) |
            (Patient.dni.ilike(f'%{search}%'))
        )
    
    # Obtener pacientes
    patients = query.order_by(Patient.first_name, Patient.last_name).all()
    
    # Construir datos de historias clínicas
    histories_data = []
    for patient in patients:
        # Obtener la historia clínica (que ahora existe porque el doctor ya atendió al paciente)
        medical_history = patient.get_medical_history()
        
        # Obtener todas las consultas del paciente (de todos los doctores)
        all_consultations = MedicalRecord.query.filter_by(
            patient_id=patient.id
        ).order_by(MedicalRecord.consultation_date.desc()).all()
        
        # Obtener solo las consultas del doctor actual
        my_consultations = MedicalRecord.query.filter_by(
            patient_id=patient.id,
            doctor_id=current_user.id
        ).order_by(MedicalRecord.consultation_date.desc()).all()
        
        # Solo incluir si el doctor actual tiene al menos una consulta
        if my_consultations:
            # Obtener la última cita del doctor con este paciente
            last_appointment = Appointment.query.filter_by(
                patient_id=patient.id,
                doctor_id=current_user.id
            ).order_by(Appointment.date_time.desc()).first()
            
            # Verificar si puede crear consulta para una nueva cita
            can_create_consultation = False
            if medical_history and last_appointment:
                # Verificar si ya existe consulta para la última cita
                existing_consultation = MedicalRecord.query.filter_by(
                    patient_id=patient.id,
                    doctor_id=current_user.id,
                    appointment_id=last_appointment.id
                ).first()
                can_create_consultation = not existing_consultation
            
            histories_data.append({
                'patient': patient,
                'medical_history': medical_history,
                'total_consultations': len(all_consultations),
                'my_consultations': len(my_consultations),
                'last_consultation': all_consultations[0] if all_consultations else None,
                'doctors_count': len(set(c.doctor_id for c in all_consultations)),
                'last_appointment': last_appointment,
                'can_create_consultation': can_create_consultation
            })
    
    return render_template('doctor/clinical_histories.html',
                         title='Historias Clínicas',
                         histories_data=histories_data,
                         search=search)

@bp.route('/api/patient/<int:patient_id>/status')
@login_required
@require_role('doctor')
def get_patient_status_api(patient_id):
    """API endpoint para obtener estado completo del paciente"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Verificar que el doctor puede acceder a este paciente
    has_appointment = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id
    ).first()
    
    if not has_appointment:
        return jsonify({'error': 'No tiene permisos para acceder a este paciente'}), 403
    
    # Obtener estado completo
    patient_status = patient.get_patient_status_for_doctor()
    
    # Agregar información adicional
    additional_info = {
        'full_name': patient.full_name,
        'dni': patient.dni,
        'age': patient.age,
        'gender': patient.gender,
        'last_consultation_date': None,
        'next_appointment_date': None
    }
    
    # Última consulta
    last_consultation = MedicalRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(MedicalRecord.consultation_date.desc()).first()
    
    if last_consultation:
        additional_info['last_consultation_date'] = last_consultation.consultation_date.strftime('%Y-%m-%d')
    
    # Próxima cita
    next_appointment = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.doctor_id == current_user.id,
        Appointment.date_time > datetime.now()
    ).order_by(Appointment.date_time).first()
    
    if next_appointment:
        additional_info['next_appointment_date'] = next_appointment.date_time.strftime('%Y-%m-%d %H:%M')
    
    # Combinar toda la información
    response_data = {**patient_status, **additional_info}
    
    return jsonify(response_data)

@bp.route('/api/validate-history-number')
@login_required  
@require_role('doctor')
def validate_history_number_api():
    """API endpoint para validar número de historia clínica"""
    history_number = request.args.get('number', '')
    
    if not history_number:
        return jsonify({'valid': False, 'message': 'Número requerido'})
    
    # Usar el método de validación del modelo
    from app.models.medical_history import MedicalHistory
    is_valid = MedicalHistory.validate_history_number(history_number)
    
    if is_valid:
        return jsonify({
            'valid': True, 
            'message': 'Formato válido',
            'format': 'HC-YYYY-NNNNNN'
        })
    else:
        return jsonify({
            'valid': False, 
            'message': 'Formato inválido. Debe ser HC-YYYY-NNNNNN',
            'format': 'HC-YYYY-NNNNNN'
        })

@bp.route('/consultation/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('doctor')
def edit_consultation(id):
    """Editar una consulta existente"""
    medical_record = MedicalRecord.query.get_or_404(id)
    
    # Verificar permisos de edición
    can_edit, message = medical_record.can_be_edited_by(current_user.id)
    if not can_edit:
        flash(f'No se puede editar la consulta: {message}', 'error')
        return redirect(url_for('doctor.view_consultation', id=id))
    
    if request.method == 'POST':
        try:
            # DEBUG: Mostrar todos los datos del formulario
            print("=== DEBUG: Datos del formulario de edición de consulta ===")
            for key, value in request.form.items():
                print(f"{key}: '{value}'")
            print("=== FIN DEBUG ===")
            
            # Procesar fecha de próxima cita
            next_appointment_notes = request.form.get('next_appointment_notes', '').strip()
            next_appointment_date = request.form.get('next_appointment_date', '').strip()
            
            if next_appointment_date:
                try:
                    date_obj = datetime.strptime(next_appointment_date, '%Y-%m-%d')
                    date_formatted = date_obj.strftime('%d/%m/%Y')
                    if next_appointment_notes:
                        next_appointment_notes += f"\nPróxima cita: {date_formatted}"
                    else:
                        next_appointment_notes = f"Próxima cita: {date_formatted}"
                except ValueError:
                    pass
            
            # Actualizar campos
            medical_record.symptoms = request.form.get('chief_complaint', '').strip()
            medical_record.diagnosis = request.form.get('diagnosis', '').strip()
            medical_record.treatment = request.form.get('treatment', '').strip()
            medical_record.prescriptions = request.form.get('prescriptions', '').strip()
            medical_record.observations = _build_observations_text(request.form)
            medical_record.next_appointment_notes = next_appointment_notes
            
            # Signos vitales
            medical_record.blood_pressure = request.form.get('blood_pressure', '').strip() or None
            medical_record.heart_rate = int(request.form.get('heart_rate', 0)) if request.form.get('heart_rate') else None
            medical_record.temperature = float(request.form.get('temperature', 0)) if request.form.get('temperature') else None
            medical_record.weight = float(request.form.get('weight', 0)) if request.form.get('weight') else None
            medical_record.height = float(request.form.get('height', 0)) if request.form.get('height') else None
            
            # Actualizar timestamp de modificación
            medical_record.updated_at = datetime.now()
            
            # Validaciones básicas
            if not all([medical_record.symptoms, medical_record.diagnosis]):
                flash('Los campos motivo de consulta y diagnóstico son obligatorios', 'error')
                return redirect(request.url)
            
            db.session.commit()
            
            # Verificar qué acción realizar según el botón presionado
            action = request.form.get('action', 'save')
            
            flash(f'Consulta actualizada exitosamente', 'success')
            
            if action == 'save_and_print':
                # Redirigir al ticket de impresión
                return redirect(url_for('doctor.print_consultation_ticket', id=medical_record.id))
            else:
                # Redirigir a la vista normal de consulta
                return redirect(url_for('doctor.view_consultation', id=medical_record.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar consulta: {str(e)}', 'error')
    
    # GET request - mostrar formulario de edición
    patient = medical_record.patient
    
    # Obtener el triage asociado si existe
    triage = None
    if medical_record.appointment_id:
        from app.models.triage import Triage
        triage = Triage.query.filter_by(appointment_id=medical_record.appointment_id).first()
    
    # Obtener información de edición
    edit_status = medical_record.get_edit_status_for_doctor(current_user.id)
    
    return render_template('doctor/consultation_edit.html',
                         title=f'Editar Consulta - {patient.full_name}',
                         patient=patient,
                         medical_record=medical_record,
                         triage=triage,
                         edit_status=edit_status)
