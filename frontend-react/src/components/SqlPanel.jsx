import React from 'react'

export default function SqlPanel({ sql }) {
  if (!sql) return null
  return (
    <div className="card">
      <div className="header"><div>SQL</div></div>
      <pre className="sql" dir="ltr">{sql}</pre>
    </div>
  )
}

