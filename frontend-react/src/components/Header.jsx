import React from 'react'
import { useAuth } from '../hooks/useAuth.js'

export default function Header({ onLogout }) {
  const { user } = useAuth()
  const initials = (user?.full_name || user?.username || user?.email || '?')
    .split(' ').map(s=>s[0]).join('').slice(0,2).toUpperCase()
  return (
    <header className="header">
      <div className="header-content container">
        <div className="header-logo">
          <div className="logo-image-fallback">KT</div>
          <div className="brand-info">
            <h1>BI Chatbot</h1>
            <p className="muted">עוזר BI לשאילתות בעברית</p>
          </div>
        </div>
        <div className="user-section">
          <div className="user-info">
            <div className="user-avatar">{initials}</div>
            <div className="user-details">
              <span className="user-name">{user?.full_name || user?.username || 'משתמש/ת'}</span>
              <span className="user-role muted">{user?.permission_group || 'user'}</span>
            </div>
          </div>
          <button className="btn" onClick={onLogout}>התנתקות</button>
        </div>
      </div>
    </header>
  )
}

