document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('voteForm');
    const message = document.getElementById('message');
    const resultsContainer = document.getElementById('resultsContainer');
    const refreshBtn = document.getElementById('refreshBtn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Reset message
        message.className = 'message hidden';
        message.textContent = '';

        const formData = new FormData(form);
        const payload = {
            candidate: formData.get('candidate'),
            private_key: formData.get('privateKey'),
            election_id: formData.get('electionId')
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

            // Clear existing options except first
            select.innerHTML = '<option value="" disabled selected>Select a candidate...</option>';

            if (data.candidates && data.candidates.length > 0) {
                data.candidates.forEach(name => {
                    const opt = document.createElement('option');
                    opt.value = name;
                    opt.textContent = name;
                    select.appendChild(opt);
                });
            } else {
                const opt = document.createElement('option');
                opt.disabled = true;
                opt.textContent = "No candidates registered";
                select.appendChild(opt);
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
