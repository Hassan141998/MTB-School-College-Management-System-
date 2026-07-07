from flask import (Blueprint, render_template, redirect, url_for, flash, request)
from flask_login import login_required, current_user
from app.models import (Department, Subject, User, ClassSection,
                         Announcement, AcademicCalendar)
from app.utils.decorators import admin_required, staff_required
from app import db
from datetime import date

settings_bp = Blueprint('settings', __name__, template_folder='../templates')


@settings_bp.route('/')
@login_required
@staff_required
def index():
    return redirect(url_for('settings.departments'))


# ─── Departments ─────────────────────────────────────────────────────────────

@settings_bp.route('/departments')
@login_required
@staff_required
def departments():
    depts = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    return render_template('settings/departments.html', departments=depts)


@settings_bp.route('/departments/add', methods=['POST'])
@login_required
@admin_required
def add_department():
    dept = Department(
        name=request.form.get('name'),
        code=request.form.get('code'),
        hod_name=request.form.get('hod_name'),
        description=request.form.get('description'),
    )
    db.session.add(dept)
    db.session.commit()
    flash(f'Department "{dept.name}" added.', 'success')
    return redirect(url_for('settings.departments'))


@settings_bp.route('/departments/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_department(id):
    dept = Department.query.get_or_404(id)
    dept.is_active = False
    db.session.commit()
    flash(f'Department "{dept.name}" removed.', 'info')
    return redirect(url_for('settings.departments'))


# ─── Subjects ────────────────────────────────────────────────────────────────

@settings_bp.route('/subjects')
@login_required
@staff_required
def subjects():
    subjects = Subject.query.filter_by(is_active=True).order_by(Subject.name).all()
    departments = Department.query.filter_by(is_active=True).all()
    return render_template('settings/subjects.html', subjects=subjects, departments=departments)


@settings_bp.route('/subjects/add', methods=['POST'])
@login_required
@admin_required
def add_subject():
    subj = Subject(
        name=request.form.get('name'),
        code=request.form.get('code'),
        department_id=request.form.get('department_id') or None,
        credit_hours=int(request.form.get('credit_hours', 3) or 3),
    )
    db.session.add(subj)
    db.session.commit()
    flash(f'Subject "{subj.name}" added.', 'success')
    return redirect(url_for('settings.subjects'))


@settings_bp.route('/subjects/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_subject(id):
    subj = Subject.query.get_or_404(id)
    subj.is_active = False
    db.session.commit()
    flash(f'Subject "{subj.name}" removed.', 'info')
    return redirect(url_for('settings.subjects'))


# ─── Classes ─────────────────────────────────────────────────────────────────

@settings_bp.route('/classes')
@login_required
@staff_required
def classes():
    class_sections = ClassSection.query.filter_by(is_active=True).order_by(
        ClassSection.class_name, ClassSection.section).all()
    return render_template('settings/classes.html', class_sections=class_sections)


@settings_bp.route('/classes/add', methods=['POST'])
@login_required
@admin_required
def add_class():
    cs = ClassSection(
        class_name=request.form.get('class_name'),
        section=request.form.get('section'),
        academic_year=request.form.get('academic_year', '2024-25'),
        max_students=int(request.form.get('max_students', 40) or 40),
    )
    db.session.add(cs)
    db.session.commit()
    flash(f'Class {cs.display_name} added.', 'success')
    return redirect(url_for('settings.classes'))


# ─── Users ────────────────────────────────────────────────────────────────────

@settings_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('settings/users.html', users=all_users)


@settings_bp.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    username = request.form.get('username')
    if User.query.filter_by(username=username).first():
        flash(f'Username "{username}" already exists.', 'danger')
        return redirect(url_for('settings.users'))
    user = User(
        username=username,
        email=request.form.get('email'),
        full_name=request.form.get('full_name'),
        role=request.form.get('role', 'teacher'),
        phone=request.form.get('phone'),
    )
    user.set_password(request.form.get('password', 'mtb@1234'))
    db.session.add(user)
    db.session.commit()
    flash(f'User "{user.username}" created with role {user.role}.', 'success')
    return redirect(url_for('settings.users'))


@settings_bp.route('/users/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Cannot deactivate your own account.', 'danger')
        return redirect(url_for('settings.users'))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('settings.users'))


# ─── Announcements ────────────────────────────────────────────────────────────

@settings_bp.route('/announcements')
@login_required
@staff_required
def announcements():
    items = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('settings/announcements.html', announcements=items)


@settings_bp.route('/announcements/add', methods=['POST'])
@login_required
@staff_required
def add_announcement():
    ann = Announcement(
        title=request.form.get('title'),
        content=request.form.get('content'),
        target_audience=request.form.get('target_audience', 'all'),
        priority=request.form.get('priority', 'normal'),
        created_by=current_user.full_name,
    )
    db.session.add(ann)
    db.session.commit()
    flash('Announcement published.', 'success')
    return redirect(url_for('settings.announcements'))


@settings_bp.route('/announcements/<int:id>/delete', methods=['POST'])
@login_required
@staff_required
def delete_announcement(id):
    ann = Announcement.query.get_or_404(id)
    ann.is_active = False
    db.session.commit()
    flash('Announcement removed.', 'info')
    return redirect(url_for('settings.announcements'))


# ─── Academic Calendar ────────────────────────────────────────────────────────

@settings_bp.route('/calendar')
@login_required
@staff_required
def calendar():
    events = AcademicCalendar.query.order_by(AcademicCalendar.start_date).all()
    return render_template('settings/calendar.html', events=events)


@settings_bp.route('/calendar/add', methods=['POST'])
@login_required
@staff_required
def add_calendar_event():
    event = AcademicCalendar(
        title=request.form.get('title'),
        event_type=request.form.get('event_type', 'event'),
        start_date=request.form.get('start_date'),
        end_date=request.form.get('end_date') or None,
        description=request.form.get('description'),
        is_holiday=request.form.get('is_holiday') == 'on',
        created_by=current_user.full_name,
    )
    db.session.add(event)
    db.session.commit()
    flash('Calendar event added.', 'success')
    return redirect(url_for('settings.calendar'))


@settings_bp.route('/calendar/<int:id>/delete', methods=['POST'])
@login_required
@staff_required
def delete_calendar_event(id):
    event = AcademicCalendar.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted.', 'info')
    return redirect(url_for('settings.calendar'))
