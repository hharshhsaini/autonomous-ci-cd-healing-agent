import React from 'react';

function Timeline({ timeline }) {
  if (!timeline || timeline.length === 0) {
    return (
      <div style={styles.container}>
        <h3 style={styles.title}>Timeline</h3>
        <div style={styles.loading}>
          <span className="material-icons" style={styles.spinner}>hourglass_empty</span>
          <span>Agent pipeline running...</span>
        </div>
      </div>
    );
  }

  const agentColors = {
    'Clone Agent': '#58a6ff',
    'Copybara Transform': '#14b8a6',
    'Test Agent': '#d29922',
    'Analyze Agent': '#bc8cff',
    'Fix Agent': '#f0e68c',
    'Verify Agent': '#3fb950',
    'Git Push Agent': '#238636'
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour12: false });
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>Timeline</h3>
      
      <div style={styles.timeline}>
        {timeline.map((event, idx) => {
          const dotColor = event.passed === false 
            ? '#f85149' 
            : agentColors[event.agent] || '#8b949e';
          
          return (
            <div key={idx} style={{
              ...styles.event,
              animation: `fadeIn 0.3s ease-in ${idx * 0.1}s both`
            }}>
              <div style={styles.timeColumn}>
                <span style={styles.time}>{formatTime(event.timestamp)}</span>
              </div>
              
              <div style={styles.lineColumn}>
                <div style={{
                  ...styles.dot,
                  background: dotColor
                }} />
                {idx < timeline.length - 1 && <div style={styles.line} />}
              </div>
              
              <div style={styles.contentColumn}>
                <div style={styles.agentName}>{event.agent}</div>
                <div style={styles.message}>{event.msg}</div>
                <div style={styles.badges}>
                  {event.iteration > 0 && (
                    <span style={styles.iterationBadge}>
                      Iteration {event.iteration}/5
                    </span>
                  )}
                  {event.passed !== undefined && (
                    <span style={{
                      ...styles.statusBadge,
                      background: event.passed ? '#238636' : '#da3633'
                    }}>
                      {event.passed ? 'PASSED' : 'FAILED'}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const styles = {
  container: {
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
  loading: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    color: '#8b949e',
    padding: '20px'
  },
  spinner: {
    fontSize: '24px',
    animation: 'spin 2s linear infinite'
  },
  timeline: {
    position: 'relative'
  },
  event: {
    display: 'flex',
    gap: '16px',
    marginBottom: '8px'
  },
  timeColumn: {
    width: '80px',
    flexShrink: 0
  },
  time: {
    color: '#8b949e',
    fontSize: '12px',
    fontFamily: 'monospace'
  },
  lineColumn: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: '20px',
    flexShrink: 0
  },
  dot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    flexShrink: 0
  },
  line: {
    width: '2px',
    flex: 1,
    background: '#30363d',
    minHeight: '30px'
  },
  contentColumn: {
    flex: 1,
    paddingBottom: '16px'
  },
  agentName: {
    color: '#c9d1d9',
    fontWeight: 'bold',
    fontSize: '14px',
    marginBottom: '4px'
  },
  message: {
    color: '#8b949e',
    fontSize: '13px',
    marginBottom: '8px'
  },
  badges: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap'
  },
  iterationBadge: {
    padding: '2px 8px',
    background: '#21262d',
    color: '#8b949e',
    fontSize: '11px',
    borderRadius: '12px',
    border: '1px solid #30363d'
  },
  statusBadge: {
    padding: '2px 8px',
    color: 'white',
    fontSize: '11px',
    fontWeight: 'bold',
    borderRadius: '12px'
  }
};

export default Timeline;
