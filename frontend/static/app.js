// Global variable to store selected browser and last result
let selectedBrowser = 'chromium';
let lastRunResult = null;

function escapeHTML(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('run-btn');
    const urlInput = document.getElementById('url-input');
    const mdFileInput = document.getElementById('md-file-input');
    const fileUploadBtn = document.querySelector('.file-upload-btn');
    const statusEl = document.getElementById('agent-status');
    const resultsPanel = document.getElementById('results-panel');
    const testList = document.getElementById('test-list');
    const metricTotal = document.getElementById('metric-total');
    const metricPassed = document.getElementById('metric-passed');
    const metricFailed = document.getElementById('metric-failed');
    const exportWordBtn = document.getElementById('export-word-btn');

    // Store markdown content when file uploaded
    let markdownContent = '';

    // Browser select elements
    const selectBtn = document.getElementById('browser-select-btn');
    const dropdownEl = document.getElementById('browser-dropdown');
    const selectedLabel = selectBtn?.querySelector('.selected-label');
    const dropdownOptions = document.querySelectorAll('.dropdown-option');

    // ========================================
    // BROWSER SELECTION HANDLING
    // ========================================

    function openDropdown() {
        selectBtn?.classList.add('open');
        dropdownEl?.classList.remove('hidden');
    }

    function closeDropdown() {
        selectBtn?.classList.remove('open');
        dropdownEl?.classList.add('hidden');
    }

    // Toggle dropdown on button click
    selectBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        if (dropdownEl?.classList.contains('hidden')) {
            openDropdown();
        } else {
            closeDropdown();
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
        closeDropdown();
    });

    // Prevent dropdown close when clicking inside
    dropdownEl?.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    // Handle option selection
    dropdownOptions.forEach(option => {
        option.addEventListener('click', () => {
            const value = option.dataset.value;
            const label = option.textContent;

            // Update selected browser
            selectedBrowser = value;

            // Update button label
            if (selectedLabel) selectedLabel.textContent = label;

            // Update active state
            dropdownOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');

            // Close dropdown
            closeDropdown();

            console.log('Browser selected:', selectedBrowser);
        });
    });

    // ========================================
    // MARKDOWN FILE UPLOAD
    // ========================================

    mdFileInput?.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            markdownContent = text;

            // Update button to show file loaded
            fileUploadBtn?.classList.add('has-file');
            fileUploadBtn.querySelector('span').textContent = file.name.slice(0, 8);

            // Try to extract URL from markdown if present
            const urlMatch = text.match(/https?:\/\/[^\s\)\]]+/);
            if (urlMatch && !urlInput.value.trim()) {
                urlInput.value = urlMatch[0];
            }

            statusEl.textContent = `Loaded: ${file.name}`;
            console.log('Markdown file loaded:', file.name);
        } catch (err) {
            statusEl.textContent = 'Error reading file: ' + err.message;
            console.error(err);
        }
    });

    // ========================================
    // RUN TESTS
    // ========================================

    runBtn.addEventListener('click', runTests);

    // Export Word button
    exportWordBtn?.addEventListener('click', async () => {
        console.log('Export button clicked. lastRunResult:', lastRunResult);
        if (!lastRunResult) {
            alert('Veuillez d\'abord terminer un test avant d\'exporter au format Word.');
            return;
        }
        const url = urlInput.value.trim();
        if (!url) {
            statusEl.textContent = 'Please enter a URL first.';
            return;
        }

        exportWordBtn.disabled = true;
        exportWordBtn.querySelector('span').textContent = 'Generating...';

        try {
            const res = await fetch('/api/export-word', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url,
                    browser: selectedBrowser,
                    results_data: lastRunResult
                })
            });

            if (!res.ok) throw new Error('Export failed');

            const blob = await res.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = `rapport_test_${Date.now()}.docx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(blobUrl);

            statusEl.textContent = 'Word report downloaded!';
        } catch (err) {
            statusEl.textContent = 'Export failed: ' + err.message;
        } finally {
            exportWordBtn.disabled = false;
            exportWordBtn.querySelector('span').textContent = 'Télécharger Word';
        }
    });

    async function runTests() {
        const url = urlInput.value.trim();

        // Need either URL or markdown content
        if (!url && !markdownContent) {
            statusEl.textContent = 'Please enter a URL or upload a .md file.';
            return;
        }

        // Validate browser selection
        if (!selectedBrowser) {
            statusEl.textContent = 'Please select a browser first.';
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
                body: JSON.stringify({
                    url,
                    markdown_content: markdownContent,
                    browser: selectedBrowser
                })
            });

            const data = await res.json();

            if (data.error) {
                statusEl.textContent = 'Error: ' + data.error;
                return;
            }

            statusEl.textContent = 'Tests complete!';
            lastRunResult = data;
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