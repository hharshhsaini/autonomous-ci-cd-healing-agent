import { useState } from 'react';
import '../styles/landing.css';

export default function LandingPage({ onLogin }) {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showInstructions, setShowInstructions] = useState(false);

  const handleTokenSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/verify-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ github_token: token })
      });

      if (!response.ok) {
        throw new Error('Invalid GitHub token');
      }

      const data = await response.json();
      
      // Save token and user info
      localStorage.setItem('github_token', token);
      localStorage.setItem('user', JSON.stringify(data));
      
      // Call onLogin callback
      if (onLogin) onLogin();
    } catch (err) {
      setError(err.message || 'Failed to verify token');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="landing-container">
      <div className="landing-content">
        {/* Logo and Title */}
        <div className="landing-header">
          <div className="logo">
            <div className="logo-icon">
              <div className="dot dot-1"></div>
              <div className="dot dot-2"></div>
              <div className="dot dot-3"></div>
              <div className="dot dot-4"></div>
            </div>
            <span className="logo-text">RIFT Agent</span>
          </div>
          <h1>Autonomous CI/CD<br/><span className="gradient-text">Healing Agent</span></h1>
          <p className="subtitle">
            Takes GitHub repo URL, clones & analyzes structure, discovers test files,
            identifies failures, generates targeted fixes, commits with [AI-AGENT]
            prefix, and monitors CI/CD until all tests pass.
          </p>
        </div>

        {/* Token Input Form */}
        <div className="token-card">
          <h2>Get Started</h2>
          <p className="token-description">Enter your GitHub Personal Access Token to continue</p>
          
          <form onSubmit={handleTokenSubmit}>
            <div className="input-group">
              <label htmlFor="token">GitHub Personal Access Token</label>
              <input
                id="token"
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                required
                disabled={loading}
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button 
              type="submit" 
              className="submit-btn"
              disabled={loading || !token}
            >
              {loading ? 'Verifying...' : 'Continue'}
            </button>
          </form>

          {/* Instructions Toggle */}
          <button 
            className="instructions-toggle"
            onClick={() => setShowInstructions(!showInstructions)}
          >
            {showInstructions ? '▼' : '▶'} How to get GitHub token?
          </button>

          {showInstructions && (
            <div className="instructions-box">
              <h3>Creating a GitHub Personal Access Token</h3>
              <ol>
                <li>Go to <a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer">GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)</a></li>
                <li>Click <strong>"Generate new token (classic)"</strong></li>
                <li>Give it a descriptive name (e.g., "RIFT Agent")</li>
                <li>Select the following scopes:
                  <ul>
                    <li><code>repo</code> - Full control of private repositories</li>
                    <li><code>workflow</code> - Update GitHub Action workflows</li>
                  </ul>
                </li>
                <li>Click <strong>"Generate token"</strong></li>
                <li>Copy the token (starts with <code>ghp_</code>) and paste it above</li>
              </ol>
              <p className="warning">⚠️ Keep your token secure! Never share it publicly.</p>
            </div>
          )}
        </div>

        {/* Features */}
        <div className="features-grid">
          <div className="feature-card">
            <span className="feature-icon">🔍</span>
            <h3>Auto-detect failures</h3>
            <p>Automatically discovers and runs all test files</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon">🤖</span>
            <h3>AI-powered fixes</h3>
            <p>Uses GPT-4o to generate targeted fixes for failures</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon">🔄</span>
            <h3>CI/CD Integration</h3>
            <p>Monitors pipeline and iterates until all tests pass</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon">🌐</span>
            <h3>Multi-Language</h3>
            <p>Python, JavaScript, TypeScript, React, Go</p>
          </div>
        </div>
      </div>
    </div>
  );
}
