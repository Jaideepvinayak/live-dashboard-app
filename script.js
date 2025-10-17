document.addEventListener('DOMContentLoaded', () => {
    // This is the URL of the API you are running locally
    const API_URL = 'http://127.0.0.1:5000/api/news';

    const container = document.getElementById('headlines-container');

    async function fetchNews() {
        try {
            const response = await fetch(API_URL);
            const data = await response.json();
            displayHeadlines(data.headlines);
        } catch (error) {
            container.innerHTML = `<p class="loading-message">Failed to load news. Is the API server running?</p>`;
        }
    }

    function displayHeadlines(headlines) {
        container.innerHTML = '';
        if (!headlines || headlines.length === 0) {
            container.innerHTML = `<p class="loading-message">No headlines found.</p>`;
            return;
        }
        headlines.forEach(article => {
            const card = document.createElement('div');
            card.className = 'headline-card';
            const link = document.createElement('a');
            link.href = article.link;
            link.textContent = article.title;
            link.target = '_blank';
            card.appendChild(link);
            container.appendChild(card);
        });
    }

    fetchNews();
});