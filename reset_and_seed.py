"""
AIMS-FR (MTB College) - One-Click Database Reset & Seed
Run ONCE to fix login issues: python reset_and_seed.py
This deletes the old database and creates a fresh one with all default data.
"""

import os
import sys


def generate_avatar(name, out_path, size=300):
    """Generate a simple initials-on-colored-circle avatar (like Gmail/Slack
    use for users without a photo). No real people involved, works offline -
    this is deliberately NOT a real photo, since using a real person's
    likeness for a fictional student/teacher record isn't appropriate."""
    from PIL import Image, ImageDraw, ImageFont
    import hashlib

    colors = ['#FF6B35', '#004E89', '#2E7D32', '#6A4C93', '#1976D2',
              '#C2185B', '#F57C00', '#00796B', '#5D4037', '#455A64']
    idx = int(hashlib.md5(name.encode()).hexdigest(), 16) % len(colors)
    bg = colors[idx]

    parts = name.replace('Mr.', '').replace('Ms.', '').replace('Dr.', '').replace('Prof.', '').split()
    initials = ''.join(p[0].upper() for p in parts[:2]) if parts else '?'

    img = Image.new('RGB', (size, size), bg)
    draw = ImageDraw.Draw(img)

    font = None
    for candidate in (
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
        'C:\\Windows\\Fonts\\arialbd.ttf',                        # Windows
        'C:\\Windows\\Fonts\\Arial Bold.ttf',
        '/Library/Fonts/Arial Bold.ttf',                          # macOS
    ):
        try:
            font = ImageFont.truetype(candidate, size // 2)
            break
        except (OSError, IOError):
            continue
    if font is None:
        try:
            font = ImageFont.load_default(size=size // 2)  # Pillow >= 10.1
        except TypeError:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]),
              initials, fill='white', font=font)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert('RGB').save(out_path, 'JPEG', quality=88)


def main():
    # ── Delete old database files ──────────────────────────────────────────
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    db_files = [
        os.path.join(BASE_DIR, 'mtb_school_dev.db'),
        os.path.join(BASE_DIR, 'mtb_school.db'),
        os.path.join(BASE_DIR, 'instance', 'mtb_school_dev.db'),
        os.path.join(BASE_DIR, 'instance', 'mtb_school.db'),
    ]

    print("Removing old database files...")
    for f in db_files:
        if os.path.exists(f):
            os.remove(f)
            print(f"   Deleted: {f}")
        else:
            print(f"   Not found (skip): {f}")

    # ── Import app and seed ─────────────────────────────────────────────────
    from app import create_app, db
    from datetime import date

    app = create_app('development')

    with app.app_context():
        print("\nCreating all database tables...")
        db.create_all()
        print("   Tables created.")

        from app.models import (
            User, Department, ClassSection, Subject, Student, Teacher,
            FeeStructure, LibraryBook, TransportRoute, AcademicCalendar,
            Announcement, SalaryRecord
        )

        print("\nSeeding default data...")

        # ── Users ────────────────────────────────────────────────────────
        users_data = [
            {'username': 'admin',        'email': 'admin@mtbschool.edu.pk',       'role': 'admin',        'password': 'admin123',     'full_name': 'System Administrator'},
            {'username': 'principal',    'email': 'principal@mtbschool.edu.pk',   'role': 'principal',    'password': 'principal123', 'full_name': 'Dr. Muhammad Tariq Baig'},
            {'username': 'hod_science',  'email': 'hod.science@mtbschool.edu.pk', 'role': 'hod',          'password': 'hod123',       'full_name': 'Prof. Asma Khatoon'},
            {'username': 'teacher1',     'email': 'teacher1@mtbschool.edu.pk',    'role': 'teacher',      'password': 'teacher123',   'full_name': 'Mr. Imran Khan'},
            {'username': 'accountant',   'email': 'accounts@mtbschool.edu.pk',    'role': 'accountant',   'password': 'accounts123',  'full_name': 'Ms. Fatima Malik'},
            {'username': 'receptionist', 'email': 'reception@mtbschool.edu.pk',   'role': 'receptionist', 'password': 'reception123', 'full_name': 'Ms. Zara Ahmed'},
            {'username': 'librarian',    'email': 'library@mtbschool.edu.pk',     'role': 'librarian',    'password': 'library123',   'full_name': 'Mr. Khalid Mehmood'},
        ]
        created_users = {}
        for ud in users_data:
            u = User(username=ud['username'], email=ud['email'], role=ud['role'],
                     full_name=ud['full_name'], is_active=True)
            u.set_password(ud['password'])
            db.session.add(u)
            created_users[ud['username']] = u
        db.session.flush()
        print(f"   {len(users_data)} users created")

        # ── Departments ──────────────────────────────────────────────────
        depts_data = [
            ('Science', 'SCI', 'Physics, Chemistry, Biology'),
            ('Mathematics', 'MATH', 'Pure and Applied Mathematics'),
            ('Humanities', 'HUM', 'History, Geography, Urdu, English'),
            ('Commerce', 'COM', 'Accounting, Economics, Business'),
            ('Computer Science', 'CS', 'Programming, Networking, IT'),
        ]
        depts = {}
        for name, code, desc in depts_data:
            d = Department(name=name, code=code, description=desc)
            db.session.add(d)
            depts[code] = d
        db.session.flush()
        print(f"   {len(depts_data)} departments created")

        # ── Subjects ─────────────────────────────────────────────────────
        # FIX: Subject model's column is `credit_hours`, not `credits`.
        subjects_data = [
            ('Physics', 'PHY', 'SCI', 4), ('Chemistry', 'CHM', 'SCI', 4),
            ('Biology', 'BIO', 'SCI', 4), ('Mathematics', 'MTH', 'MATH', 4),
            ('English', 'ENG', 'HUM', 3), ('Urdu', 'URD', 'HUM', 3),
            ('Computer Science', 'CS', 'CS', 3), ('Islamic Studies', 'ISL', 'HUM', 2),
        ]
        for name, code, dept_code, credit_hours in subjects_data:
            db.session.add(Subject(name=name, code=code,
                                    department_id=depts[dept_code].id,
                                    credit_hours=credit_hours))
        db.session.flush()
        print(f"   {len(subjects_data)} subjects created")

        # ── Class Sections ───────────────────────────────────────────────
        # FIX: ClassSection's column is `max_students`, not `capacity`.
        sections = {}
        for cls in ('9', '10', '11', '12'):
            for sec in ('A', 'B'):
                cs = ClassSection(class_name=cls, section=sec, max_students=40)
                db.session.add(cs)
                sections[f'{cls}-{sec}'] = cs
        # ADP (Associate Degree Programme): semesters 1-4.
        # BS (completion): semesters 5-8, continuing from ADP.
        for sem in ('1', '2', '3', '4'):
            cs = ClassSection(class_name='ADP', section=sem, max_students=40)
            db.session.add(cs)
            sections[f'ADP-{sem}'] = cs
        for sem in ('5', '6', '7', '8'):
            cs = ClassSection(class_name='BS', section=sem, max_students=40)
            db.session.add(cs)
            sections[f'BS-{sem}'] = cs
        db.session.flush()
        print("   16 class sections created (8 school + 4 ADP + 4 BS)")

        # ── Teachers ─────────────────────────────────────────────────────
        # FIX: Teacher's column is `join_date`, not `joining_date`.
        # FIX: Teacher has no `is_active` column — it uses `status` (string).
        year = date.today().year
        teachers_raw = [
            ('Mr. Imran Khan',     'imran@mtbschool.edu.pk',    'SCI',  'Physics',           '0300-1234567', 45000),
            ('Ms. Sana Mirza',     'sana@mtbschool.edu.pk',     'MATH', 'Mathematics',        '0301-2345678', 42000),
            ('Mr. Tariq Hussain',  'tariq@mtbschool.edu.pk',    'HUM',  'English Literature', '0302-3456789', 38000),
            ('Ms. Rukhsana Begum', 'rukhsana@mtbschool.edu.pk', 'SCI',  'Chemistry',          '0303-4567890', 44000),
            ('Mr. Zubair Ahmed',   'zubair@mtbschool.edu.pk',   'CS',   'Computer Science',   '0304-5678901', 48000),
            ('Dr. Nadia Farooq',   'nadia@mtbschool.edu.pk',    'CS',   'Software Engineering', '0305-6789012', 52000),
            ('Mr. Kashif Raza',    'kashif@mtbschool.edu.pk',   'COM',  'Accounting',         '0306-7890123', 40000),
            ('Ms. Hina Aslam',     'hina@mtbschool.edu.pk',     'MATH', 'Statistics',         '0307-8901234', 41000),
        ]
        upload_dir = os.path.join(BASE_DIR, 'app', 'static', 'uploads', 'teachers')
        for i, (name, email, dept_code, spec, phone, salary) in enumerate(teachers_raw):
            emp_id = f'EMP-{i+1:04d}'
            photo_rel = f'uploads/teachers/{emp_id}.jpg'
            generate_avatar(name, os.path.join(upload_dir, f'{emp_id}.jpg'))
            t = Teacher(employee_id=emp_id, full_name=name, email=email,
                        phone=phone, department_id=depts[dept_code].id,
                        specialization=spec, join_date=date(year - 2, 1, 15),
                        status='active', photo=photo_rel)
            db.session.add(t)
            db.session.flush()
            # FIX: SalaryRecord.month is a String, not a date; `year` is
            # required and was missing entirely; field is `payment_date`,
            # not `paid_date`.
            db.session.add(SalaryRecord(
                teacher_id=t.id,
                month=date.today().strftime('%B'),
                year=date.today().year,
                basic_salary=salary, allowances=salary * 0.1,
                deductions=salary * 0.05, net_salary=salary * 1.05,
                payment_date=date.today(), status='paid'))
        print(f"   {len(teachers_raw)} teachers created (with generated avatars)")

        # ── Students ─────────────────────────────────────────────────────
        # FIX: Student has no `is_active` column — it uses `status` (string).
        students_raw = [
            ('Ahmed Ali Khan',     'male',   '10-A', 'Ali Hassan Khan',  '0300-9876543', date(2008, 3, 15)),
            ('Fatima Zahra Malik', 'female', '10-A', 'Malik Rashid',     '0301-8765432', date(2008, 7, 22)),
            ('Muhammad Bilal',     'male',   '10-B', 'Muhammad Usman',   '0302-7654321', date(2008, 11, 5)),
            ('Ayesha Siddiqui',    'female', '9-A',  'Siddiqui Farrukh', '0303-6543210', date(2009, 1, 30)),
            ('Hamza Tariq',        'male',   '9-B',  'Tariq Mehmood',    '0304-5432109', date(2009, 5, 18)),
            ('Zainab Hussain',     'female', '11-A', 'Hussain Baksh',    '0305-4321098', date(2007, 9, 12)),
            ('Usman Ghani',        'male',   '11-B', 'Ghani ur Rehman',  '0306-3210987', date(2007, 2, 28)),
            ('Sara Nawaz',         'female', '12-A', 'Nawaz Sharif Ali', '0307-2109876', date(2006, 6, 8)),
            # ADP (semesters 1-4)
            ('Bilal Aslam',        'male',   'ADP-1', 'Aslam Pervaiz',    '0311-1112223', date(2004, 4, 12)),
            ('Mahnoor Iqbal',      'female', 'ADP-2', 'Iqbal Hussain',    '0312-2223334', date(2004, 8, 2)),
            ('Danish Raza',        'male',   'ADP-3', 'Raza Muhammad',    '0313-3334445', date(2003, 12, 19)),
            ('Kiran Shahzadi',     'female', 'ADP-4', 'Shahzad Iqbal',    '0314-4445556', date(2003, 6, 25)),
            # BS (semesters 5-8, continuing from ADP)
            ('Waqas Ahmed',        'male',   'BS-5',  'Ahmed Nawaz',      '0315-5556667', date(2003, 2, 14)),
            ('Areeba Khan',        'female', 'BS-6',  'Khan Zaman',       '0316-6667778', date(2002, 10, 30)),
            ('Talha Farooq',       'male',   'BS-7',  'Farooq Ahmed',     '0317-7778889', date(2002, 5, 9)),
            ('Rimsha Bibi',        'female', 'BS-8',  'Bibi Rehman',      '0318-8889990', date(2002, 1, 22)),
        ]
        student_upload_dir = os.path.join(BASE_DIR, 'app', 'static', 'uploads', 'students')
        for i, (name, gender, section, father, phone, dob) in enumerate(students_raw):
            reg_no = f'MTB-{year}-{i+1:04d}'
            photo_rel = f'uploads/students/{reg_no}.jpg'
            generate_avatar(name, os.path.join(student_upload_dir, f'{reg_no}.jpg'))
            db.session.add(Student(
                reg_no=reg_no, full_name=name, gender=gender,
                date_of_birth=dob, father_name=father, phone=phone,
                class_section_id=sections[section].id,
                admission_date=date(year - 1, 4, 1),
                status='active', blood_group='O+', address='Karachi, Pakistan',
                photo=photo_rel))
        print(f"   {len(students_raw)} students created (with generated avatars)")

        # ── Fee Structures ───────────────────────────────────────────────
        for cls, amount in (('9', 3500), ('10', 4000), ('11', 4500), ('12', 5000)):
            db.session.add(FeeStructure(name=f'Tuition Fee - Class {cls}',
                                        class_name=cls, amount=amount,
                                        fee_type='tuition', frequency='monthly',
                                        is_active=True))
        db.session.add(FeeStructure(name='Admission Fee', class_name=None,
                                    amount=10000, fee_type='other',
                                    frequency='one-time', is_active=True))
        db.session.add(FeeStructure(name='Annual Charges', class_name=None,
                                    amount=5000, fee_type='other',
                                    frequency='annual', is_active=True))
        print("   Fee structures created")

        # ── Library Books ────────────────────────────────────────────────
        for title, author, isbn, cat, copies, pub in (
            ('Physics for Class 10',  'Dr. A. Hameed',  '978-0001', 'Textbook',  10, 'Punjab Textbook Board'),
            ('Chemistry Fundamentals','Prof. M. Aslam',  '978-0002', 'Textbook',  8,  'Oxford University Press'),
            ('English Grammar',       'Wren & Martin',   '978-0003', 'Reference', 15, 'S. Chand Publications'),
            ('Mathematics Plus',      'Dr. R. Khan',     '978-0004', 'Textbook',  12, 'Lahore Education Board'),
            ('Pakistan Studies',      'Ikram Rabbani',   '978-0005', 'Textbook',  20, 'Carvan Publishers'),
        ):
            db.session.add(LibraryBook(title=title, author=author, isbn=isbn,
                                       category=cat, total_copies=copies,
                                       available_copies=copies, publisher=pub,
                                       is_active=True))
        print("   Library books created")

        # ── Transport Routes ─────────────────────────────────────────────
        # FIX: TransportRoute's column is `route_name`, not `name`.
        for name, stops, fee in (
            ('Route A - North Karachi', 'North Nazimabad, Nazimabad, Gulshan', 1500),
            ('Route B - Gulistan',      'Gulistan-e-Jauhar, Malir, Landhi',   1800),
            ('Route C - Clifton',       'Clifton, DHA, Korangi',              2000),
        ):
            db.session.add(TransportRoute(route_name=name, stops=stops,
                                          monthly_fee=fee, is_active=True))

        # ── Academic Calendar ────────────────────────────────────────────
        # FIX: AcademicCalendar has no `is_active` column — it has
        # `is_holiday` instead; only the Eid entry should set it True.
        calendar_data = [
            ('New Academic Year Begins', date(year, 4, 1),   date(year, 4, 1),   'academic', 'First day', False),
            ('First Term Exams',         date(year, 7, 10),  date(year, 7, 20),  'exam',     'First term exams', False),
            ('Eid ul Adha Holiday',      date(year, 6, 15),  date(year, 6, 20),  'holiday',  'Eid holidays', True),
            ('Annual Sports Day',        date(year, 11, 15), date(year, 11, 15), 'event',    'Annual sports gala', False),
            ('Final Term Exams',         date(year, 2, 1),   date(year, 2, 28),  'exam',     'Final term exams', False),
        ]
        for title, start, end, etype, desc, is_holiday in calendar_data:
            db.session.add(AcademicCalendar(title=title, start_date=start, end_date=end,
                                            event_type=etype, description=desc,
                                            is_holiday=is_holiday))

        # ── Announcements ────────────────────────────────────────────────
        # FIX: Announcement has no `publish_date` column. `created_by` is a
        # plain string column (not a foreign key), so store the name, not
        # the numeric user id.
        admin_user = created_users['admin']
        for title, content, target, priority in (
            ('Welcome to New Session 2024-25', 'We warmly welcome all students and staff.', 'all', 'high'),
            ('Fee Submission Deadline', 'Fee must be submitted by the 10th.', 'students', 'normal'),
            ('PTM Scheduled', 'PTM scheduled for next Saturday 9 AM to 1 PM.', 'parents', 'normal'),
        ):
            db.session.add(Announcement(title=title, content=content,
                                        target_audience=target, priority=priority,
                                        created_by=admin_user.full_name,
                                        is_active=True))

        # ── Final commit ─────────────────────────────────────────────────
        try:
            db.session.commit()
            print("\n" + "=" * 50)
            print("DATABASE READY!")
            print("=" * 50)
            print("\nLogin Credentials:")
            print("   admin        / admin123")
            print("   principal    / principal123")
            print("   hod_science  / hod123")
            print("   teacher1     / teacher123")
            print("   accountant   / accounts123")
            print("   receptionist / reception123")
            print("   librarian    / library123")
            print("\nNow run: python run.py")
            print("Then open: http://127.0.0.1:5000")
            print("=" * 50)
        except Exception as e:
            db.session.rollback()
            print(f"\nERROR during commit: {e}")
            sys.exit(1)


if __name__ == "__main__":
    # Guard is essential: without it, merely *importing* this file (e.g. if
    # FLASK_APP accidentally points at it) wipes the database as a side
    # effect. Only running `python reset_and_seed.py` directly triggers this.
    main()