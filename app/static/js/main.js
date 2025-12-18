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

    async function fetchResults() {
        try {
            const response = await fetch('/votes/count');
            const data = await response.json();
            resultsContainer.textContent = JSON.stringify(data, null, 2);
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
