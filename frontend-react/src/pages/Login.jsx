import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.js'
import ErrorBanner from '../components/ErrorBanner.jsx'

export default function Login() {
  const nav = useNavigate()
  const { signIn, error } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setLoading(true)
    try {
      await signIn(email, password)
      nav('/')
    } catch (e) {
      // error handled in hook
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container" style={{maxWidth: 460}}>
      <div className="card">
        <h2 style={{marginTop:0}}>התחברות</h2>
        <form onSubmit={submit} className="col">
          <label>אימייל</label>
          <input className="input" dir="ltr" value={email} onChange={e=>setEmail(e.target.value)} />
          <label>סיסמה</label>
          <input className="input" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          <ErrorBanner error={error} />
          <button className="btn" disabled={loading}>{loading ? 'מתחבר/ת...' : 'התחברות'}</button>
        </form>
      </div>
    </div>
  )
}

