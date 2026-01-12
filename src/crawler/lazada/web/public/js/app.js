// Global state
let currentConfig = {};
let currentProgress = {};
let crawlerRunning = false;

//Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadConfig();
    loadProgress();
    checkCrawlerStatus();

    // Auto-refresh every 5 seconds
    setInterval(() => {
        loadStats();
        checkCrawlerStatus();
    }, 5000);
});

// Fetch and display stats
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('totalProducts').textContent = data.totalProducts.toLocaleString();
        document.getElementById('lastUpdated').textContent = new Date(data.lastUpdated).toLocaleString('vi-VN');
        document.getElementById('platform').textContent = data.platform;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Load config
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        currentConfig = await response.json();

        document.getElementById('maxPages').value = currentConfig.maxPages;
        document.getElementById('platform').value = currentConfig.platform;

        renderKeywords();
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

// Load progress
async function loadProgress() {
    try {
        const response = await fetch('/api/progress');
        currentProgress = await response.json();

        renderKeywords();
    } catch (error) {
        console.error('Failed to load progress:', error);
    }
}

// Render keywords list
function renderKeywords() {
    const container = document.getElementById('keywordsList');

    if (!currentConfig.keywords || currentConfig.keywords.length === 0) {
        container.innerHTML = '<p style="color:#666;">No keywords yet. Add some below!</p>';
        return;
    }

    container.innerHTML = currentConfig.keywords.map((kw, index) => {
        const progressItem = currentProgress.keywords?.find(p => p.term === kw);
        const status = progressItem ? progressItem.status : 'pending';
        const badgeClass = status === 'completed' ? 'completed' : 'pending';
        const badgeText = status === 'completed' ? '✓ Completed' : '⏳ Pending';

        return `
      <div class="keyword-item">
        <div class="keyword-info">
          <span class="keyword-name">${kw}</span>
          <span class="keyword-badge ${badgeClass}">${badgeText}</span>
        </div>
        <button onclick="removeKeyword('${kw}')" class="btn btn-remove">🗑️ Remove</button>
      </div>
    `;
    }).join('');
}

// Add new keywords
async function addKeywords() {
    const input = document.getElementById('newKeywords');
    const value = input.value.trim();

    if (!value) {
        alert('Please enter at least one keyword');
        return;
    }

    // Split by comma and clean up
    const newKeywords = value.split(',').map(kw => kw.trim()).filter(kw => kw);

    // Merge with existing keywords (avoid duplicates)
    const allKeywords = [...new Set([...currentConfig.keywords, ...newKeywords])];

    try {
        const response = await fetch('/api/keywords', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keywords: allKeywords })
        });

        const result = await response.json();

        if (result.success) {
            input.value = '';
            await loadConfig();
            await loadProgress();
            appendLog('success', `✅ Added ${newKeywords.length} keyword(s)`);
        } else {
            alert('Failed to add keywords');
        }
    } catch (error) {
        console.error('Failed to add keywords:', error);
        alert('Error adding keywords');
    }
}

// Remove a keyword
async function removeKeyword(keyword) {
    if (!confirm(`Remove keyword "${keyword}"?`)) {
        return;
    }

    const newKeywords = currentConfig.keywords.filter(kw => kw !== keyword);

    try {
        const response = await fetch('/api/keywords', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keywords: newKeywords })
        });

        const result = await response.json();

        if (result.success) {
            await loadConfig();
            await loadProgress();
            appendLog('info', `🗑️ Removed keyword "${keyword}"`);
        } else {
            alert('Failed to remove keyword');
        }
    } catch (error) {
        console.error('Failed to remove keyword:', error);
        alert('Error removing keyword');
    }
}

// Save settings
async function saveSettings() {
    const maxPages = parseInt(document.getElementById('maxPages').value);

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                maxPages: maxPages,
                keywords: currentConfig.keywords
            })
        });

        const result = await response.json();

        if (result.success) {
            appendLog('success', '💾 Settings saved');
            await loadConfig();
        } else {
            alert('Failed to save settings: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Failed to save settings:', error);
        alert('Error saving settings: ' + error.message);
    }
}

// Clear cookies
async function clearCookies() {
    if (!confirm('⚠️ This will delete all saved cookies. The next crawl will require solving CAPTCHA. Continue?')) {
        return;
    }

    try {
        const response = await fetch('/api/cookies/clear', {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            appendLog('info', '🗑️ ' + result.message);
            alert('✅ Cookies cleared! Next crawl will run in visible mode for CAPTCHA.');
        } else {
            alert('Failed to clear cookies: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Failed to clear cookies:', error);
        alert('Error clearing cookies: ' + error.message);
    }
}

// Open review modal
async function openReviewModal() {
    try {
        const response = await fetch('/api/plan');
        const plan = await response.json();

        const modalBody = document.getElementById('modalBody');

        modalBody.innerHTML = `
      <div class="plan-summary">
        <div class="plan-summary-grid">
          <div class="plan-summary-item">
            <div class="plan-summary-label">Keywords</div>
            <div class="plan-summary-value">${plan.totalKeywords}</div>
          </div>
          <div class="plan-summary-item">
            <div class="plan-summary-label">Est. Products</div>
            <div class="plan-summary-value">~${plan.totalEstimatedProducts.toLocaleString()}</div>
          </div>
          <div class="plan-summary-item">
            <div class="plan-summary-label">Est. Time</div>
            <div class="plan-summary-value">${plan.totalEstimatedTime}</div>
          </div>
        </div>
      </div>
      
      ${plan.keywords.map((kw, i) => `
        <div class="plan-keyword">
          <div class="plan-keyword-header">${i + 1}. ${kw.term}</div>
          <div class="plan-keyword-details">
            Status: <strong>${kw.status}</strong><br>
            Max Pages: <strong>${kw.maxPages}</strong><br>
            Est. Products: <strong>~${kw.estimatedProducts.toLocaleString()}</strong><br>
            Est. Time: <strong>${kw.estimatedTime}</strong>
          </div>
        </div>
      `).join('')}
      
      <div class="plan-note">
        ⚠️ <strong>Note:</strong> Browser will open automatically for CAPTCHA if needed. You must solve it manually within 60 seconds.
      </div>
    `;

        document.getElementById('reviewModal').style.display = 'block';
    } catch (error) {
        console.error('Failed to load plan:', error);
        alert('Error loading plan');
    }
}

// Close review modal
function closeReviewModal() {
    document.getElementById('reviewModal').style.display = 'none';
}

// Approve and start
async function approveAndStart() {
    closeReviewModal();
    await startCrawler();
}

// Start crawler
async function startCrawler() {
    if (crawlerRunning) {
        alert('Crawler is already running!');
        return;
    }

    try {
        const response = await fetch('/api/crawler/start', { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            crawlerRunning = true;
            updateCrawlerStatus(true);
            appendLog('success', '▶️ Crawler started');
        } else {
            alert('Failed to start crawler: ' + result.message);
        }
    } catch (error) {
        console.error('Failed to start crawler:', error);
        alert('Error starting crawler');
    }
}

// Stop crawler
async function stopCrawler() {
    if (!crawlerRunning) {
        alert('Crawler is not running!');
        return;
    }

    if (!confirm('Are you sure you want to stop the crawler?')) {
        return;
    }

    try {
        const response = await fetch('/api/crawler/stop', { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            crawlerRunning = false;
            updateCrawlerStatus(false);
            appendLog('warning', '⏹️ Crawler stopped');
        } else {
            alert('Failed to stop crawler: ' + result.message);
        }
    } catch (error) {
        console.error('Failed to stop crawler:', error);
        alert('Error stopping crawler');
    }
}

// Check crawler status
async function checkCrawlerStatus() {
    try {
        const response = await fetch('/api/crawler/status');
        const status = await response.json();

        crawlerRunning = status.running;
        updateCrawlerStatus(status.running);
    } catch (error) {
        console.error('Failed to check crawler status:', error);
    }
}

// Update UI based on crawler status
function updateCrawlerStatus(running) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');

    if (running) {
        statusDot.className = 'status-dot running';
        statusText.textContent = 'Running';
        startBtn.style.display = 'none';
        stopBtn.style.display = 'inline-block';
    } else {
        statusDot.className = 'status-dot';
        statusText.textContent = 'Ready';
        startBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
    }
}

// Append log to logs container
function appendLog(level, message) {
    const container = document.getElementById('logsContainer');
    const entry = document.createElement('div');
    entry.className = `log-entry ${level}`;
    entry.textContent = message;

    container.appendChild(entry);

    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Clear logs
function clearLogs() {
    document.getElementById('logsContainer').innerHTML = '';
    appendLog('info', 'Logs cleared');
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('reviewModal');
    if (event.target == modal) {
        closeReviewModal();
    }
}
