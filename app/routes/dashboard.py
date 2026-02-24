from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import (Student, Teacher, FeePayment, Attendance,
                         ClassSection, LibraryBook, BookIssue, Exam,
                         Announcement, AcademicCalendar)
from app import db
from datetime import date, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates')


@dashboard_bp.route('/')
@login_required
def index():
    # Core stats
    total_students = Student.query.filter_by(status='active').count()
    total_teachers = Teacher.query.filter_by(status='active').count()

    # Today's attendance
    today = date.today()
    today_present = Attendance.query.filter_by(date=today, status='present').count()
    today_total = Attendance.query.filter_by(date=today).count()
    today_attendance_pct = round((today_present / today_total * 100) if today_total else 0, 1)

    # Monthly fee collection
    month_fees = db.session.query(func.sum(FeePayment.total_paid)).filter(
        func.extract('month', FeePayment.payment_date) == today.month,
        func.extract('year', FeePayment.payment_date) == today.year
    ).scalar() or 0

    # Library stats
    books_issued = BookIssue.query.filter_by(status='issued').count()
    total_books = LibraryBook.query.count()

    # Upcoming events
    upcoming_events = AcademicCalendar.query.filter(
        AcademicCalendar.start_date >= today
    ).order_by(AcademicCalendar.start_date).limit(5).all()

    # Recent announcements
    announcements = Announcement.query.filter_by(is_active=True).order_by(
        Announcement.created_at.desc()).limit(5).all()

    # Active exams
    active_exams = Exam.query.filter_by(is_active=True).count()

    stats = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'today_attendance_pct': today_attendance_pct,
        'month_fees': month_fees,
        'books_issued': books_issued,
        'total_books': total_books,
        'active_exams': active_exams,
    }

    return render_template('dashboard/index.html',
                           stats=stats,
                           upcoming_events=upcoming_events,
                           announcements=announcements,
                           today=today)


@dashboard_bp.route('/api/enrollment-data')
@login_required
def enrollment_data():
    """Chart.js: monthly enrollment trend (last 6 months)"""
    today = date.today()
    labels = []
    data = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        month_name = d.strftime('%b %Y')
        count = Student.query.filter(
            func.extract('month', Student.admission_date) == d.month,
            func.extract('year', Student.admission_date) == d.year
        ).count()
        labels.append(month_name)
        data.append(count)
    return jsonify({'labels': labels, 'data': data})


@dashboard_bp.route('/api/attendance-data')
@login_required
def attendance_data():
    """Chart.js: attendance last 7 days"""
    today = date.today()
    labels = []
    present_data = []
    absent_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime('%a %d'))
        present = Attendance.query.filter_by(date=d, status='present').count()
        absent = Attendance.query.filter_by(date=d, status='absent').count()
        present_data.append(present)
        absent_data.append(absent)
    return jsonify({'labels': labels, 'present': present_data, 'absent': absent_data})


@dashboard_bp.route('/api/fees-data')
@login_required
def fees_data():
    """Chart.js: fee collection last 6 months"""
    today = date.today()
    labels = []
    data = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i * 30)
        total = db.session.query(func.sum(FeePayment.total_paid)).filter(
            func.extract('month', FeePayment.payment_date) == d.month,
            func.extract('year', FeePayment.payment_date) == d.year
        ).scalar() or 0
        labels.append(d.strftime('%b'))
        data.append(float(total))
    return jsonify({'labels': labels, 'data': data})


@dashboard_bp.route('/api/class-stats')
@login_required
def class_stats():
    """Students per class for doughnut chart"""
    classes = ClassSection.query.filter_by(is_active=True).all()
    labels = [cs.display_name for cs in classes]
    data = [Student.query.filter_by(class_section_id=cs.id, status='active').count()
            for cs in classes]
    return jsonify({'labels': labels, 'data': data})
