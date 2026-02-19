import React from 'react';

function RunSummaryCard({ data }) {
  if (!data) return null;

  const truncateUrl = (url) => {
    if (url.length > 50) return url.substring(0, 47) + '...';
    return url;
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const borderColor = data.verify_passed ? '#238636' : '#da3633';
  const ciStatus = data.verify_passed ? (
    <>
      <span className="material-icons" style={{ fontSize: 16, verticalAlign: 'middle', marginRight: 4 }}>check_circle</span>
      PASSED
    </>
  ) : (
    <>
      <span className="material-icons" style={{ fontSize: 16, verticalAlign: 'middle', marginRight: 4 }}>cancel</span>
      FAILED
    </>
  );

  return (
    <div style={{ ...styles.card, borderColor }}>
      <h3 style={styles.title}>Run Summary</h3>
      
      <div style={styles.row}>
        <span style={styles.label}>Repository:</span>
        <a href={data.repo_url} target="_blank" rel="noopener noreferrer" style={styles.link}>
          {truncateUrl(data.repo_url)} 🔗
        </a>
      </div>

      <div style={styles.row}>
        <span style={styles.label}>Team:</span>
        <span style={styles.value}>{data.team_name}</span>
        <span style={styles.separator}>|</span>
        <span style={styles.label}>Leader:</span>
        <span style={styles.value}>{data.leader_name}</span>
      </div>

      <div style={styles.row}>
        <span style={styles.label}>Branch:</span>
        <code style={styles.branch}>⎇ {data.branch_name}</code>
      </div>

      <div style={styles.row}>
        <span style={styles.label}>Failures Detected:</span>
        <span style={styles.value}>{data.errors_found}</span>
        <span style={styles.separator}>|</span>
        <span style={styles.label}>Fixes Applied:</span>
        <span style={styles.value}>{data.errors_fixed}</span>
      </div>

      <div style={styles.row}>
        <span style={styles.label}>CI/CD Status:</span>
        <span style={{
          ...styles.badge,
          background: data.verify_passed ? '#238636' : '#da3633'
        }}>
          {ciStatus}
        </span>
      </div>

      <div style={styles.row}>
        <span style={styles.label}>Total Time:</span>
        <span style={styles.value}>{formatTime(data.score?.elapsed_seconds || 0)}</span>
      </div>
    </div>
  );
}

const styles = {
  card: {
    background: '#161b22',
    padding: '24px',
    borderRadius: '8px',
    border: '2px solid',
    marginBottom: '20px'
  },
  title: {
    color: '#c9d1d9',
    marginBottom: '20px',
    fontSize: '18px'
  },
  row: {
    display: 'flex',
    alignItems: 'center',
    marginBottom: '12px',
    flexWrap: 'wrap',
    gap: '8px'
  },
  label: {
    color: '#8b949e',
    fontSize: '14px'
  },
  value: {
    color: '#c9d1d9',
    fontSize: '14px',
    fontWeight: '500'
  },
  separator: {
    color: '#30363d',
    margin: '0 8px'
  },
  link: {
    color: '#58a6ff',
    textDecoration: 'none',
    fontSize: '14px'
  },
  branch: {
    background: '#0d1117',
    padding: '4px 8px',
    borderRadius: '4px',
    color: '#58a6ff',
    fontFamily: 'monospace',
    fontSize: '13px'
  },
  badge: {
    padding: '4px 12px',
    borderRadius: '12px',
    color: 'white',
    fontSize: '12px',
    fontWeight: 'bold'
  }
};

export default RunSummaryCard;
