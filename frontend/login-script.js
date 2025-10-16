// Login Script for KT BI Chatbot
const API_BASE = 'http://localhost:8002';

// DOM Elements
const loginForm = document.getElementById('loginForm');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const loginBtn = document.querySelector('.login-btn');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Check if already logged in
    const token = localStorage.getItem('authToken');
    if (token) {
        // Verify token is still valid
        verifyTokenAndRedirect(token);
    }
    
    // Setup form handler
    loginForm.addEventListener('submit', handleLogin);
});

// Handle login form submission
async function handleLogin(e) {
    e.preventDefault();
    
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();
    
    if (!email || !password) {
        showError('אנא הכנס אימייל וסיסמה');
        return;
    }
    
    setLoading(true);
    hideError();
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Save token and user data
            localStorage.setItem('authToken', data.access_token);
            localStorage.setItem('tokenType', data.token_type);
            
            // Get user info
            const userInfo = await getUserInfo(data.access_token);
            if (userInfo) {
                localStorage.setItem('userInfo', JSON.stringify(userInfo));
                
                // Show success and redirect
                showSuccess('התחברת בהצלחה! מעביר לצ\'אטבוט...');
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1500);
            }
        } else {
            showError(data.detail || 'שגיאה בהתחברות. אנא בדוק את הפרטים ונסה שוב');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('שגיאת תקשורת. אנא בדוק את החיבור לאינטרנט');
    } finally {
        setLoading(false);
    }
}

// Get user info after login
async function getUserInfo(token) {
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            return data;
        }
    } catch (error) {
        console.error('Error getting user info:', error);
    }
    return null;
}

// Verify existing token and redirect if valid
async function verifyTokenAndRedirect(token) {
    try {
        const userInfo = await getUserInfo(token);
        if (userInfo) {
            localStorage.setItem('userInfo', JSON.stringify(userInfo));
            window.location.href = 'index.html';
            return;
        }
    } catch (error) {
        // Token is invalid, clear storage
        localStorage.removeItem('authToken');
        localStorage.removeItem('tokenType');
        localStorage.removeItem('userInfo');
    }
}

// Removed demo user functionality - users exist only in database

// Toggle password visibility
function togglePassword() {
    const eyeIcon = document.getElementById('eyeIcon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        eyeIcon.className = 'fas fa-eye-slash';
    } else {
        passwordInput.type = 'password';
        eyeIcon.className = 'fas fa-eye';
    }
}

// UI Helper Functions
function setLoading(loading) {
    if (loading) {
        loginBtn.classList.add('loading');
        loginBtn.disabled = true;
    } else {
        loginBtn.classList.remove('loading');
        loginBtn.disabled = false;
    }
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.style.display = 'flex';
}

function hideError() {
    errorMessage.style.display = 'none';
}

function showSuccess(message) {
    // Create temporary success message
    const successDiv = document.createElement('div');
    successDiv.className = 'error-message';
    successDiv.style.background = 'rgba(16, 185, 129, 0.1)';
    successDiv.style.borderColor = 'var(--success-color)';
    successDiv.style.color = 'var(--success-color)';
    successDiv.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;
    
    // Replace error message temporarily
    const parent = errorMessage.parentNode;
    parent.insertBefore(successDiv, errorMessage);
    errorMessage.style.display = 'none';
    
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

// Handle Enter key in form
emailInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        passwordInput.focus();
    }
});

passwordInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        loginForm.dispatchEvent(new Event('submit'));
    }
});