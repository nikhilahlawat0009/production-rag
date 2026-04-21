// Interactive demo for the production RAG platform

async function performSearch() {
    const query = document.getElementById('searchQuery').value.trim();
    const resultsContainer = document.getElementById('searchResults');

    if (!query) {
        resultsContainer.innerHTML = '<p class="results-placeholder">Please enter a search query...</p>';
        return;
    }

    // Show loading state
    resultsContainer.innerHTML = '<p class="results-placeholder">Searching...</p>';

    try {
        // Make API call to the search endpoint
        const response = await fetch('http://127.0.0.1:8000/api/v1/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                limit: 5,
                search_config: {
                    bm25_weight: 0.3,
                    semantic_weight: 0.4,
                    rerank_weight: 0.3,
                    rerank_top_k: 20
                }
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data, query);

    } catch (error) {
        console.error('Search error:', error);
        resultsContainer.innerHTML = `
            <div style="color: #e53e3e; text-align: center;">
                <h3>Search Failed</h3>
                <p>Make sure the FastAPI server is running on port 8000</p>
                <p>Error: ${error.message}</p>
                <p><strong>To start the server:</strong></p>
                <code style="background: #fed7d7; padding: 10px; border-radius: 4px; display: block; margin: 10px 0;">
                cd /Users/sharmaishika/Documents/github/production-rag<br>
                source .venv/bin/activate<br>
                cd backend<br>
                uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
                </code>
            </div>
        `;
    }
}

function displayResults(data, query) {
    const resultsContainer = document.getElementById('searchResults');

    if (!data.results || data.results.length === 0) {
        resultsContainer.innerHTML = '<p class="results-placeholder">No results found for your query.</p>';
        return;
    }

    let html = `
        <h3 style="color: #2d3748; margin-bottom: 20px;">Search Results for: "${query}"</h3>
        <div style="margin-bottom: 20px; padding: 15px; background: #e6fffa; border-radius: 8px; border-left: 4px solid #38b2ac;">
            <strong>Query Analysis:</strong> ${data.query_analysis || 'Financial document search'}
        </div>
    `;

    data.results.forEach((result, index) => {
        const scoreBreakdown = result.score_breakdown || {};
        const totalScore = (scoreBreakdown.bm25 || 0) + (scoreBreakdown.semantic || 0) + (scoreBreakdown.rerank || 0);

        html += `
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                    <h4 style="color: #2d3748; margin: 0; font-size: 1.2rem;">Result ${index + 1}</h4>
                    <div style="background: #667eea; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.9rem; font-weight: 600;">
                        Score: ${totalScore.toFixed(3)}
                    </div>
                </div>

                <div style="background: #f7fafc; padding: 15px; border-radius: 6px; margin-bottom: 15px; border-left: 3px solid #667eea;">
                    <strong>Content:</strong><br>
                    ${result.content || result.text || 'No content available'}
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; font-size: 0.9rem;">
                    <div style="background: #fed7d7; padding: 8px; border-radius: 4px; text-align: center;">
                        <strong>BM25:</strong> ${(scoreBreakdown.bm25 || 0).toFixed(3)}
                    </div>
                    <div style="background: #c6f6d5; padding: 8px; border-radius: 4px; text-align: center;">
                        <strong>Semantic:</strong> ${(scoreBreakdown.semantic || 0).toFixed(3)}
                    </div>
                    <div style="background: #bee3f8; padding: 8px; border-radius: 4px; text-align: center;">
                        <strong>Rerank:</strong> ${(scoreBreakdown.rerank || 0).toFixed(3)}
                    </div>
                </div>

                ${result.metadata ? `
                    <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px; font-size: 0.9rem;">
                        <strong>Metadata:</strong> ${Object.entries(result.metadata).map(([key, value]) => `${key}: ${value}`).join(' • ')}
                    </div>
                ` : ''}
            </div>
        `;
    });

    // Add performance info if available
    if (data.performance) {
        html += `
            <div style="margin-top: 20px; padding: 15px; background: #fff5f5; border-radius: 8px; border-left: 4px solid #fc8181;">
                <h4 style="color: #c53030; margin-bottom: 10px;">Performance Metrics</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; font-size: 0.9rem;">
                    <div><strong>Total Time:</strong> ${data.performance.total_time_ms || 'N/A'}ms</div>
                    <div><strong>BM25 Time:</strong> ${data.performance.bm25_time_ms || 'N/A'}ms</div>
                    <div><strong>Semantic Time:</strong> ${data.performance.semantic_time_ms || 'N/A'}ms</div>
                    <div><strong>Rerank Time:</strong> ${data.performance.rerank_time_ms || 'N/A'}ms</div>
                </div>
            </div>
        `;
    }

    resultsContainer.innerHTML = html;
}

// Add keyboard support for search
document.getElementById('searchQuery').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        performSearch();
    }
});

// Smooth scrolling for navigation
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href').substring(1);
        const targetSection = document.getElementById(targetId);

        if (targetSection) {
            const offsetTop = targetSection.offsetTop - 80; // Account for fixed navbar
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    });
});

// Add some sample queries for demo
document.addEventListener('DOMContentLoaded', function() {
    const sampleQueries = [
        "interest rate policy",
        "FCA regulations",
        "market volatility",
        "banking sector analysis"
    ];

    // Add click handlers to sample queries in the placeholder
    const placeholder = document.querySelector('.results-placeholder');
    if (placeholder) {
        placeholder.innerHTML = `
            Try these sample queries:<br>
            ${sampleQueries.map(q => `<button onclick="document.getElementById('searchQuery').value='${q}'; performSearch()" style="margin: 5px; padding: 5px 10px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer;">${q}</button>`).join('')}
        `;
    }
});