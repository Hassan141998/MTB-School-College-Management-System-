/* =====================================================
   MTB School & College — main.js
   Sidebar, Toast, Dropzone, Dropdown, Confirm dialogs
   ===================================================== */

'use strict';

// ─── Sidebar Toggle ──────────────────────────────────

const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebar-overlay');
const toggleBtn = document.getElementById('sidebar-toggle');

function isMobile() { return window.innerWidth <= 768; }

function openSidebar() {
    sidebar.classList.add('mobile-open');
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeSidebar() {
    sidebar.classList.remove('mobile-open');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
}

function toggleSidebar() {
    if (isMobile()) {
        sidebar.classList.contains('mobile-open') ? closeSidebar() : openSidebar();
    } else {
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    }
}

// Restore sidebar state
if (!isMobile()) {
    const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (collapsed) sidebar.classList.add('collapsed');
}

if (toggleBtn) toggleBtn.addEventListener('click', toggleSidebar);
if (overlay) overlay.addEventListener('click', closeSidebar);

window.addEventListener('resize', () => {
    if (!isMobile()) {
        closeSidebar();
        document.body.style.overflow = '';
    }
});

// ─── Active nav link ─────────────────────────────────

document.querySelectorAll('.nav-link').forEach(link => {
    if (link.href && window.location.pathname.startsWith(new URL(link.href, window.location.href).pathname)) {
        link.classList.add('active');
    }
});

// ─── Dropdown ────────────────────────────────────────

document.querySelectorAll('[data-dropdown]').forEach(toggle => {
    const menuId = toggle.dataset.dropdown;
    const menu = document.getElementById(menuId);
    if (!menu) return;
    toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = menu.classList.contains('show');
        document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
        if (!isOpen) menu.classList.add('show');
    });
});

document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
});

// ─── Flash / Toast notifications ─────────────────────

function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('flash-container') ||
        (() => {
            const c = document.createElement('div');
            c.id = 'flash-container';
            c.className = 'flash-container';
            document.body.appendChild(c);
            return c;
        })();

    const icons = { success: '✓', danger: '✕', warning: '⚠', info: 'ℹ' };
    const alert = document.createElement('div');
    alert.className = `flash-alert ${type}`;
    alert.innerHTML = `
    <span class="flash-icon">${icons[type] || icons.info}</span>
    <span class="flash-msg">${message}</span>
    <button class="flash-close" onclick="this.parentElement.remove()">×</button>
  `;
    container.appendChild(alert);
    setTimeout(() => {
        alert.style.transition = 'opacity 0.4s, transform 0.4s';
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(100%)';
        setTimeout(() => alert.remove(), 400);
    }, duration);
}

// Auto-dismiss existing flash alerts
document.querySelectorAll('.flash-alert').forEach((alert, i) => {
    setTimeout(() => {
        alert.style.transition = 'opacity 0.4s, transform 0.4s';
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(100%)';
        setTimeout(() => alert.remove(), 400);
    }, 4000 + i * 500);
});

document.querySelectorAll('.flash-close').forEach(btn => {
    btn.addEventListener('click', () => btn.parentElement.remove());
});

// ─── Confirm delete dialogs ───────────────────────────

document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', (e) => {
        const msg = form.dataset.confirm || 'Are you sure?';
        if (!confirm(msg)) e.preventDefault();
    });
});

document.querySelectorAll('[data-confirm-btn]').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const msg = btn.dataset.confirmBtn || 'Are you sure?';
        if (!confirm(msg)) e.preventDefault();
    });
});

// ─── Photo preview ────────────────────────────────────

document.querySelectorAll('input[type="file"][data-preview]').forEach(input => {
    const previewId = input.dataset.preview;
    const preview = document.getElementById(previewId);
    if (!preview) return;
    input.addEventListener('change', () => {
        const file = input.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    });
});

// ─── Dropzone ────────────────────────────────────────

document.querySelectorAll('.dropzone').forEach(zone => {
    const input = zone.querySelector('input[type="file"]');
    zone.addEventListener('click', () => input && input.click());
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('active');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('active'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('active');
        if (input && e.dataTransfer.files.length) {
            input.files = e.dataTransfer.files;
            const name = zone.querySelector('.dropzone-filename');
            if (name) name.textContent = e.dataTransfer.files[0].name;
        }
    });
    if (input) {
        input.addEventListener('change', () => {
            const name = zone.querySelector('.dropzone-filename');
            if (name && input.files[0]) name.textContent = input.files[0].name;
        });
    }
});

// ─── Attendance: mark all ────────────────────────────

const markAllBtns = document.querySelectorAll('[data-mark-all]');
markAllBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const status = btn.dataset.markAll;
        document.querySelectorAll(`input[name^="status_"][value="${status}"]`).forEach(radio => {
            radio.checked = true;
        });
    });
});

// ─── Dynamic student filter (fees record payment) ─────

const studentSelect = document.getElementById('student-select');
const feeSelect = document.getElementById('fee-structure-select');
if (studentSelect && feeSelect) {
    studentSelect.addEventListener('change', () => {
        const amountInput = document.getElementById('amount-input');
        if (amountInput) {
            const selectedOpt = feeSelect.options[feeSelect.selectedIndex];
            if (selectedOpt && selectedOpt.dataset.amount) {
                amountInput.value = selectedOpt.dataset.amount;
            }
        }
    });
    feeSelect.addEventListener('change', () => {
        const amountInput = document.getElementById('amount-input');
        if (amountInput) {
            const selectedOpt = feeSelect.options[feeSelect.selectedIndex];
            if (selectedOpt && selectedOpt.dataset.amount) {
                amountInput.value = selectedOpt.dataset.amount;
                updateTotalFee();
            }
        }
    });
}

function updateTotalFee() {
    const amount = parseFloat(document.getElementById('amount-input')?.value || 0);
    const discount = parseFloat(document.getElementById('discount-input')?.value || 0);
    const fine = parseFloat(document.getElementById('fine-input')?.value || 0);
    const total = document.getElementById('total-display');
    if (total) total.textContent = 'PKR ' + (amount - discount + fine).toLocaleString();
}

['amount-input', 'discount-input', 'fine-input'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', updateTotalFee);
});

// ─── Marks auto-grade preview ─────────────────────────

document.querySelectorAll('input[data-marks]').forEach(input => {
    const total = parseFloat(input.dataset.total || 100);
    const gradeDisplay = document.getElementById(input.dataset.marks);
    input.addEventListener('input', () => {
        const val = parseFloat(input.value) || 0;
        const pct = (val / total) * 100;
        let grade = 'F';
        if (pct >= 90) grade = 'A+';
        else if (pct >= 80) grade = 'A';
        else if (pct >= 70) grade = 'B';
        else if (pct >= 60) grade = 'C';
        else if (pct >= 50) grade = 'D';
        if (gradeDisplay) {
            gradeDisplay.textContent = grade;
            gradeDisplay.className = 'grade-badge grade-' + grade.replace('+', 'plus');
        }
    });
});

// ─── Smooth scroll for anchor links ──────────────────

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
        const target = document.querySelector(anchor.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Export window.showToast for use in other scripts
window.showToast = showToast;
