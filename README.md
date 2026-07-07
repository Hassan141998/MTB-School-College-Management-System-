# MTB School & College Management System

A comprehensive, full-featured school management system built with Flask, featuring AI-powered face recognition attendance, complete fee management, examination system, library management, and detailed analytics.

---

## 🚀 Features

### Core Modules
| Module | Description |
|---|---|
| **Dashboard** | Live stats, Chart.js analytics, announcements, quick actions |
| **Students** | Full CRUD, photo upload, auto Reg No (MTB-YYYY-XXXX), Excel export |
| **Teachers** | Staff profiles, salary records, attendance tracking |
| **Fee Management** | Structures, payments, PDF receipts, defaulter tracking |
| **Attendance** | Bulk mark by class, leave application workflow, reports |
| **Face Recognition** | AI webcam registration, photo/live mode attendance |
| **Exams & Marks** | Exam creation, subject-wise marks entry, result cards, PDF |
| **Library** | Book inventory, issue/return, fine calculation (PKR 10/day) |
| **Reports** | Performance ranking, financial summary, attendance analysis |
| **Settings** | Departments, subjects, classes, users, announcements, calendar |

### Technical Highlights
- **7 role-based access levels**: Admin, Principal, HOD, Teacher, Accountant, Receptionist, Librarian
- **AI Face Recognition**: `face_recognition` + `dlib` with 5-sample registration, 0.6 tolerance
- **PDF Generation**: ReportLab fee receipts & result cards with school branding
- **Excel Exports**: openpyxl with orange-header formatting for all reports
- **Chart.js Integration**: Line, Bar, Doughnut, Radar, and dual-axis charts
- **Real-time UI**: Toast notifications, modal confirmations, auto-submit filters
- **Responsive Design**: Custom CSS with 36 sections, mobile-first breakpoints
- **Security**: Flask-Login, Werkzeug password hashing, role-gated routes

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- pip
- (Optional) CMake + build tools for face recognition

### Quick Start

```bash
# 1. Clone the repository
https://github.com/Hassan141998/MTB-School-College-Management-System-.git
# 2. Create virtual environment
python -m venv venv
source venv/bin/activate       # Linux/Mac
# venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Initialize database & seed demo data
python run.py seed-users
python run.py seed-data

# 6. Run development server
python run.py
```

Visit `http://localhost:5000` and login with **admin / admin123**

---

## 🔐 Default Login Accounts

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Principal | `principal` | `principal123` |
| Teacher | `teacher1` | `teacher123` |
| Accountant | `accountant` | `accounts123` |
| Receptionist | `receptionist` | `reception123` |
| Librarian | `librarian` | `library123` |

> ⚠️ **Change all passwords immediately in production!**

---

## 🧠 Face Recognition Setup

Face recognition requires additional system dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install cmake libopenblas-dev liblapack-dev

# Then install Python packages
pip install face_recognition dlib numpy

# Uncomment in requirements.txt and reinstall
```

Without face recognition, the system runs in **simulation mode** — all other features work normally.

---

## 📁 Project Structure

```
mtb_school/
├── run.py                      # App entry point, CLI seed commands
├── config.py                   # Configuration classes (Dev/Prod/Test)
├── wsgi.py                     # Production WSGI entry point
├── requirements.txt
├── .env.example
│
└── app/
    ├── __init__.py             # App factory, blueprints, Jinja2 filters
    ├── models.py               # 26 SQLAlchemy models
    │
    ├── routes/                 # 11 blueprint modules
    │   ├── auth.py             # Login, logout, profile
    │   ├── dashboard.py        # Main dashboard + Chart.js APIs
    │   ├── students.py         # Student CRUD + Excel export
    │   ├── teachers.py         # Teacher management + salary
    │   ├── fees.py             # Payments + PDF receipts
    │   ├── attendance.py       # Bulk mark + leave workflow
    │   ├── face_recognition.py # AI webcam + live mode
    │   ├── exams.py            # Exams + marks + results
    │   ├── library.py          # Books + issue/return + fines
    │   ├── reports.py          # Analytics + Excel exports
    │   └── settings.py         # System configuration
    │
    ├── utils/
    │   ├── helpers.py          # ID generators, grade calc, pagination
    │   ├── decorators.py       # Role-based access control
    │   ├── face_recognition_engine.py  # AI face matching engine
    │   └── pdf_generator.py    # ReportLab PDF generation
    │
    ├── static/
    │   ├── css/style.css       # 2,813 lines, 36 sections
    │   ├── js/
    │   │   ├── main.js         # 13 UI modules (sidebar, modals, forms…)
    │   │   ├── dashboard.js    # Chart.js chart definitions
    │   │   └── face-recognition.js  # Webcam, capture, live mode
    │   └── uploads/            # Student/teacher photos (gitignored)
    │
    └── templates/
        ├── base.html           # Master layout with role-gated sidebar
        ├── auth/               # login, profile, change_password
        ├── dashboard/          # index
        ├── students/           # index, add, view, edit
        ├── teachers/           # index, view, add, edit, attendance, salary
        ├── fees/               # index, collect, receipt, defaulters, structure
        ├── attendance/         # index, mark, report, leave_list, apply_leave
        ├── face_recognition/   # index, register, mark, live
        ├── exams/              # index, add, view, enter_marks, results, result_card
        ├── library/            # index, add_book, issue, issued_list
        ├── reports/            # index, performance, financial, attendance
        ├── settings/           # index, departments, subjects, classes, users…
        └── errors/             # 403, 404, 500
```

---

## 🗃️ Database Models (26 total)

`User`, `Student`, `Teacher`, `Department`, `Subject`, `ClassSection`,
`Attendance`, `TeacherAttendance`, `LeaveApplication`,
`FeeStructure`, `FeePayment`,
`Exam`, `ExamSubject`, `ExamMark`,
`Book`, `BookIssue`,
`SalaryRecord`, `FaceEncoding`,
`Announcement`, `CalendarEvent`,
`ActivityLog`, `Notification`

---

## 📊 API Endpoints (AJAX)

| Endpoint | Method | Description |
|---|---|---|
| `/api/chart/enrollment` | GET | Last 6-month enrollment chart data |
| `/api/chart/attendance` | GET | Last 7-day attendance chart data |
| `/api/chart/fees` | GET | Last 6-month fee collection data |
| `/api/chart/gender` | GET | Gender distribution data |
| `/face/api/register` | POST | Register face (5 base64 frames) |
| `/face/api/mark` | POST | Mark attendance from photo |
| `/face/api/live-frame` | POST | Process live camera frame |
| `/face/api/status` | GET | Face recognition engine status |
| `/fees/api/structure/<id>` | GET | Fee structure amount for auto-fill |
| `/attendance/api/summary` | GET | Daily attendance summary |

---

## 🌐 Production Deployment

### Gunicorn (recommended)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

### Nginx config
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /var/www/mtb_school/app/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Vercel (serverless)
```bash
npm i -g vercel
vercel --prod
```

### Environment Variables for Production
```bash
SECRET_KEY=<strong-random-64-char-key>
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host/db
```

---

## 🎨 Customization

### Brand Colors (CSS Variables)
```css
--primary:   #FF6B35;   /* Orange — primary actions */
--secondary: #004E89;   /* Navy blue — secondary elements */
--accent:    #F7B801;   /* Yellow — highlights */
```
Edit in `app/static/css/style.css` Section 1.

### School Name
Set `SCHOOL_NAME` in `.env` or `config.py`.

### Roles
Add/modify roles in `app/utils/decorators.py` and `app/routes/` route guards.

---

## 📝 License

MIT License — free to use, modify, and distribute.

---

## 🏫 Built for

MTB School & College, Pakistan — School Management System  
Stack: Flask · SQLAlchemy · SQLite/PostgreSQL · Chart.js · Bootstrap Icons · ReportLab
