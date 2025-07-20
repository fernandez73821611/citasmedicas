from functools import wraps
from flask import abort, flash, redirect, url_for, request, jsonify
from flask_login import current_user

def require_role(role):
    """Decorador para requerir un rol específico"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                # Si es una petición AJAX, devolver JSON
                if request.is_json or request.headers.get('Content-Type') == 'application/json':
                    return jsonify({'success': False, 'message': 'No autenticado'}), 401
                return redirect(url_for('auth.login'))
            
            if not current_user.has_role(role):
                # Si es una petición AJAX, devolver JSON
                if request.is_json or request.headers.get('Content-Type') == 'application/json':
                    return jsonify({'success': False, 'message': 'Sin permisos'}), 403
                flash('No tienes permisos para acceder a esta página', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorador para requerir rol de administrador"""
    return require_role('admin')(f)

def doctor_required(f):
    """Decorador para requerir rol de médico"""
    return require_role('doctor')(f)

def receptionist_required(f):
    """Decorador para requerir rol de recepcionista"""
    return require_role('receptionist')(f)

def nurse_required(f):
    """Decorador para requerir rol de enfermera"""
    return require_role('nurse')(f)
