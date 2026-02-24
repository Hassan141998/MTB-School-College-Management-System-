from flask import (Blueprint, render_template, redirect, url_for, flash, request)
from flask_login import login_required, current_user
from app.models import (Attendance, Student, ClassSection, LeaveApplication,
                         TeacherAttendance, Teacher)
from app.utils.decorators import staff_required
from app import db
from datetime import date, timedelta
from sqlalchemy import func

attendance_bp = Blueprint('attendance', __name__, template_folder='../templates')


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
    att_date = request.args.get('date', date.today().isoformat())

    students = []
    existing_att = {}
    if selected_class:
        students = Student.query.filter_by(
            class_section_id=int(selected_class), status='active'
        ).order_by(Student.full_name).all()
        existing_att = {
            a.student_id: a
            for a in Attendance.query.filter_by(date=att_date, class_section_id=int(selected_class)).all()
        }

    if request.method == 'POST':
        class_id = request.form.get('class_id')
        mark_date = request.form.get('att_date', date.today().isoformat())
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
        return redirect(url_for('attendance.mark', class_id=class_id, date=mark_date))

    return render_template('attendance/mark.html',
                           classes=classes, selected_class=selected_class,
                           students=students, att_date=att_date,
                           existing_att=existing_att, today=date.today())


@attendance_bp.route('/report')
@login_required
def report():
    student_id = request.args.get('student_id')
    from_date = request.args.get('from_date', (date.today() - timedelta(days=30)).isoformat())
    to_date = request.args.get('to_date', date.today().isoformat())
    classes = ClassSection.query.filter_by(is_active=True).all()
    class_id = request.args.get('class_id')

    query = Attendance.query
    if student_id:
        query = query.filter_by(student_id=int(student_id))
    if class_id:
        query = query.filter_by(class_section_id=int(class_id))
    if from_date:
        query = query.filter(Attendance.date >= from_date)
    if to_date:
        query = query.filter(Attendance.date <= to_date)

    records = query.order_by(Attendance.date.desc()).limit(200).all()
    students = Student.query.filter_by(status='active').order_by(Student.full_name).all()
    return render_template('attendance/report.html', records=records, classes=classes,
                           students=students, from_date=from_date, to_date=to_date,
                           class_id=class_id, student_id=student_id)


@attendance_bp.route('/leave', methods=['GET', 'POST'])
@login_required
def leave():
    if request.method == 'POST':
        leave_app = LeaveApplication(
            student_id=request.form.get('student_id'),
            from_date=request.form.get('from_date'),
            to_date=request.form.get('to_date'),
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
    from datetime import datetime
    leave_app.status = 'approved' if action == 'approve' else 'rejected'
    leave_app.approved_by = current_user.full_name
    leave_app.approved_at = datetime.utcnow()
    leave_app.remarks = request.form.get('remarks', '')
    db.session.commit()
    flash(f'Leave application {leave_app.status}.', 'success')
    return redirect(url_for('attendance.leave'))
