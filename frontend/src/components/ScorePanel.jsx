import React from 'react';

function ScorePanel({ score }) {
  if (!score || !score.total) return null;

  const total = score.total || 0;
  const base = score.base || 100;
  const speedBonus = score.speed_bonus || 0;
  const penalty = score.penalty || 0;
  const commitCount = score.commit_count || 0;
  const elapsed = score.elapsed_seconds || 0;

  const percentage = Math.min((total / 110) * 100, 100);
  const barColor = total >= 100 ? '#238636' : total >= 80 ? '#d29922' : '#da3633';

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={styles.card}>
      <h3 style={styles.title}>Score</h3>
      
      <div style={styles.scoreDisplay}>
        <span style={styles.scoreNumber}>{total}</span>
        <span style={styles.scoreMax}>/110</span>
      </div>

      <div style={styles.breakdown}>
        <div style={styles.breakdownRow}>
          <span style={styles.breakdownLabel}>Base Score:</span>
          <span style={styles.breakdownValue}>{base}</span>
        </div>
        
        <div style={styles.breakdownRow}>
          <span style={styles.breakdownLabel}>Speed Bonus (&lt;5 min):</span>
          <span style={{
            ...styles.breakdownValue,
            color: speedBonus > 0 ? '#3fb950' : '#6e7681'
          }}>
            +{speedBonus}
          </span>
        </div>
        
        <div style={styles.breakdownRow}>
          <span style={styles.breakdownLabel}>Commit Penalty:</span>
          <span style={{
            ...styles.breakdownValue,
            color: penalty > 0 ? '#f85149' : '#6e7681'
          }}>
            -{penalty}
          </span>
        </div>
        
        <div style={styles.breakdownRow}>
          <span style={styles.breakdownLabel}>Commits Used:</span>
          <span style={styles.breakdownValue}>{commitCount}/20</span>
        </div>
      </div>

      <div style={styles.progressBar}>
        <div style={{
          ...styles.progressFill,
          width: `${percentage}%`,
          background: barColor
        }} />
      </div>

      <div style={styles.speedIndicator}>
        {elapsed < 300 ? (
          <span style={styles.speedBonus}>
            <span className="material-icons" style={{ fontSize: 16, verticalAlign: 'middle', marginRight: 4 }}>bolt</span>
            SPEED BONUS ACHIEVED
          </span>
        ) : (
          <span style={styles.speedNormal}>
            <span className="material-icons" style={{ fontSize: 16, verticalAlign: 'middle', marginRight: 4 }}>schedule</span>
            {formatTime(elapsed)} elapsed
          </span>
        )}
      </div>
    </div>
  );
}

const styles = {
  card: {
    background: '#161b22',
    padding: '24px',
    borderRadius: '8px',
    border: '1px solid #30363d',
    marginBottom: '20px'
  },
  title: {
    color: '#c9d1d9',
    marginBottom: '20px',
    fontSize: '18px'
  },
  scoreDisplay: {
    textAlign: 'center',
    marginBottom: '24px'
  },
  scoreNumber: {
    fontSize: '64px',
    fontWeight: 'bold',
    color: '#58a6ff'
  },
  scoreMax: {
    fontSize: '24px',
    color: '#8b949e',
    marginLeft: '8px'
  },
  breakdown: {
    marginBottom: '20px'
  },
  breakdownRow: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '10px'
  },
  breakdownLabel: {
    color: '#8b949e',
    fontSize: '14px'
  },
  breakdownValue: {
    color: '#c9d1d9',
    fontSize: '14px',
    fontWeight: '500'
  },
  progressBar: {
    width: '100%',
    height: '12px',
    background: '#0d1117',
    borderRadius: '6px',
    overflow: 'hidden',
    marginBottom: '16px'
  },
  progressFill: {
    height: '100%',
    transition: 'width 0.3s ease'
  },
  speedIndicator: {
    textAlign: 'center'
  },
  speedBonus: {
    color: '#3fb950',
    fontSize: '14px',
    fontWeight: 'bold'
  },
  speedNormal: {
    color: '#8b949e',
    fontSize: '14px'
  }
};

export default ScorePanel;
