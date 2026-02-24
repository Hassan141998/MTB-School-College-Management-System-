/* =====================================================
   MTB School & College — dashboard.js
   Chart.js charts for dashboard
   ===================================================== */

'use strict';

const COLORS = {
    primary: '#FF6B35',
    secondary: '#004E89',
    accent: '#F7B801',
    success: '#10b981',
    info: '#3b82f6',
    danger: '#ef4444',
    primaryAlpha: 'rgba(255,107,53,0.15)',
    secondaryAlpha: 'rgba(0,78,137,0.15)',
};

Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#64748b';

// ─── Enrollment Trend Chart ───────────────────────────

async function initEnrollmentChart() {
    const ctx = document.getElementById('enrollmentChart');
    if (!ctx) return;
    try {
        const res = await fetch('/api/enrollment-data');
        const data = await res.json();
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'New Admissions',
                    data: data.data,
                    borderColor: COLORS.primary,
                    backgroundColor: COLORS.primaryAlpha,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: COLORS.primary,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: 'white',
                        bodyColor: 'rgba(255,255,255,0.8)',
                        borderColor: COLORS.primary,
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 8,
                    }
                },
                scales: {
                    x: { grid: { display: false }, border: { display: false } },
                    y: {
                        grid: { color: 'rgba(0,0,0,0.05)', drawBorder: false },
                        border: { display: false },
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                }
            }
        });
    } catch (e) { console.warn('Enrollment chart error:', e); }
}

// ─── Attendance Chart ─────────────────────────────────

async function initAttendanceChart() {
    const ctx = document.getElementById('attendanceChart');
    if (!ctx) return;
    try {
        const res = await fetch('/api/attendance-data');
        const data = await res.json();
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Present',
                        data: data.present,
                        backgroundColor: 'rgba(16,185,129,0.8)',
                        borderRadius: 6,
                        borderSkipped: false,
                    },
                    {
                        label: 'Absent',
                        data: data.absent,
                        backgroundColor: 'rgba(239,68,68,0.7)',
                        borderRadius: 6,
                        borderSkipped: false,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { usePointStyle: true, pointStyle: 'circle', padding: 16 }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: 'white',
                        bodyColor: 'rgba(255,255,255,0.8)',
                        padding: 10,
                        cornerRadius: 8,
                    }
                },
                scales: {
                    x: { grid: { display: false }, border: { display: false }, stacked: false },
                    y: {
                        grid: { color: 'rgba(0,0,0,0.05)', drawBorder: false },
                        border: { display: false },
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                }
            }
        });
    } catch (e) { console.warn('Attendance chart error:', e); }
}

// ─── Fee Collection Chart ─────────────────────────────

async function initFeesChart() {
    const ctx = document.getElementById('feesChart');
    if (!ctx) return;
    try {
        const res = await fetch('/api/fees-data');
        const data = await res.json();
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Fee Collection (PKR)',
                    data: data.data,
                    backgroundColor: COLORS.secondaryAlpha,
                    borderColor: COLORS.secondary,
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: 'white',
                        bodyColor: 'rgba(255,255,255,0.8)',
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: (ctx) => 'PKR ' + ctx.parsed.y.toLocaleString()
                        }
                    }
                },
                scales: {
                    x: { grid: { display: false }, border: { display: false } },
                    y: {
                        grid: { color: 'rgba(0,0,0,0.05)', drawBorder: false },
                        border: { display: false },
                        beginAtZero: true,
                        ticks: { callback: (v) => 'PKR ' + (v >= 1000 ? (v / 1000) + 'K' : v) }
                    }
                }
            }
        });
    } catch (e) { console.warn('Fees chart error:', e); }
}

// ─── Class Distribution Doughnut ──────────────────────

async function initClassChart() {
    const ctx = document.getElementById('classChart');
    if (!ctx) return;
    try {
        const res = await fetch('/api/class-stats');
        const data = await res.json();
        const palette = [
            COLORS.primary, COLORS.secondary, COLORS.accent, COLORS.success,
            COLORS.info, COLORS.danger, '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'
        ];
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.data,
                    backgroundColor: palette.slice(0, data.labels.length),
                    borderWidth: 2,
                    borderColor: 'white',
                    hoverBorderWidth: 3,
                    hoverOffset: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { usePointStyle: true, pointStyle: 'circle', padding: 12, font: { size: 11 } }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: 'white',
                        bodyColor: 'rgba(255,255,255,0.8)',
                        padding: 10,
                        cornerRadius: 8,
                    }
                }
            }
        });
    } catch (e) { console.warn('Class chart error:', e); }
}

// Init all dashboard charts
document.addEventListener('DOMContentLoaded', () => {
    initEnrollmentChart();
    initAttendanceChart();
    initFeesChart();
    initClassChart();
});
