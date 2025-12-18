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

    // Initial load
    fetchResults();
});
