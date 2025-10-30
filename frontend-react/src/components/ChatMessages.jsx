import React from 'react'
import MessageBubble from './MessageBubble.jsx'

export default function ChatMessages({ messages }) {
  if (!messages?.length) return null
  return (
    <div className="messages">
      {messages.map((m, i) => (
        <MessageBubble key={i} role={m.role} text={m.text} />
      ))}
    </div>
  )
}

