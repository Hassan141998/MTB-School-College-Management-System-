import os
from flask import (Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for)
from flask_login import login_required, current_user
from app.models import Student, Attendance, ClassSection
from app.utils.decorators import staff_required
from app import db
from datetime import date

face_bp = Blueprint('face', __name__, template_folder='../templates')


def get_engine():
    from app.utils.face_recognition_engine import FaceRecognitionEngine
    encodings_dir = os.path.join(current_app.static_folder, 'face_encodings')
    return FaceRecognitionEngine(encodings_dir)


@face_bp.route('/')
@login_required
def index():
    return redirect(url_for('face.register'))


@face_bp.route('/register')
@login_required
@staff_required
def register():
    students = Student.query.filter_by(status='active').order_by(Student.full_name).all()
    engine = get_engine()
    available = engine.is_available()
    return render_template('face_recognition/register.html', students=students, available=available)


@face_bp.route('/register/api', methods=['POST'])
@login_required
@staff_required
def register_api():
    data = request.get_json()
    student_id = data.get('student_id')
    frames = data.get('frames', [])

    if not student_id or not frames:
        return jsonify({'success': False, 'message': 'Missing student_id or frames.'})

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found.'})

    engine = get_engine()
    if not engine.is_available():
        # Stub: mark as registered without actual encoding
        student.has_face_registered = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'Face registration simulated (library not available).'})

    success, message = engine.register_face(student_id, frames)
    if success:
        student.has_face_registered = True
        db.session.commit()
    return jsonify({'success': success, 'message': message})


@face_bp.route('/mark')
@login_required
@staff_required
def mark():
    classes = ClassSection.query.filter_by(is_active=True).all()
    engine = get_engine()
    available = engine.is_available()
    return render_template('face_recognition/mark.html', classes=classes, available=available)


@face_bp.route('/mark/api', methods=['POST'])
@login_required
@staff_required
def mark_api():
    data = request.get_json()
    image_b64 = data.get('image')
    if not image_b64:
        return jsonify({'success': False, 'message': 'No image provided'})

    engine = get_engine()
    if not engine.is_available():
        return jsonify({'success': False, 'message': 'Face recognition library not available.',
                        'recognized': []})

    results = engine.recognize_faces(image_b64)
    marked = []
    today = date.today()

    for r in results:
        sid = r['student_id']
        student = Student.query.get(sid)
        if not student:
            continue
        existing = Attendance.query.filter_by(student_id=sid, date=today).first()
        if not existing:
            att = Attendance(
                student_id=sid,
                class_section_id=student.class_section_id,
                date=today,
                status='present',
                marked_by='Face Recognition System',
                method='face_recognition',
                confidence=r['confidence'],
            )
            db.session.add(att)
            marked.append({'name': student.full_name, 'confidence': r['confidence'],
                           'reg_no': student.reg_no})
    db.session.commit()
    return jsonify({'success': True, 'marked': marked, 'recognized': len(results)})


@face_bp.route('/live')
@login_required
@staff_required
def live():
    engine = get_engine()
    available = engine.is_available()
    return render_template('face_recognition/live.html', available=available)


@face_bp.route('/api/live-frame', methods=['POST'])
@login_required
@staff_required
def live_frame():
    """Process live camera frame every 2 seconds"""
    data = request.get_json()
    frame_b64 = data.get('frame')
    if not frame_b64:
        return jsonify({'results': []})

    engine = get_engine()
    if not engine.is_available():
        return jsonify({'results': [], 'available': False})

    results = engine.process_live_frame(frame_b64)
    today = date.today()
    response_results = []

    for r in results:
        sid = r['student_id']
        student = Student.query.get(sid)
        if not student:
            continue
        existing = Attendance.query.filter_by(student_id=sid, date=today).first()
        already_marked = existing is not None
        if not already_marked:
            att = Attendance(
                student_id=sid,
                class_section_id=student.class_section_id,
                date=today,
                status='present',
                marked_by='Face Recognition System',
                method='face_recognition',
                confidence=r['confidence'],
            )
            db.session.add(att)
        response_results.append({
            'name': student.full_name,
            'reg_no': student.reg_no,
            'confidence': r['confidence'],
            'already_marked': already_marked,
        })

    db.session.commit()
    return jsonify({'results': response_results, 'available': True})
