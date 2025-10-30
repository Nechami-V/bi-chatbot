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
    <div className="input-container">
      <form className="input-form" onSubmit={e=>{e.preventDefault(); send()}}>
        <div className="input-wrapper">
          <input
            type="text"
            id="messageInput"
            className="input"
            placeholder="שאל/י שאלה"
            dir="rtl"
            autoComplete="off"
            maxLength={500}
            value={value}
            onChange={e=>setValue(e.target.value)}
          />
          <button type="button" id="voiceBtn" className="voice-btn" onClick={()=>{}}>
            <i className="fas fa-microphone"></i>
          </button>
          <button type="submit" id="sendBtn" className="send-btn" disabled={disabled}>
            <i className="fas fa-paper-plane"></i>
          </button>
        </div>
        <div className="input-footer">
          <span className="char-count">{value.length}/500</span>
          <span className="status" id="statusIndicator">
            <i className="fas fa-circle"></i> מוכן לקבלת הודעה
          </span>
        </div>
      </form>
    </div>
  )
}
