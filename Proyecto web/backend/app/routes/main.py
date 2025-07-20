from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

# Blueprint principal
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Página principal - redirige al dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal - redirige según el rol del usuario"""
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'doctor':
        return redirect(url_for('doctor.dashboard'))
    elif current_user.role == 'receptionist':
        return redirect(url_for('receptionist.dashboard'))
    elif current_user.role == 'nurse':
        return redirect(url_for('nurse.dashboard'))
    else:
        flash('Rol de usuario no válido', 'error')
        return redirect(url_for('auth.logout'))
