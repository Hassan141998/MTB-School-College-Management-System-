from flask import (Blueprint, render_template, request, send_file)
from flask_login import login_required
from app.models import (Student, Teacher, Attendance, FeePayment, Mark,
                         Exam, ClassSection, FeeStructure)
from app.utils.decorators import staff_required
from app import db
from datetime import date, timedelta
from sqlalchemy import func
import io

reports_bp = Blueprint('reports', __name__, template_folder='../templates')


@reports_bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')


@reports_bp.route('/students')
@login_required
@staff_required
def student_report():
    classes = ClassSection.query.filter_by(is_active=True).all()
    class_id = request.args.get('class_id')
    students = []
    if class_id:
        students = Student.query.filter_by(
            class_section_id=int(class_id), status='active').order_by(Student.full_name).all()
    student_data = []
    for s in students:
        total_att = Attendance.query.filter_by(student_id=s.id).count()
        present = Attendance.query.filter_by(student_id=s.id, status='present').count()
        att_pct = round((present / total_att * 100) if total_att else 0, 1)
        total_fees = db.session.query(func.sum(FeePayment.total_paid)).filter_by(
            student_id=s.id).scalar() or 0
        student_data.append({
            'student': s, 'att_pct': att_pct, 'total_fees': total_fees,
            'present': present, 'total_att': total_att
        })
    return render_template('reports/students.html', student_data=student_data,
                           classes=classes, class_id=class_id)


@reports_bp.route('/financial')
@login_required
@staff_required
def financial_report():
    today = date.today()
    month = int(request.args.get('month', today.month))
    year = int(request.args.get('year', today.year))

    monthly_payments = FeePayment.query.filter(
        func.extract('month', FeePayment.payment_date) == month,
        func.extract('year', FeePayment.payment_date) == year
    ).order_by(FeePayment.payment_date.desc()).all()

    total = sum(p.total_paid for p in monthly_payments)
    by_type = {}
    for p in monthly_payments:
        fee_type = p.fee_structure.fee_type if p.fee_structure else 'other'
        by_type[fee_type] = by_type.get(fee_type, 0) + p.total_paid

    from app.utils.helpers import get_months
    return render_template('reports/financial.html', payments=monthly_payments,
                           total=total, by_type=by_type, month=month, year=year,
                           months=get_months(), years=range(2020, today.year + 2))


@reports_bp.route('/attendance')
@login_required
@staff_required
def attendance_report():
    classes = ClassSection.query.filter_by(is_active=True).all()
    class_id = request.args.get('class_id')
    from_date = request.args.get('from_date', (date.today() - timedelta(days=30)).isoformat())
    to_date = request.args.get('to_date', date.today().isoformat())

    data = []
    if class_id:
        students = Student.query.filter_by(
            class_section_id=int(class_id), status='active').all()
        for s in students:
            total = Attendance.query.filter(
                Attendance.student_id == s.id,
                Attendance.date >= from_date,
                Attendance.date <= to_date
            ).count()
            present = Attendance.query.filter(
                Attendance.student_id == s.id,
                Attendance.date >= from_date,
                Attendance.date <= to_date,
                Attendance.status == 'present'
            ).count()
            pct = round((present / total * 100) if total else 0, 1)
            data.append({'student': s, 'present': present, 'total': total, 'pct': pct})

    return render_template('reports/attendance.html', data=data, classes=classes,
                           class_id=class_id, from_date=from_date, to_date=to_date)


@reports_bp.route('/export/students')
@login_required
@staff_required
def export_student_report():
    """Export student performance report to Excel"""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        from flask import flash, redirect, url_for
        flash('openpyxl not installed.', 'danger')
        return redirect(url_for('reports.student_report'))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Student Performance'
    headers = ['Reg No', 'Name', "Father's Name", 'Class', 'Present', 'Total Days', 'Attendance %']
    hf = PatternFill(start_color='FF6B35', end_color='FF6B35', fill_type='solid')
    hfont = Font(color='FFFFFF', bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = hf
        cell.font = hfont
        ws.column_dimensions[cell.column_letter].width = 18

    students = Student.query.filter_by(status='active').all()
    for row, s in enumerate(students, 2):
        total = Attendance.query.filter_by(student_id=s.id).count()
        present = Attendance.query.filter_by(student_id=s.id, status='present').count()
        pct = round((present / total * 100) if total else 0, 1)
        class_name = s.class_section.display_name if s.class_section else ''
        ws.append([s.reg_no, s.full_name, s.father_name, class_name, present, total, pct])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='student_performance.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
