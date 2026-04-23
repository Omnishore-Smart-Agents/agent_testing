document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('run-btn');
    const urlInput = document.getElementById('url-input');
    const statusEl = document.getElementById('agent-status');
    const resultsPanel = document.getElementById('results-panel');
    const testList = document.getElementById('test-list');
    const metricTotal = document.getElementById('metric-total');
    const metricPassed = document.getElementById('metric-passed');
    const metricFailed = document.getElementById('metric-failed');

    runBtn.addEventListener('click', runTests);

    async function runTests() {
        const url = urlInput.value.trim();
        if (!url) {
            statusEl.textContent = 'Please enter a URL.';
            return;
        }

        setLoading(true);
        statusEl.textContent = 'Running agent...';
        resultsPanel.classList.add('hidden');
        testList.innerHTML = '';

        try {
            const res = await fetch('/api/run-agent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await res.json();

            if (data.error) {
                statusEl.textContent = 'Error: ' + data.error;
                return;
            }

            statusEl.textContent = 'Tests complete!';
            renderResults(data);
        } catch (err) {
            statusEl.textContent = 'Request failed: ' + err.message;
        } finally {
            setLoading(false);
        }
    }

    function setLoading(loading) {
        runBtn.disabled = loading;
        const btnText = runBtn.querySelector('.btn-text');
        const spinner = runBtn.querySelector('.spinner');
        if (loading) {
            btnText.textContent = 'Running...';
            spinner.classList.remove('hidden');
        } else {
            btnText.textContent = 'Run tests';
            spinner.classList.add('hidden');
        }
    }

    function renderResults(data) {
        resultsPanel.classList.remove('hidden');

        const results = data.results || [];
        metricTotal.textContent = data.total_tests || results.length;
        metricPassed.textContent = data.passed || 0;
        metricFailed.textContent = data.failed || 0;

        results.forEach((res, idx) => {
            const tc = res.test_case;
            const screenshots = res.screenshots || [];
            const screenshotCount = screenshots.length;

            const el = document.createElement('div');
            el.className = `test-item ${res.status}`;

            let screenshotsHTML = '';
            if (screenshotCount > 0) {
                screenshotsHTML = `
                    <div class="screenshots-section">
                        <button class="screenshots-toggle" data-target="shots-${idx}">
                            📷 ${screenshotCount} screenshot${screenshotCount > 1 ? 's' : ''}
                        </button>
                        <div class="screenshots-gallery hidden" id="shots-${idx}">
                            ${screenshots.map((shot, sidx) => `
                                <div class="screenshot-card">
                                    <div class="screenshot-meta">
                                        <span class="shot-label">${shot.label}</span>
                                        <span class="shot-title" title="${shot.page_title || ''}">${shot.page_title || '—'}</span>
                                        <span class="shot-url" title="${shot.url || ''}">${new URL(shot.url || 'about:blank').pathname || '/'}</span>
                                    </div>
                                    <a href="/${shot.path}" target="_blank" class="screenshot-link">
                                        <img src="/${shot.path}" alt="${shot.label}" class="screenshot-thumb" loading="lazy">
                                    </a>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            el.innerHTML = `
                <div class="test-header" onclick="this.parentElement.querySelector('.screenshots-section')?.querySelector('button')?.click()">
                    <span class="test-id">${tc?.id || '?'}</span>
                    <span class="test-status ${res.status}">${res.status.toUpperCase()}</span>
                </div>
                <div class="test-desc">${tc?.description || ''}</div>
                ${res.error ? `<div class="test-error">❌ ${res.error}</div>` : ''}
                ${screenshotsHTML}
            `;
            testList.appendChild(el);
        });

        document.querySelectorAll('.screenshots-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const target = document.getElementById(btn.dataset.target);
                if (target) target.classList.toggle('hidden');
                btn.classList.toggle('expanded');
            });
        });
    }
});