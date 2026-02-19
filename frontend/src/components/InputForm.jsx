import React, { useState } from 'react';

function InputForm({ onSubmit, loading }) {
  const [githubUrl, setGithubUrl] = useState('');
  const [teamName, setTeamName] = useState('');
  const [leaderName, setLeaderName] = useState('');
  const [branchOverride, setBranchOverride] = useState(false);
  const [customBranch, setCustomBranch] = useState('');

  const autoBranch = teamName && leaderName
    ? `${teamName.toUpperCase().replace(/\s+/g, '_')}_${leaderName.toUpperCase().replace(/\s+/g, '_')}_AI_Fix`
    : 'TEAM_NAME_LEADER_NAME_AI_Fix';

  const finalBranch = branchOverride && customBranch ? customBranch : autoBranch;

  const isValid = githubUrl && teamName && leaderName;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isValid && !loading) {
      onSubmit({ 
        githubUrl, 
        teamName, 
        leaderName,
        branchName: finalBranch
      });
    }
  };

  const handleEditBranch = () => {
    setBranchOverride(true);
    setCustomBranch(autoBranch);
  };

  return (
    <div style={styles.container}>
      <form onSubmit={handleSubmit} style={styles.form}>
        <h2 style={styles.title}>RIFT Healing Agent</h2>
        
        <div style={styles.field}>
          <label style={styles.label}>GitHub Repository URL</label>
          <input
            type="text"
            value={githubUrl}
            onChange={(e) => setGithubUrl(e.target.value)}
            placeholder="https://github.com/username/repo"
            style={styles.input}
            disabled={loading}
          />
        </div>

        <div style={styles.row}>
          <div style={styles.field}>
            <label style={styles.label}>Team Name</label>
            <input
              type="text"
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
              placeholder="Team Alpha"
              style={styles.input}
              disabled={loading}
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Team Leader Name</label>
            <input
              type="text"
              value={leaderName}
              onChange={(e) => setLeaderName(e.target.value)}
              placeholder="John Doe"
              style={styles.input}
              disabled={loading}
            />
          </div>
        </div>

        <div style={styles.preview}>
          <div style={styles.previewHeader}>
            <span style={styles.previewLabel}>Branch Preview:</span>
            {!branchOverride && (
              <button
                type="button"
                onClick={handleEditBranch}
                style={styles.editButton}
                disabled={loading}
              >
                ✏️ Edit
              </button>
            )}
          </div>
          
          {branchOverride ? (
            <div style={styles.branchEditWrapper}>
              <input
                type="text"
                value={customBranch}
                onChange={(e) => setCustomBranch(e.target.value)}
                style={styles.branchInput}
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setBranchOverride(false)}
                style={styles.cancelButton}
                disabled={loading}
              >
                ✕
              </button>
            </div>
          ) : (
            <code style={styles.previewCode}>{finalBranch}</code>
          )}
        </div>

        <button
          type="submit"
          disabled={!isValid || loading}
          style={{
            ...styles.button,
            ...((!isValid || loading) && styles.buttonDisabled)
          }}
        >
          {loading ? (
            <>
              <span className="material-icons" style={{ fontSize: 18, verticalAlign: 'middle', marginRight: 4 }}>hourglass_empty</span>
              Analyzing...
            </>
          ) : (
            <>
              <span className="material-icons" style={{ fontSize: 18, verticalAlign: 'middle', marginRight: 4 }}>rocket_launch</span>
              Run Agent
            </>
          )}
        </button>
      </form>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    background: '#0d1117',
    padding: '20px'
  },
  form: {
    background: '#161b22',
    padding: '40px',
    borderRadius: '12px',
    width: '100%',
    maxWidth: '600px',
    border: '1px solid #30363d'
  },
  title: {
    color: '#58a6ff',
    marginBottom: '30px',
    textAlign: 'center'
  },
  field: {
    marginBottom: '20px',
    flex: 1
  },
  row: {
    display: 'flex',
    gap: '15px'
  },
  label: {
    display: 'block',
    color: '#c9d1d9',
    marginBottom: '8px',
    fontSize: '14px'
  },
  input: {
    width: '100%',
    padding: '10px',
    background: '#0d1117',
    border: '1px solid #30363d',
    borderRadius: '6px',
    color: '#c9d1d9',
    fontSize: '14px',
    boxSizing: 'border-box'
  },
  tokenWrapper: {
    position: 'relative'
  },
  eyeButton: {
    position: 'absolute',
    right: '10px',
    top: '50%',
    transform: 'translateY(-50%)',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '18px'
  },
  preview: {
    background: '#0d1117',
    padding: '12px',
    borderRadius: '6px',
    marginBottom: '20px',
    border: '1px solid #30363d'
  },
  previewHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px'
  },
  previewLabel: {
    color: '#8b949e',
    fontSize: '12px'
  },
  editButton: {
    background: 'none',
    border: 'none',
    color: '#58a6ff',
    fontSize: '12px',
    cursor: 'pointer',
    padding: '2px 6px'
  },
  previewCode: {
    color: '#58a6ff',
    fontFamily: 'monospace',
    fontSize: '14px'
  },
  branchEditWrapper: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center'
  },
  branchInput: {
    flex: 1,
    padding: '6px',
    background: '#161b22',
    border: '1px solid #30363d',
    borderRadius: '4px',
    color: '#c9d1d9',
    fontFamily: 'monospace',
    fontSize: '13px'
  },
  cancelButton: {
    background: '#da3633',
    border: 'none',
    color: 'white',
    padding: '6px 10px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  button: {
    width: '100%',
    padding: '12px',
    background: '#238636',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer'
  },
  buttonDisabled: {
    background: '#21262d',
    color: '#484f58',
    cursor: 'not-allowed'
  }
};

export default InputForm;
