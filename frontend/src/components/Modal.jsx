import React, { useEffect } from 'react';

export default function Modal({ isOpen, onClose, title, subtitle, children }) {
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEsc);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <button style={styles.close} onClick={onClose}>✕</button>
        
        {title && <h2 style={styles.title}>{title}</h2>}
        {subtitle && <p style={styles.subtitle}>{subtitle}</p>}
        
        <div style={styles.content}>
          {children}
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: '20px'
  },
  modal: {
    background: 'var(--card)',
    border: '1px solid var(--border)',
    borderRadius: '8px',
    maxWidth: '700px',
    width: '100%',
    maxHeight: '90vh',
    overflow: 'auto',
    padding: '24px',
    position: 'relative'
  },
  close: {
    position: 'absolute',
    top: '16px',
    right: '16px',
    background: 'none',
    color: 'var(--text)',
    fontSize: '20px',
    padding: '4px 8px',
    cursor: 'pointer'
  },
  title: {
    fontSize: '18px',
    fontWeight: 600,
    marginBottom: '8px',
    color: 'var(--text)'
  },
  subtitle: {
    fontSize: '12px',
    color: 'var(--text-dim)',
    marginBottom: '20px'
  },
  content: {
    marginTop: '20px'
  }
};
