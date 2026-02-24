"""
Utility helpers for MTB School & College Management System
"""
from datetime import date
from app import db


def generate_reg_no():
    """Generate student registration number: MTB-YYYY-XXXX"""
    from app.models import Student
    year = date.today().year
    prefix = f'MTB-{year}-'
    last = Student.query.filter(Student.reg_no.like(f'{prefix}%')).order_by(
        Student.id.desc()).first()
    if last:
        try:
            seq = int(last.reg_no.split('-')[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f'{prefix}{seq:04d}'


def generate_employee_id():
    """Generate teacher employee ID: EMP-YYYY-XXXX"""
    from app.models import Teacher
    year = date.today().year
    prefix = f'EMP-{year}-'
    last = Teacher.query.filter(Teacher.employee_id.like(f'{prefix}%')).order_by(
        Teacher.id.desc()).first()
    if last:
        try:
            seq = int(last.employee_id.split('-')[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f'{prefix}{seq:04d}'


def generate_receipt_no():
    """Generate fee receipt number: RCP-YYYYMMDD-XXXX"""
    from app.models import FeePayment
    today_str = date.today().strftime('%Y%m%d')
    prefix = f'RCP-{today_str}-'
    count = FeePayment.query.filter(FeePayment.receipt_no.like(f'{prefix}%')).count()
    return f'{prefix}{count + 1:04d}'


def calculate_grade(percentage):
    """Return letter grade based on percentage"""
    if percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'B'
    elif percentage >= 60:
        return 'C'
    elif percentage >= 50:
        return 'D'
    else:
        return 'F'


def calculate_grade_from_marks(obtained, total):
    """Calculate grade from raw marks"""
    if total <= 0:
        return 'N/A', 0
    pct = (obtained / total) * 100
    return calculate_grade(pct), round(pct, 2)


def calculate_attendance_percentage(present, total):
    """Calculate attendance percentage"""
    if total == 0:
        return 0.0
    return round((present / total) * 100, 2)


def paginate_query(query, page, per_page=15):
    """Paginate a SQLAlchemy query"""
    return query.paginate(page=page, per_page=per_page, error_out=False)


def log_activity(action, module=None, details=None, user_id=None):
    """Log user activity"""
    from app.models import ActivityLog
    from flask import request
    try:
        log = ActivityLog(
            user_id=user_id,
            action=action,
            module=module,
            details=details,
            ip_address=request.remote_addr if request else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()


def get_months():
    return ['January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December']


def get_current_academic_year():
    today = date.today()
    if today.month >= 4:
        return f'{today.year}-{str(today.year + 1)[2:]}'
    else:
        return f'{today.year - 1}-{str(today.year)[2:]}'
