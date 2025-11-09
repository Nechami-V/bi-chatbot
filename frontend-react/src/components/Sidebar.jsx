import React from 'react'

export default function Sidebar({ onFeature }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-section graph-section">
        <div className="graph-header">
          <button className="btn" onClick={onFeature}><span>גרפים (בקרוב)</span></button>
        </div>
        <div className="graph-container" />
      </div>
      <div className="sidebar-section features-section">
        <h3>פיצ'רים</h3>
        <div className="feature-grid">
          {[
            ['ניתוח מגמות','fa-chart-line'],
            ['ייצוא תוצאות','fa-file-export'],
            ['ייבוא CSV','fa-file-import'],
            ['המלצות','fa-lightbulb'],
            ['הרשאות','fa-shield-alt'],
          ].map(([label, icon]) => (
            <button key={label} className="feature-btn" onClick={onFeature}>
              <i className={`fas ${icon}`}></i>
              <span>{label}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}

