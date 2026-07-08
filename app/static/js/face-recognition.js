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

    // Draws a bounding box + name/class label around every detected face.
    // Must be called AFTER captureFrame() (which draws the still frame the
    // face locations correspond to) - draws directly on top of that same
    // canvas so box coordinates line up pixel-for-pixel with what the
    // server analyzed.
    drawDetections(detections) {
        if (!this.ctx || !detections || !detections.length) return;
        detections.forEach(d => {
            const loc = d.location;
            if (!loc) return;
            const { top, right, bottom, left } = loc;
            const w = right - left;
            const h = bottom - top;
            const color = d.known ? '#22C55E' : '#EF4444';
            const label = d.known
                ? `${d.name}${d.class_name ? ' · ' + d.class_name : ''}${d.confidence ? ' (' + d.confidence + '%)' : ''}`
                : 'Unknown';

            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = 3;
            this.ctx.strokeRect(left, top, w, h);

            this.ctx.font = 'bold 16px sans-serif';
            const textWidth = this.ctx.measureText(label).width;
            const labelHeight = 24;
            const labelY = top - labelHeight >= 0 ? top - labelHeight : bottom;

            this.ctx.fillStyle = color;
            this.ctx.fillRect(left, labelY, Math.max(w, textWidth + 12), labelHeight);
            this.ctx.fillStyle = '#fff';
            this.ctx.fillText(label, left + 6, labelY + labelHeight - 7);
        });
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

    async captureSample(providedFrame) {
        if (!providedFrame && !this.isRunning) return;
        if (this.samples.length >= this.maxSamples) {
            this.showError('Maximum 5 samples already captured.');
            return;
        }

        const frame = providedFrame || this.captureFrame();
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

            const detections = data.detections || [];
            this.drawDetections(detections);

            const list = document.getElementById('recognition-results');
            if (list) {
                if (detections.length === 0) {
                    list.innerHTML = '<div class="empty-state" style="padding:24px"><div class="empty-state-icon">🔍</div><div>No faces detected</div></div>';
                } else {
                    list.innerHTML = detections.map(d => `
            <div class="live-result-item ${d.known ? '' : 'unknown'}">
              <div class="cell-avatar">${d.known ? d.name.charAt(0) : '?'}</div>
              <div>
                <div class="live-result-name">${d.known ? d.name : 'Unknown face'}</div>
                <div class="live-result-meta">${d.known ? (d.class_name + ' — Marked Present ✓') : 'Not registered'}</div>
              </div>
              <div class="live-result-conf">${d.known ? d.confidence + '%' : ''}</div>
            </div>
          `).join('');
                }
            }
            const markedList = data.marked || [];
            if (markedList.length > 0 && window.showToast) {
                window.showToast(`${markedList.length} student(s) marked present.`, 'success');
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
            this.drawDetections(results.map(r => ({
                location: r.location, known: r.known, name: r.name,
                class_name: r.class_name, confidence: r.confidence,
            })));
            // NOTE: live.html's actual container id is 'live-results-container'
            // (not 'live-results' - that id doesn't exist on this page, which
            // is why detections never appeared before).
            const list = document.getElementById('live-results-container');

            if (results.length > 0) {
                document.getElementById('live-empty-state')?.remove();

                // Show the most recent face's name + class on top of the
                // video feed for a few seconds.
                const latest = results[0];
                const overlay = document.getElementById('live-face-overlay');
                if (overlay) {
                    document.getElementById('live-face-overlay-name').textContent = latest.name;
                    document.getElementById('live-face-overlay-class').textContent = latest.class_name || '';
                    overlay.style.display = 'block';
                    overlay.style.opacity = '1';
                    clearTimeout(this._overlayTimeout);
                    this._overlayTimeout = setTimeout(() => {
                        overlay.style.opacity = '0';
                        setTimeout(() => { overlay.style.display = 'none'; }, 300);
                    }, 3000);
                }

                if (list) {
                    results.forEach(r => {
                        const item = document.createElement('div');
                        item.className = `live-detection-item ${r.known ? 'known' : 'unknown'}`;
                        item.innerHTML = `
              <div class="cell-avatar">${r.known ? r.name.charAt(0) : '?'}</div>
              <div style="flex:1">
                <div class="live-result-name">${r.name}</div>
                <div class="live-result-meta">${r.reg_no} · ${r.class_name || ''} — ${new Date().toLocaleTimeString()}</div>
              </div>
              <div class="live-result-conf">${r.confidence}%</div>
            `;
                        list.prepend(item);
                    });
                    if (window.showToast) {
                        const newlyMarked = results.filter(r => r.known && !r.already_marked);
                        if (newlyMarked.length) {
                            window.showToast(`${newlyMarked.map(r => r.name).join(', ')} marked present`, 'success', 2500);
                        }
                    }
                }
            }
            // Update counter
            const counter = document.getElementById('marked-count');
            if (counter) counter.textContent = parseInt(counter.textContent || 0) + results.filter(r => r.known && !r.already_marked).length;
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
                // Reveal the actual video feed + overlays here (fixes the
                // black-screen bug). register.html's old inline onclick
                // tried to find #camera-video inside the button's own
                // parent (.camera-footer), but the video actually lives in
                // a sibling div (.camera-feed-wrapper), so it always
                // silently failed and the video stayed hidden forever.
                if (app.video) app.video.style.display = 'block';
                const faceGuide = document.getElementById('face-guide');
                if (faceGuide) faceGuide.style.display = 'block';
                const scanLine = document.getElementById('scan-line');
                if (scanLine) scanLine.style.display = 'block';
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

    // Upload-photo alternative to webcam capture (register mode).
    // Reuses captureSample()'s existing thumbnail/progress logic by
    // passing it an already-captured frame instead of grabbing one from
    // the video feed.
    const uploadInput = document.getElementById('upload-photo-input');
    if (uploadInput) {
        uploadInput.addEventListener('change', () => {
            const files = Array.from(uploadInput.files || []);
            files.forEach(file => {
                if (!file.type.startsWith('image/')) return;
                const reader = new FileReader();
                reader.onload = (e) => app.captureSample(e.target.result);
                reader.readAsDataURL(file);
            });
            uploadInput.value = '';
        });
    }
});
