import React from 'react';

export default function StatCard({ icon, label, value, subtext, subtextColor }) {
  return (
    <div
      style={styles.card}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'rgba(0,255,136,0.3)';
        e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.3)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <div style={styles.header}>
        <span className="material-icons" style={styles.icon}>{icon}</span>
        <span style={styles.label}>{label}</span>
      </div>
      <div style={styles.value}>{value}</div>
      {subtext && (
        <div style={{ ...styles.subtext, color: subtextColor || 'var(--text-dim)' }}>
          {subtext}
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    background: 'var(--card)',
    border: '1px solid var(--border)',
    borderRadius: '8px',
    padding: '20px 24px',
    flex: 1,
    transition: 'all 0.25s ease',
    cursor: 'default'
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '12px'
  },
  icon: {
    fontSize: '20px',
    color: 'var(--green)'
  },
  label: {
    fontSize: '11px',
    color: 'var(--text-dim)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  value: {
    fontSize: '48px',
    fontWeight: 300,
    color: 'var(--text)',
    marginBottom: '8px',
    lineHeight: 1.1
  },
  subtext: {
    fontSize: '12px'
  }
};
