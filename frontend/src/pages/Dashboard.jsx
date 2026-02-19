import React, { useState, useEffect } from 'react';
import { getStats, getRuns } from '../utils/api';
import { formatPercent } from '../utils/formatters';
import StatCard from '../components/StatCard';
import WeeklyActivityChart from '../components/WeeklyActivityChart';
import BugDistributionChart from '../components/BugDistributionChart';
import SuccessRateTrend from '../components/SuccessRateTrend';
import RecentRunsList from '../components/RecentRunsList';
import Modal from '../components/Modal';

const EMPTY_STATS = {
  successRate: 0,
  totalFixes: 0,
  avgFixTime: 0,
  byDay: {},
  byBugType: {},
  thisMonth: 0,
  lastMonth: 0,
  totalRuns: 0
};

export default function Dashboard({ setScreen, setCurrentRunId }) {
  const [stats, setStats] = useState(null);
  const [runs, setRuns] = useState([]);
  const [modalContent, setModalContent] = useState(null);
  const [apiConnected, setApiConnected] = useState(false);

  const fetchData = async () => {
    try {
      const [statsData, runsData] = await Promise.all([getStats(), getRuns()]);
      setStats(statsData || EMPTY_STATS);
      setRuns(Array.isArray(runsData) ? runsData : []);
      setApiConnected(true);
    } catch (err) {
      console.warn('API unreachable:', err.message);
      setStats(EMPTY_STATS);
      setRuns([]);
      setApiConnected(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) return <div style={styles.loading}><span className="material-icons" style={styles.spinner}>bolt</span> Loading...</div>;

  // Format avg fix time for display
  const avgFixMinutes = (stats.avgFixTime / 60).toFixed(1);
  const avgFixDisplay = stats.avgFixTime === 0 ? '—' : avgFixMinutes >= 1 ? `${avgFixMinutes}m` : `${Math.round(stats.avgFixTime)}s`;

  // Compute dynamic subtexts
  const successDiff = stats.thisMonth - stats.lastMonth;
  const successSubtext = stats.totalRuns === 0
    ? 'No runs yet'
    : successDiff >= 0
      ? `↑ ${Math.round(Math.abs(successDiff))}% from last month`
      : `↓ ${Math.round(Math.abs(successDiff))}% from last month`;

  const hasData = stats.totalRuns > 0;

  return (
    <div style={styles.container}>
      {/* Backend Status Banner */}
      {!apiConnected && (
        <div style={styles.errorBanner}>
          🔴 Backend not connected — start the backend server to use RIFT.
        </div>
      )}

      {/* Page Header */}
      <div style={styles.pageHeader}>
        <div>
          <div style={styles.brandRow}>
            <span className="material-icons" style={styles.bolt}>bolt</span>
            <span style={styles.brandName}>RIFT</span>
          </div>
          <h1 style={styles.heading}>dashboard</h1>
        </div>
        <div style={styles.headerActions}>
          <button style={styles.newRunBtn} onClick={() => setScreen('run')}>
            + new run
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div style={styles.statsRow}>
        <StatCard
          icon="analytics"
          label="Success Rate"
          value={hasData ? formatPercent(stats.successRate) : '—'}
          subtext={successSubtext}
          subtextColor={hasData && successDiff >= 0 ? 'var(--green)' : hasData ? 'var(--red)' : 'var(--text-dim)'}
        />
        <StatCard
          icon="build"
          label="Total Fixes Applied"
          value={hasData ? stats.totalFixes : '—'}
          subtext={hasData ? `${stats.totalRuns} runs completed` : 'No runs yet'}
          subtextColor={hasData ? 'var(--green)' : 'var(--text-dim)'}
        />
        <StatCard
          icon="schedule"
          label="Avg Fix Time"
          value={avgFixDisplay}
          subtext={hasData ? '' : 'No runs yet'}
          subtextColor="var(--text-dim)"
        />
      </div>

      {/* Charts Row — only show if there's data */}
      {hasData ? (
        <div style={styles.chartsRow}>
          <div
            style={styles.chartCard}
            onClick={() => setModalContent('weekly')}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--green)'}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <WeeklyActivityChart data={stats.byDay} />
          </div>
          <div
            style={styles.chartCard}
            onClick={() => setModalContent('bugs')}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--green)'}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <BugDistributionChart data={stats.byBugType} />
          </div>
          <div
            style={styles.chartCard}
            onClick={() => setModalContent('success')}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--green)'}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <SuccessRateTrend
              thisMonth={stats.thisMonth}
              lastMonth={stats.lastMonth}
            />
          </div>
        </div>
      ) : (
        <div style={styles.emptyCharts}>
          <span className="material-icons" style={styles.emptyIcon}>trending_up</span>
          <p style={styles.emptyTitle}>No data yet</p>
          <p style={styles.emptySubtext}>Run your first healing scan to see analytics here.</p>
          <button style={styles.emptyBtn} onClick={() => setScreen('run')}><span className="material-icons" style={{ fontSize: 18, verticalAlign: 'middle' }}>bolt</span> Start First Run</button>
        </div>
      )}

      {/* Recent Runs */}
      <RecentRunsList
        runs={runs.slice(0, 10)}
        onRunClick={(runId) => {
          setCurrentRunId(runId);
          setScreen('results');
        }}
      />

      {/* Modals */}
      {hasData && (
        <>
          <Modal
            isOpen={modalContent === 'weekly'}
            onClose={() => setModalContent(null)}
            title="Weekly Activity Details"
            subtitle="Detailed breakdown of runs and fixes"
          >
            <WeeklyActivityChart data={stats.byDay} detailed />
          </Modal>

          <Modal
            isOpen={modalContent === 'bugs'}
            onClose={() => setModalContent(null)}
            title="Bug Type Distribution"
            subtitle="Complete breakdown of bug types fixed"
          >
            <BugDistributionChart data={stats.byBugType} detailed />
          </Modal>

          <Modal
            isOpen={modalContent === 'success'}
            onClose={() => setModalContent(null)}
            title="Success Rate Trend"
            subtitle="Monthly comparison of success rates"
          >
            <SuccessRateTrend
              thisMonth={stats.thisMonth}
              lastMonth={stats.lastMonth}
              detailed
            />
          </Modal>
        </>
      )}
    </div>
  );
}

const styles = {
  container: {
    padding: '24px 32px',
    maxWidth: '1400px',
    margin: '0 auto'
  },
  loading: {
    padding: '80px',
    textAlign: 'center',
    color: 'var(--text-dim)',
    fontSize: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px'
  },
  spinner: {
    fontSize: '24px',
    animation: 'pulse 1.5s ease-in-out infinite'
  },
  errorBanner: {
    background: 'rgba(248,81,73,0.1)',
    border: '1px solid rgba(248,81,73,0.3)',
    borderRadius: '6px',
    padding: '10px 16px',
    marginBottom: '16px',
    fontSize: '12px',
    color: '#f85149',
    textAlign: 'center'
  },
  pageHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    marginBottom: '28px'
  },
  brandRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    marginBottom: '2px'
  },
  bolt: {
    fontSize: '18px'
  },
  brandName: {
    fontSize: '14px',
    fontWeight: 700,
    color: 'var(--green)',
    letterSpacing: '1px'
  },
  heading: {
    fontSize: '32px',
    fontWeight: 300,
    color: 'var(--text)',
    lineHeight: 1.2
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px'
  },
  newRunBtn: {
    padding: '8px 18px',
    background: 'var(--green)',
    color: 'var(--bg)',
    borderRadius: '6px',
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
    border: 'none',
    transition: 'opacity 0.2s'
  },
  statsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '16px',
    marginBottom: '20px'
  },
  chartsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '16px',
    marginBottom: '28px'
  },
  chartCard: {
    background: 'var(--card)',
    border: '1px solid var(--border)',
    borderRadius: '8px',
    padding: '20px',
    cursor: 'pointer',
    transition: 'border-color 0.25s ease'
  },
  emptyCharts: {
    background: 'var(--card)',
    border: '1px solid var(--border)',
    borderRadius: '8px',
    padding: '60px 40px',
    textAlign: 'center',
    marginBottom: '28px'
  },
  emptyIcon: {
    fontSize: '40px',
    marginBottom: '12px'
  },
  emptyTitle: {
    fontSize: '18px',
    fontWeight: 500,
    color: 'var(--text)',
    marginBottom: '6px'
  },
  emptySubtext: {
    fontSize: '13px',
    color: 'var(--text-dim)',
    marginBottom: '20px'
  },
  emptyBtn: {
    padding: '10px 24px',
    background: 'var(--green)',
    color: 'var(--bg)',
    borderRadius: '6px',
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
    border: 'none'
  }
};
