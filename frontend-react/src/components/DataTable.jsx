import React from 'react'

export default function DataTable({ data }) {
  if (!data || !Array.isArray(data) || data.length === 0) return null
  const keys = Object.keys(data[0] || {})
  return (
    <div className="card">
      <div className="header"><div>תוצאות</div><div className="muted">{data.length} שורות</div></div>
      <div style={{overflowX:'auto'}}>
        <table dir="rtl">
          <thead>
            <tr>
              {keys.map(k => <th key={k}>{k}</th>)}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i}>
                {keys.map(k => <td key={k}>{String(row?.[k] ?? '')}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

