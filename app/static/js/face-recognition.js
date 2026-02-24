/* =====================================================
   MTB School & College — face-recognition.js
   Webcam capture, base64 encoding, register & recognize APIs
   ===================================================== */

'use strict';

class FaceRecognitionApp {
    constructor(options = {}) {
        this.mode = options.mode || 'register'; // 'register' | 'mark' | 'live'
        this.video = document.getElementById('camera-video');
        this.canvas = document.getElementById('camera-canvas');
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
        this.stream = null;
        this.isRunning = false;
        this.samples = [];
        this.maxSamples = 5;
        this.liveInterval = null;
        this.processInterval = 2000; // ms between live frame processing
    }

    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
                audio: false
            });
            if (this.video) {
                this.video.srcObject = this.stream;
                await this.video.play();
                this.isRunning = true;
                this.updateStatus('active', 'Camera Active');
                return true;
            }
        } catch (err) {
            console.error('Camera error:', err);
            this.updateStatus('error', 'Camera Access Denied');
            this.showError('Could not access camera. Please allow camera permissions.');
            return false;
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(t => t.stop());
            this.stream = null;
        }
        this.isRunning = false;
        if (this.liveInterval) { clearInterval(this.liveInterval); this.liveInterval = null; }
        this.updateStatus('inactive', 'Camera Off');
    }

    captureFrame() {
        if (!this.video || !this.canvas || !this.ctx) return null;
        const { videoWidth: w, videoHeight: h } = this.video;
        this.canvas.width = w || 640;
        this.canvas.height = h || 480;
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        return this.canvas.toDataURL('image/jpeg', 0.85);
    }

    updateStatus(state, text) {
        const dot = document.querySelector('.status-dot');
        const label = document.querySelector('.camera-status span');
        if (dot) dot.className = `status-dot ${state === 'active' ? 'active' : state === 'processing' ? 'processing' : ''}`;
        if (label) label.textContent = text;
    }

    showError(msg) {
        if (window.showToast) window.showToast(msg, 'danger');
        else alert(msg);
    }

    // ─── REGISTER MODE ─────────────────────────────────

    async captureSample() {
        if (!this.isRunning) return;
        if (this.samples.length >= this.maxSamples) {
            this.showError('Maximum 5 samples already captured.');
            return;
        }

        const frame = this.captureFrame();
        if (!frame) return;

        const idx = this.samples.length;
        this.samples.push(frame);

        // Update thumbnail
        const thumb = document.getElementById(`sample-${idx}`);
        if (thumb) {
            const img = document.createElement('img');
            img.src = frame;
            thumb.innerHTML = '';
            thumb.appendChild(img);
            thumb.classList.add('captured');
        }

        // Update progress
        const pills = document.querySelectorAll('.step-pill');
        pills.forEach((p, i) => {
            if (i < this.samples.length) p.classList.add('done');
            if (i === this.samples.length) p.classList.add('active');
        });

        const countEl = document.getElementById('sample-count');
        if (countEl) countEl.textContent = this.samples.length;

        if (this.samples.length >= this.maxSamples) {
            document.getElementById('capture-btn')?.setAttribute('disabled', 'true');
            document.getElementById('register-btn')?.removeAttribute('disabled');
            if (window.showToast) window.showToast('5 samples captured! Click "Register Face" to save.', 'success');
        }
    }

    async registerFace(studentId) {
        if (this.samples.length < 1) {
            this.showError('Please capture at least 1 sample first.');
            return;
        }

        const btn = document.getElementById('register-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Registering...';
        }

        try {
            const res = await fetch('/face/register/api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_id: studentId, frames: this.samples })
            });
            const data = await res.json();
            if (data.success) {
                if (window.showToast) window.showToast(data.message, 'success');
                this.samples = [];
                document.querySelectorAll('.step-pill').forEach(p => { p.classList.remove('done', 'active'); });
                document.querySelectorAll('.sample-thumb').forEach((t, i) => {
                    t.innerHTML = String(i + 1);
                    t.classList.remove('captured');
                });
                if (document.getElementById('sample-count')) document.getElementById('sample-count').textContent = '0';
            } else {
                if (window.showToast) window.showToast(data.message, 'danger');
            }
        } catch (err) {
            this.showError('Registration failed. Please try again.');
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '🔒 Register Face'; }
        }
    }

    // ─── MARK MODE ─────────────────────────────────────

    async recognizeFace() {
        if (!this.isRunning) return;
        const frame = this.captureFrame();
        if (!frame) return;

        this.updateStatus('processing', 'Processing...');
        const btn = document.getElementById('recognize-btn');
        if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Recognizing...'; }

        try {
            const res = await fetch('/face/mark/api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: frame })
            });
            const data = await res.json();
            this.updateStatus('active', 'Camera Active');

            const results = data.marked || [];
            const list = document.getElementById('recognition-results');
            if (list) {
                if (results.length === 0) {
                    list.innerHTML = '<div class="empty-state" style="padding:24px"><div class="empty-state-icon">🔍</div><div>No faces recognized</div></div>';
                } else {
                    list.innerHTML = results.map(r => `
            <div class="live-result-item">
              <div class="cell-avatar">${r.name.charAt(0)}</div>
              <div>
                <div class="live-result-name">${r.name}</div>
                <div class="live-result-meta">${r.reg_no} — Marked Present ✓</div>
              </div>
              <div class="live-result-conf">${r.confidence}%</div>
            </div>
          `).join('');
                }
            }
            if (results.length > 0 && window.showToast) {
                window.showToast(`${results.length} student(s) marked present.`, 'success');
            }
        } catch (err) {
            this.updateStatus('active', 'Camera Active');
            this.showError('Recognition failed. Please try again.');
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '📸 Capture & Recognize'; }
        }
    }

    // ─── LIVE MODE ─────────────────────────────────────

    startLive() {
        if (!this.isRunning) return;
        if (this.liveInterval) clearInterval(this.liveInterval);
        document.getElementById('live-status')?.classList.remove('d-none');
        this.liveInterval = setInterval(() => this.processLiveFrame(), this.processInterval);
        this.updateStatus('processing', 'Live • Processing');
    }

    stopLive() {
        if (this.liveInterval) { clearInterval(this.liveInterval); this.liveInterval = null; }
        document.getElementById('live-status')?.classList.add('d-none');
        this.updateStatus('active', 'Camera Active');
    }

    async processLiveFrame() {
        const frame = this.captureFrame();
        if (!frame) return;
        try {
            const res = await fetch('/face/api/live-frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ frame })
            });
            const data = await res.json();
            const results = data.results || [];
            const list = document.getElementById('live-results');
            if (list && results.length > 0) {
                results.forEach(r => {
                    if (!r.already_marked) {
                        const item = document.createElement('div');
                        item.className = 'live-result-item';
                        item.innerHTML = `
              <div class="cell-avatar">${r.name.charAt(0)}</div>
              <div>
                <div class="live-result-name">${r.name}</div>
                <div class="live-result-meta">${r.reg_no} — ${new Date().toLocaleTimeString()}</div>
              </div>
              <div class="live-result-conf">${r.confidence}%</div>
            `;
                        list.prepend(item);
                        if (window.showToast) window.showToast(`${r.name} marked present (${r.confidence}%)`, 'success', 2500);
                    }
                });
            }
            // Update counter
            const counter = document.getElementById('marked-count');
            if (counter) counter.textContent = parseInt(counter.textContent || 0) + results.filter(r => !r.already_marked).length;
        } catch (err) {
            // silently fail for live frames
        }
    }
}

// ─── Init on DOMContentLoaded ─────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    const mode = document.body.dataset.faceMode;
    if (!mode) return;

    const app = new FaceRecognitionApp({ mode });
    window.faceApp = app;

    // Start camera button
    const startBtn = document.getElementById('start-camera-btn');
    const stopBtn = document.getElementById('stop-camera-btn');

    if (startBtn) {
        startBtn.addEventListener('click', async () => {
            const ok = await app.startCamera();
            if (ok) {
                startBtn.style.display = 'none';
                if (stopBtn) stopBtn.style.display = 'inline-flex';
                document.querySelector('.camera-placeholder')?.remove();
                if (mode === 'live') {
                    setTimeout(() => app.startLive(), 1000);
                }
            }
        });
    }

    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            app.stopCamera();
            startBtn.style.display = 'inline-flex';
            stopBtn.style.display = 'none';
        });
    }

    // Capture sample button (register mode)
    document.getElementById('capture-btn')?.addEventListener('click', () => app.captureSample());

    // Register button
    document.getElementById('register-btn')?.addEventListener('click', () => {
        const sid = document.getElementById('student-id-input')?.value;
        if (!sid) { window.showToast && window.showToast('Please select a student first.', 'warning'); return; }
        app.registerFace(sid);
    });

    // Recognize button (mark mode)
    document.getElementById('recognize-btn')?.addEventListener('click', () => app.recognizeFace());
});
