import { useState, useEffect } from "react";
import { getClientId, authGithub } from "../utils/api";
import "../styles/landing.css";

export default function LandingPage({ onLogin }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [clientId, setClientId] = useState(null);

  // Fetch client ID on mount
  useEffect(() => {
    getClientId()
      .then((data) => setClientId(data.client_id))
      .catch(() => setError("Backend not reachable"));
  }, []);

  // Handle OAuth callback code in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");

    if (code) {
      setLoading(true);
      setError("");

      // Clean the URL
      window.history.replaceState({}, "", window.location.pathname);

      authGithub(code)
        .then((data) => {
          // Save token and user info
          localStorage.setItem("github_token", data.github_token);
          if (onLogin) {
            onLogin({
              user_id: data.user_id,
              username: data.username,
              avatar_url: data.avatar_url,
            });
          }
        })
        .catch((err) => {
          setError(err.message || "Login failed");
          setLoading(false);
        });
    }
  }, [onLogin]);

  const handleGitHubLogin = () => {
    if (!clientId) {
      setError("OAuth not configured. Check backend .env");
      return;
    }

    const scope = "repo";
    const authUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&scope=${scope}`;

    window.location.href = authUrl;
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
          <h1>
            Autonomous CI/CD
            <br />
            <span className="gradient-text">Healing Agent</span>
          </h1>
          <p className="subtitle">
            Takes GitHub repo URL, clones & analyzes structure, discovers test
            files, identifies failures, generates targeted fixes, commits with
            [AI-AGENT] prefix, and monitors CI/CD until all tests pass.
          </p>
        </div>

        {/* Login Card */}
        <div className="token-card">
          <h2>Get Started</h2>
          <p className="token-description">
            Login with your GitHub account to get started. We'll use your
            account to clone repositories and push fixes.
          </p>

          {error && <div className="error-message">{error}</div>}

          <button
            className="github-login-btn"
            onClick={handleGitHubLogin}
            disabled={loading || !clientId}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Authenticating...
              </>
            ) : (
              <>
                <svg
                  className="github-icon"
                  viewBox="0 0 24 24"
                  width="24"
                  height="24"
                  fill="currentColor"
                >
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                </svg>
                Login with GitHub
              </>
            )}
          </button>

          <div className="divider-line">
            <span>Secure OAuth Authentication</span>
          </div>

          <p className="scope-info">
            We request <code>repo</code> scope to clone and push to your
            repositories. Your token is stored securely and never shared.
          </p>
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
