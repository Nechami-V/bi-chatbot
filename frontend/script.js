// BI Chatbot Frontend - Modern JavaScript Implementation
class BiChatbot {
    constructor() {
        this.apiUrl = 'http://localhost:8080';
        this.isLoading = false;
        this.messageCount = 0;
        
        // DOM Elements
        this.elements = {
            chatMessages: document.getElementById('chatMessages'),
            messageInput: document.getElementById('messageInput'),
            chatForm: document.getElementById('chatForm'),
            sendBtn: document.getElementById('sendBtn'),
            charCount: document.getElementById('charCount'),
            statusIndicator: document.getElementById('statusIndicator'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            toast: document.getElementById('toast')
        };
        
        this.init();
    }
    
    init() {
        console.log('🚀 BI Chatbot initialized');
        
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
            // Send to API
            const response = await fetch(`${this.apiUrl}/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
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

// Service worker registration (for future PWA capabilities)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        console.log('📱 Service Worker support detected');
        // Future: Register service worker for offline capabilities
    });
}