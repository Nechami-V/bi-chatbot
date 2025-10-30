import React from 'react'

export default function MessageBubble({ role, text }) {
  const me = role === 'me'
  return (
    <div className={`bubble ${me ? 'me' : 'ai'}`} dir="rtl">
      {text}
    </div>
  )
}

