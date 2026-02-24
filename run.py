import os
import click
from datetime import date, timedelta
from app import create_app, db
from app.models import (
    User, Department, Subject, ClassSection, Student, Teacher,
    LibraryBook, FeeStructure, Announcement, AcademicCalendar
)

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Student=Student, Teacher=Teacher)

@app.cli.command("seed-db")
def seed_db():
    """Seed the database with initial demo data."""
    click.echo("Dropping all tables and recreating...")
    db.drop_all()
    db.create_all()

    click.echo("Seeding users...")
    admin = User(username='admin', email='admin@mtb.edu.pk', full_name='System Administrator', role='admin')
    admin.set_password('admin123')
    
    teacher = User(username='teacher1', email='teacher@mtb.edu.pk', full_name='Demo Teacher', role='teacher')
    teacher.set_password('teacher123')
    
    staff = User(username='staff1', email='staff@mtb.edu.pk', full_name='Accountant', role='staff')
    staff.set_password('staff123')
    
    db.session.add_all([admin, teacher, staff])

    click.echo("Seeding departments, classes, subjects...")
    # Departments
    sci = Department(name='Science', code='SCI')
    arts = Department(name='Arts', code='ART')
    com = Department(name='Computer Science', code='CS')
    db.session.add_all([sci, arts, com])
    
    # Classes
    c9 = ClassSection(class_name='9th', section='A', max_students=40)
    c10 = ClassSection(class_name='10th', section='A', max_students=40)
    db.session.add_all([c9, c10])
    
    # Subjects
    s1 = Subject(name='Mathematics', code='MATH-101', department=sci)
    s2 = Subject(name='Physics', code='PHY-101', department=sci)
    s3 = Subject(name='Computer Science', code='CS-101', department=com)
    s4 = Subject(name='English', code='ENG-101', department=arts)
    db.session.add_all([s1, s2, s3, s4])
    db.session.commit()

    click.echo("Seeding demo students and teachers...")
    t1 = Teacher(employee_id='T-1001', full_name='Asiya Khan', department=sci, designation='Senior Teacher', basic_salary=65000)
    t2 = Teacher(employee_id='T-1002', full_name='Usman Ali', department=com, designation='Lecturer', basic_salary=55000)
    db.session.add_all([t1, t2])
    
    st1 = Student(reg_no='MTB-24-001', full_name='Ahmed Raza', class_section=c10, status='active')
    st2 = Student(reg_no='MTB-24-002', full_name='Fatima Noor', class_section=c10, status='active')
    st3 = Student(reg_no='MTB-24-003', full_name='Bilal Hassan', class_section=c9, status='active')
    db.session.add_all([st1, st2, st3])
    db.session.commit()

    click.echo("Seeding fee structures and announcements...")
    fs1 = FeeStructure(name='Monthly Tuition', amount=2500, fee_type='tuition')
    fs2 = FeeStructure(name='Annual Charges', amount=5000, fee_type='other')
    db.session.add_all([fs1, fs2])
    
    ann = Announcement(title='Welcome to MTB School Portal', content='The new portal is now live with face recognition attendance.', priority='high', target_audience='all')
    db.session.add(ann)
    
    cal = AcademicCalendar(title='Summer Vacation', start_date=date.today() + timedelta(days=30), end_date=date.today() + timedelta(days=90), event_type='other', is_holiday=True)
    db.session.add(cal)
    db.session.commit()

    click.echo("✅ Database seeded successfully!")
    click.echo("Login Credentials:")
    click.echo("Admin: admin / admin123")
    click.echo("Teacher: teacher1 / teacher123")
    click.echo("Staff: staff1 / staff123")

if __name__ == '__main__':
    app.run(debug=True)
