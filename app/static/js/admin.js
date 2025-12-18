document.addEventListener('DOMContentLoaded', () => {
    const adminMessage = document.getElementById('adminMessage');

    function showMessage(text, type) {
        adminMessage.textContent = text;
        adminMessage.className = `message ${type}`;
        adminMessage.style.display = 'block';
        setTimeout(() => {
            adminMessage.style.display = 'none';
        }, 5000);
    }

    // --- Candidate Management ---
    const addCandidateForm = document.getElementById('addCandidateForm');
    addCandidateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(addCandidateForm);
        try {
            const res = await fetch('/candidates/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: formData.get('name') })
            });
            const data = await res.json();
            if (res.ok) {
                showMessage(data.message, 'success');
                addCandidateForm.reset();
                updateCandidateList();
            } else {
                showMessage(data.message, 'error');
            }
        } catch (err) {
            showMessage(err.message, 'error');
        }
    });

    async function updateCandidateList() {
        try {
            const res = await fetch('/candidates');
            const data = await res.json();
            const div = document.getElementById('candidateList');
            if (data.candidates.length > 0) {
                div.innerHTML = '<strong>Registered Candidates:</strong><ul style="margin: 0.5rem 0; padding-left: 1.5rem;">' +
                    data.candidates.map(c =>
                        `<li style="margin: 0.3rem 0; display: flex; justify-content: space-between; align-items: center;">
                            <span>${c}</span>
                            <button onclick="removeCandidate('${c}')" class="secondary-btn" style="width: auto; padding: 0.2rem 0.5rem; font-size: 0.8rem; margin-left: 1rem;">✕ Remove</button>
                        </li>`
                    ).join('') + '</ul>';
            } else {
                div.innerHTML = '<em style="opacity: 0.7;">No candidates yet.</em>';
            }
        } catch (err) { }
    }
    updateCandidateList();

    // Remove candidate function (global)
    window.removeCandidate = async function (name) {
        if (!confirm(`Remove candidate "${name}"?`)) return;
        try {
            const res = await fetch('/candidates/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const data = await res.json();
            if (res.ok) {
                showMessage(data.message, 'success');
                updateCandidateList();
            } else {
                showMessage(data.message, 'error');
            }
        } catch (err) {
            showMessage('Error removing candidate', 'error');
        }
    };

    // --- Election Timer ---
    const setTimerForm = document.getElementById('setTimerForm');
    setTimerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(setTimerForm);
        try {
            const res = await fetch('/election/window', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_time: parseFloat(formData.get('start_time')),
                    end_time: parseFloat(formData.get('end_time'))
                })
            });
            const data = await res.json();
            if (res.ok) showMessage(data.message, 'success');
            else showMessage(data.message || 'Error', 'error');
        } catch (err) {
            showMessage(err.message, 'error');
        }
    });

    document.getElementById('setWindowNowBtn').addEventListener('click', () => {
        const now = Math.floor(Date.now() / 1000);
        setTimerForm.querySelector('[name=start_time]').value = now;
        setTimerForm.querySelector('[name=end_time]').value = now + 3600;
    });

    // --- Node Operations ---
    document.getElementById('mineBtn').addEventListener('click', async () => {
        try {
            const res = await fetch('/mine');
            const data = await res.json();
            showMessage(data.message + ` (Block ${data.index})`, 'success');
        } catch (err) { showMessage(err.message, 'error'); }
    });

    document.getElementById('resolveBtn').addEventListener('click', async () => {
        try {
            const res = await fetch('/nodes/resolve');
            const data = await res.json();
            showMessage(data.message, 'success');
        } catch (err) { showMessage(err.message, 'error'); }
    });

    // Verify Chain Integrity
    document.getElementById('verifyBtn').addEventListener('click', async () => {
        const resultDiv = document.getElementById('integrityResult');
        resultDiv.textContent = 'Checking...';
        resultDiv.style.color = '';

        try {
            const res = await fetch('/chain/verify');
            const data = await res.json();

            if (data.valid) {
                resultDiv.innerHTML = `✓ <strong>Chain is valid!</strong><br>Blocks checked: ${data.blocks_checked}`;
                resultDiv.style.color = 'var(--success-color)';
            } else {
                resultDiv.innerHTML = `✗ <strong>Chain integrity failed!</strong><br>Errors:<br>` +
                    data.errors.map(e => `• ${e}`).join('<br>');
                resultDiv.style.color = 'var(--error-color)';
            }
        } catch (err) {
            resultDiv.textContent = 'Error checking integrity';
            resultDiv.style.color = 'var(--error-color)';
        }
    });

    // --- Activity Log ---
    async function fetchLogs() {
        try {
            const res = await fetch('/logs/recent');
            if (res.status === 401) {
                window.location.href = '/admin/login';
                return;
            }
            const data = await res.json();
            const logDiv = document.getElementById('activityLog');

            if (data.logs && data.logs.length > 0) {
                logDiv.innerHTML = data.logs.reverse().map(log => {
                    const color = log.level === 'ERROR' ? 'var(--error-color)' :
                        log.level === 'WARNING' ? 'orange' : 'var(--text-color)';
                    return `<div style="color: ${color}; margin-bottom: 0.3rem;">[${log.timestamp.split('T')[1].split('.')[0]}] [${log.level}] ${log.message}</div>`;
                }).join('');
            } else {
                logDiv.textContent = 'No activity yet.';
            }
        } catch (err) {
            console.error('Failed to fetch logs', err);
        }
    }
    fetchLogs();
    setInterval(fetchLogs, 5000);

    // --- Logout ---
    document.getElementById('logoutBtn').addEventListener('click', async () => {
        try {
            await fetch('/admin/logout', { method: 'POST' });
            window.location.href = '/admin/login';
        } catch (err) {
            showMessage('Logout failed', 'error');
        }
    });
});
