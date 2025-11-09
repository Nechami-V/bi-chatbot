import React from 'react'
export default function ErrorBanner({ error }) {
  if (!error) return null
  return <div className="error">{String(error)}</div>
}

