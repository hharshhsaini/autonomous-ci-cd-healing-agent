/**
 * RIFT API Service Layer
 * Centralizes all backend API calls.
 */

const getApiUrl = () =>
    import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Health check — GET /api/health
 * @returns {{ status: string, active_jobs: number }}
 */
export async function checkHealth() {
    const res = await fetch(`${getApiUrl()}/api/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
    return res.json();
}

/**
 * Start a new healing run — POST /api/run-agent
 * @param {{ github_url: string, team_name: string, leader_name: string, branch_name?: string }} payload
 * @returns {{ job_id: string, branch_name: string }}
 */
export async function startRun(payload) {
    const res = await fetch(`${getApiUrl()}/api/run-agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Start run failed: ${res.status}`);
    }
    return res.json();
}

/**
 * Get job status — GET /api/status/{jobId}
 * @param {string} jobId
 */
export async function getRunStatus(jobId) {
    const res = await fetch(`${getApiUrl()}/api/status/${jobId}`);
    if (!res.ok) throw new Error(`Status fetch failed: ${res.status}`);
    return res.json();
}

/**
 * Get final results — GET /api/results/{jobId}
 * @param {string} jobId
 */
export async function getRunResults(jobId) {
    const res = await fetch(`${getApiUrl()}/api/results/${jobId}`);
    if (!res.ok) throw new Error(`Results fetch failed: ${res.status}`);
    return res.json();
}

/**
 * Get all completed runs — GET /api/runs
 * @returns {Array} list of completed run objects
 */
export async function getRuns() {
    const res = await fetch(`${getApiUrl()}/api/runs`);
    if (!res.ok) throw new Error(`Runs fetch failed: ${res.status}`);
    return res.json();
}

/**
 * Get dashboard stats — GET /api/stats
 * @returns {{ successRate, totalFixes, avgFixTime, byDay, byBugType, thisMonth, lastMonth, totalRuns }}
 */
export async function getStats() {
    const res = await fetch(`${getApiUrl()}/api/stats`);
    if (!res.ok) throw new Error(`Stats fetch failed: ${res.status}`);
    return res.json();
}

/**
 * Get the SSE stream URL for a job
 * @param {string} jobId
 * @returns {string} full URL for EventSource
 */
export function getStreamUrl(jobId) {
    return `${getApiUrl()}/api/stream/${jobId}`;
}
