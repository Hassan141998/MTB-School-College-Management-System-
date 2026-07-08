from flask import (Blueprint, render_template, redirect, url_for, flash, request)
from flask_login import login_required, current_user
from app.models import (Attendance, Student, ClassSection, LeaveApplication,
                         TeacherAttendance, Teacher)
from app.utils.decorators import staff_required
from app import db
from datetime import date, timedelta, datetime
from sqlalchemy import func

attendance_bp = Blueprint('attendance', __name__, template_folder='../templates')


def parse_date(value, default=None):
    """Parse a 'YYYY-MM-DD' string (from a form field or query arg) into a
    real Python date object. SQLite's Date column type rejects plain
    strings, which is exactly what was crashing POST /attendance/mark."""
    if isinstance(value, date):
        return value
    if not value:
        return default if default is not None else date.today()
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return default if default is not None else date.today()


@attendance_bp.route('/')
@login_required
def index():
    return redirect(url_for('attendance.mark'))


@attendance_bp.route('/mark', methods=['GET', 'POST'])
@login_required
@staff_required
def mark():
    classes = ClassSection.query.filter_by(is_active=True).all()
    selected_class = request.args.get('class_id', '')
    att_date_str = request.args.get('date', date.today().isoformat())
    att_date_obj = parse_date(att_date_str)

    students = []
    existing_att = {}
    if selected_class:
        students = Student.query.filter_by(
            class_section_id=int(selected_class), status='active'
        ).order_by(Student.full_name).all()
        existing_att = {
            a.student_id: a
            for a in Attendance.query.filter_by(date=att_date_obj, class_section_id=int(selected_class)).all()
        }

    if request.method == 'POST':
        class_id = request.form.get('class_id')
        mark_date = parse_date(request.form.get('att_date'), default=date.today())
        all_students = Student.query.filter_by(class_section_id=class_id, status='active').all()
        marked = 0
        for student in all_students:
            status = request.form.get(f'status_{student.id}', 'absent')
            existing = Attendance.query.filter_by(
                student_id=student.id, date=mark_date).first()
            if existing:
                existing.status = status
                existing.marked_by = current_user.full_name
                existing.method = 'manual'
            else:
                att = Attendance(
                    student_id=student.id,
                    class_section_id=int(class_id),
                    date=mark_date,
                    status=status,
                    marked_by=current_user.full_name,
                    method='manual',
                )
                db.session.add(att)
            marked += 1
        db.session.commit()
        flash(f'Attendance marked for {marked} students.', 'success')
        return redirect(url_for('attendance.mark', class_id=class_id, date=mark_date.isoformat()))

    return render_template('attendance/mark.html',
                           classes=classes, selected_class=selected_class,
                           students=students, att_date=att_date_str,
                           existing_att=existing_att, today=date.today())


@attendance_bp.route('/report')
@login_required
def report():
    classes = ClassSection.query.filter_by(is_active=True).all()
    class_id = request.args.get('class_id', type=int)

    today = date.today()
    month_str = request.args.get('month', today.strftime('%Y-%m'))
    try:
        year, month = map(int, month_str.split('-'))
        start = date(year, month, 1)
    except (ValueError, TypeError):
        start = today.replace(day=1)
        month_str = start.strftime('%Y-%m')
    if start.month == 12:
        end = date(start.year, 12, 31)
    else:
        end = date(start.year, start.month + 1, 1) - timedelta(days=1)

    report_data = []
    if class_id:
        students = Student.query.filter_by(
            class_section_id=class_id, status='active').order_by(Student.full_name).all()
        for s in students:
            recs = Attendance.query.filter(
                Attendance.student_id == s.id,
                Attendance.date >= start, Attendance.date <= end
            ).all()
            present = sum(1 for r in recs if r.status == 'present')
            absent = sum(1 for r in recs if r.status == 'absent')
            leave = sum(1 for r in recs if r.status == 'leave')
            total = len(recs)
            percentage = round((present / total * 100) if total else 0, 1)
            report_data.append({
                'student': s, 'present': present, 'absent': absent,
                'leave': leave, 'total': total, 'percentage': percentage,
            })

    return render_template('attendance/report.html', report_data=report_data,
                           classes=classes, class_id=class_id,
                           start=start, end=end, month_str=month_str)


@attendance_bp.route('/leave', methods=['GET', 'POST'])
@login_required
def leave():
    if request.method == 'POST':
        leave_app = LeaveApplication(
            student_id=request.form.get('student_id'),
            from_date=parse_date(request.form.get('from_date')),
            to_date=parse_date(request.form.get('to_date')),
            reason=request.form.get('reason'),
            leave_type=request.form.get('leave_type', 'sick'),
        )
        db.session.add(leave_app)
        db.session.commit()
        flash('Leave application submitted.', 'success')
        return redirect(url_for('attendance.leave'))

    applications = LeaveApplication.query.order_by(
        LeaveApplication.created_at.desc()).limit(50).all()
    students = Student.query.filter_by(status='active').order_by(Student.full_name).all()
    return render_template('attendance/leave.html', applications=applications, students=students)


@attendance_bp.route('/leave/<int:id>/approve', methods=['POST'])
@login_required
@staff_required
def approve_leave(id):
    leave_app = LeaveApplication.query.get_or_404(id)
    action = request.form.get('action', 'approve')
    leave_app.status = 'approved' if action == 'approve' else 'rejected'
    leave_app.approved_by = current_user.full_name
    leave_app.approved_at = datetime.utcnow()
    leave_app.remarks = request.form.get('remarks', '')
    db.session.commit()
    flash(f'Leave application {leave_app.status}.', 'success')
    return redirect(url_for('attendance.leave'))