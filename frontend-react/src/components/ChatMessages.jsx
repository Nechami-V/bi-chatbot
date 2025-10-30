import React from 'react'

export default function ChatMessages({ messages }) {
  return (
    <div className="chat-messages" id="chatMessages">
      {/* Welcome (optional) can be injected here if needed */}
      {messages?.map((m, i) => (
        <div key={i} className={`message ${m.role === 'me' ? 'user-message' : 'bot-message'}`}>
          <div className="message-avatar">
            <img src="/assets/kt-logo.png" alt="KT Bot" />
          </div>
          <div className="message-content">
            <p>{m.text}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
