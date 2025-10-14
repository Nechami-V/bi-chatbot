// KT BI Chatbot Frontend - Modern JavaScript Implementation with Authentication
class BiChatbot {
    constructor() {
        this.apiUrl = 'http://localhost:8002';
        this.isLoading = false;
        this.messageCount = 0;
        this.authToken = null;
        this.userInfo = null;
        
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
        console.log('🚀 KT BI Chatbot initialized');
        
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
        input.addEventListener('input', function() {
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
            this.showToast('לא ניתן להתחבר לשרת. בדוק שהשרת רץ על localhost:8000', 'error');
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
        this.updateCharCount(0);
        this.toggleSendButton();
        
        // Show loading
        this.setLoading(true);
        
        try {
            // Send to API with authentication
            const response = await fetch(`${this.apiUrl}/ask`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({ question: message })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
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
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-${type === 'user' ? 'user' : 'robot'}"></i>
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
        
        // Add the main answer (clean and simple)
        if (data.answer) {
            content += `<p>${this.escapeHtml(data.answer)}</p>`;
        }
        
        // Add data table if available (but clean)
        if (data.data && Array.isArray(data.data) && data.data.length > 0) {
            content += this.formatSimpleDataTable(data.data);
        }
        
        // Add technical details in a collapsible section (optional)
        const hasDetails = data.sql_query || data.execution_time;
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
            
            if (data.sql_query) {
                content += `
                    <div style="margin-bottom: 0.75rem; padding: 0.5rem; background: #f8fafc; border-radius: 0.5rem; border-right: 2px solid #64748b;">
                        <p style="font-weight: 600; color: #475569; margin-bottom: 0.25rem; font-size: 0.85rem;">
                            <i class="fas fa-database"></i> SQL Query:
                        </p>
                        <code style="background: #ffffff; padding: 0.5rem; border-radius: 0.25rem; display: block; font-family: 'Courier New', monospace; font-size: 0.8rem; direction: ltr; text-align: left; color: #374151;">
                            ${this.escapeHtml(data.sql_query)}
                        </code>
                    </div>
                `;
            }
            
            if (data.execution_time) {
                content += `
                    <p style="font-size: 0.8rem; color: #64748b; margin: 0;">
                        <i class="fas fa-clock"></i> זמן ביצוע: ${data.execution_time.toFixed(2)} שניות
                    </p>
                `;
            }
            
            content += `</div></div>`;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                ${content}
            </div>
        `;
        
        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatSimpleDataTable(data) {
        if (!data || data.length === 0) return '';
        
        const headers = Object.keys(data[0]);
        const maxRows = 5; // Show only top 5 results for cleaner look
        
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
        
        data.slice(0, maxRows).forEach((row, index) => {
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
        // Keep the old function for technical details section if needed
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
        
        // Auto-hide after 5 seconds
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

// Add some helpful utilities
window.addEventListener('beforeunload', (e) => {
    if (window.chatbot && window.chatbot.isLoading) {
        e.preventDefault();
        e.returnValue = 'יש בקשה בתהליך. האם אתה בטוח שברצונך לצאת?';
    }
});

// Authentication Methods - Added to BiChatbot class
BiChatbot.prototype.checkAuthentication = function() {
    const token = localStorage.getItem('authToken');
    const userInfo = localStorage.getItem('userInfo');
    
    console.log('🔐 Checking authentication:', {
        hasToken: !!token,
        hasUserInfo: !!userInfo,
        tokenLength: token ? token.length : 0
    });
    
    if (!token || !userInfo) {
        console.log('❌ Missing authentication data, redirecting to login');
        // Redirect to login
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

BiChatbot.prototype.setupUserInterface = function() {
    const user = this.userInfo.user;
    
    // Update user display
    this.elements.userName.textContent = user.full_name;
    this.elements.userRole.textContent = this.getRoleDisplay(user.permission_group);
    
    // Create user initials
    const initials = this.getUserInitials(user.first_name, user.last_name);
    this.elements.userAvatar.textContent = initials;
    
    // Update welcome message
    this.elements.welcomeText.innerHTML = `
        <strong>שלום ${user.first_name}!</strong> אני הצ'אט בוט שלך לניתוח נתונים עסקיים.
        <br>אני כאן כדי לעזור לך להבין את הנתונים שלך ולענות על השאלות העסקיות שלך.
    `;
};

BiChatbot.prototype.getUserInitials = function(firstName, lastName) {
    if (!firstName || !lastName) return '??';
    return firstName.charAt(0) + lastName.charAt(0);
};

BiChatbot.prototype.getRoleDisplay = function(permissionGroup) {
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

BiChatbot.prototype.getAuthHeaders = function() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.authToken}`
    };
};

BiChatbot.prototype.logout = function() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('tokenType');
    localStorage.removeItem('userInfo');
    window.location.href = 'login.html';
};

// Voice recording functions
BiChatbot.prototype.toggleRecording = async function() {
    console.log('🎤 Toggle recording called, authToken:', this.authToken ? 'EXISTS' : 'NULL');
    
    if (!this.authToken) {
        console.error('❌ No auth token available');
        this.showToast('יש להתחבר תחילה', 'error');
        return;
    }
    
    if (!this.isRecording) {
        await this.startRecording();
    } else {
        await this.stopRecording();
    }
};

BiChatbot.prototype.startRecording = async function() {
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
        
        console.log('🎤 Recording started');
        
        // Update UI
        this.elements.voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
        this.elements.voiceBtn.classList.add('recording');
        this.elements.statusIndicator.innerHTML = '<i class="fas fa-circle"></i> מקליט...';
        
    } catch (error) {
        console.error('Microphone error:', error);
        this.showToast('שגיאה בגישה למיקרופון: ' + error.message, 'error');
    }
};

BiChatbot.prototype.stopRecording = async function() {
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

BiChatbot.prototype.sendVoiceQuery = async function(audioBlob) {
    this.setLoading(true);
    
    console.log('🎙️ Sending voice query:', {
        size: audioBlob.size,
        type: audioBlob.type,
        authToken: this.authToken ? 'Present' : 'Missing',
        apiUrl: this.apiUrl
    });
    
    try {
        debugger;
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recording.webm');
        
        console.log('📤 Making fetch request to:', `${this.apiUrl}/voice-query`);
        console.log('📤 Request headers:', { 'Authorization': `Bearer ${this.authToken}` });
        console.log('📤 FormData entries:');
        for (let [key, value] of formData.entries()) {
            console.log(`  ${key}:`, value instanceof Blob ? `Blob(${value.size} bytes, ${value.type})` : value);
        }
        
        const response = await fetch(`${this.apiUrl}/voice-query`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.authToken}`
            },
            body: formData
        });
        
        console.log('📥 Response received:', response.status, response.statusText);
        
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
        this.processResponse(data);
        
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
        console.log('📱 Service Worker support detected');
        // Future: Register service worker for offline capabilities
    });
}