import React from 'react';
import { formatDate } from '../utils/formatters';

export default function RecentRunsList({ runs, onRunClick }) {
    if (!runs || runs.length === 0) {
        return (
            <div style={styles.container}>
                <h3 style={styles.heading}>Recent Runs</h3>
                <div style={styles.empty}>
                    <p style={styles.emptyText}>No runs yet. Click "+ new run" to get started.</p>
                </div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            <h3 style={styles.heading}>Recent Runs</h3>
            <div style={styles.list}>
                {runs.map((run) => {
                    const passed = run.ci_status === 'PASSED';
                    const runId = run.job_id || run.id;
                    const teamName = run.team_name || run.team;
                    return (
                        <div
                            key={runId}
                            style={styles.row}
                            onClick={() => onRunClick && onRunClick(runId)}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.borderColor = 'var(--green)';
                                e.currentTarget.style.background = 'var(--card2)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.borderColor = 'var(--border)';
                                e.currentTarget.style.background = 'var(--card)';
                            }}
                        >
                            <div style={styles.rowLeft}>
                                <div style={styles.repoName}>{run.repo}</div>
                                <div style={styles.meta}>
                                    {teamName && <span style={styles.team}>{teamName}</span>}
                                    <span style={styles.dot}>•</span>
                                    <span style={styles.date}>{formatDate(run.timestamp)}</span>
                                </div>
                            </div>
                            <div style={styles.rowRight}>
                                <div style={styles.scoreSection}>
                                    <span style={styles.scoreLabel}>score</span>
                                    <span style={{ ...styles.scoreValue, color: passed ? 'var(--green)' : 'var(--red)' }}>
                                        {run.score?.total || 0}
                                    </span>
                                </div>
                                <div style={{
                                    ...styles.statusIcon,
                                    background: passed ? 'rgba(0,255,136,0.15)' : 'rgba(248,81,73,0.15)',
                                    color: passed ? 'var(--green)' : 'var(--red)'
                                }}>
                                    <span className="material-icons" style={{ fontSize: 14 }}>
                                        {passed ? 'check_circle' : 'cancel'}
                                    </span>
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
        marginTop: '8px'
    },
    heading: {
        fontSize: '16px',
        fontWeight: 600,
        color: 'var(--text)',
        marginBottom: '16px'
    },
    list: {
        display: 'flex',
        flexDirection: 'column',
        gap: '8px'
    },
    row: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px 20px',
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: '6px',
        cursor: 'pointer',
        transition: 'all 0.2s ease'
    },
    rowLeft: {
        display: 'flex',
        flexDirection: 'column',
        gap: '4px'
    },
    repoName: {
        fontSize: '14px',
        fontWeight: 500,
        color: 'var(--blue)'
    },
    meta: {
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        fontSize: '11px',
        color: 'var(--text-dim)'
    },
    team: {
        color: 'var(--text-muted)',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        fontSize: '10px'
    },
    dot: {
        color: 'var(--text-muted)'
    },
    date: {
        color: 'var(--text-dim)'
    },
    rowRight: {
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
    },
    scoreSection: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: '2px'
    },
    scoreLabel: {
        fontSize: '9px',
        color: 'var(--text-muted)',
        textTransform: 'uppercase',
        letterSpacing: '0.5px'
    },
    scoreValue: {
        fontSize: '20px',
        fontWeight: 500
    },
    statusIcon: {
        width: '32px',
        height: '32px',
        borderRadius: '6px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '16px',
        fontWeight: 700
    },
    empty: {
        padding: '40px',
        textAlign: 'center',
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: '6px'
    },
    emptyText: {
        color: 'var(--text-dim)',
        fontSize: '13px'
    }
};
