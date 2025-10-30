import React, { useState } from 'react'
import { useAuth } from '../hooks/useAuth.js'
import { ask } from '../services/api.js'
import ChatInput from '../components/ChatInput.jsx'
import ChatMessages from '../components/ChatMessages.jsx'
import SqlPanel from '../components/SqlPanel.jsx'
import DataTable from '../components/DataTable.jsx'
import ErrorBanner from '../components/ErrorBanner.jsx'
import Loader from '../components/Loader.jsx'
import Header from '../components/Header.jsx'
import Sidebar from '../components/Sidebar.jsx'
import Toast from '../components/Toast.jsx'

export default function Chat() {
  const { token } = useAuth()
  const [messages, setMessages] = useState([])
  const [sql, setSql] = useState('')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  async function onSend(question) {
    setError('')
    setLoading(true)
    setMessages(m => [...m, { role: 'me', text: question }])
    try {
      const resp = await ask(token, question)
      setSql(resp?.sql || '')
      setData(resp?.data || [])
      const ans = (resp?.answer || '').trim()
      if (ans) setMessages(m => [...m, { role: 'ai', text: ans }])
    } catch (e) {
      setError(String(e?.message || e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Header onLogout={()=> setToast('התנתקת בהצלחה')} />
      <div className="main-wrapper container" style={{display:'flex', gap:16}}>
        <main className="chat-container" style={{flex:1}}>
          <ErrorBanner error={error} />
          <ChatInput onSend={onSend} disabled={loading} />
          {loading && <Loader text="מחשב/ת תשובה..." />}
          <ChatMessages messages={messages} />
          <SqlPanel sql={sql} />
          <DataTable data={data} />
        </main>
        <Sidebar onFeature={()=> setToast('בקרוב...')} />
      </div>
      <Toast message={toast} onClose={()=> setToast('')} />
    </>
  )
}
