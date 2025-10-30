import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Chat from './pages/Chat.jsx'
import Navbar from './components/Navbar.jsx'
import { useAuth } from './hooks/useAuth.js'

export default function App() {
  const { token } = useAuth()
  return (
    <div className="app">
      <Navbar />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={token ? <Chat /> : <Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to={token ? '/' : '/login'} replace />} />
      </Routes>
    </div>
  )
}

