/**
 * RIFT API Service Layer
 * Centralizes all backend API calls with auth support.
 */

const getApiUrl = () => import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Get auth headers from localStorage token.
 */
function getAuthHeaders() {
  const token = localStorage.getItem("github_token");
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

// ─── Auth ────────────────────────────────────────────────────────

/**
 * Get GitHub OAuth client ID from backend.
 */
export async function getClientId() {
  const res = await fetch(`${getApiUrl()}/api/auth/client-id`);
  if (!res.ok) throw new Error("OAuth not configured");
  return res.json();
}

/**
 * Exchange GitHub OAuth code for token.
 * @param {string} code - The OAuth code from GitHub redirect
 */
export async function authGithub(code) {
  const res = await fetch(`${getApiUrl()}/api/auth/github`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Authentication failed");
  }
  return res.json();
}

/**
 * Verify an existing GitHub token.
 * @param {string} github_token
 */
export async function verifyToken(github_token) {
  const res = await fetch(`${getApiUrl()}/api/auth/verify-token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ github_token }),
  });
  if (!res.ok) throw new Error("Invalid token");
  return res.json();
}

// ─── Core API ────────────────────────────────────────────────────

/**
 * Health check — GET /api/health
 */
export async function checkHealth() {
  const res = await fetch(`${getApiUrl()}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

/**
 * Start a new healing run — POST /api/run-agent
 * Sends user's GitHub token in Authorization header.
 */
export async function startRun(payload) {
  const res = await fetch(`${getApiUrl()}/api/run-agent`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Start run failed: ${res.status}`);
  }
  return res.json();
}

/**
 * Get job status — GET /api/status/{jobId}
 */
export async function getRunStatus(jobId) {
  const res = await fetch(`${getApiUrl()}/api/status/${jobId}`);
  if (!res.ok) throw new Error(`Status fetch failed: ${res.status}`);
  return res.json();
}

/**
 * Get final results — GET /api/results/{jobId}
 */
export async function getRunResults(jobId) {
  const res = await fetch(`${getApiUrl()}/api/results/${jobId}`);
  if (!res.ok) throw new Error(`Results fetch failed: ${res.status}`);
  return res.json();
}

/**
 * Get all completed runs — GET /api/runs
 */
export async function getRuns() {
  const res = await fetch(`${getApiUrl()}/api/runs`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Runs fetch failed: ${res.status}`);
  return res.json();
}

/**
 * Get dashboard stats — GET /api/stats
 */
export async function getStats() {
  const res = await fetch(`${getApiUrl()}/api/stats`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Stats fetch failed: ${res.status}`);
  return res.json();
}

/**
 * Get the SSE stream URL for a job
 */
export function getStreamUrl(jobId) {
  return `${getApiUrl()}/api/stream/${jobId}`;
}
