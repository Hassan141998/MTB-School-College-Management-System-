import os
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app)
from flask_login import login_required, current_user
from app.models import Teacher, Department, SalaryRecord, TeacherAttendance
from app.utils.helpers import generate_employee_id, paginate_query
from app.utils.decorators import staff_required, admin_required
from app import db
from datetime import date

teachers_bp = Blueprint('teachers', __name__, template_folder='../templates')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@teachers_bp.route('/')
@login_required
def list_teachers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    dept_id = request.args.get('dept_id', '')

    query = Teacher.query
    if search:
        query = query.filter(
            db.or_(Teacher.full_name.ilike(f'%{search}%'),
                   Teacher.employee_id.ilike(f'%{search}%'))
        )
    if dept_id:
        query = query.filter_by(department_id=int(dept_id))

    pagination = paginate_query(query.order_by(Teacher.id.desc()), page, 15)
    departments = Department.query.filter_by(is_active=True).all()
    return render_template('teachers/list.html', teachers=pagination.items,
                           pagination=pagination, departments=departments,
                           search=search, dept_id=dept_id)


@teachers_bp.route('/add', methods=['GET', 'POST'])
@login_required
@staff_required
def add_teacher():
    departments = Department.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        teacher = Teacher(
            employee_id=generate_employee_id(),
            full_name=request.form.get('full_name'),
            father_name=request.form.get('father_name'),
            gender=request.form.get('gender'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            cnic=request.form.get('cnic'),
            qualification=request.form.get('qualification'),
            specialization=request.form.get('specialization'),
            department_id=request.form.get('department_id') or None,
            designation=request.form.get('designation', 'Teacher'),
            basic_salary=float(request.form.get('basic_salary', 0) or 0),
            join_date=request.form.get('join_date') or date.today(),
        )
        photo = request.files.get('photo')
        if photo and allowed_file(photo.filename):
            from werkzeug.utils import secure_filename
            filename = f"{teacher.employee_id}_{secure_filename(photo.filename)}"
            upload_dir = os.path.join(current_app.static_folder, 'uploads', 'teachers')
            os.makedirs(upload_dir, exist_ok=True)
            photo.save(os.path.join(upload_dir, filename))
            teacher.photo = f'uploads/teachers/{filename}'

        db.session.add(teacher)
        db.session.commit()
        flash(f'Teacher {teacher.full_name} added! Employee ID: {teacher.employee_id}', 'success')
        return redirect(url_for('teachers.view_teacher', id=teacher.id))
    return render_template('teachers/add.html', departments=departments)


@teachers_bp.route('/<int:id>')
@login_required
def view_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    salary_records = SalaryRecord.query.filter_by(teacher_id=id).order_by(
        SalaryRecord.year.desc(), SalaryRecord.id.desc()).limit(6).all()
    recent_att = TeacherAttendance.query.filter_by(teacher_id=id).order_by(
        TeacherAttendance.date.desc()).limit(10).all()
    return render_template('teachers/view.html', teacher=teacher,
                           salary_records=salary_records, recent_att=recent_att)


@teachers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@staff_required
def edit_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    departments = Department.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        teacher.full_name = request.form.get('full_name', teacher.full_name)
        teacher.gender = request.form.get('gender', teacher.gender)
        teacher.phone = request.form.get('phone', teacher.phone)
        teacher.email = request.form.get('email', teacher.email)
        teacher.address = request.form.get('address', teacher.address)
        teacher.qualification = request.form.get('qualification', teacher.qualification)
        teacher.specialization = request.form.get('specialization', teacher.specialization)
        teacher.department_id = request.form.get('department_id') or teacher.department_id
        teacher.designation = request.form.get('designation', teacher.designation)
        teacher.basic_salary = float(request.form.get('basic_salary', teacher.basic_salary) or teacher.basic_salary)
        teacher.status = request.form.get('status', teacher.status)

        photo = request.files.get('photo')
        if photo and allowed_file(photo.filename):
            from werkzeug.utils import secure_filename
            filename = f"{teacher.employee_id}_{secure_filename(photo.filename)}"
            upload_dir = os.path.join(current_app.static_folder, 'uploads', 'teachers')
            os.makedirs(upload_dir, exist_ok=True)
            photo.save(os.path.join(upload_dir, filename))
            teacher.photo = f'uploads/teachers/{filename}'

        db.session.commit()
        flash('Teacher updated successfully.', 'success')
        return redirect(url_for('teachers.view_teacher', id=id))
    return render_template('teachers/edit.html', teacher=teacher, departments=departments)


@teachers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    teacher.status = 'inactive'
    db.session.commit()
    flash(f'Teacher {teacher.full_name} deactivated.', 'info')
    return redirect(url_for('teachers.list_teachers'))


@teachers_bp.route('/<int:id>/salary', methods=['GET', 'POST'])
@login_required
@staff_required
def salary_records(id):
    teacher = Teacher.query.get_or_404(id)
    if request.method == 'POST':
        basic = float(request.form.get('basic_salary', teacher.basic_salary) or 0)
        allow = float(request.form.get('allowances', 0) or 0)
        deduct = float(request.form.get('deductions', 0) or 0)
        record = SalaryRecord(
            teacher_id=id,
            month=request.form.get('month'),
            year=int(request.form.get('year', date.today().year)),
            basic_salary=basic,
            allowances=allow,
            deductions=deduct,
            net_salary=basic + allow - deduct,
            payment_date=request.form.get('payment_date') or date.today(),
            payment_method=request.form.get('payment_method', 'cash'),
            status='paid',
            notes=request.form.get('notes'),
        )
        db.session.add(record)
        db.session.commit()
        flash('Salary record added.', 'success')
        return redirect(url_for('teachers.salary_records', id=id))
    records = SalaryRecord.query.filter_by(teacher_id=id).order_by(
        SalaryRecord.year.desc(), SalaryRecord.id.desc()).all()
    from app.utils.helpers import get_months
    return render_template('teachers/salary.html', teacher=teacher,
                           records=records, months=get_months(), today=date.today())


@teachers_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
@staff_required
def mark_attendance():
    teachers = Teacher.query.filter_by(status='active').all()
    today = date.today()
    if request.method == 'POST':
        att_date = request.form.get('att_date', today.isoformat())
        marked = 0
        for teacher in teachers:
            status = request.form.get(f'status_{teacher.id}', 'absent')
            existing = TeacherAttendance.query.filter_by(
                teacher_id=teacher.id,
                date=att_date
            ).first()
            if existing:
                existing.status = status
                existing.marked_by = current_user.full_name
            else:
                att = TeacherAttendance(
                    teacher_id=teacher.id,
                    date=att_date,
                    status=status,
                    marked_by=current_user.full_name,
                    check_in=request.form.get(f'check_in_{teacher.id}'),
                    check_out=request.form.get(f'check_out_{teacher.id}'),
                )
                db.session.add(att)
            marked += 1
        db.session.commit()
        flash(f'Attendance marked for {marked} teachers.', 'success')
        return redirect(url_for('teachers.mark_attendance'))

    att_date = request.args.get('date', today.isoformat())
    existing_att = {a.teacher_id: a for a in TeacherAttendance.query.filter_by(date=att_date).all()}
    return render_template('teachers/attendance.html', teachers=teachers,
                           today=today, att_date=att_date, existing_att=existing_att)
