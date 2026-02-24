"""
Role-based access decorators for MTB School & College
"""
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Administrator access required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


def staff_required(f):
    """Allow admin, principal, hod, teacher, accountant, receptionist, librarian"""
    STAFF_ROLES = {'admin', 'principal', 'hod', 'teacher', 'accountant', 'receptionist', 'librarian'}

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in STAFF_ROLES:
            flash('Staff access required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Allow specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash(f'Access restricted. Required role(s): {", ".join(roles)}.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated
    return decorator
