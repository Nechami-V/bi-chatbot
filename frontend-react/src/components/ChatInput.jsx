import React, { useState } from 'react'

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const send = () => {
    const q = value.trim()
    if (!q) return
    onSend?.(q)
    setValue('')
  }
  return (
    <div className="card row" style={{gap:10}}>
      <textarea className="textarea" dir="rtl" placeholder="שאל/י שאלה בעברית" value={value} onChange={e=>setValue(e.target.value)} onKeyDown={e=>{ if(e.key==='Enter' && (e.ctrlKey||e.metaKey)) send() }} />
      <div className="row" style={{justifyContent:'space-between', width:'100%'}}>
        <div className="muted">Ctrl/Cmd+Enter לשליחה</div>
        <button className="btn" disabled={disabled} onClick={send}>שליחה</button>
      </div>
    </div>
  )
}

