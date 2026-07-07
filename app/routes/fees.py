from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, send_file, make_response)
from flask_login import login_required, current_user
from app.models import FeePayment, FeeStructure, Student, ClassSection
from app.utils.helpers import generate_receipt_no, paginate_query
from app.utils.decorators import role_required
from app import db
from datetime import date
import io

fees_bp = Blueprint('fees', __name__, template_folder='../templates')


@fees_bp.route('/')
@login_required
def index():
    return redirect(url_for('fees.payments'))


@fees_bp.route('/structure')
@login_required
def structure():
    fee_structures = FeeStructure.query.filter_by(is_active=True).order_by(
        FeeStructure.class_name, FeeStructure.fee_type).all()
    return render_template('fees/structure.html', fee_structures=fee_structures)


@fees_bp.route('/structure/add', methods=['POST'])
@login_required
@role_required('admin', 'principal', 'accountant')
def add_structure():
    fs = FeeStructure(
        name=request.form.get('name'),
        class_name=request.form.get('class_name'),
        amount=float(request.form.get('amount', 0) or 0),
        frequency=request.form.get('frequency', 'monthly'),
        fee_type=request.form.get('fee_type', 'tuition'),
        academic_year=request.form.get('academic_year', '2024-25'),
    )
    db.session.add(fs)
    db.session.commit()
    flash('Fee structure added.', 'success')
    return redirect(url_for('fees.structure'))


@fees_bp.route('/structure/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'principal', 'accountant')
def delete_structure(id):
    fs = FeeStructure.query.get_or_404(id)
    fs.is_active = False
    db.session.commit()
    flash('Fee structure removed.', 'info')
    return redirect(url_for('fees.structure'))


@fees_bp.route('/payments')
@login_required
def payments():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    month_filter = request.args.get('month', '')

    query = FeePayment.query.join(Student, FeePayment.student_id == Student.id)
    if search:
        query = query.filter(
            db.or_(Student.full_name.ilike(f'%{search}%'),
                   Student.reg_no.ilike(f'%{search}%'),
                   FeePayment.receipt_no.ilike(f'%{search}%'))
        )
    if month_filter:
        query = query.filter(FeePayment.month == month_filter)

    pagination = paginate_query(query.order_by(FeePayment.id.desc()), page, 15)
    from app.utils.helpers import get_months
    total_collected = db.session.query(db.func.sum(FeePayment.total_paid)).scalar() or 0
    return render_template('fees/payments.html', payments=pagination.items,
                           pagination=pagination, search=search,
                           month_filter=month_filter, months=get_months(),
                           total_collected=total_collected)


@fees_bp.route('/record', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'principal', 'accountant', 'receptionist')
def record_payment():
    students = Student.query.filter_by(status='active').order_by(Student.full_name).all()
    fee_structures = FeeStructure.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0) or 0)
        discount = float(request.form.get('discount', 0) or 0)
        fine = float(request.form.get('fine', 0) or 0)
        payment = FeePayment(
            receipt_no=generate_receipt_no(),
            student_id=request.form.get('student_id'),
            fee_structure_id=request.form.get('fee_structure_id') or None,
            amount=amount,
            discount=discount,
            fine=fine,
            total_paid=amount - discount + fine,
            payment_date=request.form.get('payment_date') or date.today(),
            month=request.form.get('month'),
            year=int(request.form.get('year', date.today().year)),
            payment_method=request.form.get('payment_method', 'cash'),
            bank_reference=request.form.get('bank_reference'),
            collected_by=current_user.full_name,
            notes=request.form.get('notes'),
        )
        db.session.add(payment)
        db.session.commit()
        flash(f'Payment recorded. Receipt No: {payment.receipt_no}', 'success')
        return redirect(url_for('fees.download_receipt', id=payment.id))
    from app.utils.helpers import get_months
    return render_template('fees/record_payment.html', students=students,
                           fee_structures=fee_structures, today=date.today(),
                           months=get_months(), years=range(2020, date.today().year + 2))


@fees_bp.route('/receipt/<int:id>')
@login_required
def download_receipt(id):
    payment = FeePayment.query.get_or_404(id)
    try:
        from app.utils.pdf_generator import generate_fee_receipt
        pdf_bytes = generate_fee_receipt(payment)
        if pdf_bytes:
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename=receipt_{payment.receipt_no}.pdf'
            return response
    except Exception as e:
        flash(f'Could not generate PDF: {str(e)}', 'warning')
    return redirect(url_for('fees.payments'))


@fees_bp.route('/defaulters')
@login_required
def defaulters():
    """Students with unpaid fees"""
    classes = ClassSection.query.filter_by(is_active=True).all()
    class_id = request.args.get('class_id', '')

    paid_ids = db.session.query(FeePayment.student_id).filter(
        FeePayment.month == date.today().strftime('%B'),
        FeePayment.year == date.today().year
    ).subquery()

    query = Student.query.filter(
        Student.status == 'active',
        ~Student.id.in_(paid_ids)
    )
    if class_id:
        query = query.filter_by(class_section_id=int(class_id))

    defaulter_list = query.order_by(Student.full_name).all()
    return render_template('fees/defaulters.html', defaulters=defaulter_list,
                           classes=classes, class_id=class_id,
                           current_month=date.today().strftime('%B %Y'))
