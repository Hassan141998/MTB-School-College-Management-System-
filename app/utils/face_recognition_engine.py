"""
Face Recognition Engine with graceful fallback
Uses face-recognition + OpenCV when available; stub otherwise.
"""
import os
import base64
import pickle
import io

FACE_RECOGNITION_AVAILABLE = False
try:
    import face_recognition
    import cv2
    import numpy as np
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    pass


class FaceRecognitionEngine:
    def __init__(self, encodings_dir):
        self.encodings_dir = encodings_dir
        os.makedirs(encodings_dir, exist_ok=True)
        self.known_encodings = []
        self.known_ids = []
        self._load_all_encodings()

    def _encoding_path(self, student_id):
        return os.path.join(self.encodings_dir, f'student_{student_id}.pkl')

    def _load_all_encodings(self):
        """Load all stored face encodings into memory"""
        self.known_encodings = []
        self.known_ids = []
        if not FACE_RECOGNITION_AVAILABLE:
            return
        for fname in os.listdir(self.encodings_dir):
            if fname.startswith('student_') and fname.endswith('.pkl'):
                try:
                    sid = int(fname.replace('student_', '').replace('.pkl', ''))
                    with open(os.path.join(self.encodings_dir, fname), 'rb') as f:
                        encodings = pickle.load(f)
                    for enc in encodings:
                        self.known_encodings.append(enc)
                        self.known_ids.append(sid)
                except Exception:
                    pass

    def _b64_to_image(self, b64_string):
        """Convert base64 string to numpy image array"""
        if not FACE_RECOGNITION_AVAILABLE:
            return None
        import numpy as np
        # Strip data URL prefix if present
        if ',' in b64_string:
            b64_string = b64_string.split(',')[1]
        img_bytes = base64.b64decode(b64_string)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            return None
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        return img_rgb

    def register_face(self, student_id, frames_b64):
        """
        Register face from multiple base64 frames.
        Returns (success: bool, message: str)
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return False, 'Face recognition library not installed. Please install face-recognition and opencv-python-headless.'

        encodings = []
        for frame in frames_b64:
            img = self._b64_to_image(frame)
            if img is None:
                continue
            face_locs = face_recognition.face_locations(img)
            if not face_locs:
                continue
            face_encs = face_recognition.face_encodings(img, face_locs)
            if face_encs:
                encodings.append(face_encs[0])

        if len(encodings) < 1:
            return False, 'No faces detected in the provided frames. Please ensure good lighting and face visibility.'

        with open(self._encoding_path(student_id), 'wb') as f:
            pickle.dump(encodings, f)

        # Reload all encodings
        self._load_all_encodings()
        return True, f'Face registered successfully with {len(encodings)} sample(s).'

    def recognize_faces(self, image_b64):
        """
        Recognize faces in a base64 image.
        Returns list of dicts: [{student_id, confidence, name}]
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return []
        if not self.known_encodings:
            return []

        img = self._b64_to_image(image_b64)
        if img is None:
            return []

        face_locs = face_recognition.face_locations(img)
        if not face_locs:
            return []

        face_encs = face_recognition.face_encodings(img, face_locs)
        results = []
        for enc in face_encs:
            distances = face_recognition.face_distance(self.known_encodings, enc)
            if len(distances) == 0:
                continue
            best_idx = int(distances.argmin())
            best_dist = distances[best_idx]
            confidence = round((1 - best_dist) * 100, 1)
            if confidence >= 50:
                results.append({
                    'student_id': self.known_ids[best_idx],
                    'confidence': confidence,
                    'distance': float(best_dist)
                })
        return results

    def process_live_frame(self, frame_b64):
        """Process a single live camera frame (called every 2 seconds)"""
        return self.recognize_faces(frame_b64)

    def is_available(self):
        return FACE_RECOGNITION_AVAILABLE

    def student_has_face(self, student_id):
        return os.path.exists(self._encoding_path(student_id))
