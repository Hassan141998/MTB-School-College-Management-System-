from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date


# ─── User ───────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='student')
    # Roles: admin, principal, hod, teacher, accountant, receptionist, librarian, student, parent
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles):
        return self.role in roles

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── Department ──────────────────────────────────────────────────────────────

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    hod_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subjects = db.relationship('Subject', backref='department', lazy='dynamic')
    teachers = db.relationship('Teacher', backref='department', lazy='dynamic')


# ─── Subject ─────────────────────────────────────────────────────────────────

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    credit_hours = db.Column(db.Integer, default=3)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    timetable_entries = db.relationship('Timetable', backref='subject', lazy='dynamic')


# ─── Class / Section ─────────────────────────────────────────────────────────

class ClassSection(db.Model):
    __tablename__ = 'class_sections'
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False, default='2024-25')
    max_students = db.Column(db.Integer, default=40)
    is_active = db.Column(db.Boolean, default=True)

    students = db.relationship('Student', backref='class_section', lazy='dynamic')
    timetable_entries = db.relationship('Timetable', backref='class_section', lazy='dynamic')
    attendances = db.relationship('Attendance', backref='class_section', lazy='dynamic')

    @property
    def display_name(self):
        return f"{self.class_name} - {self.section}"


# ─── Timetable ───────────────────────────────────────────────────────────────

class Timetable(db.Model):
    __tablename__ = 'timetable'
    id = db.Column(db.Integer, primary_key=True)
    class_section_id = db.Column(db.Integer, db.ForeignKey('class_sections.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    day_of_week = db.Column(db.String(10), nullable=False)  # Monday-Saturday
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    room = db.Column(db.String(20))


# ─── Student ─────────────────────────────────────────────────────────────────

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.String(20), unique=True, nullable=False)  # MTB-YYYY-XXXX
    full_name = db.Column(db.String(120), nullable=False)
    father_name = db.Column(db.String(120))
    mother_name = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    parent_phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    city = db.Column(db.String(60))
    cnic = db.Column(db.String(20))
    blood_group = db.Column(db.String(5))
    religion = db.Column(db.String(30))
    photo = db.Column(db.String(200))
    class_section_id = db.Column(db.Integer, db.ForeignKey('class_sections.id'))
    admission_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='active')  # active, inactive, transferred, graduated
    has_face_registered = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attendances = db.relationship('Attendance', backref='student', lazy='dynamic')
    fee_payments = db.relationship('FeePayment', backref='student', lazy='dynamic')
    marks = db.relationship('Mark', backref='student', lazy='dynamic')
    book_issues = db.relationship('BookIssue', backref='student', lazy='dynamic')
    transport = db.relationship('StudentTransport', backref='student', uselist=False)
    achievements = db.relationship('Achievement', backref='student', lazy='dynamic')
    disciplinary = db.relationship('DisciplinaryRecord', backref='student', lazy='dynamic')
    medical = db.relationship('MedicalRecord', backref='student', uselist=False)
    leave_applications = db.relationship('LeaveApplication', backref='student', lazy='dynamic')

    def __repr__(self):
        return f'<Student {self.reg_no} - {self.full_name}>'


# ─── Teacher ─────────────────────────────────────────────────────────────────

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    father_name = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    cnic = db.Column(db.String(20))
    qualification = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    designation = db.Column(db.String(60), default='Teacher')
    basic_salary = db.Column(db.Float, default=0)
    join_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='active')
    photo = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    salary_records = db.relationship('SalaryRecord', backref='teacher', lazy='dynamic')
    timetable_entries = db.relationship('Timetable', backref='teacher', lazy='dynamic')
    teacher_attendances = db.relationship('TeacherAttendance', backref='teacher', lazy='dynamic')

    def __repr__(self):
        return f'<Teacher {self.employee_id} - {self.full_name}>'


# ─── Salary Record ───────────────────────────────────────────────────────────

class SalaryRecord(db.Model):
    __tablename__ = 'salary_records'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    month = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    basic_salary = db.Column(db.Float, default=0)
    allowances = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)
    net_salary = db.Column(db.Float, default=0)
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(30), default='cash')
    status = db.Column(db.String(20), default='pending')  # pending, paid
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Student Attendance ──────────────────────────────────────────────────────

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_section_id = db.Column(db.Integer, db.ForeignKey('class_sections.id'))
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(10), nullable=False, default='present')  # present, absent, late, leave
    marked_by = db.Column(db.String(100))
    method = db.Column(db.String(30), default='manual')  # manual, face_recognition
    confidence = db.Column(db.Float)  # For face recognition
    remarks = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='unique_student_date'),)


# ─── Teacher Attendance ──────────────────────────────────────────────────────

class TeacherAttendance(db.Model):
    __tablename__ = 'teacher_attendance'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(10), nullable=False, default='present')
    check_in = db.Column(db.String(10))
    check_out = db.Column(db.String(10))
    marked_by = db.Column(db.String(100))
    remarks = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('teacher_id', 'date', name='unique_teacher_date'),)


# ─── Leave Application ───────────────────────────────────────────────────────

class LeaveApplication(db.Model):
    __tablename__ = 'leave_applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    leave_type = db.Column(db.String(30), default='sick')  # sick, casual, emergency, other
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approved_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Fee Structure ───────────────────────────────────────────────────────────

class FeeStructure(db.Model):
    __tablename__ = 'fee_structure'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50))
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), default='monthly')  # monthly, quarterly, annual, one-time
    fee_type = db.Column(db.String(30), default='tuition')  # tuition, exam, library, transport, uniform, other
    academic_year = db.Column(db.String(20), default='2024-25')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship('FeePayment', backref='fee_structure', lazy='dynamic')


# ─── Fee Payment ─────────────────────────────────────────────────────────────

class FeePayment(db.Model):
    __tablename__ = 'fee_payments'
    id = db.Column(db.Integer, primary_key=True)
    receipt_no = db.Column(db.String(30), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    fee_structure_id = db.Column(db.Integer, db.ForeignKey('fee_structure.id'))
    amount = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    fine = db.Column(db.Float, default=0)
    total_paid = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, default=date.today)
    month = db.Column(db.String(20))
    year = db.Column(db.Integer)
    payment_method = db.Column(db.String(30), default='cash')  # cash, bank, online
    bank_reference = db.Column(db.String(100))
    collected_by = db.Column(db.String(100))
    status = db.Column(db.String(20), default='paid')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Exam ────────────────────────────────────────────────────────────────────

class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    exam_type = db.Column(db.String(30), default='mid-term')  # mid-term, final, unit-test, other
    class_section_id = db.Column(db.Integer, db.ForeignKey('class_sections.id'))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    academic_year = db.Column(db.String(20), default='2024-25')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exam_subjects = db.relationship('ExamSubject', backref='exam', lazy='dynamic')
    marks = db.relationship('Mark', backref='exam', lazy='dynamic')


# ─── Exam Subject ─────────────────────────────────────────────────────────────

class ExamSubject(db.Model):
    __tablename__ = 'exam_subjects'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    total_marks = db.Column(db.Integer, default=100)
    passing_marks = db.Column(db.Integer, default=33)
    exam_date = db.Column(db.Date)
    exam_time = db.Column(db.String(20))

    subject = db.relationship('Subject', backref='exam_subjects')


# ─── Mark ────────────────────────────────────────────────────────────────────

class Mark(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    obtained_marks = db.Column(db.Float, default=0)
    total_marks = db.Column(db.Integer, default=100)
    grade = db.Column(db.String(5))
    remarks = db.Column(db.String(100))
    entered_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject = db.relationship('Subject', backref='marks')


# ─── Library Book ─────────────────────────────────────────────────────────────

class LibraryBook(db.Model):
    __tablename__ = 'library_books'
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(30), unique=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150))
    publisher = db.Column(db.String(150))
    category = db.Column(db.String(60))
    edition = db.Column(db.String(20))
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    price = db.Column(db.Float)
    location = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    issues = db.relationship('BookIssue', backref='book', lazy='dynamic')


# ─── Book Issue ───────────────────────────────────────────────────────────────

class BookIssue(db.Model):
    __tablename__ = 'book_issues'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('library_books.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    issue_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    fine_amount = db.Column(db.Float, default=0)
    fine_paid = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='issued')  # issued, returned, overdue
    issued_by = db.Column(db.String(100))
    returned_to = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def calculate_fine(self):
        if self.status == 'issued' and self.due_date and self.due_date < date.today():
            days_overdue = (date.today() - self.due_date).days
            return days_overdue * 10  # PKR 10/day
        return 0


# ─── Transport Route ─────────────────────────────────────────────────────────

class TransportRoute(db.Model):
    __tablename__ = 'transport_routes'
    id = db.Column(db.Integer, primary_key=True)
    route_name = db.Column(db.String(100), nullable=False)
    route_code = db.Column(db.String(20), unique=True)
    stops = db.Column(db.Text)
    driver_name = db.Column(db.String(100))
    driver_phone = db.Column(db.String(20))
    vehicle_no = db.Column(db.String(20))
    monthly_fee = db.Column(db.Float, default=0)
    is_active = db.Column(db.Boolean, default=True)

    students = db.relationship('StudentTransport', backref='route', lazy='dynamic')


# ─── Student Transport ───────────────────────────────────────────────────────

class StudentTransport(db.Model):
    __tablename__ = 'student_transport'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('transport_routes.id'), nullable=False)
    pickup_stop = db.Column(db.String(100))
    start_date = db.Column(db.Date, default=date.today)
    is_active = db.Column(db.Boolean, default=True)


# ─── Achievement ─────────────────────────────────────────────────────────────

class Achievement(db.Model):
    __tablename__ = 'achievements'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(60))  # academic, sports, arts, other
    description = db.Column(db.Text)
    award_date = db.Column(db.Date)
    awarded_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Disciplinary Record ──────────────────────────────────────────────────────

class DisciplinaryRecord(db.Model):
    __tablename__ = 'disciplinary_records'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    incident_date = db.Column(db.Date, default=date.today)
    incident_type = db.Column(db.String(60))
    description = db.Column(db.Text)
    action_taken = db.Column(db.Text)
    reported_by = db.Column(db.String(100))
    severity = db.Column(db.String(20), default='minor')  # minor, moderate, severe
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Medical Record ───────────────────────────────────────────────────────────

class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    blood_group = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    medical_conditions = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    doctor_name = db.Column(db.String(100))
    doctor_phone = db.Column(db.String(20))
    last_checkup = db.Column(db.Date)
    notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─── Announcement ────────────────────────────────────────────────────────────

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    target_audience = db.Column(db.String(30), default='all')  # all, students, teachers, parents
    priority = db.Column(db.String(10), default='normal')  # low, normal, high, urgent
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(100))
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Academic Calendar ────────────────────────────────────────────────────────

class AcademicCalendar(db.Model):
    __tablename__ = 'academic_calendar'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(30), default='event')  # holiday, exam, event, meeting
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)
    is_holiday = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Activity Log ─────────────────────────────────────────────────────────────

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(200), nullable=False)
    module = db.Column(db.String(50))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
