import os
import click
from datetime import date, timedelta
from app import create_app, db
from app.models import (
    User, Department, Subject, ClassSection, Student, Teacher,
    LibraryBook, FeeStructure, Announcement, AcademicCalendar
)

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
