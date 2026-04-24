document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('run-btn');
    const urlInput = document.getElementById('url-input');
    const statusText = document.getElementById('agent-status');
    const browserSelectBtn = document.getElementById('browser-select-btn');
    const browserSelectDropdown = document.getElementById('browser-select-dropdown');
    const browserSelectHidden = document.getElementById('browser-select');
    const selectedText = document.querySelector('.selected-text');
    const optionItems = document.querySelectorAll('.option-item');
    
    const resultsPanel = document.getElementById('results-panel');
    const testList = document.getElementById('test-list');
    
    const metricTotal = document.getElementById('metric-total');
    const metricPassed = document.getElementById('metric-passed');
    const metricFailed = document.getElementById('metric-failed');
    
    // Browser select dropdown toggle
    browserSelectBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        browserSelectDropdown.classList.toggle('hidden');
    });

    // Option selection
    optionItems.forEach(item => {
        item.addEventListener('click', () => {
            const value = item.dataset.value;
            const label = item.querySelector('span:last-child').textContent;
            
            selectedText.textContent = label;
            browserSelectHidden.value = value;
            
            optionItems.forEach(i => i.classList.remove('selected'));
            item.classList.add('selected');
            
            browserSelectDropdown.classList.add('hidden');
        });
    });

    // Close dropdown on outside click
    document.addEventListener('click', () => {
        browserSelectDropdown.classList.add('hidden');
    });
    
    // UI states
    const setLoading = (isLoading) => {
        const btnText = runBtn.querySelector('.btn-text');
        const spinner = runBtn.querySelector('.spinner');
        
        runBtn.disabled = isLoading;
        urlInput.disabled = isLoading;
        browserSelectBtn.disabled = isLoading;
        
        if (isLoading) {
            btnText.classList.add('hidden');
            spinner.classList.remove('hidden');
            statusText.textContent = "Agent is working... (Extracting DOM, LLM Planning, Playwright Executing)";
            resultsPanel.classList.add('hidden');
        } else {
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
    };

    const renderResults = (data) => {
        if (!data || data.error !== undefined || !data.results) {
            statusText.textContent = `❌ Agent Failed: ${data?.error || "Unknown Error"}`;
            return;
        }

        statusText.textContent = `✅ Testing Complete. Generated report in output/ directory.`;
        
        // Update metrics
        metricTotal.textContent = data.total_tests;
        metricPassed.textContent = data.passed;
        metricFailed.textContent = data.failed;
        
        // Clear list
        testList.innerHTML = '';
        
        // Render tests
        data.results.forEach(res => {
            const isPassed = res.status === "passed";
            const test = res.test_case;
            
            const li = document.createElement('div');
            li.className = `test-item`;
            
            let errorHtml = '';
            if (!isPassed && res.error) {
                errorHtml = `<div class="test-error">${res.error}</div>`;
            }

            li.innerHTML = `
                <div class="test-item-header">
                    <div class="test-title">
                        <span class="test-id">${test.id}</span>
                        ${test.description}
                    </div>
                    <span class="status-badge ${res.status}">${res.status}</span>
                </div>
                <div class="test-details">
                    <div><strong>Expected:</strong> ${test.expected}</div>
                </div>
                ${errorHtml}
            `;
            
            testList.appendChild(li);
        });

        resultsPanel.classList.remove('hidden');
    };

    runBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        const browser = browserSelectHidden.value;
        if (!url) return;
        
        setLoading(true);
        
        try {
            const response = await fetch('/api/run-agent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, browser })
            });
            
            const data = await response.json();
            renderResults(data);
            
        } catch (error) {
            console.error(error);
            statusText.textContent = "❌ Network or Server Error occurred.";
        } finally {
            setLoading(false);
        }
    });
});