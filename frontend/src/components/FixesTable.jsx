import React from 'react';
import DiffViewer from './DiffViewer';

function FixesTable({ fixes, filter, onFilterChange }) {
  const [visibleItems, setVisibleItems] = React.useState(50);

  // Reset pagination when filter changes
  React.useEffect(() => {
    setVisibleItems(50);
  }, [filter]);

  if (!fixes) return null;

  const types = ['ALL', 'LINTING', 'SYNTAX', 'LOGIC', 'TYPE_ERROR', 'IMPORT', 'INDENTATION'];
  const filtered = filter === 'ALL' ? fixes : fixes.filter(f => f.type === filter);
  const visibleFixes = filtered.slice(0, visibleItems);

  const typeColors = {
    LINTING: '#58a6ff',
    SYNTAX: '#f85149',
    LOGIC: '#56d4dd',
    TYPE_ERROR: '#bc8cff',
    IMPORT: '#3fb950',
    INDENTATION: '#d29922'
  };

  const truncatePath = (path) => {
    if (path.length > 40) return '...' + path.substring(path.length - 37);
    return path;
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>Fixes Applied</h3>
        <span style={styles.count}>Showing {visibleFixes.length} of {filtered.length} fixes</span>
      </div>

      <div style={styles.filters}>
        {types.map(type => (
          <button
            key={type}
            onClick={() => onFilterChange(type)}
            style={{
              ...styles.filterButton,
              ...(filter === type && styles.filterButtonActive)
            }}
          >
            {type}
          </button>
        ))}
      </div>

      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr style={styles.headerRow}>
              <th style={styles.th}>File</th>
              <th style={styles.th}>Bug Type</th>
              <th style={styles.th}>Line</th>
              <th style={styles.th}>Commit Message</th>
              <th style={styles.th}>Status</th>
            </tr>
          </thead>
          <tbody>
            {visibleFixes.map((fix, idx) => (
              <React.Fragment key={fix.id}>
                <tr style={{
                  ...styles.row,
                  background: idx % 2 === 0 ? '#0d1117' : '#161b22',
                  borderBottom: fix.diff && fix.status === "fixed" ? 'none' : '1px solid #21262d'
                }}>
                  <td style={styles.td}>
                    <code style={styles.file}>{truncatePath(fix.file)}</code>
                  </td>
                  <td style={styles.td}>
                    <span style={{
                      ...styles.badge,
                      background: typeColors[fix.type] || '#6e7681'
                    }}>
                      {fix.type}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <code style={styles.line}>{fix.line}</code>
                  </td>
                  <td style={styles.td}>
                    <code style={styles.commit}>{fix.commit_message}</code>
                  </td>
                  <td style={styles.td}>
                    {fix.status === 'fixed' ? (
                      <span style={{ ...styles.status, color: '#3fb950' }}>
                        <span className="material-icons" style={{ fontSize: 14, verticalAlign: 'middle', marginRight: 4 }}>check_circle</span>
                        Fixed
                      </span>
                    ) : (
                      <span style={{ ...styles.status, color: '#f85149' }}>
                        <span className="material-icons" style={{ fontSize: 14, verticalAlign: 'middle', marginRight: 4 }}>cancel</span>
                        Failed
                      </span>
                    )}
                  </td>
                </tr>
                {fix.diff && fix.status === "fixed" && (
                  <tr key={`${fix.id}-diff`} style={{ background: idx % 2 === 0 ? '#0d1117' : '#161b22' }}>
                    <td colSpan="5" style={{ padding: '0 12px 16px 12px', borderBottom: '1px solid #21262d' }}>
                      <DiffViewer diff={fix.diff} />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
      {filtered.length > visibleItems && (
        <button
          style={{ ...styles.filterButton, marginTop: '16px', width: '100%', padding: '10px' }}
          onClick={() => setVisibleItems(prev => prev + 50)}
        >
          Load More ({filtered.length - visibleItems} remaining)
        </button>
      )}
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
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px'
  },
  title: {
    color: '#c9d1d9',
    fontSize: '18px',
    margin: 0
  },
  count: {
    color: '#8b949e',
    fontSize: '14px'
  },
  filters: {
    display: 'flex',
    gap: '8px',
    marginBottom: '16px',
    flexWrap: 'wrap'
  },
  filterButton: {
    padding: '6px 12px',
    background: '#21262d',
    border: '1px solid #30363d',
    borderRadius: '6px',
    color: '#8b949e',
    fontSize: '12px',
    cursor: 'pointer'
  },
  filterButtonActive: {
    background: '#58a6ff',
    color: 'white',
    borderColor: '#58a6ff'
  },
  tableWrapper: {
    overflowX: 'auto',
    maxHeight: '500px',
    overflowY: 'auto'
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse'
  },
  headerRow: {
    borderBottom: '1px solid #30363d'
  },
  th: {
    padding: '12px',
    textAlign: 'left',
    color: '#8b949e',
    fontSize: '12px',
    fontWeight: '600',
    textTransform: 'uppercase'
  },
  row: {
    borderBottom: '1px solid #21262d'
  },
  td: {
    padding: '12px',
    fontSize: '13px'
  },
  file: {
    color: '#8b949e',
    fontFamily: 'monospace',
    fontSize: '12px'
  },
  badge: {
    padding: '4px 8px',
    borderRadius: '4px',
    color: 'white',
    fontSize: '11px',
    fontWeight: 'bold'
  },
  line: {
    color: '#c9d1d9',
    fontFamily: 'monospace'
  },
  commit: {
    color: '#6e7681',
    fontFamily: 'monospace',
    fontSize: '11px'
  },
  status: {
    fontWeight: 'bold',
    fontSize: '13px'
  }
};

export default FixesTable;
