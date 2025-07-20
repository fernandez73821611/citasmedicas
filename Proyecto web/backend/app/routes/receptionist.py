from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc, extract
from decimal import Decimal
from datetime import datetime, date, timedelta
from app.utils.decorators import require_role
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.user import User
from app.models.specialty import Specialty
from app.models.invoice import Invoice
from app import db

# Blueprint para recepcionista
bp = Blueprint('receptionist', __name__)

# API Endpoints para AJAX
@bp.route('/api/patients/search')
@login_required
@require_role('receptionist')
def search_patients():
    """API para búsqueda de pacientes con autocompletado"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:        # Si no hay query o es muy corta, devolver todos los pacientes activos
        patients = Patient.query.filter_by(is_active=True).order_by(Patient.first_name, Patient.last_name).limit(50).all()
    else:        # Búsqueda por nombre, apellido o DNI
        search_term = f'%{query}%'
        patients = Patient.query.filter(
            Patient.is_active == True,
            db.or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.dni.ilike(search_term),
                func.concat(Patient.first_name, ' ', Patient.last_name).ilike(search_term)
            )
        ).order_by(Patient.first_name, Patient.last_name).limit(20).all()
      # Convertir a JSON
    patients_data = []
    for patient in patients:
        patients_data.append({
            'id': patient.id,
            'name': patient.first_name,
            'lastname': patient.last_name,
            'dni': patient.dni,
            'email': patient.email,
            'phone': patient.phone,
            'address': patient.address
        })
    
    return jsonify({
        'success': True,
        'patients': patients_data,
        'total': len(patients_data)
    })

@bp.route('/dashboard')
@login_required
@require_role('receptionist')
def dashboard():
    """Dashboard del recepcionista"""
    today = date.today()
    
    # Citas de hoy
    today_appointments = Appointment.query.filter(
        Appointment.date_time >= datetime.combine(today, datetime.min.time()),
        Appointment.date_time < datetime.combine(today, datetime.max.time())
    ).order_by(Appointment.date_time).all()
    
    # Total de pacientes
    total_patients = Patient.query.count()
    
    # Pacientes nuevos hoy
    new_patients_today = Patient.query.filter(
        Patient.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    # Pacientes recientes
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    
    # Médicos activos
    active_doctors = User.query.filter_by(role='doctor', is_active=True).count()
    
    # Especialidades disponibles
    specialties_count = Specialty.query.filter_by(is_active=True).count()
    
    # Pagos pendientes (placeholder por ahora)
    pending_payments = 0
    
    return render_template('receptionist/dashboard.html', 
                         title='Dashboard Recepcionista',
                         today_appointments=today_appointments,
                         total_patients=total_patients,
                         new_patients_today=new_patients_today,
                         recent_patients=recent_patients,
                         active_doctors=active_doctors,
                         specialties_count=specialties_count,
                         pending_payments=pending_payments)

@bp.route('/schedule')
@login_required
@require_role('receptionist')
def schedule():
    """Programar citas - redirige a nueva cita"""
    return redirect(url_for('receptionist.new_appointment'))

@bp.route('/billing')
@login_required
@require_role('receptionist')
def billing():
    """Facturación - Dashboard principal"""
    # Obtener filtros
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Query base
    query = Invoice.query
    
    # Aplicar filtros
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    
    if search:
        search_term = f"%{search}%"
        query = query.join(Patient).filter(
            db.or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.dni.ilike(search_term),
                Invoice.invoice_number.ilike(search_term)
            )
        )
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Invoice.issue_date >= start_date_obj)
        except ValueError:
            flash('Fecha de inicio inválida', 'error')
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Invoice.issue_date <= end_date_obj)
        except ValueError:
            flash('Fecha de fin inválida', 'error')
    
    # Obtener facturas
    invoices = query.order_by(desc(Invoice.created_at)).all()
      # Estadísticas
    stats = get_billing_statistics()
    
    return render_template('receptionist/billing.html', 
                         title='Facturación',
                         invoices=invoices,
                         stats=stats,
                         status_filter=status_filter,
                         search=search,
                         start_date=start_date,
                         end_date=end_date,
                         today=date.today())

@bp.route('/patients')
@login_required
@require_role('receptionist')
def patients():
    """Gestión de pacientes"""
    search = request.args.get('search', '')
    gender = request.args.get('gender', '')
    
    query = Patient.query
    
    # Aplicar filtro de búsqueda
    if search:
        query = query.filter(
            (Patient.first_name.ilike(f'%{search}%')) |
            (Patient.last_name.ilike(f'%{search}%')) |
            (Patient.dni.ilike(f'%{search}%'))
        )
    
    # Aplicar filtro de género si se especifica
    if gender in ['M', 'F']:
        # Convertir 'M' a 'Masculino' y 'F' a 'Femenino' para la consulta
        gender_mapping = {'M': 'Masculino', 'F': 'Femenino'}
        query = query.filter_by(gender=gender_mapping[gender])
    
    # Ordenar y obtener resultados
    patients = query.order_by(Patient.created_at.desc()).all()
    
    return render_template('receptionist/patients.html', 
                         title='Gestión de Pacientes', 
                         patients=patients,
                         search=search,
                         selected_gender=gender)

@bp.route('/patients/new', methods=['GET', 'POST'])
@login_required
@require_role('receptionist')
def new_patient():
    """Registrar nuevo paciente"""
    if request.method == 'POST':
        try:
            # Obtener y limpiar datos del formulario
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            dni = request.form.get('dni', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            birth_date_str = request.form.get('birth_date', '').strip()
            gender = request.form.get('gender', '').strip()
            blood_type = request.form.get('blood_type', '').strip()
            emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
            emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()
            emergency_contact_relationship = request.form.get('emergency_contact_relationship', '').strip()
            
            # Datos del apoderado/tutor legal (para menores de edad)
            guardian_name = request.form.get('guardian_name', '').strip()
            guardian_dni = request.form.get('guardian_dni', '').strip()
            guardian_phone = request.form.get('guardian_phone', '').strip()
            guardian_relationship = request.form.get('guardian_relationship', '').strip()
            
            # Validaciones básicas de campos obligatorios
            required_fields = {
                'first_name': first_name,
                'last_name': last_name,
                'dni': dni,
                'birth_date': birth_date_str
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                field_names = {
                    'first_name': 'Nombres',
                    'last_name': 'Apellidos',
                    'dni': 'DNI',
                    'birth_date': 'Fecha de nacimiento'
                }
                missing_field_names = [field_names[field] for field in missing_fields]
                flash(f'Los siguientes campos son obligatorios: {", ".join(missing_field_names)}', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Registrar Paciente', patient=None)
            
            # Validar DNI (8 dígitos)
            if not dni.isdigit() or len(dni) != 8:
                flash('El DNI debe contener exactamente 8 dígitos', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Registrar Paciente', patient=None)
            
            # Validar email si se proporciona
            if email:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    flash('Formato de email inválido', 'error')
                    return render_template('receptionist/patient_form.html', 
                                         title='Registrar Paciente', patient=None)
            
            # Validar teléfono si se proporciona (9 dígitos)
            if phone and (not phone.isdigit() or len(phone) != 9):
                flash('El teléfono debe contener exactamente 9 dígitos', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Registrar Paciente', patient=None)
            
            # Validar formato de fecha y calcular edad
            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                
                if birth_date >= today:
                    flash('La fecha de nacimiento debe ser anterior a hoy', 'error')
                    return render_template('receptionist/patient_form.html', 
                                         title='Registrar Paciente', patient=None)
                
                if age > 120:
                    flash('La edad no puede ser mayor a 120 años', 'error')
                    return render_template('receptionist/patient_form.html', 
                                         title='Registrar Paciente', patient=None)
                
                # Validar datos del apoderado si el paciente es menor de edad
                if age < 18:
                    guardian_required_fields = {
                        'guardian_name': guardian_name,
                        'guardian_dni': guardian_dni,
                        'guardian_phone': guardian_phone,
                        'guardian_relationship': guardian_relationship
                    }
                    
                    missing_guardian_fields = [field for field, value in guardian_required_fields.items() if not value]
                    if missing_guardian_fields:
                        field_names = {
                            'guardian_name': 'Nombre del apoderado',
                            'guardian_dni': 'DNI del apoderado',
                            'guardian_phone': 'Teléfono del apoderado',
                            'guardian_relationship': 'Parentesco'
                        }
                        missing_field_names = [field_names[field] for field in missing_guardian_fields]
                        flash(f'Para menores de edad son obligatorios: {", ".join(missing_field_names)}', 'error')
                        return render_template('receptionist/patient_form.html', 
                                             title='Registrar Paciente', patient=None)
                    
                    # Validar DNI del apoderado (8 dígitos)
                    if not guardian_dni.isdigit() or len(guardian_dni) != 8:
                        flash('El DNI del apoderado debe contener exactamente 8 dígitos', 'error')
                        return render_template('receptionist/patient_form.html', 
                                             title='Registrar Paciente', patient=None)
                    
                    # Validar teléfono del apoderado (9 dígitos)
                    if not guardian_phone.isdigit() or len(guardian_phone) != 9:
                        flash('El teléfono del apoderado debe contener exactamente 9 dígitos', 'error')
                        return render_template('receptionist/patient_form.html', 
                                             title='Registrar Paciente', patient=None)
                
            except ValueError:
                flash('Formato de fecha de nacimiento inválido (YYYY-MM-DD)', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Registrar Paciente', patient=None)
            
            # Validar género
            valid_genders = ['M', 'F', 'Otro']
            if gender and gender not in valid_genders:
                flash(f'Género inválido. Debe ser uno de: {", ".join(valid_genders)}', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Registrar Paciente', patient=None)
            
            # Validar tipo de sangre
            valid_blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            if blood_type and blood_type not in valid_blood_types:
                flash(f'Tipo de sangre inválido. Debe ser uno de: {", ".join(valid_blood_types)}', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Registrar Paciente', patient=None)
            
            # Verificar DNI único
            existing_patient = Patient.query.filter_by(dni=dni).first()
            if existing_patient:
                flash(f'Ya existe un paciente registrado con DNI {dni}', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Registrar Paciente', patient=None)
            
            # Verificar email único si se proporciona
            if email:
                existing_email = Patient.query.filter_by(email=email).first()
                if existing_email:
                    flash('Ya existe un paciente registrado con este email', 'error')
                    return render_template('receptionist/patient_form.html', 
                                         title='Registrar Paciente', patient=None)
            
            # Crear nuevo paciente con datos del formulario
            patient = Patient(
                first_name=first_name,
                last_name=last_name,
                dni=dni,
                phone=phone if phone else None,
                email=email if email else None,
                address=address if address else None,
                birth_date=birth_date,
                gender=gender if gender else None,
                blood_type=blood_type if blood_type else None,
                emergency_contact_name=emergency_contact_name if emergency_contact_name else None,
                emergency_contact_phone=emergency_contact_phone if emergency_contact_phone else None,
                emergency_contact_relationship=emergency_contact_relationship if emergency_contact_relationship else None,
                # Datos del apoderado (solo si es menor de edad)
                guardian_name=guardian_name if age < 18 and guardian_name else None,
                guardian_dni=guardian_dni if age < 18 and guardian_dni else None,
                guardian_phone=guardian_phone if age < 18 and guardian_phone else None,
                guardian_relationship=guardian_relationship if age < 18 and guardian_relationship else None
            )
            
            from app import db
            db.session.add(patient)
            db.session.commit()
            
            flash(f'Paciente {patient.full_name} registrado exitosamente', 'success')
            return redirect(url_for('receptionist.patients'))
            
        except ValueError as e:
            flash('Fecha de nacimiento inválida.', 'error')
        except Exception as e:
            from app import db
            db.session.rollback()
            flash('Error al registrar paciente. Intente nuevamente.', 'error')
    
    return render_template('receptionist/patient_form.html', 
                         title='Registrar Paciente',
                         patient=None)

@bp.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('receptionist')
def edit_patient(patient_id):
    """Editar paciente existente"""
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        try:
            # Obtener y limpiar datos del formulario
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            dni = request.form.get('dni', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            birth_date_str = request.form.get('birth_date', '').strip()
            gender = request.form.get('gender', '').strip()
            blood_type = request.form.get('blood_type', '').strip()
            emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
            emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()
            emergency_contact_relationship = request.form.get('emergency_contact_relationship', '').strip()
            
            # Datos del apoderado/tutor legal (para menores de edad)
            guardian_name = request.form.get('guardian_name', '').strip()
            guardian_dni = request.form.get('guardian_dni', '').strip()
            guardian_phone = request.form.get('guardian_phone', '').strip()
            guardian_relationship = request.form.get('guardian_relationship', '').strip()
            
            # Validaciones básicas de campos obligatorios
            if not all([first_name, last_name, dni, birth_date_str]):
                flash('Los campos nombres, apellidos, DNI y fecha de nacimiento son obligatorios', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Editar Paciente', patient=patient)
            
            # Validar DNI (8 dígitos)
            if not dni.isdigit() or len(dni) != 8:
                flash('El DNI debe contener exactamente 8 dígitos', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Editar Paciente', patient=patient)
            
            # Validar email si se proporciona
            if email:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    flash('Formato de email inválido', 'error')
                    return render_template('receptionist/patient_form.html', 
                                         title='Editar Paciente', patient=patient)
            
            # Validar teléfono si se proporciona (9 dígitos)
            if phone and (not phone.isdigit() or len(phone) != 9):
                flash('El teléfono debe contener exactamente 9 dígitos', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Editar Paciente', patient=patient)
            
            # Validar formato de fecha y calcular edad
            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                
                if birth_date >= today:
                    flash('La fecha de nacimiento debe ser anterior a hoy', 'error')
                    return render_template('receptionist/patient_form.html', 
                                         title='Editar Paciente', patient=patient)
                
                if age > 120:
                    flash('La edad no puede ser mayor a 120 años', 'error')
                    return render_template('receptionist/patient_form.html', 
                                         title='Editar Paciente', patient=patient)
                
                # Validar datos del apoderado si el paciente es menor de edad
                if age < 18:
                    guardian_required_fields = {
                        'guardian_name': guardian_name,
                        'guardian_dni': guardian_dni,
                        'guardian_phone': guardian_phone,
                        'guardian_relationship': guardian_relationship
                    }
                    
                    missing_guardian_fields = [field for field, value in guardian_required_fields.items() if not value]
                    if missing_guardian_fields:
                        field_names = {
                            'guardian_name': 'Nombre del apoderado',
                            'guardian_dni': 'DNI del apoderado',
                            'guardian_phone': 'Teléfono del apoderado',
                            'guardian_relationship': 'Parentesco'
                        }
                        missing_field_names = [field_names[field] for field in missing_guardian_fields]
                        flash(f'Para menores de edad son obligatorios: {", ".join(missing_field_names)}', 'error')
                        return render_template('receptionist/patient_form.html', 
                                             title='Editar Paciente', patient=patient)
                    
                    # Validar DNI del apoderado (8 dígitos)
                    if not guardian_dni.isdigit() or len(guardian_dni) != 8:
                        flash('El DNI del apoderado debe contener exactamente 8 dígitos', 'error')
                        return render_template('receptionist/patient_form.html', 
                                             title='Editar Paciente', patient=patient)
                    
                    # Validar teléfono del apoderado (9 dígitos)
                    if not guardian_phone.isdigit() or len(guardian_phone) != 9:
                        flash('El teléfono del apoderado debe contener exactamente 9 dígitos', 'error')
                        return render_template('receptionist/patient_form.html', 
                                             title='Editar Paciente', patient=patient)
                
            except ValueError:
                flash('Formato de fecha de nacimiento inválido (YYYY-MM-DD)', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Editar Paciente', patient=patient)
            
            # Validar género
            valid_genders = ['M', 'F', 'Otro']
            if gender and gender not in valid_genders:
                flash(f'Género inválido. Debe ser uno de: {", ".join(valid_genders)}', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Editar Paciente', patient=patient)
            
            # Validar tipo de sangre
            valid_blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            if blood_type and blood_type not in valid_blood_types:
                flash(f'Tipo de sangre inválido. Debe ser uno de: {", ".join(valid_blood_types)}', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Editar Paciente', patient=patient)
            
            # Verificar DNI único (excluyendo el paciente actual)
            existing_patient = Patient.query.filter(Patient.dni == dni, Patient.id != patient_id).first()
            if existing_patient:
                flash(f'Ya existe otro paciente registrado con DNI {dni}', 'error')
                return render_template('receptionist/patient_form.html', 
                                     title='Editar Paciente', patient=patient)
            
            # Verificar email único si se proporciona (excluyendo el paciente actual)
            if email:
                existing_email = Patient.query.filter(Patient.email == email, Patient.id != patient_id).first()
                if existing_email:
                    flash('Ya existe otro paciente registrado con este email', 'error')
                    return render_template('receptionist/patient_form.html', 
                                         title='Editar Paciente', patient=patient)
            
            # Actualizar datos del paciente
            patient.first_name = first_name
            patient.last_name = last_name
            patient.dni = dni
            patient.phone = phone if phone else None
            patient.email = email if email else None
            patient.address = address if address else None
            patient.birth_date = birth_date
            patient.gender = gender if gender else None
            patient.blood_type = blood_type if blood_type else None
            patient.emergency_contact_name = emergency_contact_name if emergency_contact_name else None
            patient.emergency_contact_phone = emergency_contact_phone if emergency_contact_phone else None
            patient.emergency_contact_relationship = emergency_contact_relationship if emergency_contact_relationship else None
            
            # Actualizar datos del apoderado solo si es menor de edad
            if age < 18:
                patient.guardian_name = guardian_name if guardian_name else None
                patient.guardian_dni = guardian_dni if guardian_dni else None
                patient.guardian_phone = guardian_phone if guardian_phone else None
                patient.guardian_relationship = guardian_relationship if guardian_relationship else None
            else:
                # Si ya no es menor, limpiar datos del apoderado
                patient.guardian_name = None
                patient.guardian_dni = None
                patient.guardian_phone = None
                patient.guardian_relationship = None
            
            from app import db
            db.session.commit()
            
            flash(f'Paciente {patient.full_name} actualizado exitosamente', 'success')
            return redirect(url_for('receptionist.patients'))
            
        except Exception as e:
            from app import db
            db.session.rollback()
            if 'UNIQUE constraint failed: patients.dni' in str(e):
                flash('Error: Ya existe un paciente con ese DNI', 'error')
            elif 'UNIQUE constraint failed: patients.email' in str(e):
                flash('Error: Ya existe un paciente con ese email', 'error')
            else:
                flash('Error al actualizar paciente', 'error')
    
    return render_template('receptionist/patient_form.html', 
                         title='Editar Paciente',
                         patient=patient)

@bp.route('/patients/<int:patient_id>')
@login_required
@require_role('receptionist')
def view_patient(patient_id):
    """Ver detalles del paciente"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Obtener citas del paciente
    recent_appointments = patient.appointments.order_by(Appointment.date_time.desc()).limit(5).all()
    
    return render_template('receptionist/patient_detail.html', 
                         title=f'Paciente: {patient.full_name}',
                         patient=patient,
                         recent_appointments=recent_appointments)

@bp.route('/patients/<int:patient_id>/delete', methods=['POST'])
@login_required
@require_role('receptionist')
def delete_patient(patient_id):
    """Eliminar paciente (recepcionista)"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        
        # Verificar si el paciente tiene citas futuras
        future_appointments = Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.date_time > datetime.now(),
            Appointment.status.in_(['scheduled', 'confirmed'])
        ).count()
        
        if future_appointments > 0:
            return jsonify({
                'success': False,
                'message': f'No se puede eliminar el paciente {patient.full_name}. Tiene {future_appointments} citas futuras programadas. Cancele las citas primero.'
            }), 400
        
        from app import db
        
        # Eliminar registros relacionados en orden
        from app.models.medical_record import MedicalRecord
        MedicalRecord.query.filter_by(patient_id=patient_id).delete()
        Appointment.query.filter_by(patient_id=patient_id).delete()
        
        # Guardar información para el mensaje
        patient_name = patient.full_name
        
        # Eliminar el paciente
        db.session.delete(patient)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Paciente {patient_name} eliminado exitosamente.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al eliminar paciente: {str(e)}'
        }), 500

@bp.route('/appointments')
@login_required
@require_role('receptionist')
def appointments():
    """Lista de citas para recepcionista"""
    # Obtener filtros de la URL
    date_filter = request.args.get('date', '')
    doctor_filter = request.args.get('doctor', '')
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    # Query base
    query = Appointment.query
    
    # Aplicar filtros
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(
                Appointment.date_time >= datetime.combine(filter_date, datetime.min.time()),
                Appointment.date_time <= datetime.combine(filter_date, datetime.max.time())
            )
        except ValueError:
            flash('Formato de fecha inválido', 'error')
    
    if doctor_filter:
        query = query.filter(Appointment.doctor_id == doctor_filter)
    
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    
    if search:
        # Buscar por nombre de paciente o DNI
        query = query.join(Patient).filter(
            (Patient.first_name.ilike(f'%{search}%')) |
            (Patient.last_name.ilike(f'%{search}%')) |
            (Patient.dni.ilike(f'%{search}%'))
        )
    
    # Ordenar por fecha y hora
    appointments = query.order_by(Appointment.date_time.desc()).all()
    
    # Obtener doctores para el filtro
    doctors = User.query.filter_by(role='doctor', is_active=True).all()
    
    return render_template('receptionist/appointments.html',
                         title='Gestión de Citas',
                         appointments=appointments,
                         doctors=doctors,
                         date_filter=date_filter,
                         doctor_filter=doctor_filter,
                         status_filter=status_filter,
                         search=search)

@bp.route('/appointments/new', methods=['GET', 'POST'])
@login_required
@require_role('receptionist')
def new_appointment():
    """Crear nueva cita"""
    if request.method == 'POST':
        try:
            # Debug - Imprimir todos los datos del formulario
            print("=== DEBUG: Datos del formulario ===")
            for key, value in request.form.items():
                print(f"{key}: '{value}'")
            print("=== FIN DEBUG ===")
            
            # Obtener datos del formulario
            patient_id = request.form.get('patient_id')
            doctor_id = request.form.get('doctor_id')
            specialty_id = request.form.get('specialty_id')
            appointment_date = request.form.get('appointment_date')
            appointment_time = request.form.get('appointment_time')
            reason = request.form.get('reason', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validaciones básicas
            missing_fields = []
            if not patient_id:
                missing_fields.append('Paciente')
            if not doctor_id:
                missing_fields.append('Doctor')
            if not specialty_id:
                missing_fields.append('Especialidad')
            if not appointment_date:
                missing_fields.append('Fecha')
            if not appointment_time:
                missing_fields.append('Hora')
            
            if missing_fields:
                flash(f'Los siguientes campos son obligatorios: {", ".join(missing_fields)}', 'error')
                # Obtener datos para repoblar el formulario
                patients = Patient.query.order_by(Patient.first_name, Patient.last_name).all()
                doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).all()
                specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
                
                return render_template('receptionist/appointment_form.html',
                                     title='Nueva Cita',
                                     patients=patients,
                                     doctors=doctors,
                                     specialties=specialties,
                                     appointment=None,
                                     form_data=request.form)
            
            # Combinar fecha y hora
            try:
                date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                time_obj = datetime.strptime(appointment_time, '%H:%M').time()
                appointment_datetime = datetime.combine(date_obj, time_obj)
            except ValueError:
                flash('Formato de fecha u hora inválido', 'error')
                # Obtener datos para repoblar el formulario
                patients = Patient.query.order_by(Patient.first_name, Patient.last_name).all()
                doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).all()
                specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
                
                return render_template('receptionist/appointment_form.html',
                                     title='Nueva Cita',
                                     patients=patients,
                                     doctors=doctors,
                                     specialties=specialties,
                                     appointment=None,
                                     form_data=request.form)
            
            # Validar que la fecha sea futura
            if appointment_datetime <= datetime.now():
                flash('La cita debe ser programada para una fecha y hora futura', 'error')
                # Obtener datos para repoblar el formulario
                patients = Patient.query.order_by(Patient.first_name, Patient.last_name).all()
                doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).all()
                specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
                
                return render_template('receptionist/appointment_form.html',
                                     title='Nueva Cita',
                                     patients=patients,
                                     doctors=doctors,
                                     specialties=specialties,
                                     appointment=None,
                                     form_data=request.form)
            
            # Verificar disponibilidad del doctor
            existing_appointment = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date_time == appointment_datetime,
                Appointment.status.in_(['scheduled', 'confirmed'])
            ).first()
            
            if existing_appointment:
                flash('El doctor ya tiene una cita programada en esa fecha y hora', 'error')
                # Obtener datos para repoblar el formulario
                patients = Patient.query.order_by(Patient.first_name, Patient.last_name).all()
                doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).all()
                specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
                
                return render_template('receptionist/appointment_form.html',
                                     title='Nueva Cita',
                                     patients=patients,
                                     doctors=doctors,
                                     specialties=specialties,
                                     appointment=None,
                                     form_data=request.form)
            
            # Verificar que el paciente no tenga cita en la misma hora
            patient_conflict = Appointment.query.filter(
                Appointment.patient_id == patient_id,
                Appointment.date_time == appointment_datetime,
                Appointment.status.in_(['scheduled', 'confirmed'])
            ).first()
            
            if patient_conflict:
                flash('El paciente ya tiene una cita programada en esa fecha y hora', 'error')
                # Obtener datos para repoblar el formulario
                patients = Patient.query.order_by(Patient.first_name, Patient.last_name).all()
                doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).all()
                specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
                
                return render_template('receptionist/appointment_form.html',
                                     title='Nueva Cita',
                                     patients=patients,
                                     doctors=doctors,
                                     specialties=specialties,
                                     appointment=None,
                                     form_data=request.form)
            
            # Crear la cita
            appointment = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                specialty_id=specialty_id,
                date_time=appointment_datetime,
                reason=reason if reason else None,
                notes=notes if notes else None,
                status='scheduled'
            )
            
            from app import db
            db.session.add(appointment)
            db.session.commit()
            
            # Obtener datos para el mensaje
            patient = db.session.get(Patient, patient_id)
            doctor = db.session.get(User, doctor_id)
            
            flash(f'Cita programada exitosamente para {patient.full_name} con Dr. {doctor.full_name}', 'success')
            return redirect(url_for('receptionist.appointments'))
            
        except Exception as e:
            from app import db
            db.session.rollback()
            flash(f'Error al crear la cita: {str(e)}', 'error')
            # Obtener datos para repoblar el formulario
            patients = Patient.query.order_by(Patient.first_name, Patient.last_name).all()
            doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).all()
            specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
            
            return render_template('receptionist/appointment_form.html',
                                 title='Nueva Cita',
                                 patients=patients,
                                 doctors=doctors,
                                 specialties=specialties,
                                 appointment=None,
                                 form_data=request.form)
    
    # GET - Mostrar formulario
    patients = Patient.query.order_by(Patient.first_name, Patient.last_name).all()
    doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).all()
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
    
    # Verificar si se pasó un patient_id en la URL para pre-llenar el formulario
    patient_id = request.args.get('patient_id')
    form_data = {}
    if patient_id:
        try:
            patient = Patient.query.get(int(patient_id))
            if patient:
                form_data['patient_id'] = patient.id
        except (ValueError, TypeError):
            # Si patient_id no es un número válido, ignorar
            pass
    
    return render_template('receptionist/appointment_form.html',
                         title='Nueva Cita',
                         patients=patients,
                         doctors=doctors,
                         specialties=specialties,
                         appointment=None,
                         form_data=form_data if form_data else None)

@bp.route('/appointments/<int:appointment_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('receptionist')
def edit_appointment(appointment_id):
    """Editar cita existente"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verificar que la cita pueda ser editada
    if appointment.status not in ['scheduled']:
        flash('Solo se pueden editar citas programadas', 'error')
        return redirect(url_for('receptionist.appointments'))
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            patient_id = request.form.get('patient_id')
            doctor_id = request.form.get('doctor_id')
            specialty_id = request.form.get('specialty_id')
            appointment_date = request.form.get('appointment_date')
            appointment_time = request.form.get('appointment_time')
            reason = request.form.get('reason', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validaciones básicas
            if not all([patient_id, doctor_id, specialty_id, appointment_date, appointment_time]):
                flash('Todos los campos obligatorios deben ser completados', 'error')
                return render_template('receptionist/appointment_form.html',
                                     title='Editar Cita',
                                     appointment=appointment,
                                     patients=Patient.query.order_by(Patient.first_name).all(),
                                     doctors=User.query.filter_by(role='doctor', is_active=True).all(),
                                     specialties=Specialty.query.filter_by(is_active=True).all())
            
            # Combinar fecha y hora
            try:
                date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                time_obj = datetime.strptime(appointment_time, '%H:%M').time()
                appointment_datetime = datetime.combine(date_obj, time_obj)
            except ValueError:
                flash('Formato de fecha u hora inválido', 'error')
                return render_template('receptionist/appointment_form.html',
                                     title='Editar Cita',
                                     appointment=appointment,
                                     patients=Patient.query.order_by(Patient.first_name).all(),
                                     doctors=User.query.filter_by(role='doctor', is_active=True).all(),
                                     specialties=Specialty.query.filter_by(is_active=True).all())
            
            # Validar que la fecha sea futura
            if appointment_datetime <= datetime.now():
                flash('La cita debe ser programada para una fecha y hora futura', 'error')
                return render_template('receptionist/appointment_form.html',
                                     title='Editar Cita',
                                     appointment=appointment,
                                     patients=Patient.query.order_by(Patient.first_name).all(),
                                     doctors=User.query.filter_by(role='doctor', is_active=True).all(),
                                     specialties=Specialty.query.filter_by(is_active=True).all())
            
            # Si cambió la fecha/hora, verificar disponibilidad
            if appointment_datetime != appointment.date_time or int(doctor_id) != appointment.doctor_id:
                existing_appointment = Appointment.query.filter(
                    Appointment.doctor_id == doctor_id,
                    Appointment.date_time == appointment_datetime,
                    Appointment.status.in_(['scheduled', 'confirmed']),
                    Appointment.id != appointment_id  # Excluir la cita actual
                ).first()
                
                if existing_appointment:
                    flash('El doctor ya tiene una cita programada en esa fecha y hora', 'error')
                    return render_template('receptionist/appointment_form.html',
                                         title='Editar Cita',
                                         appointment=appointment,
                                         patients=Patient.query.order_by(Patient.first_name).all(),
                                         doctors=User.query.filter_by(role='doctor', is_active=True).all(),
                                         specialties=Specialty.query.filter_by(is_active=True).all())
            
            # Actualizar la cita
            appointment.patient_id = patient_id
            appointment.doctor_id = doctor_id
            appointment.specialty_id = specialty_id
            appointment.date_time = appointment_datetime
            appointment.reason = reason if reason else None
            appointment.notes = notes if notes else None
            
            from app import db
            db.session.commit()
            
            flash('Cita actualizada exitosamente', 'success')
            return redirect(url_for('receptionist.appointments'))
            
        except Exception as e:
            from app import db
            db.session.rollback()
            flash(f'Error al actualizar la cita: {str(e)}', 'error')
    
    # GET - Mostrar formulario
    patients = Patient.query.order_by(Patient.first_name, Patient.last_name).all()
    doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).all()
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
    
    return render_template('receptionist/appointment_form.html',
                         title='Editar Cita',
                         appointment=appointment,
                         patients=patients,
                         doctors=doctors,
                         specialties=specialties)

@bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@require_role('receptionist')
def cancel_appointment(appointment_id):
    """Cancelar cita"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        
        if not appointment.can_be_cancelled:
            return jsonify({
                'success': False,
                'message': 'Esta cita no puede ser cancelada'            }), 400
        
        appointment.status = 'cancelled'
        appointment.notes = f"Cancelada por recepcionista el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Cita cancelada exitosamente'
        })
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al cancelar cita: {str(e)}'
        }), 500

@bp.route('/appointments/<int:appointment_id>')
@login_required
@require_role('receptionist')
def view_appointment(appointment_id):
    """Ver detalles de la cita"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Obtener citas recientes del paciente
    recent_appointments = Appointment.query.filter_by(patient_id=appointment.patient_id)\
                                          .filter(Appointment.id != appointment_id)\
                                          .order_by(Appointment.date_time.desc())\
                                          .limit(5).all()
    
    return render_template('receptionist/appointment_detail.html',
                         title=f'Cita: {appointment.patient.full_name}',
                         appointment=appointment,
                         recent_appointments=recent_appointments)

def get_billing_statistics():
    """Obtener estadísticas de facturación"""
    today = date.today()
    current_month = today.replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    stats = {}
    
    # Total de facturas
    stats['total_invoices'] = Invoice.query.count()
    
    # Facturas por estado    stats['pending_invoices'] = Invoice.query.filter_by(status='pending').count()
    stats['paid_invoices'] = Invoice.query.filter_by(status='paid').count()
    stats['overdue_invoices'] = Invoice.query.filter(
        Invoice.status == 'pending',
        Invoice.due_date < today
    ).count()
    
    # Montos totales
    stats['total_pending_amount'] = db.session.query(
        func.sum(Invoice.total_amount)
    ).filter_by(status='pending').scalar() or Decimal('0.00')
    
    stats['total_paid_amount'] = db.session.query(
        func.sum(Invoice.total_amount)
    ).filter_by(status='paid').scalar() or Decimal('0.00')
      # Ingresos del mes actual
    stats['monthly_income'] = db.session.query(
        func.sum(Invoice.total_amount)
    ).filter(
        Invoice.status == 'paid',
        Invoice.payment_date >= current_month
    ).scalar() or Decimal('0.00')
    
    # Ingresos del mes pasado
    stats['last_month_income'] = db.session.query(
        func.sum(Invoice.total_amount)
    ).filter(
        Invoice.status == 'paid',
        Invoice.payment_date >= last_month,
        Invoice.payment_date < current_month
    ).scalar() or Decimal('0.00')
    
    # Calcular crecimiento mensual
    if stats['last_month_income'] > 0:
        growth = ((stats['monthly_income'] - stats['last_month_income']) / stats['last_month_income']) * 100
        stats['monthly_growth'] = round(float(growth), 1)
    else:
        stats['monthly_growth'] = 0.0
    
    return stats


@bp.route('/billing/new')
@login_required
@require_role('receptionist')
def new_invoice():
    """Crear nueva factura"""    # Obtener citas completadas sin factura
    completed_appointments = Appointment.query.filter(
        Appointment.status == 'completed'
    ).outerjoin(Invoice).filter(Invoice.id.is_(None)).order_by(desc(Appointment.date_time)).all()
    
    # Obtener todos los pacientes para facturación manual
    patients = Patient.query.filter_by(is_active=True).order_by(Patient.last_name, Patient.first_name).all()
    
    # Obtener doctores
    doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.last_name, User.first_name).all()
    
    return render_template('receptionist/invoice_form.html',
                         title='Nueva Factura',
                         completed_appointments=completed_appointments,
                         patients=patients,
                         doctors=doctors)


@bp.route('/billing/new', methods=['POST'])
@login_required
@require_role('receptionist')
def create_invoice():
    """Crear nueva factura/pago"""
    try:
        # Debug - Imprimir todos los datos del formulario
        print("=== DEBUG: Datos del formulario de facturación ===")
        for key, value in request.form.items():
            print(f"{key}: '{value}'")
        print("=== FIN DEBUG ===")
        
        # Obtener datos del formulario
        appointment_id = request.form.get('appointment_id')
        patient_id = request.form.get('patient_id')
        payment_method = request.form.get('payment_method')
        voucher_type = request.form.get('voucher_type')
        total_amount = request.form.get('total_amount')
        payment_notes = request.form.get('payment_notes', '').strip()
        
        # Datos del comprobante
        client_name = request.form.get('client_name', '').strip()
        client_dni = request.form.get('client_dni', '').strip()
        company_name = request.form.get('company_name', '').strip()
        company_ruc = request.form.get('company_ruc', '').strip()
        company_address = request.form.get('company_address', '').strip()
        
        print(f"=== DEBUG: Valores procesados ===")
        print(f"appointment_id: {appointment_id}")
        print(f"patient_id: {patient_id}")
        print(f"payment_method: {payment_method}")
        print(f"voucher_type: {voucher_type}")
        print(f"total_amount: {total_amount}")
        print(f"=== FIN DEBUG ===")
        
        # Validaciones básicas
        if not patient_id:
            flash('Debe seleccionar un paciente', 'error')
            return redirect(url_for('receptionist.new_invoice'))
        
        if not payment_method:
            flash('Debe seleccionar un método de pago', 'error')
            return redirect(url_for('receptionist.new_invoice'))
            
        if not voucher_type:
            flash('Debe seleccionar un tipo de comprobante', 'error')
            return redirect(url_for('receptionist.new_invoice'))
        
        if not total_amount:
            flash('Debe especificar el monto total', 'error')
            return redirect(url_for('receptionist.new_invoice'))
        
        # Validar monto total
        try:
            total_amount = float(total_amount)
            if total_amount <= 0:
                flash('El monto total debe ser mayor a cero', 'error')
                return redirect(url_for('receptionist.new_invoice'))
        except (ValueError, TypeError):
            flash('Monto total inválido', 'error')
            return redirect(url_for('receptionist.new_invoice'))
        
        try:
            subtotal = Decimal(total_amount) if total_amount else Decimal('0.00')
        except:
            subtotal = Decimal('0.00')
            
        if subtotal <= 0:
            flash('El monto debe ser mayor a 0', 'error')
            return redirect(url_for('receptionist.new_invoice'))
        
        # Validaciones específicas por tipo de comprobante
        if voucher_type == 'boleta':
            if not client_name or not client_dni:
                flash('Complete los datos requeridos para la boleta', 'error')
                return redirect(url_for('receptionist.new_invoice'))
        elif voucher_type == 'factura':
            if not company_name or not company_ruc or not company_address:
                flash('Complete los datos requeridos para la factura', 'error')
                return redirect(url_for('receptionist.new_invoice'))
        
        # Procesar el monto total
        try:
            subtotal = Decimal(str(total_amount))
        except (ValueError, TypeError):
            flash('Monto total inválido', 'error')
            return redirect(url_for('receptionist.new_invoice'))
        
        # Obtener información del paciente y cita
        patient = db.session.get(Patient, patient_id)
        if not patient:
            flash('Paciente no encontrado', 'error')
            return redirect(url_for('receptionist.new_invoice'))
        
        # Obtener doctor (de la cita o usar uno por defecto)
        doctor_id = None
        description = f"Pago por consulta médica - {patient.full_name}"
        
        if appointment_id:
            appointment = db.session.get(Appointment, appointment_id)
            if appointment:
                doctor_id = appointment.doctor_id
                doctor = db.session.get(User, doctor_id)
                specialty = db.session.get(Specialty, appointment.specialty_id)
                description = f"Consulta {specialty.name if specialty else 'Médica'} - Dr. {doctor.full_name if doctor else 'N/A'}"
        
        # Si no hay doctor de la cita, usar el primer doctor activo
        if not doctor_id:
            first_doctor = User.query.filter_by(role='doctor', is_active=True).first()
            if first_doctor:
                doctor_id = first_doctor.id
            else:
                flash('No hay doctores disponibles para asociar la factura', 'error')
                return redirect(url_for('receptionist.new_invoice'))
        
        # Crear nueva factura
        invoice = Invoice(
            patient_id=patient_id,
            appointment_id=appointment_id if appointment_id else None,
            doctor_id=doctor_id,
            invoice_number=Invoice.get_next_invoice_number(),
            issue_date=date.today(),
            due_date=date.today(),  # Fecha de vencimiento igual a hoy para pagos inmediatos
            subtotal=Decimal('0.00'),  # Se calculará automáticamente
            total_amount=Decimal('0.00'),  # Se calculará automáticamente
            discount_percentage=0.0,
            tax_percentage=0.0,
            status='paid',
            payment_date=date.today(),
            payment_method=payment_method,
            notes=description,
            created_by=current_user.id
        )
        
        # Crear servicio asociado a la factura
        from app.models.invoice import InvoiceService
        
        # Obtener información del servicio desde la cita si existe
        service_description = "Consulta médica"
        service_price = subtotal  # Precio por defecto
        
        if appointment_id:
            appointment = db.session.get(Appointment, appointment_id)
            if appointment:
                # Usar el precio real de la especialidad, no el que viene del formulario
                specialty = db.session.get(Specialty, appointment.specialty_id)
                if specialty:
                    service_price = specialty.base_price
                    service_description = f"Consulta médica - {specialty.name}"
                
                # Solo añadir el motivo si es diferente a la especialidad
                if appointment.reason and appointment.reason != specialty.name:
                    service_description = f"Consulta médica - {appointment.reason}"
        
        # Agregar a la base de datos
        db.session.add(invoice)
        db.session.flush()  # Para obtener el ID de la factura
        
        # Limpiar cualquier servicio existente (por si hay duplicados)
        existing_services = InvoiceService.query.filter_by(invoice_id=invoice.id).all()
        for existing_service in existing_services:
            db.session.delete(existing_service)
        db.session.flush()
        
        # Crear UN SOLO servicio de factura
        service = InvoiceService(
            invoice_id=invoice.id,
            description=service_description,
            quantity=1,
            unit_price=service_price,
            notes=appointment.notes if appointment_id and appointment and appointment.notes else None
        )
        
        db.session.add(service)
        
        # Recalcular totales ahora que tiene servicios
        invoice.calculate_totals()
        
        # Marcar como pagada inmediatamente
        invoice.mark_as_paid(payment_method, date.today())
        
        # Agregar notas adicionales del formulario
        payment_notes = request.form.get('payment_notes', '').strip()
        if payment_notes:
            current_notes = invoice.notes or ""
            invoice.notes = f"{current_notes}\n{payment_notes}".strip()
        
        # Guardar información del comprobante
        voucher_info = {
            'type': voucher_type,
            'payment_method': payment_method
        }
        
        if voucher_type == 'boleta':
            voucher_info.update({
                'client_name': client_name,
                'client_dni': client_dni
            })
        elif voucher_type == 'factura':
            voucher_info.update({
                'company_name': company_name,
                'company_ruc': company_ruc,
                'company_address': company_address
            })
        
        # Guardar información del comprobante en las notas (temporal)
        if not invoice.notes:
            invoice.notes = ""
        invoice.notes += f"\n\nComprobante: {voucher_type.upper()}"
        if voucher_type == 'boleta':
            invoice.notes += f"\nCliente: {client_name}\nDNI: {client_dni}"
        else:
            invoice.notes += f"\nEmpresa: {company_name}\nRUC: {company_ruc}\nDirección: {company_address}"
        invoice.notes += f"\nMétodo de pago: {payment_method}"
        
        # Guardar en base de datos
        db.session.add(invoice)
        db.session.commit()
        
        flash(f'Pago procesado exitosamente. Factura {invoice.invoice_number} generada.', 'success')
        return redirect(url_for('receptionist.view_invoice', invoice_id=invoice.id))
        
    except ValueError as e:
        print(f"=== DEBUG: ValueError en create_invoice ===")
        print(f"Error: {str(e)}")
        print(f"=== FIN DEBUG ===")
        db.session.rollback()
        flash(f'Error en los datos ingresados: {str(e)}', 'error')
        return redirect(url_for('receptionist.new_invoice'))
    except Exception as e:
        print(f"=== DEBUG: Exception en create_invoice ===")
        print(f"Error: {str(e)}")
        print(f"Type: {type(e)}")
        import traceback
        traceback.print_exc()
        print(f"=== FIN DEBUG ===")
        db.session.rollback()
        flash(f'Error al procesar el pago: {str(e)}', 'error')
        return redirect(url_for('receptionist.new_invoice'))


@bp.route('/billing/<int:invoice_id>')
@login_required
@require_role('receptionist')
def view_invoice(invoice_id):
    """Ver detalles de factura"""
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('receptionist/invoice_detail.html',
                         title=f'Factura {invoice.invoice_number}',
                         invoice=invoice)


@bp.route('/billing/<int:invoice_id>/pay', methods=['POST'])
@login_required
@require_role('receptionist')
def pay_invoice(invoice_id):
    """Marcar factura como pagada"""
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        
        if invoice.status == 'paid':
            return jsonify({
                'success': False,
                'message': 'La factura ya está pagada'
            })
        
        payment_method = request.json.get('payment_method', 'cash')
        payment_date = request.json.get('payment_date')
        
        if payment_date:
            payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
        else:
            payment_date = date.today()
        
        # Marcar como pagada
        invoice.mark_as_paid(payment_method, payment_date)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Factura {invoice.invoice_number} marcada como pagada'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al procesar pago: {str(e)}'
        })


@bp.route('/billing/<int:invoice_id>/cancel', methods=['POST'])
@login_required
@require_role('receptionist')
def cancel_invoice(invoice_id):
    """Cancelar factura"""
    try:
        invoice = Invoice.query.get_or_404(invoice_id)        
        if invoice.status == 'paid':
            return jsonify({
                'success': False,
                'message': 'No se puede cancelar una factura pagada'
            })
        
        invoice.status = 'cancelled'
        invoice.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Factura {invoice.invoice_number} cancelada'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al cancelar factura: {str(e)}'
        })


@bp.route('/billing/<int:invoice_id>/print-data')
@login_required
@require_role('receptionist')
def get_invoice_print_data(invoice_id):
    """Obtener datos de factura para impresión"""
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        
        # Obtener datos del paciente
        patient = invoice.patient
        
        # Verificar si es menor de edad para datos del tutor
        is_minor = patient.is_minor
        
        # Datos del doctor
        doctor = invoice.doctor
        
        # Datos de la cita si existe
        appointment = invoice.appointment
        
        # Preparar datos para el ticket
        invoice_data = {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'issue_date': invoice.issue_date.isoformat(),
            'total_amount': float(invoice.total_amount),
            'payment_status': invoice.status,
            'payment_method': invoice.payment_method,
            'payment_date': invoice.payment_date.isoformat() if invoice.payment_date else None,
            
            # Datos del paciente
            'patient_name': patient.full_name,
            'patient_dni': patient.dni,
            'patient_is_minor': is_minor,
            
            # Datos del tutor (si es menor)
            'guardian_name': patient.guardian_name if is_minor else None,
            'guardian_dni': patient.guardian_dni if is_minor else None,
            
            # Datos del doctor
            'doctor_name': f"{doctor.first_name} {doctor.last_name}",
            
            # Datos de la cita
            'appointment_date': appointment.appointment_date.isoformat() if appointment else None,
            
            # Datos del recepcionista que atiende
            'receptionist_name': f"{current_user.first_name} {current_user.last_name}"
        }
        
        return jsonify({
            'success': True,
            'invoice': invoice_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener datos: {str(e)}'
        })


@bp.route('/billing/reports')
@login_required
@require_role('receptionist')
def billing_reports():
    """Reportes de facturación"""
    # Período de reporte (últimos 6 meses por defecto)
    end_date = date.today()
    start_date = end_date - timedelta(days=180)
    
    # Parámetros de consulta
    start_date_param = request.args.get('start_date')
    end_date_param = request.args.get('end_date')
    
    if start_date_param:
        start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
    if end_date_param:
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
    
    # Estadísticas del período
    period_stats = get_period_billing_stats(start_date, end_date)
    
    # Ingresos mensuales para gráfico
    monthly_income = get_monthly_income_data(start_date, end_date)
    
    # Estadísticas por doctor
    doctor_stats = get_doctor_billing_stats(start_date, end_date)
    
    return render_template('receptionist/billing_reports.html',
                         title='Reportes de Facturación',
                         period_stats=period_stats,
                         monthly_income=monthly_income,
                         doctor_stats=doctor_stats,
                         start_date=start_date,
                         end_date=end_date)


def get_period_billing_stats(start_date, end_date):
    """Estadísticas de facturación para un período"""
    stats = {}
    
    # Facturas del período
    period_invoices = Invoice.query.filter(
        Invoice.issue_date.between(start_date, end_date)
    )    
    stats['total_invoices'] = period_invoices.count()
    stats['paid_invoices'] = period_invoices.filter_by(status='paid').count()
    stats['pending_invoices'] = period_invoices.filter_by(status='pending').count()
    
    # Montos
    stats['total_amount'] = db.session.query(
        func.sum(Invoice.total_amount)
    ).filter(
        Invoice.issue_date.between(start_date, end_date)
    ).scalar() or Decimal('0.00')
    
    stats['paid_amount'] = db.session.query(
        func.sum(Invoice.total_amount)    ).filter(
        Invoice.issue_date.between(start_date, end_date),
        Invoice.status == 'paid'
    ).scalar() or Decimal('0.00')
    
    stats['pending_amount'] = db.session.query(
        func.sum(Invoice.total_amount)
    ).filter(
        Invoice.issue_date.between(start_date, end_date),
        Invoice.status == 'pending'
    ).scalar() or Decimal('0.00')
    
    # Porcentajes
    if stats['total_invoices'] > 0:
        stats['payment_rate'] = round((stats['paid_invoices'] / stats['total_invoices']) * 100, 1)
    else:
        stats['payment_rate'] = 0
    
    return stats


def get_monthly_income_data(start_date, end_date):
    """Datos de ingresos mensuales para gráficos"""
    monthly_data = []
    
    # Agrupar por mes
    monthly_income = db.session.query(
        extract('year', Invoice.payment_date).label('year'),
        extract('month', Invoice.payment_date).label('month'),
        func.sum(Invoice.total_amount).label('total')
    ).filter(
        Invoice.status == 'paid',
        Invoice.payment_date.between(start_date, end_date)
    ).group_by(
        extract('year', Invoice.payment_date),
        extract('month', Invoice.payment_date)
    ).order_by('year', 'month').all()
    
    for item in monthly_income:
        month_name = date(int(item.year), int(item.month), 1).strftime('%B %Y')
        monthly_data.append({
            'month': f"{int(item.year)}-{int(item.month):02d}",
            'month_name': month_name,
            'amount': float(item.total)
        })
    
    return monthly_data


def get_doctor_billing_stats(start_date, end_date):
    """Estadísticas de facturación por doctor"""
    doctor_stats = []
    
    doctor_data = db.session.query(
        User.id,
        User.first_name,
        User.last_name,
        func.count(Invoice.id).label('total_invoices'),
        func.sum(Invoice.total_amount).label('total_amount'),
        func.count(func.nullif(Invoice.status != 'paid', True)).label('paid_invoices')
    ).join(
        Invoice, User.id == Invoice.doctor_id
    ).filter(
        Invoice.issue_date.between(start_date, end_date)
    ).group_by(
        User.id, User.first_name, User.last_name
    ).order_by(func.sum(Invoice.total_amount).desc()).all()
    
    for doctor in doctor_data:
        doctor_stats.append({
            'id': doctor.id,
            'name': f"Dr. {doctor.first_name} {doctor.last_name}",
            'total_invoices': doctor.total_invoices,
            'total_amount': float(doctor.total_amount or 0),
            'paid_invoices': doctor.paid_invoices or 0,
            'payment_rate': round((doctor.paid_invoices or 0) / doctor.total_invoices * 100, 1) if doctor.total_invoices > 0 else 0        })
    
    return doctor_stats

# API para obtener horarios disponibles
@bp.route('/api/available-times')
@login_required
@require_role('receptionist')
def api_available_times():
    """API para obtener horarios disponibles de un doctor en una fecha específica"""
    try:
        doctor_id = request.args.get('doctor_id')
        date_str = request.args.get('date')
        specialty_id = request.args.get('specialty_id')
        
        if not doctor_id or not date_str:
            return jsonify({'success': False, 'error': 'Parámetros faltantes'}), 400
        
        # Parsear fecha
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Formato de fecha inválido'}), 400
        
        # Obtener doctor y verificar especialidad
        from app.models.work_schedule import WorkSchedule
        doctor = db.session.get(User, doctor_id)
        if not doctor:
            return jsonify({'success': False, 'error': 'Doctor no encontrado'}), 404
        
        # Usar la especialidad del doctor automáticamente
        doctor_specialty_id = doctor.specialty_id if doctor.specialty else None
        
        # Verificar que la fecha esté dentro de la vigencia del doctor
        schedules = WorkSchedule.query.filter_by(
            doctor_id=int(doctor_id),
            day_of_week=date_obj.weekday(),
            is_active=True
        ).all()
        
        valid_schedules = []
        for schedule in schedules:
            if (schedule.start_date <= date_obj and 
                (not schedule.end_date or schedule.end_date >= date_obj)):
                valid_schedules.append(schedule)
        
        if not valid_schedules:
            return jsonify({
                'success': True,
                'available_times': [],
                'message': 'No hay horarios disponibles para esta fecha'
            })
        
        # Obtener horarios disponibles
        available_times = WorkSchedule.get_available_times(
            int(doctor_id), 
            date_obj, 
            doctor_specialty_id
        )
        
        # Formatear horarios para respuesta
        formatted_times = [time.strftime('%H:%M') for time in available_times]
        
        return jsonify({
            'success': True,
            'available_times': formatted_times,
            'date': date_str,
            'doctor_id': doctor_id,
            'specialty_id': doctor_specialty_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API para obtener especialidad del doctor
@bp.route('/api/doctors/<int:doctor_id>/specialty')
@login_required
@require_role('receptionist')
def api_doctor_specialty(doctor_id):
    """API para obtener la especialidad de un doctor específico"""
    try:
        doctor = User.query.filter_by(id=doctor_id, role='doctor', is_active=True).first()
        if not doctor:
            return jsonify({'success': False, 'error': 'Doctor no encontrado'}), 404
        
        return jsonify({
            'success': True,
            'doctor_id': doctor.id,
            'doctor_name': doctor.full_name,
            'specialty_id': doctor.specialty_id,
            'specialty_name': doctor.specialty.name if doctor.specialty else None
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API para obtener fechas disponibles del doctor
@bp.route('/api/doctors/<int:doctor_id>/available-dates')
@login_required
@require_role('receptionist')
def api_doctor_available_dates(doctor_id):
    """API para obtener fechas disponibles de un doctor específico"""
    try:
        from app.models.work_schedule import WorkSchedule
        from datetime import datetime, timedelta
        
        doctor = User.query.filter_by(id=doctor_id, role='doctor', is_active=True).first()
        if not doctor:
            return jsonify({'success': False, 'error': 'Doctor no encontrado'}), 404
        
        # Obtener todos los horarios del doctor
        schedules = WorkSchedule.query.filter_by(
            doctor_id=doctor_id,
            is_active=True
        ).all()
        
        if not schedules:
            return jsonify({
                'success': True,
                'available_dates': [],
                'message': 'Doctor sin horarios configurados'
            })
        
        # Obtener el rango de fechas de vigencia
        start_dates = [s.start_date for s in schedules if s.start_date]
        end_dates = [s.end_date for s in schedules if s.end_date]
        
        if not start_dates:
            return jsonify({
                'success': True,
                'available_dates': [],
                'message': 'Doctor sin fechas de vigencia configuradas'
            })
        
        # Calcular rango de fechas disponibles
        min_start_date = min(start_dates)
        max_end_date = max(end_dates) if end_dates else (min_start_date + timedelta(days=365))
        
        # Obtener días de la semana disponibles
        available_weekdays = set()
        for schedule in schedules:
            if (schedule.start_date and schedule.start_date <= datetime.now().date() + timedelta(days=365) and
                (not schedule.end_date or schedule.end_date >= datetime.now().date())):
                available_weekdays.add(schedule.day_of_week)
        
        # Generar fechas disponibles
        available_dates = []
        current_date = max(min_start_date, datetime.now().date())
        end_date = min(max_end_date, datetime.now().date() + timedelta(days=90))  # Máximo 3 meses
        
        while current_date <= end_date:
            # Verificar si el día de la semana tiene horarios
            if current_date.weekday() in available_weekdays:
                # Verificar si hay horarios válidos para esta fecha
                valid_schedules = [s for s in schedules if 
                                 s.day_of_week == current_date.weekday() and
                                 s.start_date <= current_date and
                                 (not s.end_date or s.end_date >= current_date)]
                
                if valid_schedules:
                    available_dates.append(current_date.strftime('%Y-%m-%d'))
            
            current_date += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'available_dates': available_dates,
            'validity_start': min_start_date.strftime('%Y-%m-%d'),
            'validity_end': max_end_date.strftime('%Y-%m-%d') if max_end_date else None,
            'doctor_id': doctor_id,
            'doctor_name': doctor.full_name
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API para búsqueda de doctores en tiempo real
@bp.route('/api/doctors/search')
@login_required
@require_role('receptionist')
def search_doctors():
    """API para búsqueda de doctores con autocompletado"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        # Si no hay query o es muy corta, devolver todos los doctores activos
        doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).limit(20).all()
    else:
        # Búsqueda por nombre o apellido
        search_term = f'%{query}%'
        doctors = User.query.filter(
            User.role == 'doctor',
            User.is_active == True,
            (User.first_name.ilike(search_term) | 
             User.last_name.ilike(search_term))
        ).order_by(User.first_name, User.last_name).limit(20).all()
    
    # Convertir a JSON
    doctors_data = []
    for doctor in doctors:
        doctors_data.append({
            'id': doctor.id,
            'name': doctor.first_name,
            'lastname': doctor.last_name,
            'full_name': doctor.full_name,
            'specialty_id': doctor.specialty_id,
            'specialty_name': doctor.specialty.name if doctor.specialty else 'Sin especialidad'
        })
    
    return jsonify({
        'success': True,
        'doctors': doctors_data,
        'total': len(doctors_data)
    })

# API para obtener información de citas del paciente (para facturación)
@bp.route('/api/patient/<int:patient_id>/appointments')
@login_required
@require_role('receptionist')
def get_patient_appointments(patient_id):
    """API para obtener citas del paciente que pueden ser facturadas"""
    try:
        # Obtener todas las citas del paciente que NO estén canceladas y NO tengan factura
        appointments = Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.status != 'cancelled'  # Excluir canceladas
        ).outerjoin(Invoice).filter(Invoice.id.is_(None)).order_by(desc(Appointment.date_time)).all()
        
        # Si no hay ninguna cita pendiente de facturación, devolver lista vacía (ya no forzamos la última cita)
        # De esta manera el recepcionista no verá citas canceladas por error.
        
        appointments_data = []
        for appointment in appointments:
            # Obtener información del doctor y especialidad
            doctor = db.session.get(User, appointment.doctor_id)
            specialty = db.session.get(Specialty, appointment.specialty_id)
            
            # Usar el precio configurado por el administrador
            cost = 80.00  # Costo base por defecto
            if specialty and specialty.base_price:
                cost = float(specialty.base_price)  # Usar precio configurado por administrador
            
            appointments_data.append({
                'id': appointment.id,
                'date': appointment.date_time.strftime('%Y-%m-%dT%H:%M:00'),  # Formato ISO con segundos
                'date_formatted': appointment.date_time.strftime('%d/%m/%Y %H:%M'),
                'doctor': f"Dr. {doctor.first_name} {doctor.last_name}" if doctor else "No especificado",
                'doctor_id': appointment.doctor_id,
                'specialty': specialty.name if specialty else "No especificado",
                'specialty_id': appointment.specialty_id,
                'cost': cost,
                'reason': appointment.reason or "Consulta médica",
                'notes': appointment.notes or "",
                'status': appointment.status,
                'can_be_billed': appointment.status == 'completed'
            })
        
        return jsonify({
            'success': True,
            'appointments': appointments_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
