from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from sqlalchemy import func, extract, distinct, and_
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, date
from collections import defaultdict
import json
import csv
import io
from app.utils.decorators import require_role
from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord
from app.models.specialty import Specialty
from app.models.salary_configuration import SalaryConfiguration, CommissionRecord
from app.models.work_schedule import WorkSchedule
from app.models.invoice import Invoice
from app import db

# Blueprint para administrador
bp = Blueprint('admin', __name__)

@bp.route('/dashboard')
@login_required
@require_role('admin')
def dashboard():
    """Dashboard del administrador"""
    today = date.today()
    
    # Estadísticas básicas
    stats = {
        'total_users': User.query.count(),
        'total_patients': Patient.query.count(),
        'active_doctors': User.query.filter_by(role='doctor', is_active=True).count(),
        'active_nurses': User.query.filter_by(role='nurse', is_active=True).count(),
        'active_receptionists': User.query.filter_by(role='receptionist', is_active=True).count(),
        'total_specialties': Specialty.query.filter_by(is_active=True).count(),
    }
    
    # Citas de hoy
    today_appointments = Appointment.query.filter(
        func.date(Appointment.date_time) == today
    ).count()
    
    # Citas pendientes (futuras)
    pending_appointments = Appointment.query.filter(
        Appointment.date_time > datetime.now(),
        Appointment.status == 'scheduled'
    ).count()
    
    # Citas completadas este mes
    start_of_month = today.replace(day=1)
    completed_this_month = Appointment.query.filter(
        Appointment.date_time >= start_of_month,
        Appointment.status == 'completed'
    ).count()
    
    # Ingresos del mes actual
    monthly_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.issue_date >= start_of_month,
        Invoice.status == 'paid'
    ).scalar() or 0
    
    # Últimos pacientes registrados
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    
    # Citas de hoy por estado
    today_appointments_by_status = db.session.query(
        Appointment.status, 
        func.count(Appointment.id)
    ).filter(
        func.date(Appointment.date_time) == today
    ).group_by(Appointment.status).all()
    
    # Médicos más activos (por citas este mes)
    top_doctors = db.session.query(
        User.first_name,
        User.last_name,
        func.count(Appointment.id).label('appointment_count')
    ).join(Appointment, User.id == Appointment.doctor_id)\
     .filter(
         Appointment.date_time >= start_of_month,
         User.role == 'doctor'
     ).group_by(User.id, User.first_name, User.last_name)\
     .order_by(func.count(Appointment.id).desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         title='Dashboard Administrativo',
                         stats=stats,
                         today_appointments=today_appointments,
                         pending_appointments=pending_appointments,
                         completed_this_month=completed_this_month,
                         monthly_revenue=monthly_revenue,
                         recent_patients=recent_patients,
                         today_appointments_by_status=dict(today_appointments_by_status),
                         top_doctors=top_doctors)

@bp.route('/users')
@login_required
@require_role('admin')
def users():
    """Gestión de usuarios"""
    users = User.query.order_by(User.created_at.desc()).all()
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
    return render_template('admin/users.html', title='Gestión de Usuarios', users=users, specialties=specialties)

@bp.route('/users/add', methods=['POST'])
@login_required
@require_role('admin')
def add_user():
    """Agregar nuevo usuario"""
    try:
        # Obtener datos del formulario
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', '').strip()
        password = request.form.get('password', '').strip()
        specialty_id = request.form.get('specialty_id')
        
        # Validaciones básicas de campos requeridos
        if not all([username, email, first_name, last_name, role, password]):
            flash('Todos los campos obligatorios deben ser completados.', 'error')
            return redirect(url_for('admin.users'))
        
        # Validaciones de formato y longitud
        import re
        
        # Validar username
        if not re.match(r'^[a-zA-Z0-9._-]+$', username) or len(username) < 3 or len(username) > 50:
            flash('El nombre de usuario debe tener entre 3-50 caracteres y solo puede contener letras, números, puntos, guiones y guiones bajos.', 'error')
            return redirect(url_for('admin.users'))
        
        # Validar email
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email) or len(email) > 100:
            flash('Por favor ingrese un email válido (máximo 100 caracteres).', 'error')
            return redirect(url_for('admin.users'))
        
        # Validar nombres
        name_regex = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'
        if not re.match(name_regex, first_name) or len(first_name) < 2 or len(first_name) > 50:
            flash('El nombre debe tener entre 2-50 caracteres y solo puede contener letras y espacios.', 'error')
            return redirect(url_for('admin.users'))
            
        if not re.match(name_regex, last_name) or len(last_name) < 2 or len(last_name) > 50:
            flash('El apellido debe tener entre 2-50 caracteres y solo puede contener letras y espacios.', 'error')
            return redirect(url_for('admin.users'))
        
        # Validar teléfono (opcional)
        if phone and (not re.match(r'^[0-9]{9}$', phone)):
            flash('El teléfono debe tener exactamente 9 dígitos (solo números).', 'error')
            return redirect(url_for('admin.users'))
        
        # Validar contraseña
        if len(password) < 6 or len(password) > 100:
            flash('La contraseña debe tener entre 6-100 caracteres.', 'error')
            return redirect(url_for('admin.users'))
        
        # Validar rol
        valid_roles = ['admin', 'doctor', 'receptionist', 'nurse']
        if role not in valid_roles:
            flash('Rol inválido seleccionado.', 'error')
            return redirect(url_for('admin.users'))
        
        # Validar especialidad para médicos
        if role == 'doctor':
            if not specialty_id:
                flash('Los médicos deben tener una especialidad asignada.', 'error')
                return redirect(url_for('admin.users'))
            
            try:
                specialty_id = int(specialty_id)
            except (ValueError, TypeError):
                flash('Especialidad inválida seleccionada.', 'error')
                return redirect(url_for('admin.users'))
            
            # Verificar que la especialidad existe y está activa
            specialty = Specialty.query.filter_by(id=specialty_id, is_active=True).first()
            if not specialty:
                flash('Especialidad inválida o inactiva seleccionada.', 'error')
                return redirect(url_for('admin.users'))
        else:
            specialty_id = None  # No médicos no tienen especialidad
        
        # Verificar que el username no exista (case insensitive)
        if User.query.filter(func.lower(User.username) == username.lower()).first():
            flash('El nombre de usuario ya existe. Por favor, elija otro.', 'error')
            return redirect(url_for('admin.users'))
        
        # Verificar que el email no exista (case insensitive)
        if User.query.filter(func.lower(User.email) == email.lower()).first():
            flash('El email ya está registrado. Por favor, use otro email.', 'error')
            return redirect(url_for('admin.users'))
        
        # Crear nuevo usuario
        new_user = User(
            username=username,
            email=email,
            first_name=first_name.title(),  # Capitalizar primera letra
            last_name=last_name.title(),    # Capitalizar primera letra
            phone=phone if phone else None,
            role=role,
            specialty_id=specialty_id,
            is_active=True
        )
        
        # Establecer contraseña (se hashea automáticamente en el modelo)
        new_user.set_password(password)
        
        # Guardar en la base de datos
        db.session.add(new_user)
        db.session.commit()
        
        # Mensaje de éxito con especialidad si aplica
        if role == 'doctor' and specialty_id:
            specialty_name = db.session.get(Specialty, specialty_id).name
            flash(f'Médico {username} creado exitosamente con especialidad en {specialty_name}.', 'success')
        else:
            role_names = {
                'admin': 'Administrador',
                'doctor': 'Médico',
                'receptionist': 'Recepcionista',
                'nurse': 'Enfermera'
            }
            flash(f'Usuario {username} creado exitosamente con rol de {role_names.get(role, role)}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear el usuario: {str(e)}', 'error')
    
    return redirect(url_for('admin.users'))

@bp.route('/reports')
@login_required
@require_role('admin')
def reports():
    """Reportes administrativos"""
    # Obtener fechas para filtros (últimos 30 días por defecto)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    # Parámetros de consulta
    period = request.args.get('period', '30')
    start_date_param = request.args.get('start_date')
    end_date_param = request.args.get('end_date')
    
    if start_date_param:
        start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
    if end_date_param:
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
    elif period:
        days = int(period)
        start_date = end_date - timedelta(days=days-1)
    
    # Estadísticas generales
    stats = get_general_statistics(start_date, end_date)
    
    # Estadísticas por especialidad
    specialty_stats = get_specialty_statistics(start_date, end_date)
    
    # Estadísticas mensuales para gráficos
    monthly_stats = get_monthly_statistics()
    
    # Estadísticas de doctores
    doctor_stats = get_doctor_statistics(start_date, end_date)
    
    return render_template('admin/reports.html', 
                         title='Reportes Administrativos',
                         stats=stats,
                         specialty_stats=specialty_stats,
                         monthly_stats=monthly_stats,
                         doctor_stats=doctor_stats,
                         start_date=start_date,
                         end_date=end_date,
                         period=period)

@bp.route('/patients')
@login_required
@require_role('admin')
def patients():
    """Vista de todos los pacientes para administrador"""
    # Obtener parámetros de búsqueda
    search = request.args.get('search', '')
    gender = request.args.get('gender', '')
    status = request.args.get('status', '')
    
    print(f"DEBUG - Parámetros recibidos - search: '{search}', gender: '{gender}', status: '{status}'")
    
    # Construir query base
    query = Patient.query
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.dni.ilike(search_term),
                Patient.email.ilike(search_term)
            )
        )
    
    # Aplicar filtro de género si se especifica
    if gender:
        print(f"DEBUG - Aplicando filtro de género: '{gender}'")
        # Convertir el valor del formulario al formato de la base de datos
        # Comparación insensible a mayúsculas/minúsculas y espacios
        normalized_gender = gender.strip().lower()
        query = query.filter(func.lower(func.trim(Patient.gender)) == normalized_gender)
    
    # Ejecutar query con ordenamiento
    patients = query.order_by(Patient.created_at.desc()).all()
    
    print(f"DEBUG - Número de pacientes encontrados: {len(patients)}")
    if patients:
        print(f"DEBUG - Primer paciente: {patients[0].first_name} {patients[0].last_name} (Género: {patients[0].gender})")
    
    return render_template('admin/patients.html', 
                         title='Todos los Pacientes', 
                         patients=patients,
                         selected_gender=gender)

@bp.route('/patients/<int:id>')
@login_required
@require_role('admin')
def patient_detail(id):
    """Ver detalles de un paciente específico"""
    patient = Patient.query.get_or_404(id)
    # Obtener citas del paciente
    appointments = Appointment.query.filter_by(patient_id=id).order_by(Appointment.date_time.desc()).all()
    # Obtener historial médico
    medical_records = MedicalRecord.query.filter_by(patient_id=id).order_by(MedicalRecord.created_at.desc()).all()
    
    return render_template('admin/patient_detail.html', 
                         title=f'Paciente: {patient.first_name} {patient.last_name}',
                         patient=patient,
                         appointments=appointments,
                         medical_records=medical_records)
    # Obtener citas del paciente
    appointments = Appointment.query.filter_by(patient_id=id).order_by(Appointment.date_time.desc()).all()
    # Obtener historial médico
    medical_records = MedicalRecord.query.filter_by(patient_id=id).order_by(MedicalRecord.created_at.desc()).all()
    
    return render_template('admin/patient_detail.html', 
                         title=f'Paciente: {patient.first_name} {patient.last_name}',
                         patient=patient,
                         appointments=appointments,
                         medical_records=medical_records)

@bp.route('/patients/new', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def new_patient():
    """Crear nuevo paciente (redirige a recepcionista)"""
    # El admin puede crear pacientes, pero usamos la funcionalidad del recepcionista
    return redirect(url_for('receptionist.new_patient'))

@bp.route('/patients/<int:id>/edit')
@login_required
@require_role('admin')
def edit_patient(id):
    """Editar paciente (redirige a recepcionista)"""
    # El admin puede editar pacientes, pero usamos la funcionalidad del recepcionista
    return redirect(url_for('receptionist.edit_patient', patient_id=id))

@bp.route('/patients/<int:id>/delete', methods=['POST', 'GET'])
@login_required
@require_role('admin')
def delete_patient(id):
    """Eliminar paciente (solo admin)"""
    patient = Patient.query.get_or_404(id)
    
    try:
        # Eliminar registros relacionados primero
        MedicalRecord.query.filter_by(patient_id=id).delete()
        Appointment.query.filter_by(patient_id=id).delete()
        
        # Eliminar el paciente
        db.session.delete(patient)
        db.session.commit()
        
        flash(f'Paciente {patient.first_name} {patient.last_name} eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar paciente: {str(e)}', 'error')
    
    return redirect(url_for('admin.patients'))


def get_general_statistics(start_date, end_date):
    """Obtener estadísticas generales del sistema"""
    stats = {}
    
    # Total de pacientes
    stats['total_patients'] = Patient.query.count()
    
    # Pacientes activos
    stats['active_patients'] = Patient.query.filter_by(is_active=True).count()
    
    # Total de doctores
    stats['total_doctors'] = User.query.filter_by(role='doctor').count()
    
    # Citas en el período
    appointments_query = Appointment.query.filter(
        func.date(Appointment.date_time).between(start_date, end_date)
    )
    stats['total_appointments'] = appointments_query.count()
    
    # Citas por estado
    stats['scheduled_appointments'] = appointments_query.filter_by(status='scheduled').count()
    stats['completed_appointments'] = appointments_query.filter_by(status='completed').count()
    stats['cancelled_appointments'] = appointments_query.filter_by(status='cancelled').count()
    stats['no_show_appointments'] = appointments_query.filter_by(status='no_show').count()
    
    # Registros médicos en el período
    stats['medical_records'] = MedicalRecord.query.filter(
        func.date(MedicalRecord.created_at).between(start_date, end_date)
    ).count()
    
    # Nuevos pacientes en el período
    stats['new_patients'] = Patient.query.filter(
        func.date(Patient.created_at).between(start_date, end_date)
    ).count()
    
    # Tasas de ocupación y cancelación
    if stats['total_appointments'] > 0:
        stats['completion_rate'] = round((stats['completed_appointments'] / stats['total_appointments']) * 100, 1)
        stats['cancellation_rate'] = round((stats['cancelled_appointments'] / stats['total_appointments']) * 100, 1)
        stats['no_show_rate'] = round((stats['no_show_appointments'] / stats['total_appointments']) * 100, 1)
    else:
        stats['completion_rate'] = 0
        stats['cancellation_rate'] = 0
        stats['no_show_rate'] = 0
    
    return stats


def get_specialty_statistics(start_date, end_date):
    """Obtener estadísticas por especialidad"""
    specialty_stats = []
    
    specialties = db.session.query(
        Specialty.name,
        func.count(Appointment.id).label('total_appointments'),
        func.count(func.nullif(Appointment.status == 'completed', False)).label('completed'),
        func.count(func.nullif(Appointment.status == 'cancelled', False)).label('cancelled')
    ).join(
        Appointment, Specialty.id == Appointment.specialty_id
    ).filter(
        func.date(Appointment.date_time).between(start_date, end_date)
    ).group_by(
        Specialty.id, Specialty.name
    ).all()
    
    for specialty in specialties:
        specialty_data = {
            'name': specialty.name,
            'total_appointments': specialty.total_appointments,
            'completed': specialty.completed or 0,
            'cancelled': specialty.cancelled or 0,
            'completion_rate': round((specialty.completed or 0) / specialty.total_appointments * 100, 1) if specialty.total_appointments > 0 else 0
        }
        specialty_stats.append(specialty_data)
    
    return sorted(specialty_stats, key=lambda x: x['total_appointments'], reverse=True)


def get_monthly_statistics():
    """Obtener estadísticas mensuales para gráficos (últimos 12 meses)"""
    monthly_stats = []
    
    # Obtener los últimos 12 meses
    current_date = date.today()
    for i in range(11, -1, -1):
        month_date = current_date.replace(day=1) - timedelta(days=i*30)
        year = month_date.year
        month = month_date.month
        
        # Citas del mes
        appointments = Appointment.query.filter(
            extract('year', Appointment.date_time) == year,
            extract('month', Appointment.date_time) == month
        ).count()
        
        # Nuevos pacientes del mes
        new_patients = Patient.query.filter(
            extract('year', Patient.created_at) == year,
            extract('month', Patient.created_at) == month
        ).count()
        
        # Registros médicos del mes
        medical_records = MedicalRecord.query.filter(
            extract('year', MedicalRecord.created_at) == year,
            extract('month', MedicalRecord.created_at) == month
        ).count()
        
        monthly_stats.append({
            'month': f"{year}-{month:02d}",
            'month_name': month_date.strftime('%B %Y'),
            'appointments': appointments,
            'new_patients': new_patients,
            'medical_records': medical_records
        })
    
    return monthly_stats


def get_doctor_statistics(start_date, end_date):
    """Obtener estadísticas por doctor"""
    doctor_stats = []
    
    doctors = db.session.query(
        User.id,
        User.first_name,
        User.last_name,
        User.email,
        Specialty.name.label('specialty_name'),
        func.count(Appointment.id).label('total_appointments'),
        func.count(func.nullif(Appointment.status == 'completed', False)).label('completed'),
        func.count(func.nullif(Appointment.status == 'cancelled', False)).label('cancelled'),
        func.count(distinct(Appointment.patient_id)).label('unique_patients')
    ).join(
        Specialty, User.specialty_id == Specialty.id
    ).outerjoin(
        Appointment, User.id == Appointment.doctor_id
    ).filter(
        User.role == 'doctor',
        db.or_(
            Appointment.id.is_(None),
            func.date(Appointment.date_time).between(start_date, end_date)
        )
    ).group_by(
        User.id, User.first_name, User.last_name, User.email, Specialty.name
    ).all()
    
    for doctor in doctors:
        doctor_data = {
            'id': doctor.id,
            'name': f"{doctor.first_name} {doctor.last_name}",
            'email': doctor.email,
            'specialty': doctor.specialty_name,
            'total_appointments': doctor.total_appointments,
            'completed': doctor.completed or 0,
            'cancelled': doctor.cancelled or 0,
            'unique_patients': doctor.unique_patients or 0,
            'completion_rate': round((doctor.completed or 0) / doctor.total_appointments * 100, 1) if doctor.total_appointments > 0 else 0
        }
        doctor_stats.append(doctor_data)
    
    return sorted(doctor_stats, key=lambda x: x['total_appointments'], reverse=True)


# API endpoints para datos en tiempo real
@bp.route('/api/reports/general')
@login_required
@require_role('admin')
def api_general_stats():
    """API para estadísticas generales"""
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    stats = get_general_statistics(start_date, end_date)
    return jsonify(stats)


@bp.route('/api/reports/export/<format>')
@login_required
@require_role('admin')
def export_reports(format):
    """Exportar reportes en diferentes formatos"""
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if format == 'csv':
        return export_csv_report(start_date, end_date)
    elif format == 'json':
        return export_json_report(start_date, end_date)
    elif format == 'pdf':
        from app.routes.admin_pdf_utils import render_report_pdf
        # Reutilizar la lógica de obtención de datos del reporte
        stats = get_general_statistics(start_date, end_date)
        specialty_stats = get_specialty_statistics(start_date, end_date)
        monthly_stats = get_monthly_statistics()
        doctor_stats = get_doctor_statistics(start_date, end_date)
        pdf_file = render_report_pdf(stats, specialty_stats, monthly_stats, doctor_stats, start_date, end_date, request.args.get('period', '30'))
        from flask import send_file
        return send_file(pdf_file, mimetype='application/pdf', as_attachment=True, download_name='reporte_admin.pdf')
    else:
        flash('Formato de exportación no válido', 'error')
        return redirect(url_for('admin.reports'))


def export_csv_report(start_date, end_date):
    """Exportar reporte en formato CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escribir encabezados
    writer.writerow(['Fecha de Reporte', f'{start_date} a {end_date}'])
    writer.writerow([])
    
    # Estadísticas generales
    stats = get_general_statistics(start_date, end_date)
    writer.writerow(['Estadísticas Generales'])
    writer.writerow(['Métrica', 'Valor'])
    writer.writerow(['Total de Pacientes', stats['total_patients']])
    writer.writerow(['Pacientes Activos', stats['active_patients']])
    writer.writerow(['Total de Doctores', stats['total_doctors']])
    writer.writerow(['Total de Citas', stats['total_appointments']])
    writer.writerow(['Citas Completadas', stats['completed_appointments']])
    writer.writerow(['Citas Canceladas', stats['cancelled_appointments']])
    writer.writerow(['Tasa de Completado (%)', stats['completion_rate']])
    writer.writerow(['Tasa de Cancelación (%)', stats['cancellation_rate']])
    writer.writerow([])
    
    # Estadísticas por especialidad
    specialty_stats = get_specialty_statistics(start_date, end_date)
    writer.writerow(['Estadísticas por Especialidad'])
    writer.writerow(['Especialidad', 'Total Citas', 'Completadas', 'Canceladas', 'Tasa Completado (%)'])
    for specialty in specialty_stats:
        writer.writerow([
            specialty['name'],
            specialty['total_appointments'],
            specialty['completed'],
            specialty['cancelled'],
            specialty['completion_rate']
        ])
    
    # Preparar respuesta
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=reporte_{start_date}_{end_date}.csv'
    
    return response


def export_json_report(start_date, end_date):
    """Exportar reporte en formato JSON"""
    report_data = {
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'general_statistics': get_general_statistics(start_date, end_date),
        'specialty_statistics': get_specialty_statistics(start_date, end_date),
        'doctor_statistics': get_doctor_statistics(start_date, end_date),
        'monthly_statistics': get_monthly_statistics(),
        'generated_at': datetime.now().isoformat()
    }
    
    response = make_response(json.dumps(report_data, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=reporte_{start_date}_{end_date}.json'
    
    return response

# =============================================================================
# GESTIÓN DE ESPECIALIDADES MÉDICAS
# =============================================================================

@bp.route('/specialties')
@login_required
@require_role('admin')
def specialties():
    """Gestión de especialidades médicas"""
    # Obtener parámetros de búsqueda
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    # Construir query base
    query = Specialty.query
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Specialty.name.ilike(search_term),
                Specialty.description.ilike(search_term)
            )
        )
    
    if status:
        is_active = status == 'active'
        query = query.filter(Specialty.is_active == is_active)
    
    # Obtener especialidades ordenadas
    specialties = query.order_by(Specialty.name).all()
    
    return render_template('admin/specialties.html', 
                         title='Gestión de Especialidades Médicas',
                         specialties=specialties,
                         search=search,
                         selected_status=status)


@bp.route('/specialties/add', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def add_specialty():
    """Agregar nueva especialidad médica"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            consultation_duration = int(request.form.get('consultation_duration', 30))
            base_price = float(request.form.get('base_price', 0))
            is_active = request.form.get('is_active') == '1'  # Checkbox: presente = True, ausente = False
            
            # Validaciones
            if not name or base_price <= 0:
                flash('Complete todos los campos obligatorios correctamente.', 'error')
                return redirect(url_for('admin.add_specialty'))
            
            # Verificar que el nombre no exista
            existing_specialty = Specialty.query.filter_by(name=name).first()
            if existing_specialty:
                flash(f'Ya existe una especialidad con el nombre "{name}".', 'error')
                return redirect(url_for('admin.add_specialty'))
            
            # Crear nueva especialidad
            specialty = Specialty(
                name=name,
                description=description,
                consultation_duration=consultation_duration,
                base_price=base_price,
                is_active=is_active
            )
            
            db.session.add(specialty)
            db.session.commit()
            
            flash(f'Especialidad "{name}" creada exitosamente.', 'success')
            return redirect(url_for('admin.specialties'))
            
        except ValueError as e:
            flash('Error en los datos ingresados. Verifique los valores numéricos.', 'error')
            return redirect(url_for('admin.add_specialty'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear especialidad: {str(e)}', 'error')
            return redirect(url_for('admin.add_specialty'))
    
    # GET request - mostrar formulario
    return render_template('admin/specialty_form.html',
                         title='Nueva Especialidad Médica',
                         specialty=None)


@bp.route('/specialties/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def edit_specialty(id):
    """Editar especialidad médica"""
    specialty = Specialty.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            consultation_duration = int(request.form.get('consultation_duration', 30))
            base_price = float(request.form.get('base_price', 0))
            is_active = request.form.get('is_active') == '1'  # Checkbox: presente = True, ausente = False
            
            # Validaciones
            if not name or base_price <= 0:
                flash('Complete todos los campos obligatorios correctamente.', 'error')
                return redirect(url_for('admin.edit_specialty', id=id))
            
            # Verificar que el nombre no exista en otra especialidad
            existing_specialty = Specialty.query.filter(
                Specialty.name == name,
                Specialty.id != id
            ).first()
            if existing_specialty:
                flash(f'Ya existe otra especialidad con el nombre "{name}".', 'error')
                return redirect(url_for('admin.edit_specialty', id=id))
            
            # Actualizar especialidad
            specialty.name = name
            specialty.description = description
            specialty.consultation_duration = consultation_duration
            specialty.base_price = base_price
            specialty.is_active = is_active
            
            db.session.commit()
            
            flash(f'Especialidad "{name}" actualizada exitosamente.', 'success')
            return redirect(url_for('admin.specialties'))
            
        except ValueError as e:
            flash('Error en los datos ingresados. Verifique los valores numéricos.', 'error')
            return redirect(url_for('admin.edit_specialty', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar especialidad: {str(e)}', 'error')
            return redirect(url_for('admin.edit_specialty', id=id))
    
    # GET request - mostrar formulario
    return render_template('admin/specialty_form.html',
                         title='Editar Especialidad Médica',
                         specialty=specialty)


@bp.route('/specialties/<int:id>/toggle', methods=['POST'])
@login_required
@require_role('admin')
def toggle_specialty_status(id):
    """Activar/desactivar especialidad médica"""
    specialty = Specialty.query.get_or_404(id)
    
    try:
        specialty.is_active = not specialty.is_active
        db.session.commit()
        
        status = "activada" if specialty.is_active else "desactivada"
        flash(f'Especialidad "{specialty.name}" {status} exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado de la especialidad: {str(e)}', 'error')
    
    return redirect(url_for('admin.specialties'))


@bp.route('/specialties/<int:id>/delete', methods=['POST'])
@login_required
@require_role('admin')
def delete_specialty(id):
    """Eliminar especialidad médica"""
    specialty = Specialty.query.get_or_404(id)
    
    try:
        # Verificar si la especialidad está siendo usada
        appointments_count = Appointment.query.filter_by(specialty_id=id).count()
        users_count = User.query.filter_by(specialty_id=id).count()
        
        if appointments_count > 0 or users_count > 0:
            # No eliminar, solo desactivar
            specialty.is_active = False
            db.session.commit()
            flash(f'Especialidad "{specialty.name}" desactivada (estaba en uso).', 'info')
        else:
            # Eliminar completamente
            specialty_name = specialty.name
            db.session.delete(specialty)
            db.session.commit()
            flash(f'Especialidad "{specialty_name}" eliminada exitosamente.', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar especialidad: {str(e)}', 'error')
    
    return redirect(url_for('admin.specialties'))

# ===============================================
# GESTIÓN DE COMISIONES Y SALARIOS
# ===============================================

@bp.route('/salary-management')
@login_required
@require_role('admin')
def salary_management():
    """Gestión de configuración de salarios por doctor"""
    # Obtener todos los doctores
    doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).all()
    
    # Obtener configuraciones existentes
    configurations = {}
    existing_configs = SalaryConfiguration.query.filter_by(is_active=True).all()
    
    for config in existing_configs:
        configurations[config.doctor_id] = config
    
    return render_template('admin/salary_management.html',
                         title='Gestión de Comisiones y Salarios',
                         doctors=doctors,
                         configurations=configurations)


@bp.route('/salary-management/configure/<int:doctor_id>', methods=['POST'])
@login_required
@require_role('admin')
def configure_doctor_salary(doctor_id):
    """Configurar porcentaje de comisión para un doctor"""
    try:
        doctor = User.query.filter_by(id=doctor_id, role='doctor', is_active=True).first_or_404()
        
        # Obtener datos del formulario
        commission_percentage = float(request.form.get('commission_percentage', 0))
        
        # Validaciones
        if commission_percentage < 0 or commission_percentage > 100:
            flash('El porcentaje debe estar entre 0% y 100%.', 'error')
            return redirect(url_for('admin.salary_management'))
        
        # Buscar configuración existente
        existing_config = SalaryConfiguration.query.filter_by(doctor_id=doctor_id).first()
        
        if existing_config:
            # Actualizar configuración existente
            existing_config.commission_percentage = commission_percentage
            existing_config.is_active = True
            existing_config.updated_at = datetime.utcnow()
        else:
            # Crear nueva configuración
            new_config = SalaryConfiguration(
                doctor_id=doctor_id,
                commission_percentage=commission_percentage,
                is_active=True
            )
            db.session.add(new_config)
        
        db.session.commit()
        
        flash(f'Comisión configurada para Dr. {doctor.full_name}: {commission_percentage}%', 'success')
        
    except ValueError:
        flash('Error: Ingrese un porcentaje válido.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al configurar comisión: {str(e)}', 'error')
    
    return redirect(url_for('admin.salary_management'))


@bp.route('/commission-reports')
@login_required
@require_role('admin')
def commission_reports():
    """Reportes de comisiones generadas"""
    # Obtener parámetros de filtro
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    doctor_id = request.args.get('doctor_id', '')
    
    # Construir query base
    query = CommissionRecord.query
    
    # Aplicar filtros
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(CommissionRecord.generated_date >= start_date_obj)
        except ValueError:
            start_date = ''
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(CommissionRecord.generated_date <= end_date_obj)
        except ValueError:
            end_date = ''
    
    if doctor_id:
        query = query.filter(CommissionRecord.doctor_id == doctor_id)
    
    # Obtener registros ordenados por fecha
    commission_records = query.order_by(CommissionRecord.generated_date.desc()).all()
    
    # Calcular totales
    total_commissions = sum(record.commission_amount for record in commission_records)
    
    # Obtener lista de doctores para filtro
    doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).all()
    
    return render_template('admin/commission_reports.html',
                         title='Reportes de Comisiones',
                         commission_records=commission_records,
                         total_commissions=total_commissions,
                         doctors=doctors,
                         start_date=start_date,
                         end_date=end_date,
                         selected_doctor_id=doctor_id)


@bp.route('/api/commissions/summary')
@login_required
@require_role('admin')
def commissions_summary_api():
    """API para obtener resumen de comisiones"""
    try:
        # Obtener comisiones por doctor en el último mes
        one_month_ago = datetime.utcnow().date() - timedelta(days=30)
        
        summary = db.session.query(
            User.id,
            User.first_name,
            User.last_name,
            func.sum(CommissionRecord.commission_amount).label('total_commissions'),
            func.count(CommissionRecord.id).label('total_records')
        ).join(
            CommissionRecord, User.id == CommissionRecord.doctor_id
        ).filter(
            CommissionRecord.generated_date >= one_month_ago
        ).group_by(
            User.id, User.first_name, User.last_name
        ).all()
        
        result = []
        for doctor in summary:
            result.append({
                'doctor_id': doctor.id,
                'doctor_name': f"{doctor.first_name} {doctor.last_name}",
                'total_commissions': float(doctor.total_commissions or 0),
                'total_records': doctor.total_records or 0
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'period': '30 days'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===============================================
# GESTIÓN DE HORARIOS DE TRABAJO
# ===============================================

@bp.route('/work-schedules')
@login_required
@require_role('admin')
def work_schedules():
    """Gestión de horarios de trabajo por doctor"""
    # Obtener todos los doctores activos
    doctors = User.query.filter_by(role='doctor', is_active=True).order_by(User.first_name, User.last_name).all()
    
    # Obtener horarios existentes agrupados por doctor
    doctor_schedules = {}
    total_schedules = 0
    doctors_without_schedule = 0
    
    for doctor in doctors:
        schedules = WorkSchedule.query.filter_by(doctor_id=doctor.id, is_active=True).order_by(WorkSchedule.day_of_week).all()
        doctor_schedules[doctor.id] = schedules
        
        # Contar horarios totales
        total_schedules += len(schedules)
        
        # Contar doctores sin horarios
        if len(schedules) == 0:
            doctors_without_schedule += 1
    
    # Obtener especialidades activas
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
    
    # Preparar métricas
    metrics = {
        'total_doctors': len(doctors),
        'total_schedules': total_schedules,
        'doctors_without_schedule': doctors_without_schedule,
        'total_specialties': len(specialties)
    }
    
    return render_template('admin/work_schedules.html',
                         title='Gestión de Horarios de Trabajo',
                         doctors=doctors,
                         doctor_schedules=doctor_schedules,
                         specialties=specialties,
                         metrics=metrics)


@bp.route('/work-schedules/doctor/<int:doctor_id>')
@login_required
@require_role('admin')
def doctor_schedule_detail(doctor_id):
    """Detalle de horarios de un doctor específico"""
    doctor = User.query.filter_by(id=doctor_id, role='doctor', is_active=True).first_or_404()
    
    # Obtener horarios por día de la semana
    schedules_by_day = {}
    for day in range(7):  # 0=Lunes, 6=Domingo
        schedules = WorkSchedule.query.filter_by(
            doctor_id=doctor_id, 
            day_of_week=day, 
            is_active=True
        ).all()
        schedules_by_day[day] = schedules
    
    # Obtener especialidades del doctor
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
    
    return render_template('admin/doctor_schedule_detail.html',
                         title=f'Horarios - Dr. {doctor.full_name}',
                         doctor=doctor,
                         schedules_by_day=schedules_by_day,
                         specialties=specialties,
                         days=['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'])


@bp.route('/work-schedules/create/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def create_work_schedule(doctor_id):
    """Crear nuevo horario de trabajo"""
    doctor = User.query.filter_by(id=doctor_id, role='doctor', is_active=True).first_or_404()
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            day_of_week = int(request.form.get('day_of_week'))
            specialty_id = doctor.specialty_id if doctor.specialty else None  # Usar la especialidad del doctor
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date') or None
            appointment_duration = int(request.form.get('appointment_duration', 30))
            break_start_time = request.form.get('break_start_time') or None
            break_end_time = request.form.get('break_end_time') or None
            max_patients_per_day = request.form.get('max_patients_per_day') or None
            
            # Validaciones
            if day_of_week < 0 or day_of_week > 6:
                flash('Día de la semana inválido.', 'error')
                return redirect(url_for('admin.doctor_schedule_detail', doctor_id=doctor_id))
            
            # Convertir fechas
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = None
                if end_date:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                    if start_date_obj > end_date_obj:
                        flash('La fecha de inicio debe ser anterior a la fecha de fin.', 'error')
                        return redirect(url_for('admin.doctor_schedule_detail', doctor_id=doctor_id))
            except ValueError:
                flash('Formato de fecha inválido. Use YYYY-MM-DD', 'error')
                return redirect(url_for('admin.doctor_schedule_detail', doctor_id=doctor_id))
            
            # Convertir horarios
            try:
                start_time_obj = datetime.strptime(start_time, '%H:%M').time()
                end_time_obj = datetime.strptime(end_time, '%H:%M').time()
                
                if start_time_obj >= end_time_obj:
                    flash('La hora de inicio debe ser anterior a la hora de fin.', 'error')
                    return redirect(url_for('admin.doctor_schedule_detail', doctor_id=doctor_id))
                
                break_start_obj = None
                break_end_obj = None
                if break_start_time and break_end_time:
                    break_start_obj = datetime.strptime(break_start_time, '%H:%M').time()
                    break_end_obj = datetime.strptime(break_end_time, '%H:%M').time()
                    
                    if break_start_obj >= break_end_obj:
                        flash('La hora de inicio del descanso debe ser anterior a la hora de fin.', 'error')
                        return redirect(url_for('admin.doctor_schedule_detail', doctor_id=doctor_id))
                        
            except ValueError:
                flash('Formato de hora inválido. Use HH:MM', 'error')
                return redirect(url_for('admin.doctor_schedule_detail', doctor_id=doctor_id))
            
            # Verificar conflictos existentes
            existing_schedule = WorkSchedule.query.filter_by(
                doctor_id=doctor_id,
                day_of_week=day_of_week,
                is_active=True
            ).first()
            
            if existing_schedule:
                flash('Ya existe un horario para este doctor en este día.', 'error')
                return redirect(url_for('admin.doctor_schedule_detail', doctor_id=doctor_id))
            
            # Crear nuevo horario
            new_schedule = WorkSchedule(
                doctor_id=doctor_id,
                specialty_id=specialty_id,  # Usar la especialidad del doctor
                day_of_week=day_of_week,
                start_time=start_time_obj,
                end_time=end_time_obj,
                start_date=start_date_obj,
                end_date=end_date_obj,
                appointment_duration=appointment_duration,
                break_start_time=break_start_obj,
                break_end_time=break_end_obj,
                max_patients_per_day=int(max_patients_per_day) if max_patients_per_day else None,
                is_active=True
            )
            
            db.session.add(new_schedule)
            db.session.commit()
            
            flash(f'Horario creado exitosamente para Dr. {doctor.full_name}', 'success')
            return redirect(url_for('admin.doctor_schedule_detail', doctor_id=doctor_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear horario: {str(e)}', 'error')
            return redirect(url_for('admin.doctor_schedule_detail', doctor_id=doctor_id))
    
    # GET - Mostrar formulario
    days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    return render_template('admin/work_schedule_form.html',
                         title=f'Nuevo Horario - Dr. {doctor.full_name}',
                         doctor=doctor,
                         days=days,
                         schedule=None)


@bp.route('/work-schedules/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def edit_work_schedule(schedule_id):
    """Editar horario de trabajo existente"""
    schedule = WorkSchedule.query.get_or_404(schedule_id)
    doctor = schedule.doctor
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario (similar a create)
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date') or None
            appointment_duration = int(request.form.get('appointment_duration', 30))
            break_start_time = request.form.get('break_start_time') or None
            break_end_time = request.form.get('break_end_time') or None
            max_patients_per_day = request.form.get('max_patients_per_day') or None
            
            # Convertir horarios y validar (mismo código que create)
            try:
                start_time_obj = datetime.strptime(start_time, '%H:%M').time()
                end_time_obj = datetime.strptime(end_time, '%H:%M').time()
                
                if start_time_obj >= end_time_obj:
                    flash('La hora de inicio debe ser anterior a la hora de fin.', 'error')
                    return redirect(url_for('admin.edit_work_schedule', schedule_id=schedule_id))
                
                break_start_obj = None
                break_end_obj = None
                if break_start_time and break_end_time:
                    break_start_obj = datetime.strptime(break_start_time, '%H:%M').time()
                    break_end_obj = datetime.strptime(break_end_time, '%H:%M').time()
                    
                    if break_start_obj >= break_end_obj:
                        flash('La hora de inicio del descanso debe ser anterior a la hora de fin.', 'error')
                        return redirect(url_for('admin.edit_work_schedule', schedule_id=schedule_id))
                        
            except ValueError:
                flash('Formato de hora inválido. Use HH:MM', 'error')
                return redirect(url_for('admin.edit_work_schedule', schedule_id=schedule_id))
            
            # Convertir fechas
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = None
                if end_date:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                    if start_date_obj > end_date_obj:
                        flash('La fecha de inicio debe ser anterior a la fecha de fin.', 'error')
                        return redirect(url_for('admin.edit_work_schedule', schedule_id=schedule_id))
            except ValueError:
                flash('Formato de fecha inválido. Use YYYY-MM-DD', 'error')
                return redirect(url_for('admin.edit_work_schedule', schedule_id=schedule_id))
            
            # VERIFICAR SI LAS FECHAS DE VIGENCIA CAMBIARON ANTES DE ACTUALIZAR
            dates_changed = (schedule.start_date != start_date_obj or 
                           schedule.end_date != end_date_obj)
            
            # Actualizar horario
            schedule.start_time = start_time_obj
            schedule.end_time = end_time_obj
            schedule.start_date = start_date_obj
            schedule.end_date = end_date_obj
            schedule.appointment_duration = appointment_duration
            schedule.break_start_time = break_start_obj
            schedule.break_end_time = break_end_obj
            schedule.max_patients_per_day = int(max_patients_per_day) if max_patients_per_day else None
            schedule.updated_at = datetime.utcnow()
            
            # NUEVA FUNCIONALIDAD: Actualizar fechas de vigencia para todos los días del doctor
            # Solo si las fechas de vigencia han cambiado
            if dates_changed:
                
                # Obtener todos los horarios del mismo doctor
                doctor_schedules = WorkSchedule.query.filter_by(
                    doctor_id=doctor.id,
                    is_active=True
                ).all()
                
                # Contar cuántos horarios se actualizarán
                updated_count = 0
                
                for other_schedule in doctor_schedules:
                    if other_schedule.id != schedule.id:  # No actualizar el actual
                        other_schedule.start_date = start_date_obj
                        other_schedule.end_date = end_date_obj
                        other_schedule.updated_at = datetime.utcnow()
                        updated_count += 1
                
                db.session.commit()
                
                if updated_count > 0:
                    flash(f'Horario actualizado exitosamente. Las fechas de vigencia también se actualizaron para {updated_count} día(s) adicional(es) del doctor.', 'success')
                else:
                    flash(f'Horario actualizado exitosamente', 'success')
            else:
                db.session.commit()
                flash(f'Horario actualizado exitosamente', 'success')
            return redirect(url_for('admin.doctor_schedule_detail', doctor_id=doctor.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar horario: {str(e)}', 'error')
    
    # GET - Mostrar formulario
    days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    return render_template('admin/work_schedule_form.html',
                         title=f'Editar Horario - Dr. {doctor.full_name}',
                         doctor=doctor,
                         days=days,
                         schedule=schedule)


@bp.route('/work-schedules/<int:schedule_id>/toggle', methods=['POST'])
@login_required
@require_role('admin')
def toggle_work_schedule(schedule_id):
    """Activar/desactivar horario de trabajo"""
    try:
        schedule = WorkSchedule.query.get_or_404(schedule_id)
        schedule.is_active = not schedule.is_active
        schedule.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        status = "activado" if schedule.is_active else "desactivado"
        flash(f'Horario {status} exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado del horario: {str(e)}', 'error')
    
    return redirect(url_for('admin.doctor_schedule_detail', doctor_id=schedule.doctor_id))


@bp.route('/work-schedules/<int:schedule_id>/delete', methods=['POST'])
@login_required
@require_role('admin')
def delete_work_schedule(schedule_id):
    """Eliminar horario de trabajo"""
    try:
        schedule = WorkSchedule.query.get_or_404(schedule_id)
        doctor_id = schedule.doctor_id
        
        # Verificar si hay citas futuras asociadas a este horario
        from app.models.appointment import Appointment
        future_appointments = Appointment.query.filter(
            Appointment.doctor_id == schedule.doctor_id,
            Appointment.date_time > datetime.utcnow(),
            Appointment.status.in_(['scheduled', 'in_triage', 'ready_for_doctor'])
        ).count()
        
        if future_appointments > 0:
            flash('No se puede eliminar el horario porque hay citas futuras programadas.', 'error')
        else:
            db.session.delete(schedule)
            db.session.commit()
            flash('Horario eliminado exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar horario: {str(e)}', 'error')
    
    return redirect(url_for('admin.doctor_schedule_detail', doctor_id=doctor_id))


# API para obtener horarios disponibles en tiempo real
@bp.route('/api/work-schedules/available-times')
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
        
        # Obtener horarios disponibles
        available_times = WorkSchedule.get_available_times(
            int(doctor_id), 
            date_obj, 
            int(specialty_id) if specialty_id else None
        )
        
        # Formatear horarios para respuesta
        formatted_times = [time.strftime('%H:%M') for time in available_times]
        
        return jsonify({
            'success': True,
            'available_times': formatted_times,
            'date': date_str,
            'doctor_id': doctor_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
@require_role('admin')
def edit_user(user_id):
    """Editar usuario existente"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Obtener datos del formulario
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', '').strip()
        specialty_id = request.form.get('specialty_id')
        
        # Validaciones
        if not all([username, email, first_name, last_name, role]):
            flash('Todos los campos obligatorios deben estar completos', 'error')
            return redirect(url_for('admin.users'))
        
        # Verificar que el nombre de usuario no esté en uso por otro usuario
        existing_user = User.query.filter(User.username == username, User.id != user_id).first()
        if existing_user:
            flash('El nombre de usuario ya está en uso', 'error')
            return redirect(url_for('admin.users'))
        
        # Verificar que el email no esté en uso por otro usuario
        existing_email = User.query.filter(User.email == email, User.id != user_id).first()
        if existing_email:
            flash('El email ya está en uso', 'error')
            return redirect(url_for('admin.users'))
        
        # Actualizar datos del usuario
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone if phone else None
        user.role = role
        
        # Manejar especialidad para médicos
        if role == 'doctor' and specialty_id:
            specialty = Specialty.query.get(specialty_id)
            if specialty:
                user.specialty_id = specialty_id
            else:
                flash('Especialidad no válida', 'error')
                return redirect(url_for('admin.users'))
        else:
            user.specialty_id = None
        
        # Actualizar timestamp
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Usuario {username} actualizado exitosamente', 'success')
        return redirect(url_for('admin.users'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar el usuario: {str(e)}', 'error')
        return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@require_role('admin')
def toggle_user_status(user_id):
    """Activar/desactivar usuario"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Evitar desactivar al usuario actual
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'No puede desactivar su propio usuario'}), 400
        
        data = request.get_json()
        activate = data.get('activate', False)
        
        user.is_active = activate
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        action = 'activado' if activate else 'desactivado'
        return jsonify({
            'success': True, 
            'message': f'Usuario {user.username} {action} exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/users/<int:user_id>/delete', methods=['DELETE'])
@login_required
@require_role('admin')
def delete_user(user_id):
    """Eliminar usuario"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Evitar eliminar al usuario actual
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'No puede eliminar su propio usuario'}), 400
        
        # Verificar si el usuario tiene datos relacionados
        if user.role == 'doctor':
            appointments_count = Appointment.query.filter_by(doctor_id=user_id).count()
            records_count = MedicalRecord.query.filter_by(doctor_id=user_id).count()
            
            if appointments_count > 0 or records_count > 0:
                return jsonify({
                    'success': False, 
                    'message': f'No se puede eliminar el usuario porque tiene {appointments_count} citas y {records_count} registros médicos asociados'
                }), 400
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Usuario {username} eliminado exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
