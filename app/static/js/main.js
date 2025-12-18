document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('voteForm');
    const message = document.getElementById('message');
    const resultsContainer = document.getElementById('resultsContainer');
    const refreshBtn = document.getElementById('refreshBtn');

    // OTP Session
    let sessionToken = null;
    const requestOtpBtn = document.getElementById('requestOtpBtn');
    const verifyOtpBtn = document.getElementById('verifyOtpBtn');
    const otpSection = document.getElementById('otpSection');
    const verificationStatus = document.getElementById('verificationStatus');
    const submitBtn = document.getElementById('submitBtn');
    const generateKeysBtn = document.getElementById('generateKeysBtn');

    // Generate Key Pair
    generateKeysBtn.addEventListener('click', async () => {
        generateKeysBtn.disabled = true;
        generateKeysBtn.textContent = 'Generating...';

        try {
            const res = await fetch('/wallet/generate', { method: 'POST' });
            const data = await res.json();

            if (res.ok) {
                document.getElementById('privateKey').value = data.private_key;
                const keyDisplay = document.getElementById('keyDisplay');
                keyDisplay.style.display = 'block';
                keyDisplay.innerHTML = `
                    <p style="margin: 0 0 0.5rem 0; color: var(--accent-color);"><strong>⚠️ SAVE YOUR PRIVATE KEY SECURELY!</strong></p>
                    <p style="margin: 0 0 0.5rem 0; font-size: 0.85rem; opacity: 0.8;">You need this to vote. It will not be shown again.</p>
                    <p style="margin: 0; font-size: 0.75rem;"><strong>Your Public Key (Voter ID):</strong><br>
                    <code style="font-size: 0.7rem; word-break: break-all;">${data.public_key.substring(0, 80)}...</code></p>
                `;
                showMessage('Key pair generated! Your private key is in the field below.', 'success');
            } else {
                showMessage('Failed to generate keys', 'error');
            }
        } catch (err) {
            showMessage('Network error', 'error');
        }

        generateKeysBtn.disabled = false;
        generateKeysBtn.textContent = '🔑 Generate New Key Pair';
    });

    // Request OTP
    requestOtpBtn.addEventListener('click', async () => {
        const email = document.getElementById('voterEmail').value;
        if (!email) {
            showMessage('Please enter your email', 'error');
            return;
        }

        try {
            const res = await fetch('/auth/request-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await res.json();

            if (res.ok) {
                otpSection.style.display = 'block';
                // Show OTP prominently (dev mode - SMTP not configured)
                if (data.otp) {
                    verificationStatus.innerHTML = `<strong style="color: var(--accent-color);">⚠️ SMTP not configured (Dev Mode)</strong><br>Your OTP: <code style="background: rgba(108,92,231,0.3); padding: 0.3rem 0.6rem; border-radius: 4px; font-size: 1.2rem; font-weight: bold;">${data.otp}</code>`;
                    // Auto-fill OTP input
                    document.getElementById('otpCode').value = data.otp;
                } else {
                    verificationStatus.textContent = data.message;
                }
                verificationStatus.className = 'message success';
            } else {
                showMessage(data.message, 'error');
            }
        } catch (err) {
            showMessage('Network error', 'error');
        }
    });

    // Verify OTP
    verifyOtpBtn.addEventListener('click', async () => {
        const email = document.getElementById('voterEmail').value;
        const otp = document.getElementById('otpCode').value;

        if (!otp) {
            verificationStatus.textContent = 'Please enter the OTP';
            verificationStatus.className = 'message error';
            return;
        }

        try {
            const res = await fetch('/auth/verify-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp })
            });
            const data = await res.json();

            if (res.ok) {
                sessionToken = data.session_token;
                verificationStatus.textContent = '✓ Email verified! You can now submit your vote.';
                verificationStatus.className = 'message success';
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Vote';
                // Disable OTP inputs
                document.getElementById('voterEmail').disabled = true;
                document.getElementById('otpCode').disabled = true;
                requestOtpBtn.disabled = true;
                verifyOtpBtn.disabled = true;
            } else {
                verificationStatus.textContent = data.message;
                verificationStatus.className = 'message error';
            }
        } catch (err) {
            verificationStatus.textContent = 'Network error';
            verificationStatus.className = 'message error';
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Reset message
        message.className = 'message hidden';
        message.textContent = '';

        const formData = new FormData(form);
        const payload = {
            candidate: formData.get('candidate'),
            private_key: formData.get('privateKey'),
            election_id: formData.get('electionId'),
            session_token: sessionToken
        };

        try {
            const response = await fetch('/vote/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                showMessage(data.message, 'success');
                fetchResults();
            } else {
                showMessage(data.message || 'Error submitting vote', 'error');
            }
        } catch (error) {
            showMessage('Network error occurred', 'error');
        }
    });

    refreshBtn.addEventListener('click', fetchResults);

    function showMessage(text, type) {
        message.textContent = text;
        message.className = `message ${type}`;
    }

    // Chart.js Setup
    let resultsChart = null;
    const ctx = document.getElementById('resultsChart').getContext('2d');

    function initChart() {
        resultsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Votes',
                    data: [],
                    backgroundColor: 'rgba(108, 92, 231, 0.7)',
                    borderColor: 'rgba(108, 92, 231, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#e0e0e0' },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    },
                    x: {
                        ticks: { color: '#e0e0e0' },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#e0e0e0' } }
                }
            }
        });
    }
    initChart();

    async function fetchResults() {
        try {
            const response = await fetch('/votes/count');
            const data = await response.json();
            resultsContainer.textContent = JSON.stringify(data, null, 2);

            // Update chart with first election or 'default'
            const electionId = Object.keys(data)[0] || 'default';
            const votes = data[electionId] || {};

            const labels = Object.keys(votes);
            const counts = Object.values(votes);

            resultsChart.data.labels = labels;
            resultsChart.data.datasets[0].data = counts;
            resultsChart.update();

        } catch (error) {
            resultsContainer.textContent = 'Failed to load results.';
        }
    }

    async function fetchCandidates() {
        try {
            const res = await fetch('/candidates');
            const data = await res.json();
            const select = document.getElementById('candidate');
            const resultsSection = document.querySelector('.card:has(#resultsContainer)') || document.getElementById('resultsContainer')?.parentElement;

            // Clear existing options except first
            select.innerHTML = '<option value="" disabled selected>Select a candidate...</option>';

            if (data.candidates && data.candidates.length > 0) {
                data.candidates.forEach(name => {
                    const opt = document.createElement('option');
                    opt.value = name;
                    opt.textContent = name;
                    select.appendChild(opt);
                });
                // Show results section when candidates exist
                if (resultsSection) resultsSection.style.display = 'block';
            } else {
                const opt = document.createElement('option');
                opt.disabled = true;
                opt.textContent = "No candidates registered";
                select.appendChild(opt);
                // Hide results section when no candidates
                if (resultsSection) {
                    resultsSection.style.display = 'none';
                }
            }
        } catch (err) {
            console.error("Failed to fetch candidates", err);
        }
    }

    async function fetchStats() {
        try {
            const res = await fetch('/stats');
            const data = await res.json();
            document.getElementById('statsBlocks').textContent = `Blocks: ${data.chain_length}`;
            document.getElementById('statsPeers').textContent = `Peers: ${data.nodes_count}`;
        } catch (err) {
            console.error("Failed to fetch stats", err);
        }
    }

    // Initial load
    fetchResults();
    fetchCandidates();
    fetchStats();

    // Auto-refresh every 5 seconds
    setInterval(() => {
        fetchResults();
        fetchStats();
    }, 5000);
});
