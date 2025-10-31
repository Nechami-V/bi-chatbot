import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Chat from './pages/Chat.jsx'
import Header from './components/Header.jsx'
import { useAuth } from './hooks/useAuth.js'

export default function App() {
  const { token, signOut } = useAuth()
  return (
    <div className="app-container">
      <Header onLogout={signOut} />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={token ? <Chat /> : <Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to={token ? '/' : '/login'} replace />} />
      </Routes>
    </div>
  )
}
