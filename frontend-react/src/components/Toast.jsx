import React, { useEffect } from 'react'

export default function Toast({ message, onClose }) {
  useEffect(()=>{
    if (!message) return
    const id = setTimeout(()=> onClose?.(), 2500)
    return ()=> clearTimeout(id)
  }, [message])
  if (!message) return null
  return (
    <div className="toast" role="alert">
      <span className="toast-message">{message}</span>
      <button className="toast-close" onClick={onClose}>×</button>
    </div>
  )
}

