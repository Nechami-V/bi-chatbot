import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.js'

export default function Navbar() {
  const { user, signOut } = useAuth()
  const nav = useNavigate()
  function onLogout() { signOut(); nav('/login') }
  return (
    <div className="nav">
      <div className="container row" style={{justifyContent:'space-between'}}>
        <div className="brand">BI Chatbot</div>
        <div className="row" style={{gap:16}}>
          <Link to="/">צ'אט</Link>
          {user ? (
            <button className="btn" onClick={onLogout}>התנתקות</button>
          ) : (
            <Link className="btn" to="/login">כניסה</Link>
          )}
        </div>
      </div>
    </div>
  )
}

