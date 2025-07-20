from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from sqlalchemy import func, extract, distinct
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
from app import db

# Blueprint para administrador
bp = Blueprint('admin', __name__)

@bp.route('/dashboard')
@login_required
@require_role('admin')
def dashboard():
    """Dashboard del administrador"""
    return render_template('admin/dashboard.html', title='Dashboard Administrativo')

@bp.route('/users')
@login_required
@require_role('admin')
def users():
    """Gestión de usuarios"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', title='Gestión de Usuarios', users=users)

@bp.route('/users/add', methods=['POST'])
@login_required
@require_role('admin')
def add_user():
    """Agregar nuevo usuario"""
    try:
        # Obtener datos del formulario
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validaciones básicas
        if not all([username, email, first_name, last_name, role, password]):
            flash('Todos los campos obligatorios deben ser completados.', 'error')
            return redirect(url_for('admin.users'))
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return redirect(url_for('admin.users'))
        
        if role not in ['admin', 'doctor', 'receptionist']:
            flash('Rol inválido seleccionado.', 'error')
            return redirect(url_for('admin.users'))
        
        # Verificar que el username no exista
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe. Por favor, elija otro.', 'error')
            return redirect(url_for('admin.users'))
        
        # Verificar que el email no exista
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado. Por favor, use otro email.', 'error')
            return redirect(url_for('admin.users'))
        
        # Crear nuevo usuario
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone if phone else None,
            role=role,
            is_active=True
        )
        
        # Establecer contraseña (se hashea automáticamente en el modelo)
        new_user.set_password(password)
        
        # Guardar en la base de datos
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Usuario {username} creado exitosamente con rol de {role}.', 'success')
        
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
    
    if gender:
        query = query.filter(Patient.gender == gender)
    
    # Ejecutar query con ordenamiento
    patients = query.order_by(Patient.created_at.desc()).all()
    
    return render_template('admin/patients.html', title='Todos los Pacientes', patients=patients)

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
# GESTIÓN DE SERVICIOS MÉDICOS
# =============================================================================

@bp.route('/services')
@login_required
@require_role('admin')
def services():
    """Gestión de servicios médicos"""
    # Obtener parámetros de búsqueda
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    specialty_id = request.args.get('specialty_id', '')
    status = request.args.get('status', '')
    
    # Construir query base
    query = MedicalService.query
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                MedicalService.name.ilike(search_term),
                MedicalService.code.ilike(search_term),
                MedicalService.description.ilike(search_term)
            )
        )
    
    if category:
        query = query.filter(MedicalService.category == category)
    
    if specialty_id:
        query = query.filter(MedicalService.specialty_id == specialty_id)
    
    if status:
        is_active = status == 'active'
        query = query.filter(MedicalService.is_active == is_active)
    
    # Ejecutar query con joins
    services = query.options(
        joinedload(MedicalService.specialty),
        joinedload(MedicalService.created_by_user)
    ).order_by(MedicalService.category, MedicalService.name).all()
    
    # Obtener datos para filtros
    categories = db.session.query(MedicalService.category).distinct().filter(
        MedicalService.category.isnot(None)
    ).all()
    categories = [cat[0] for cat in categories]
    
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
    
    return render_template('admin/services.html', 
                         title='Gestión de Servicios Médicos',
                         services=services,
                         categories=categories,
                         specialties=specialties,
                         search=search,
                         selected_category=category,
                         selected_specialty=specialty_id,
                         selected_status=status)


@bp.route('/services/add', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def add_service():
    """Agregar nuevo servicio médico"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', '').strip()
            base_price = float(request.form.get('base_price', 0))
            min_price = request.form.get('min_price', '')
            max_price = request.form.get('max_price', '')
            specialty_id = request.form.get('specialty_id', '')
            duration_minutes = int(request.form.get('duration_minutes', 30))
            requires_preparation = bool(request.form.get('requires_preparation'))
            preparation_instructions = request.form.get('preparation_instructions', '').strip()
            is_active = bool(request.form.get('is_active', True))
            
            # Validaciones
            if not name or not code or not category or base_price <= 0:
                flash('Complete todos los campos obligatorios correctamente.', 'error')
                return redirect(url_for('admin.add_service'))
            
            # Verificar que el código no exista
            existing_service = MedicalService.query.filter_by(code=code).first()
            if existing_service:
                flash(f'Ya existe un servicio con el código {code}.', 'error')
                return redirect(url_for('admin.add_service'))
            
            # Crear nuevo servicio
            service = MedicalService(
                name=name,
                code=code,
                description=description,
                category=category,
                base_price=base_price,
                min_price=float(min_price) if min_price else None,
                max_price=float(max_price) if max_price else None,
                specialty_id=int(specialty_id) if specialty_id else None,
                duration_minutes=duration_minutes,
                requires_preparation=requires_preparation,
                preparation_instructions=preparation_instructions,
                is_active=is_active,
                created_by=current_user.id
            )
            
            db.session.add(service)
            db.session.commit()
            
            flash(f'Servicio médico "{name}" creado exitosamente.', 'success')
            return redirect(url_for('admin.services'))
            
        except ValueError as e:
            flash('Error en los datos ingresados. Verifique los valores numéricos.', 'error')
            return redirect(url_for('admin.add_service'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear servicio: {str(e)}', 'error')
            return redirect(url_for('admin.add_service'))
    
    # GET request - mostrar formulario
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
    next_code = MedicalService.get_next_code()
    
    # Categorías predefinidas
    default_categories = [
        'Consulta Médica',
        'Examen de Laboratorio',
        'Examen Radiológico',
        'Procedimiento Quirúrgico',
        'Procedimiento Diagnóstico',
        'Terapia',
        'Vacunación',
        'Emergencia',
        'Otros'
    ]
    
    return render_template('admin/service_form.html',
                         title='Nuevo Servicio Médico',
                         service=None,
                         specialties=specialties,
                         next_code=next_code,
                         default_categories=default_categories)


@bp.route('/services/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def edit_service(id):
    """Editar servicio médico"""
    service = MedicalService.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', '').strip()
            base_price = float(request.form.get('base_price', 0))
            min_price = request.form.get('min_price', '')
            max_price = request.form.get('max_price', '')
            specialty_id = request.form.get('specialty_id', '')
            duration_minutes = int(request.form.get('duration_minutes', 30))
            requires_preparation = bool(request.form.get('requires_preparation'))
            preparation_instructions = request.form.get('preparation_instructions', '').strip()
            is_active = bool(request.form.get('is_active', True))
            
            # Validaciones
            if not name or not code or not category or base_price <= 0:
                flash('Complete todos los campos obligatorios correctamente.', 'error')
                return redirect(url_for('admin.edit_service', id=id))
            
            # Verificar que el código no exista en otro servicio
            existing_service = MedicalService.query.filter(
                MedicalService.code == code,
                MedicalService.id != id
            ).first()
            if existing_service:
                flash(f'Ya existe otro servicio con el código {code}.', 'error')
                return redirect(url_for('admin.edit_service', id=id))
            
            # Actualizar servicio
            service.name = name
            service.code = code
            service.description = description
            service.category = category
            service.base_price = base_price
            service.min_price = float(min_price) if min_price else None
            service.max_price = float(max_price) if max_price else None
            service.specialty_id = int(specialty_id) if specialty_id else None
            service.duration_minutes = duration_minutes
            service.requires_preparation = requires_preparation
            service.preparation_instructions = preparation_instructions
            service.is_active = is_active
            service.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Servicio médico "{name}" actualizado exitosamente.', 'success')
            return redirect(url_for('admin.services'))
            
        except ValueError as e:
            flash('Error en los datos ingresados. Verifique los valores numéricos.', 'error')
            return redirect(url_for('admin.edit_service', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar servicio: {str(e)}', 'error')
            return redirect(url_for('admin.edit_service', id=id))
    
    # GET request - mostrar formulario
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
    
    # Categorías predefinidas
    default_categories = [
        'Consulta Médica',
        'Examen de Laboratorio',
        'Examen Radiológico',
        'Procedimiento Quirúrgico',
        'Procedimiento Diagnóstico',
        'Terapia',
        'Vacunación',
        'Emergencia',
        'Otros'
    ]
    
    return render_template('admin/service_form.html',
                         title='Editar Servicio Médico',
                         service=service,
                         specialties=specialties,
                         default_categories=default_categories)


@bp.route('/services/<int:id>/delete', methods=['POST'])
@login_required
@require_role('admin')
def delete_service(id):
    """Eliminar servicio médico"""
    service = MedicalService.query.get_or_404(id)
    
    try:
        # Verificar si el servicio está siendo usado en facturas
        from app.models.invoice import InvoiceService
        in_use = InvoiceService.query.filter(
            InvoiceService.description.like(f'%{service.name}%')
        ).first()
        
        if in_use:
            # No eliminar, solo desactivar
            service.is_active = False
            db.session.commit()
            flash(f'Servicio "{service.name}" desactivado (estaba en uso en facturas).', 'info')
        else:
            # Eliminar completamente
            db.session.delete(service)
            db.session.commit()
            flash(f'Servicio médico "{service.name}" eliminado exitosamente.', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar servicio: {str(e)}', 'error')
    
    return redirect(url_for('admin.services'))


@bp.route('/services/<int:id>/toggle', methods=['POST'])
@login_required
@require_role('admin')
def toggle_service_status(id):
    """Activar/desactivar servicio médico"""
    service = MedicalService.query.get_or_404(id)
    
    try:
        service.is_active = not service.is_active
        service.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = "activado" if service.is_active else "desactivado"
        flash(f'Servicio "{service.name}" {status} exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado del servicio: {str(e)}', 'error')
    
    return redirect(url_for('admin.services'))


@bp.route('/api/services/by-category')
@login_required
@require_role('admin')
def api_services_by_category():
    """API para obtener servicios agrupados por categoría"""
    category = request.args.get('category')
    specialty_id = request.args.get('specialty_id')
    
    query = MedicalService.query.filter_by(is_active=True)
    
    if category:
        query = query.filter(MedicalService.category == category)
    
    if specialty_id:
        query = query.filter(MedicalService.specialty_id == specialty_id)
    
    services = query.order_by(MedicalService.name).all()
    
    result = []
    for service in services:
        result.append({
            'id': service.id,
            'name': service.name,
            'code': service.code,
            'base_price': float(service.base_price),
            'duration_minutes': service.duration_minutes,
            'category': service.category
        })
    
    return jsonify(result)
