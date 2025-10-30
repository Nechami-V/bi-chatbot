// KT BI Chatbot Frontend - Modern JavaScript Implementation with Authentication
class BiChatbot {
    constructor() {
        this.apiUrl = 'http://localhost:8002';
        this.isLoading = false;
        this.messageCount = 0;
        this.authToken = null;
        this.userInfo = null;
        this.sidebarChart = null; // Chart.js instance for the sidebar sampleChart

        // Voice recording variables
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.isRecording = false;

        // DOM Elements
        this.elements = {
            chatMessages: document.getElementById('chatMessages'),
            messageInput: document.getElementById('messageInput'),
            chatForm: document.getElementById('chatForm'),
            sendBtn: document.getElementById('sendBtn'),
            charCount: document.getElementById('charCount'),
            statusIndicator: document.getElementById('statusIndicator'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            toast: document.getElementById('toast'),
            welcomeText: document.getElementById('welcomeText'),
            userName: document.getElementById('userName'),
            userRole: document.getElementById('userRole'),
            userAvatar: document.getElementById('userAvatar'),
            voiceBtn: document.getElementById('voiceBtn')
        };

        this.init();
    }

    init() {
        // Check authentication first
        this.checkAuthentication();

        // Event listeners
        this.setupEventListeners();

        // Check API connection
        this.checkApiConnection();

        // Focus on input
        this.elements.messageInput.focus();

        // Auto-resize input
        this.setupAutoResize();
    }

    setupEventListeners() {
        // Form submission
        this.elements.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // Input character count
        this.elements.messageInput.addEventListener('input', (e) => {
            this.updateCharCount(e.target.value.length);
            this.toggleSendButton();
        });

        // Enter key handling
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Toast close
        const toastClose = this.elements.toast.querySelector('.toast-close');
        if (toastClose) {
            toastClose.addEventListener('click', () => this.hideToast());
        }

        // Auto-hide toast after 5 seconds
        let toastTimer;
        const observer = new MutationObserver(() => {
            if (this.elements.toast.style.display === 'flex') {
                clearTimeout(toastTimer);
                toastTimer = setTimeout(() => this.hideToast(), 5000);
            }
        });
        observer.observe(this.elements.toast, { attributes: true, attributeFilter: ['style'] });
    }

    setupAutoResize() {
        const input = this.elements.messageInput;
        input.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    }

    async checkApiConnection() {
        try {
            this.updateStatus('בודק חיבור לשרת...', 'loading');

            const response = await fetch(`${this.apiUrl}/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.updateStatus('מוכן לשאלות', 'online');
                this.showToast('חיבור לשרת הצליח! ✅', 'success');
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('API Connection failed:', error);
            this.updateStatus('שגיאה בחיבור לשרת', 'error');
            this.showToast('לא ניתן להתחבר לשרת. בדוק שהשרת רץ על localhost:8002', 'error');
        }
    }

    async sendMessage() {
        const message = this.elements.messageInput.value.trim();

        if (!message || this.isLoading) {
            return;
        }

        // Add user message to chat
        this.addMessage(message, 'user');

        // Clear input
        this.elements.messageInput.value = '';
        this.toggleSendButton();

        // Show loading
        this.setLoading(true);

        try {
            // Send to API with authentication
            const t0 = performance.now();
            const response = await fetch(`${this.apiUrl}/ask`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({ question: message })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            data.client_time_ms = performance.now() - t0;

            // Add bot response
            this.addBotResponse(data);

        } catch (error) {
            console.error('Send message failed:', error);
            this.addErrorMessage(error.message);
            this.showToast('שגיאה בשליחת השאלה. נסה שוב.', 'error');

        } finally {
            this.setLoading(false);
        }
    }

    addMessage(content, type = 'user') {
        this.messageCount++;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        let avatarHtml = '';
        if (type === 'user') {
            // User initials
            const initials = this.userInfo && this.userInfo.user
                ? this.getUserInitials(this.userInfo.user.first_name, this.userInfo.user.last_name)
                : '??';
            avatarHtml = initials;
        } else {
            // Bot KT logo
            avatarHtml = '<img src="assets/kt-logo.png" alt="KT Bot">';
        }

        messageDiv.innerHTML = `
            <div class="message-avatar">
                ${avatarHtml}
            </div>
            <div class="message-content">
                <p>${this.escapeHtml(content)}</p>
            </div>
        `;

        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        return messageDiv;
    }

    addBotResponse(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';

        let content = '';

        // Main answer
        if (data.answer) {
            content += `<p>${this.escapeHtml(data.answer)}</p>`;
        }

        // Collapsible technical details (SQL / etc.)
        const hasDetails = (data.sql || (data.data && Array.isArray(data.data) && data.data.length > 0));
        if (hasDetails) {
            const detailsId = `details-${Date.now()}`;
            content += `
                <div style="margin-top: 1rem; border-top: 1px solid #e2e8f0; padding-top: 0.75rem;">
                    <button onclick="document.getElementById('${detailsId}').style.display = document.getElementById('${detailsId}').style.display === 'none' ? 'block' : 'none'"
                            style="background: none; border: none; color: #64748b; font-size: 0.85rem; cursor: pointer; text-decoration: underline;">
                        <i class="fas fa-info-circle"></i> פרטים טכניים
                    </button>
                    <div id="${detailsId}" style="display: none; margin-top: 0.5rem;">
            `;

            if (data.sql) {
                content += `
                    <div style="margin-bottom: 0.75rem; padding: 0.5rem; background: #f8fafc; border-radius: 0.5rem; border-right: 2px solid #64748b;">
                        <p style="font-weight: 600; color: #475569; margin-bottom: 0.25rem; font-size: 0.85rem;">
                            <i class="fas fa-database"></i> SQL Query:
                        </p>
                        <code style="background: #ffffff; padding: 0.5rem; border-radius: 0.25rem; display: block; font-family: 'Courier New', monospace; font-size: 0.8rem; direction: ltr; text-align: left; color: #374151;">
                            ${this.escapeHtml(data.sql)}
                        </code>
                    </div>
                `;
            }

            content += `</div></div>`;
        }

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <img src="assets/kt-logo.png" alt="KT Bot">
            </div>
            <div class="message-content">
                ${content}
            </div>
        `;

        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // ===== Visualization handling =====
        // We DO NOT render charts inside the chat message.
        // We ONLY update the fixed sidebar chart.
        try {
            let vizUsed = null;

            if (data.visualization) {
                vizUsed = data.visualization; // keep the data for the sidebar
                console.log(vizUsed);
                
            } else if (data.data && Array.isArray(data.data) && data.data.length > 0) {
                // Try to infer a viz for the sidebar only
                const inferred = this.inferVisualizationFromData(data.data);
                if (inferred) {
                    vizUsed = inferred;
                }
            }

            // Update the fixed sidebar chart only
            if (vizUsed) {
                this.updateSidebarChart(vizUsed);
            }
        } catch (err) {
            console.warn('Visualization handling failed:', err);
        }
    }

    inferVisualizationFromData(rows) {
        if (!rows || rows.length === 0) return null;
        const first = rows[0];
        const cols = Object.keys(first);

        function tryNumber(v) {
            if (v === null || v === undefined) return null;
            if (typeof v === 'number') return v;
            const s = String(v).replace(/,/g, '').replace(/\s+/g, '');
            const n = Number(s);
            return Number.isFinite(n) ? n : null;
        }

        if (cols.length === 1) {
            const c = cols[0];
            const n = tryNumber(first[c]);
            if (n !== null) {
                return { chart_type: 'metric', title: c, labels: [c], values: [n], value_field: c };
            }
            return null;
        }

        if (cols.length >= 2) {
            const a = cols[0], b = cols[1];
            const aNums = rows.map(r => tryNumber(r[a]));
            const bNums = rows.map(r => tryNumber(r[b]));

            const aAllNum = aNums.every(v => v !== null);
            const bAllNum = bNums.every(v => v !== null);

            // prefer categorical label + numeric value
            if (!aAllNum && bAllNum) {
                return { chart_type: 'bar', title: `${b} by ${a}`, label_field: a, value_field: b, labels: rows.map(r => String(r[a])), values: bNums };
            }
            if (!bAllNum && aAllNum) {
                return { chart_type: 'bar', title: `${a} by ${b}`, label_field: b, value_field: a, labels: rows.map(r => String(r[b])), values: aNums };
            }

            // both numeric -> scatter
            if (aAllNum && bAllNum) {
                const scatter = rows.map((r, i) => ({ x: aNums[i], y: bNums[i] }));
                return { chart_type: 'scatter', title: `${a} vs ${b}`, label_field: a, value_field: b, labels: rows.map((_, i) => String(i)), values: scatter };
            }
        }

        return null;
    }

    // (renderVisualization stays here but is NOT called anywhere from chat)
    renderVisualization(viz, container) {
        if (!viz || !container) return;

        const chartType = viz.chart_type || 'bar';
        const title = viz.title || '';
        const labels = Array.isArray(viz.labels) ? viz.labels : [];
        const values = Array.isArray(viz.values) ? viz.values : [];

        const wrapper = document.createElement('div');
        wrapper.style.marginTop = '0.75rem';
        wrapper.style.padding = '0.5rem';
        wrapper.style.borderRadius = '0.5rem';
        wrapper.style.background = '#ffffff';
        wrapper.style.border = '1px solid #eef2f7';

        if (title) {
            const h = document.createElement('div');
            h.style.fontWeight = '600';
            h.style.color = '#0f172a';
            h.style.marginBottom = '0.5rem';
            h.textContent = title;
            wrapper.appendChild(h);
        }

        if (chartType === 'metric') {
            const metricVal = (values && values.length > 0) ? values[0] : (viz.value || null);
            const metricDiv = document.createElement('div');
            metricDiv.style.fontSize = '1.9rem';
            metricDiv.style.fontWeight = '700';
            metricDiv.style.color = '#111827';
            metricDiv.style.textAlign = 'center';
            metricDiv.textContent = metricVal !== null && metricVal !== undefined ? String(metricVal) : '-';
            wrapper.appendChild(metricDiv);
            container.appendChild(wrapper);
            return;
        }

        const canvas = document.createElement('canvas');
        const canvasId = `viz-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
        canvas.id = canvasId;
        canvas.style.width = '100%';
        canvas.style.maxHeight = '260px';
        wrapper.appendChild(canvas);
        container.appendChild(wrapper);

        const ctx = canvas.getContext('2d');
        const colors = ['#7C3AED', '#F59E0B', '#4F46E5', '#10B981', '#EF4444', '#06B6D4', '#F97316', '#8B5CF6'];

        let config = {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: viz.value_field || '',
                    data: values,
                    backgroundColor: colors.slice(0, labels.length),
                    borderColor: '#ffffff',
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: { display: false }
                }
            }
        };

        if (chartType === 'line') {
            config.type = 'line';
            config.data.datasets[0].fill = false;
            config.data.datasets[0].borderColor = colors[0];
            config.data.datasets[0].tension = 0.2;
        } else if (chartType === 'pie' || chartType === 'donut') {
            config.type = 'pie';
            config.data.datasets[0].backgroundColor = colors.slice(0, labels.length);
        } else if (chartType === 'scatter') {
            config.type = 'scatter';
            config.data = { datasets: [{ label: viz.value_field || '', data: values, backgroundColor: colors[0] }] };
            config.options.scales = { x: { type: 'linear', position: 'bottom' } };
        }

        try {
            // eslint-disable-next-line no-undef
            new Chart(ctx, config);
        } catch (err) {
            console.warn('Chart render error', err);
        }
    }

    formatSimpleDataTable(data) {
        if (!data || data.length === 0) return '';

        const headers = Object.keys(data[0]);
        const maxRows = 5;

        let tableHtml = `
            <div style="margin-top: 1rem;">
                <div style="overflow-x: auto; border-radius: 0.5rem; border: 1px solid #e2e8f0; background: #f8fafc;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f1f5f9;">
        `;

        headers.forEach(header => {
            tableHtml += `<th style="padding: 0.5rem 0.75rem; text-align: right; font-weight: 600; font-size: 0.9rem; color: #374151;">${this.escapeHtml(header)}</th>`;
        });

        tableHtml += `</tr></thead><tbody>`;

        data.slice(0, maxRows).forEach((row) => {
            const bgColor = '#ffffff';
            tableHtml += `<tr style="background: ${bgColor};">`;

            headers.forEach(header => {
                const value = row[header] !== null && row[header] !== undefined ? row[header] : '-';
                tableHtml += `<td style="padding: 0.5rem 0.75rem; text-align: right; font-size: 0.9rem; color: #1f2937;">${this.escapeHtml(String(value))}</td>`;
            });

            tableHtml += `</tr>`;
        });

        tableHtml += `</tbody></table></div>`;

        if (data.length > maxRows) {
            tableHtml += `<p style="margin-top: 0.5rem; font-size: 0.85rem; color: #64748b; text-align: center; font-style: italic;">מציג ${maxRows} מתוך ${data.length} תוצאות</p>`;
        }

        tableHtml += `</div>`;

        return tableHtml;
    }

    formatDataTable(data) {
        return this.formatSimpleDataTable(data);
    }

    addErrorMessage(error) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-exclamation-triangle" style="color: #dc2626;"></i>
            </div>
            <div class="message-content" style="border-right: 3px solid #dc2626; background: #fef2f2;">
                <p><strong>שגיאה:</strong></p>
                <p>מצטער, אירעה שגיאה בעיבוד השאלה שלך.</p>
                <p style="font-size: 0.9rem; color: #7f1d1d; margin-top: 0.5rem;">
                    פרטי השגיאה: ${this.escapeHtml(error)}
                </p>
            </div>
        `;

        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    setLoading(loading) {
        this.isLoading = loading;

        if (loading) {
            this.elements.loadingOverlay.style.display = 'flex';
            this.elements.sendBtn.disabled = true;
            this.updateStatus('מעבד שאלה...', 'loading');
        } else {
            this.elements.loadingOverlay.style.display = 'none';
            this.elements.sendBtn.disabled = false;
            this.updateStatus('מוכן לשאלות', 'online');
        }

        this.toggleSendButton();
    }

    updateCharCount(count) {
        this.elements.charCount.textContent = `${count}/500`;

        if (count > 450) {
            this.elements.charCount.style.color = '#dc2626';
        } else if (count > 400) {
            this.elements.charCount.style.color = '#d97706';
        } else {
            this.elements.charCount.style.color = '#64748b';
        }
    }

    toggleSendButton() {
        const hasText = this.elements.messageInput.value.trim().length > 0;
        this.elements.sendBtn.disabled = !hasText || this.isLoading;
    }

    updateStatus(message, type) {
        this.elements.statusIndicator.innerHTML = `
            <i class="fas fa-circle"></i> ${message}
        `;
        this.elements.statusIndicator.className = `status ${type}`;
    }

    showToast(message, type = 'info') {
        const toast = this.elements.toast;
        const messageEl = toast.querySelector('.toast-message');

        messageEl.textContent = message;
        toast.className = `toast ${type}`;
        toast.style.display = 'flex';

        setTimeout(() => this.hideToast(), 5000);
    }

    hideToast() {
        this.elements.toast.style.display = 'none';
    }

    scrollToBottom() {
        setTimeout(() => {
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        }, 100);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new BiChatbot();
});

// Warn on unload while loading
window.addEventListener('beforeunload', (e) => {
    if (window.chatbot && window.chatbot.isLoading) {
        e.preventDefault();
        e.returnValue = 'יש בקשה בתהליך. האם אתה בטוח שברצונך לצאת?';
    }
});

// Authentication Methods - Added to BiChatbot class
BiChatbot.prototype.checkAuthentication = function () {
    const token = localStorage.getItem('authToken');
    const userInfo = localStorage.getItem('userInfo');

    if (!token || !userInfo) {
        window.location.href = 'login.html';
        return;
    }

    try {
        this.authToken = token;
        this.userInfo = JSON.parse(userInfo);
        this.setupUserInterface();
    } catch (error) {
        console.error('Error parsing user info:', error);
        this.logout();
    }
};

BiChatbot.prototype.setupUserInterface = function () {
    const user = this.userInfo.user;

    this.elements.userName.textContent = user.full_name;
    this.elements.userRole.textContent = this.getRoleDisplay(user.permission_group);

    const initials = this.getUserInitials(user.first_name, user.last_name);
    this.elements.userAvatar.textContent = initials;

    this.elements.welcomeText.innerHTML = `
        <strong>שלום ${user.first_name}!</strong> אני הצ'אט בוט שלך לניתוח נתונים עסקיים.
        <br>אני כאן כדי לעזור לך להבין את הנתונים שלך ולענות על השאלות העסקיות שלך.
    `;
};

BiChatbot.prototype.getUserInitials = function (firstName, lastName) {
    if (!firstName || !lastName) return '??';
    return firstName.charAt(0) + lastName.charAt(0);
};

BiChatbot.prototype.getRoleDisplay = function (permissionGroup) {
    const roleMap = {
        'admin': 'מנהל מערכת',
        'sales_manager': 'מנהל מכירות',
        'sales': 'איש מכירות',
        'marketing': 'שיווק',
        'finance': 'כספים',
        'readonly': 'צפייה בלבד'
    };
    return roleMap[permissionGroup] || permissionGroup;
};

BiChatbot.prototype.getAuthHeaders = function () {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.authToken}`
    };
};

// Update or replace the sidebar sampleChart with a new visualization
BiChatbot.prototype.updateSidebarChart = function (viz) {
    if (!viz) return;
    const container = document.querySelector('.sidebar .graph-container');
    if (!container) return;

    function ensureCanvas() {
        let canvas = container.querySelector('#sampleChart');
        if (!canvas) {
            container.innerHTML = '';
            canvas = document.createElement('canvas');
            canvas.id = 'sampleChart';
            canvas.width = 250;
            canvas.height = 200;
            container.appendChild(canvas);
        }
        return canvas;
    }

    const chartType = viz.chart_type || 'bar';

    // Metric: render a big number instead of a chart
    if (chartType === 'metric') {
        try { if (this.sidebarChart) { this.sidebarChart.destroy(); this.sidebarChart = null; } } catch (e) { }
        container.innerHTML = '';
        const title = document.createElement('div');
        title.style.fontWeight = '600';
        title.style.marginBottom = '0.5rem';
        title.textContent = viz.title || '';
        const val = document.createElement('div');
        val.style.fontSize = '2.2rem';
        val.style.fontWeight = '700';
        val.style.textAlign = 'center';
        val.textContent = (viz.values && viz.values.length > 0) ? String(viz.values[0]) : '-';
        container.appendChild(title);
        container.appendChild(val);
        return;
    }

    const canvas = ensureCanvas();

    try { if (this.sidebarChart) { this.sidebarChart.destroy(); this.sidebarChart = null; } } catch (e) { }

    const ctx = canvas.getContext('2d');
    const labels = Array.isArray(viz.labels) ? viz.labels : [];
    const values = Array.isArray(viz.values) ? viz.values : [];
    const colors = ['#7C3AED', '#F59E0B', '#4F46E5', '#10B981', '#EF4444', '#06B6D4', '#F97316', '#8B5CF6'];

    let config = {
        type: 'bar',
        data: { labels: labels, datasets: [{ label: viz.value_field || '', data: values, backgroundColor: colors.slice(0, labels.length) }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, title: { display: !!viz.title } } }
    };

    if (chartType === 'line') {
        config.type = 'line';
        config.data.datasets[0].fill = false;
        config.data.datasets[0].borderColor = colors[0];
        config.data.datasets[0].tension = 0.2;
    } else if (chartType === 'pie' || chartType === 'donut') {
        config.type = 'pie';
        config.data.datasets[0].backgroundColor = colors.slice(0, labels.length);
    } else if (chartType === 'scatter') {
        config.type = 'scatter';
        config.data = { datasets: [{ label: viz.value_field || '', data: values, backgroundColor: colors[0] }] };
        config.options.scales = { x: { type: 'linear', position: 'bottom' } };
    }

    try {
        // eslint-disable-next-line no-undef
        this.sidebarChart = new Chart(ctx, config);
    } catch (err) {
        console.warn('Sidebar chart render error', err);
    }
};

BiChatbot.prototype.logout = function () {
    localStorage.removeItem('authToken');
    localStorage.removeItem('tokenType');
    localStorage.removeItem('userInfo');
    window.location.href = 'login.html';
};

// Voice recording functions
BiChatbot.prototype.toggleRecording = async function () {
    if (!this.authToken) {
        this.showToast('יש להתחבר תחילה', 'error');
        return;
    }

    if (!this.isRecording) {
        await this.startRecording();
    } else {
        await this.stopRecording();
    }
};

BiChatbot.prototype.startRecording = async function () {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(stream);
        this.recordedChunks = [];

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.recordedChunks.push(event.data);
            }
        };

        this.mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(this.recordedChunks, { type: 'audio/webm' });
            await this.sendVoiceQuery(audioBlob);
        };

        this.mediaRecorder.start();
        this.isRecording = true;

        // Update UI
        this.elements.voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
        this.elements.voiceBtn.classList.add('recording');
        this.elements.statusIndicator.innerHTML = '<i class="fas fa-circle"></i> מקליט...';

    } catch (error) {
        console.error('Microphone error:', error);
        this.showToast('שגיאה בגישה למיקרופון: ' + error.message, 'error');
    }
};

BiChatbot.prototype.stopRecording = async function () {
    if (this.mediaRecorder && this.isRecording) {
        this.mediaRecorder.stop();
        this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        this.isRecording = false;

        // Update UI
        this.elements.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        this.elements.voiceBtn.classList.remove('recording');
        this.elements.statusIndicator.innerHTML = '<i class="fas fa-circle"></i> מעבד...';
    }
};

BiChatbot.prototype.sendVoiceQuery = async function (audioBlob) {
    this.setLoading(true);

    try {
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recording.webm');

        const response = await fetch(`${this.apiUrl}/voice-query`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.authToken}`
            },
            body: formData
        });

        if (!response.ok) {
            let errorMessage = 'שגיאה בשליחת השאילתה הקולית';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
            } catch (parseError) {
                errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();

        // Add voice query message to chat
        this.addMessage(data.question, 'user');

        // Process the response
        this.addBotResponse(data);

        // Reset status
        this.elements.statusIndicator.innerHTML = '<i class="fas fa-circle"></i> מוכן לשאלות';

    } catch (error) {
        console.error('Voice query error:', error);
        let errorMessage = 'שגיאה לא ידועה';

        if (error instanceof Error) {
            errorMessage = error.message;
        } else if (typeof error === 'string') {
            errorMessage = error;
        } else if (error && error.message) {
            errorMessage = error.message;
        } else if (error && error.detail) {
            errorMessage = error.detail;
        }

        this.showToast('שגיאה בשליחת השאילתה הקולית: ' + errorMessage, 'error');
        this.elements.statusIndicator.innerHTML = '<i class="fas fa-circle"></i> מוכן לשאלות';
    } finally {
        this.setLoading(false);
    }
};

// Global logout function
function handleLogout() {
    if (window.chatbot) {
        window.chatbot.logout();
    } else {
        localStorage.clear();
        window.location.href = 'login.html';
    }
}

// Global voice recording function
function toggleRecording() {
    if (window.chatbot) {
        window.chatbot.toggleRecording();
    }
}

// Service worker registration (for future PWA capabilities)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // Future: Register service worker for offline capabilities
    });
}

// ========================================
// NEW SIDEBAR FEATURES
// ========================================

function showFeatureInDevelopment() {
    const toast = document.getElementById('toast');
    const toastMessage = toast.querySelector('.toast-message');

    toastMessage.textContent = '🚧 בפיתוח';
    toast.classList.add('show', 'warning');

    setTimeout(() => {
        toast.classList.remove('show', 'warning');
    }, 2000);
}

// Initialize sample chart placeholder (only in sidebar)
function initSampleChart() {
    const container = document.querySelector('.sidebar .graph-container');
    if (!container) {
        console.warn('Sidebar graph container not found');
        return;
    }

    container.innerHTML = '';
    const placeholder = document.createElement('div');
    placeholder.style.minHeight = '200px';
    placeholder.style.display = 'flex';
    placeholder.style.alignItems = 'center';
    placeholder.style.justifyContent = 'center';
    placeholder.style.color = '#6b7280';
    placeholder.style.fontSize = '0.95rem';
    placeholder.textContent = 'גרף עדכני יופיע כאן לאחר שאילתא.';
    container.appendChild(placeholder);

    if (typeof Chart !== 'undefined') {
        const canvasEl = document.createElement('canvas');
        canvasEl.id = 'sampleChart';
        canvasEl.style.display = 'none'; // יופעל רק כשיגיע viz ראשון
        canvasEl.width = 250;
        canvasEl.height = 200;
        container.appendChild(canvasEl);
        try { if (window.chatbot) window.chatbot.sidebarChart = null; } catch (e) { }
    }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    initSampleChart();
});