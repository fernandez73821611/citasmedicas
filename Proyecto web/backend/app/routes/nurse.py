from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app.utils.decorators import require_role
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.triage import Triage
from app.models.user import User
from app.models.invoice import Invoice
from app import db

# Blueprint para enfermera
bp = Blueprint('nurse', __name__)

@bp.route('/dashboard')
@login_required
@require_role('nurse')
def dashboard():
    """Dashboard de enfermera"""
    today = date.today()
    
    # Estadísticas para el dashboard
    pending_triages = Triage.query.filter_by(status='pending').count()
    completed_today = Triage.query.filter(
        Triage.nurse_id == current_user.id,
        Triage.completed_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    # Pacientes del mes
    start_of_month = datetime(today.year, today.month, 1)
    patients_this_month = Triage.query.filter(
        Triage.nurse_id == current_user.id,
        Triage.created_at >= start_of_month
    ).count()
    
    # Citas de hoy que necesitan triage (SOLO PAGADAS)
    today_paid_appointments_query = Appointment.query.join(
        Invoice, Appointment.id == Invoice.appointment_id
    ).filter(
        Appointment.date_time >= datetime.combine(today, datetime.min.time()),
        Appointment.date_time < datetime.combine(today, datetime.max.time()),
        Appointment.status == 'scheduled',
        Invoice.status == 'paid'
    ).outerjoin(
        Triage, Appointment.id == Triage.appointment_id
    ).filter(
        Triage.id.is_(None)  # Sin triage existente
    )
    
    # Obtener tanto la lista como el conteo
    today_appointments = today_paid_appointments_query.all()
    today_appointments_count = len(today_appointments)
    
    return render_template('nurse/dashboard.html', 
                         title='Dashboard Enfermería',
                         pending_triages=pending_triages,
                         completed_today=completed_today,
                         patients_this_month=patients_this_month,
                         today_appointments=today_appointments,
                         today_appointments_count=today_appointments_count)

@bp.route('/triage')
@login_required
@require_role('nurse')
def triage_list():
    """Lista de triages pendientes y completados"""
    status_filter = request.args.get('status', 'all')
    patient_search = request.args.get('search', '')
    
    # Query base
    query = Triage.query
    
    # Filtros
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if patient_search:
        query = query.join(Patient).filter(
            db.or_(
                Patient.first_name.contains(patient_search),
                Patient.last_name.contains(patient_search),
                Patient.dni.contains(patient_search)
            )
        )
    
    # Obtener triages ordenados por prioridad y fecha
    triages = query.order_by(
        db.case(
            (Triage.priority_level == 'alta', 1),
            (Triage.priority_level == 'media', 2),
            (Triage.priority_level == 'baja', 3),
            else_=4
        ),
        Triage.created_at.desc()
    ).all()
    
    return render_template('nurse/triage.html', 
                         title='Gestión de Triage',
                         triages=triages,
                         status_filter=status_filter,
                         patient_search=patient_search)

@bp.route('/triage/new', methods=['GET', 'POST'])
@login_required
@require_role('nurse')
def new_triage():
    """Crear nuevo triage"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            patient_id = request.form.get('patient_id')
            appointment_id = request.form.get('appointment_id') or None
            
            # Validar que el paciente existe
            patient = Patient.query.get_or_404(patient_id)
            
            # Validaciones específicas por edad
            required_fields = []
            age_group = patient.age_group
            
            # Determinar campos requeridos según edad
            if age_group == 'lactante':
                required_fields = ['chief_complaint', 'weight', 'height', 'temperature', 'heart_rate']
            elif age_group == 'preescolar':
                required_fields = ['chief_complaint', 'weight', 'height', 'temperature', 'heart_rate']
                if patient.age >= 3:
                    required_fields.extend(['systolic', 'diastolic'])
            elif age_group in ['escolar', 'adolescente', 'adulto']:
                required_fields = ['chief_complaint', 'systolic', 'diastolic', 'heart_rate', 'temperature', 'weight', 'height']
            elif age_group == 'adulto_mayor':
                required_fields = ['chief_complaint', 'systolic', 'diastolic', 'heart_rate', 'temperature', 'weight']
            
            # Validar campos requeridos
            missing_fields = []
            for field in required_fields:
                if not request.form.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                flash(f'Campos requeridos para {patient.age_group_label}: {", ".join(missing_fields)}', 'error')
                return redirect(url_for('nurse.new_triage'))
            
            # Si hay cita asociada, validar que esté pagada
            if appointment_id:
                appointment = Appointment.query.get_or_404(appointment_id)
                
                # VALIDACIÓN CRÍTICA: Verificar pago antes de triage
                if not appointment.is_paid:
                    flash(f'No se puede iniciar triage. La cita debe tener pago confirmado. Estado actual: {appointment.payment_status}', 'error')
                    return redirect(url_for('nurse.new_triage'))
                
                # VALIDACIÓN CRÍTICA: Verificar que el triage se haga el mismo día de la cita
                today = date.today()
                appointment_date = appointment.date_time.date()
                if appointment_date != today:
                    flash(f'No se puede hacer triage. El triage solo se puede realizar el mismo día de la cita programada. Cita programada para: {appointment_date.strftime("%d/%m/%Y")}, Hoy es: {today.strftime("%d/%m/%Y")}', 'error')
                    return redirect(url_for('nurse.new_triage'))
                
                # Verificar que no exista ya un triage para esta cita
                existing_triage = Triage.query.filter_by(appointment_id=appointment_id).first()
                if existing_triage:
                    flash('Ya existe un triage para esta cita', 'error')
                    return redirect(url_for('nurse.view_triage', triage_id=existing_triage.id))
                
                # Cambiar estado de la cita a "in_triage" al iniciar
                appointment.status = 'in_triage'
            
            # Crear nuevo triage
            triage = Triage(
                patient_id=patient_id,
                appointment_id=appointment_id,
                nurse_id=current_user.id,
                
                # Signos vitales
                blood_pressure_systolic=request.form.get('systolic') or None,
                blood_pressure_diastolic=request.form.get('diastolic') or None,
                heart_rate=request.form.get('heart_rate') or None,
                temperature=request.form.get('temperature') or None,
                respiratory_rate=request.form.get('respiratory_rate') or None,
                oxygen_saturation=request.form.get('oxygen_saturation') or None,
                weight=request.form.get('weight') or None,
                height=request.form.get('height') or None,
                
                # Información clínica
                chief_complaint=request.form.get('chief_complaint'),
                pain_scale=request.form.get('pain_scale') or None,
                priority_level=request.form.get('priority_level', 'media'),
                allergies=request.form.get('allergies'),
                current_medications=request.form.get('current_medications'),
                blood_type=request.form.get('blood_type'),
                nurse_observations=request.form.get('nurse_observations'),
                
                # Campos específicos por edad - Lactantes comunes
                sleep_pattern=request.form.get('sleep_pattern'),
                irritability=request.form.get('irritability'),
                fontanel=request.form.get('fontanel'),
                
                # Lactante menor (0-6 meses)
                feeding_status=request.form.get('feeding_status'),
                
                # Preescolares
                psychomotor_development=request.form.get('psychomotor_development'),
                social_behavior=request.form.get('social_behavior'),
                toilet_training=request.form.get('toilet_training'),
                
                # Escolares
                school_performance=request.form.get('school_performance'),
                physical_activity=request.form.get('physical_activity'),
                mood_state=request.form.get('mood_state'),
                
                # Adolescentes
                pubertal_development=request.form.get('pubertal_development'),
                menstruation_status=request.form.get('menstruation_status'),
                risk_behaviors=request.form.get('risk_behaviors'),
                
                # Adultos Mayores (65+ años)
                mobility_status=request.form.get('mobility_status'),
                cognitive_status=request.form.get('cognitive_status'),
                fall_risk=request.form.get('fall_risk'),
                functional_status=request.form.get('functional_status'),
                chronic_conditions=request.form.get('chronic_conditions'),
                medication_polypharmacy=request.form.get('medication_polypharmacy')
            )
            
            # Si se marca como completado
            if request.form.get('complete_triage'):
                triage.mark_completed()
                
                # Actualizar estado de la cita a "ready_for_doctor"
                if appointment_id:
                    appointment.status = 'ready_for_doctor'
            
            db.session.add(triage)
            db.session.commit()
            
            flash('Triage registrado exitosamente', 'success')
            return redirect(url_for('nurse.triage_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar triage: {str(e)}', 'error')
    
    # GET request - mostrar formulario
    # Verificar si se especifica una cita específica
    appointment_id = request.args.get('appointment_id')
    selected_appointment = None
    
    if appointment_id:
        # Verificar que la cita existe y está disponible para triage
        selected_appointment = Appointment.query.filter_by(
            id=appointment_id,
            status='scheduled'
        ).join(Invoice).filter(Invoice.status == 'paid').first()
        
        if not selected_appointment:
            flash('La cita especificada no está disponible para triage', 'error')
            return redirect(url_for('nurse.dashboard'))
        
        # Verificar que no tenga triage existente
        existing_triage = Triage.query.filter_by(appointment_id=appointment_id).first()
        if existing_triage:
            flash('Ya existe un triage para esta cita', 'info')
            return redirect(url_for('nurse.view_triage', triage_id=existing_triage.id))
    
    # Obtener SOLO pacientes que tienen citas pagadas para hoy
    today = date.today()
    paid_appointments = Appointment.query.join(
        Invoice, Appointment.id == Invoice.appointment_id
    ).filter(
        Appointment.date_time >= datetime.combine(today, datetime.min.time()),
        Appointment.date_time < datetime.combine(today, datetime.max.time()),
        Appointment.status == 'scheduled',
        Invoice.status == 'paid'
    ).outerjoin(
        Triage, Appointment.id == Triage.appointment_id
    ).filter(
        Triage.id.is_(None)  # Sin triage existente
    ).all()
    
    # Extraer pacientes únicos de las citas pagadas
    patients_with_paid_appointments = []
    seen_patient_ids = set()
    
    for appointment in paid_appointments:
        if appointment.patient_id not in seen_patient_ids:
            patients_with_paid_appointments.append(appointment.patient)
            seen_patient_ids.add(appointment.patient_id)
    
    return render_template('nurse/triage_form.html', 
                         title='Nuevo Triage',
                         patients=patients_with_paid_appointments,
                         appointments=paid_appointments,
                         selected_appointment=selected_appointment)

@bp.route('/triage/<int:triage_id>')
@login_required
@require_role('nurse')
def view_triage(triage_id):
    """Ver detalles de un triage"""
    triage = Triage.query.get_or_404(triage_id)
    
    return render_template('nurse/triage_detail.html', 
                         title=f'Triage - {triage.patient.full_name}',
                         triage=triage)

@bp.route('/triage/<int:triage_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('nurse')
def edit_triage(triage_id):
    """Editar un triage existente"""
    triage = Triage.query.get_or_404(triage_id)
    
    if request.method == 'POST':
        try:
            # Actualizar campos del triage
            triage.blood_pressure_systolic = request.form.get('systolic') or None
            triage.blood_pressure_diastolic = request.form.get('diastolic') or None
            triage.heart_rate = request.form.get('heart_rate') or None
            triage.temperature = request.form.get('temperature') or None
            triage.respiratory_rate = request.form.get('respiratory_rate') or None
            triage.oxygen_saturation = request.form.get('oxygen_saturation') or None
            triage.weight = request.form.get('weight') or None
            triage.height = request.form.get('height') or None
            triage.chief_complaint = request.form.get('chief_complaint')
            triage.pain_scale = request.form.get('pain_scale') or None
            triage.priority_level = request.form.get('priority_level', 'media')
            triage.allergies = request.form.get('allergies')
            triage.current_medications = request.form.get('current_medications')
            triage.blood_type = request.form.get('blood_type')
            triage.nurse_observations = request.form.get('nurse_observations')
            
            # Si se marca como completado
            if request.form.get('complete_triage') and triage.status != 'completed':
                triage.mark_completed()
                
                # Actualizar estado de la cita a "ready_for_doctor"
                if triage.appointment:
                    triage.appointment.status = 'ready_for_doctor'
            
            db.session.commit()
            flash('Triage actualizado exitosamente', 'success')
            return redirect(url_for('nurse.triage_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar triage: {str(e)}', 'error')
    
    # GET request - mostrar formulario con datos del triage
    return render_template('nurse/triage_form.html', 
                         title=f'Editar Triage - {triage.patient.full_name}',
                         triage=triage)

@bp.route('/triage/<int:triage_id>/complete', methods=['POST'])
@login_required
@require_role('nurse')
def complete_triage(triage_id):
    """Marcar un triage como completado"""
    triage = Triage.query.get_or_404(triage_id)
    
    # Verificar que sea el enfermero asignado
    if triage.nurse_id != current_user.id:
        flash('No tiene permisos para completar este triage', 'error')
        return redirect(url_for('nurse.triage_list'))
    
    # Verificar que esté en estado pendiente
    if triage.status != 'pending':
        flash('Este triage ya ha sido completado o no está en estado pendiente', 'warning')
        return redirect(url_for('nurse.triage_list'))
    
    try:
        # Marcar como completado
        triage.mark_completed()
        
        # Actualizar estado de la cita a "ready_for_doctor"
        if triage.appointment:
            triage.appointment.status = 'ready_for_doctor'
        
        db.session.commit()
        flash(f'Triage completado exitosamente para {triage.patient.full_name}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al completar triage: {str(e)}', 'error')
    
    return redirect(url_for('nurse.triage_list'))

@bp.route('/patients')
@login_required
@require_role('nurse')
def patients():
    """Mis pacientes - pacientes a los que he realizado triage"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Query base - pacientes a los que he realizado triage
    query = Patient.query.join(Triage).filter(
        Triage.nurse_id == current_user.id,
        Patient.is_active == True
    ).distinct()
    
    # Filtro de búsqueda
    if search:
        query = query.filter(
            (Patient.first_name.ilike(f'%{search}%')) |
            (Patient.last_name.ilike(f'%{search}%')) |
            (Patient.dni.ilike(f'%{search}%')) |
            (Patient.email.ilike(f'%{search}%'))
        )
    
    # Obtener pacientes
    patients = query.order_by(Patient.first_name, Patient.last_name).all()
    
    # Agregar información adicional para cada paciente
    patients_data = []
    for patient in patients:
        # Último triage que hice a este paciente
        last_triage = Triage.query.filter_by(
            patient_id=patient.id,
            nurse_id=current_user.id
        ).order_by(Triage.created_at.desc()).first()
        
        # Próxima cita del paciente que podría necesitar triage
        next_appointment = Appointment.query.join(
            Invoice, Appointment.id == Invoice.appointment_id
        ).filter(
            Appointment.patient_id == patient.id,
            Appointment.date_time > datetime.now(),
            Appointment.status.in_(['scheduled', 'confirmed']),
            Invoice.status == 'paid'
        ).outerjoin(
            Triage, Appointment.id == Triage.appointment_id
        ).filter(
            Triage.id.is_(None)  # Sin triage existente
        ).order_by(Appointment.date_time).first()
        
        # Total de triages que he realizado a este paciente
        total_triages = Triage.query.filter_by(
            patient_id=patient.id,
            nurse_id=current_user.id
        ).count()
        
        # Último estado de prioridad asignado
        priority_level = last_triage.priority_level if last_triage else None
        
        patients_data.append({
            'patient': patient,
            'last_triage': last_triage,
            'next_appointment': next_appointment,
            'total_triages': total_triages,
            'priority_level': priority_level
        })
    
    return render_template('nurse/patients.html', 
                         title='Mis Pacientes',
                         patients_data=patients_data,
                         search=search)

@bp.route('/api/patient/<int:patient_id>/paid-appointment')
@login_required
@require_role('nurse')
def get_patient_paid_appointment(patient_id):
    """Obtener la cita pagada de un paciente para hoy"""
    try:
        today = date.today()
        
        # Buscar la cita pagada del paciente para hoy
        paid_appointment = Appointment.query.join(
            Invoice, Appointment.id == Invoice.appointment_id
        ).filter(
            Appointment.patient_id == patient_id,
            Appointment.date_time >= datetime.combine(today, datetime.min.time()),
            Appointment.date_time < datetime.combine(today, datetime.max.time()),
            Appointment.status == 'scheduled',
            Invoice.status == 'paid'
        ).outerjoin(
            Triage, Appointment.id == Triage.appointment_id
        ).filter(
            Triage.id.is_(None)  # Sin triage existente
        ).first()
        
        if paid_appointment:
            return jsonify({
                'success': True,
                'appointment': {
                    'id': paid_appointment.id,
                    'date_time': paid_appointment.date_time.strftime('%H:%M'),
                    'doctor_name': f"Dr. {paid_appointment.doctor.full_name}",
                    'specialty': paid_appointment.specialty.name if paid_appointment.specialty else 'Sin especialidad',
                    'reason': paid_appointment.reason or 'Sin motivo especificado'
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No se encontró cita pagada para este paciente hoy'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener información de la cita: {str(e)}'
        }), 500

@bp.route('/triage/appointment/<int:appointment_id>')
@login_required
@require_role('nurse')
def start_triage_for_appointment(appointment_id):
    """Iniciar triage para una cita específica"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verificar que la cita esté en estado correcto para triage
    if appointment.status != 'scheduled':
        flash('Esta cita no está disponible para triage', 'error')
        return redirect(url_for('nurse.dashboard'))
    
    # Verificar si ya existe un triage para esta cita
    existing_triage = Triage.query.filter_by(appointment_id=appointment_id).first()
    if existing_triage:
        flash('Ya existe un triage para esta cita', 'info')
        return redirect(url_for('nurse.view_triage', triage_id=existing_triage.id))
    
    # Redirigir al formulario de nuevo triage con el appointment_id
    return redirect(url_for('nurse.new_triage', appointment_id=appointment_id))
