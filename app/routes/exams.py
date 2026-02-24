from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, make_response)
from flask_login import login_required, current_user
from app.models import Exam, ExamSubject, Mark, Student, ClassSection, Subject
from app.utils.decorators import staff_required
from app.utils.helpers import calculate_grade_from_marks, paginate_query
from app import db
from datetime import date

exams_bp = Blueprint('exams', __name__, template_folder='../templates')


@exams_bp.route('/')
@login_required
def list_exams():
    exams = Exam.query.order_by(Exam.created_at.desc()).all()
    classes = ClassSection.query.filter_by(is_active=True).all()
    return render_template('exams/list.html', exams=exams, classes=classes)


@exams_bp.route('/add', methods=['GET', 'POST'])
@login_required
@staff_required
def add_exam():
    classes = ClassSection.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        exam = Exam(
            name=request.form.get('name'),
            exam_type=request.form.get('exam_type', 'mid-term'),
            class_section_id=request.form.get('class_section_id') or None,
            start_date=request.form.get('start_date') or None,
            end_date=request.form.get('end_date') or None,
            academic_year=request.form.get('academic_year', '2024-25'),
        )
        db.session.add(exam)
        db.session.commit()
        flash(f'Exam "{exam.name}" created.', 'success')
        return redirect(url_for('exams.exam_subjects', exam_id=exam.id))
    return render_template('exams/add.html', classes=classes)


@exams_bp.route('/<int:exam_id>/subjects', methods=['GET', 'POST'])
@login_required
@staff_required
def exam_subjects(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    subjects = Subject.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        total_marks = int(request.form.get('total_marks', 100))
        passing_marks = int(request.form.get('passing_marks', 33))
        existing = ExamSubject.query.filter_by(
            exam_id=exam_id, subject_id=subject_id).first()
        if not existing:
            es = ExamSubject(
                exam_id=exam_id,
                subject_id=subject_id,
                total_marks=total_marks,
                passing_marks=passing_marks,
                exam_date=request.form.get('exam_date') or None,
                exam_time=request.form.get('exam_time'),
            )
            db.session.add(es)
            db.session.commit()
            flash('Subject added to exam.', 'success')
        else:
            flash('Subject already added.', 'warning')
        return redirect(url_for('exams.exam_subjects', exam_id=exam_id))

    exam_subs = ExamSubject.query.filter_by(exam_id=exam_id).all()
    return render_template('exams/subjects.html', exam=exam,
                           subjects=subjects, exam_subs=exam_subs)


@exams_bp.route('/<int:exam_id>/marks', methods=['GET', 'POST'])
@login_required
@staff_required
def enter_marks(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    exam_subs = ExamSubject.query.filter_by(exam_id=exam_id).all()
    if not exam_subs:
        flash('Add subjects to exam first.', 'warning')
        return redirect(url_for('exams.exam_subjects', exam_id=exam_id))

    selected_sub_id = request.args.get('subject_id', exam_subs[0].subject_id if exam_subs else None, type=int)
    selected_sub = next((es for es in exam_subs if es.subject_id == selected_sub_id), exam_subs[0] if exam_subs else None)

    if exam.class_section_id:
        students = Student.query.filter_by(
            class_section_id=exam.class_section_id, status='active').order_by(Student.full_name).all()
    else:
        students = Student.query.filter_by(status='active').order_by(Student.full_name).all()

    if request.method == 'POST':
        sub_id = int(request.form.get('subject_id'))
        sub_total = int(request.form.get('total_marks', 100))
        saved = 0
        for student in students:
            marks_str = request.form.get(f'marks_{student.id}', '')
            if marks_str == '':
                continue
            obtained = float(marks_str)
            grade, pct = calculate_grade_from_marks(obtained, sub_total)
            existing = Mark.query.filter_by(
                student_id=student.id, exam_id=exam_id, subject_id=sub_id).first()
            if existing:
                existing.obtained_marks = obtained
                existing.grade = grade
                existing.entered_by = current_user.full_name
            else:
                mark = Mark(
                    student_id=student.id,
                    exam_id=exam_id,
                    subject_id=sub_id,
                    obtained_marks=obtained,
                    total_marks=sub_total,
                    grade=grade,
                    entered_by=current_user.full_name,
                )
                db.session.add(mark)
            saved += 1
        db.session.commit()
        flash(f'Marks saved for {saved} students.', 'success')
        return redirect(url_for('exams.enter_marks', exam_id=exam_id, subject_id=sub_id))

    existing_marks = {
        m.student_id: m for m in Mark.query.filter_by(
            exam_id=exam_id, subject_id=selected_sub_id).all()
    } if selected_sub_id else {}

    return render_template('exams/marks.html', exam=exam, exam_subs=exam_subs,
                           selected_sub=selected_sub, students=students,
                           existing_marks=existing_marks)


@exams_bp.route('/<int:exam_id>/results')
@login_required
def results(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    exam_subs = ExamSubject.query.filter_by(exam_id=exam_id).all()

    if exam.class_section_id:
        students = Student.query.filter_by(
            class_section_id=exam.class_section_id, status='active').order_by(Student.full_name).all()
    else:
        students = Student.query.filter_by(status='active').order_by(Student.full_name).all()

    results_data = []
    for student in students:
        student_marks = Mark.query.filter_by(student_id=student.id, exam_id=exam_id).all()
        total_obtained = sum(m.obtained_marks for m in student_marks)
        total_possible = sum(es.total_marks for es in exam_subs)
        pct = round((total_obtained / total_possible * 100) if total_possible else 0, 1)
        grade, _ = calculate_grade_from_marks(total_obtained, total_possible)
        results_data.append({
            'student': student, 'marks': {m.subject_id: m for m in student_marks},
            'total_obtained': total_obtained, 'total_possible': total_possible,
            'percentage': pct, 'grade': grade,
        })
    results_data.sort(key=lambda x: x['total_obtained'], reverse=True)
    return render_template('exams/results.html', exam=exam, exam_subs=exam_subs,
                           results_data=results_data)


@exams_bp.route('/<int:exam_id>/result/<int:student_id>/pdf')
@login_required
def result_pdf(exam_id, student_id):
    exam = Exam.query.get_or_404(exam_id)
    student = Student.query.get_or_404(student_id)
    exam_subs = ExamSubject.query.filter_by(exam_id=exam_id).all()

    subject_marks = []
    for es in exam_subs:
        mark = Mark.query.filter_by(
            student_id=student_id, exam_id=exam_id, subject_id=es.subject_id).first()
        if mark:
            subject_marks.append({
                'subject_name': es.subject.name if es.subject else 'Subject',
                'obtained': mark.obtained_marks,
                'total': mark.total_marks,
                'grade': mark.grade or 'N/A',
            })

    try:
        from app.utils.pdf_generator import generate_result_card
        pdf_bytes = generate_result_card(student, exam, subject_marks)
        if pdf_bytes:
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = (
                f'inline; filename=result_{student.reg_no}_{exam_id}.pdf')
            return response
    except Exception as e:
        flash(f'Could not generate PDF: {str(e)}', 'warning')
    return redirect(url_for('exams.results', exam_id=exam_id))
