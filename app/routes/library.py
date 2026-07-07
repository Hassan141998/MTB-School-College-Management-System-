from flask import (Blueprint, render_template, redirect, url_for, flash, request)
from flask_login import login_required, current_user
from app.models import LibraryBook, BookIssue, Student
from app.utils.decorators import role_required
from app.utils.helpers import paginate_query
from app import db
from datetime import date, timedelta

library_bp = Blueprint('library', __name__, template_folder='../templates')

LOAN_DAYS = 14  # Default loan period
FINE_PER_DAY = 10  # PKR 10 per day


@library_bp.route('/')
@login_required
def index():
    return redirect(url_for('library.books'))


@library_bp.route('/books')
@login_required
def books():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = LibraryBook.query.filter_by(is_active=True)
    if search:
        query = query.filter(
            db.or_(LibraryBook.title.ilike(f'%{search}%'),
                   LibraryBook.author.ilike(f'%{search}%'),
                   LibraryBook.isbn.ilike(f'%{search}%'))
        )
    pagination = paginate_query(query.order_by(LibraryBook.title), page, 15)
    return render_template('library/books.html', books=pagination.items,
                           pagination=pagination, search=search)


@library_bp.route('/books/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'librarian', 'principal')
def add_book():
    if request.method == 'POST':
        copies = int(request.form.get('total_copies', 1) or 1)
        book = LibraryBook(
            isbn=request.form.get('isbn'),
            title=request.form.get('title'),
            author=request.form.get('author'),
            publisher=request.form.get('publisher'),
            category=request.form.get('category'),
            edition=request.form.get('edition'),
            total_copies=copies,
            available_copies=copies,
            price=float(request.form.get('price', 0) or 0),
            location=request.form.get('location'),
        )
        db.session.add(book)
        db.session.commit()
        flash(f'Book "{book.title}" added to library.', 'success')
        return redirect(url_for('library.books'))
    return render_template('library/add_book.html')


@library_bp.route('/books/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'librarian')
def delete_book(id):
    book = LibraryBook.query.get_or_404(id)
    book.is_active = False
    db.session.commit()
    flash(f'Book "{book.title}" removed.', 'info')
    return redirect(url_for('library.books'))


@library_bp.route('/issues')
@login_required
def issues():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'issued')
    query = BookIssue.query
    if status:
        query = query.filter_by(status=status)
    pagination = paginate_query(query.order_by(BookIssue.id.desc()), page, 15)
    # Calculate fines
    today = date.today()
    for issue in pagination.items:
        if issue.status == 'issued' and issue.due_date and issue.due_date < today:
            issue._current_fine = (today - issue.due_date).days * FINE_PER_DAY
        else:
            issue._current_fine = 0
    return render_template('library/issues.html', issues=pagination.items,
                           pagination=pagination, status=status, today=today)


@library_bp.route('/issue', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'librarian', 'receptionist')
def issue_book():
    books = LibraryBook.query.filter(
        LibraryBook.is_active == True,
        LibraryBook.available_copies > 0
    ).order_by(LibraryBook.title).all()
    students = Student.query.filter_by(status='active').order_by(Student.full_name).all()

    if request.method == 'POST':
        book_id = int(request.form.get('book_id'))
        student_id = int(request.form.get('student_id'))
        book = LibraryBook.query.get_or_404(book_id)

        if book.available_copies < 1:
            flash('No copies available for this book.', 'danger')
            return redirect(url_for('library.issue_book'))

        due_date = date.today() + timedelta(days=LOAN_DAYS)
        issue = BookIssue(
            book_id=book_id,
            student_id=student_id,
            issue_date=date.today(),
            due_date=due_date,
            issued_by=current_user.full_name,
        )
        book.available_copies -= 1
        db.session.add(issue)
        db.session.commit()
        flash(f'Book issued. Due date: {due_date.strftime("%d %b %Y")}', 'success')
        return redirect(url_for('library.issues'))

    return render_template('library/issue_book.html', books=books, students=students,
                           today=date.today())


@library_bp.route('/return/<int:issue_id>', methods=['POST'])
@login_required
@role_required('admin', 'librarian', 'receptionist')
def return_book(issue_id):
    issue = BookIssue.query.get_or_404(issue_id)
    return_date = date.today()
    fine = 0
    if issue.due_date and return_date > issue.due_date:
        fine = (return_date - issue.due_date).days * FINE_PER_DAY

    issue.return_date = return_date
    issue.fine_amount = fine
    issue.status = 'returned'
    issue.returned_to = current_user.full_name
    issue.book.available_copies += 1
    db.session.commit()

    if fine > 0:
        flash(f'Book returned. Fine: PKR {fine}', 'warning')
    else:
        flash('Book returned successfully.', 'success')
    return redirect(url_for('library.issues'))
