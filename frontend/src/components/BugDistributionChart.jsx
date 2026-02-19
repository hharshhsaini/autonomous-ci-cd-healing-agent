import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const BUG_COLORS = {
  SYNTAX: '#f85149',
  LOGIC: '#bc8cff',
  TYPE_ERROR: '#ffa657',
  LINTING: '#00ff88',
  IMPORT: '#39d3f5',
  INDENTATION: '#e3b341'
};

const BUG_LABELS = {
  SYNTAX: 'Syntax',
  LOGIC: 'Logic',
  TYPE_ERROR: 'Type Error',
  LINTING: 'Linting',
  IMPORT: 'Import',
  INDENTATION: 'Indentation'
};

export default function BugDistributionChart({ data, detailed }) {
  const chartData = Object.entries(data || {}).map(([type, count]) => ({
    name: type,
    label: BUG_LABELS[type] || type,
    value: count,
    color: BUG_COLORS[type] || 'var(--text-dim)'
  }));

  const total = chartData.reduce((sum, d) => sum + d.value, 0);

  if (!detailed) {
    return (
      <div>
        <div style={styles.header}>
          <h3 style={styles.title}>Bug Type Distribution</h3>
        </div>
        <ResponsiveContainer width="100%" height={170}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={70}
              paddingAngle={2}
              dataKey="value"
              stroke="none"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: 'var(--card2)',
                border: '1px solid var(--border)',
                fontSize: '11px',
                borderRadius: '6px'
              }}
              formatter={(value, name) => {
                const item = chartData.find(d => d.name === name);
                return [`${value} (${total > 0 ? ((value / total) * 100).toFixed(0) : 0}%)`, item?.label || name];
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div style={styles.legend}>
          {chartData.map(item => (
            <div key={item.name} style={styles.legendItem}>
              <span style={{ ...styles.legendDot, background: item.color }}></span>
              <span style={styles.legendText}>{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Detailed modal view
  return (
    <div>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={80}
            outerRadius={120}
            paddingAngle={3}
            dataKey="value"
            stroke="none"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: 'var(--card2)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              fontSize: '12px'
            }}
            formatter={(value, name) => {
              const item = chartData.find(d => d.name === name);
              return [`${value} bugs (${total > 0 ? ((value / total) * 100).toFixed(0) : 0}%)`, item?.label || name];
            }}
          />
        </PieChart>
      </ResponsiveContainer>

      <div style={styles.percentageGrid}>
        {chartData.map(item => {
          const percent = total > 0 ? ((item.value / total) * 100).toFixed(0) : 0;
          return (
            <div key={item.name} style={styles.percentCard}>
              <div style={styles.percentLabel}>{item.label}</div>
              <div style={{ ...styles.percentValue, color: item.color }}>{percent}%</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const styles = {
  header: {
    marginBottom: '8px'
  },
  title: {
    fontSize: '14px',
    fontWeight: 600,
    color: 'var(--text)'
  },
  legend: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '12px',
    marginTop: '8px',
    justifyContent: 'center'
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    fontSize: '10px'
  },
  legendDot: {
    width: '8px',
    height: '8px',
    borderRadius: '2px',
    flexShrink: 0
  },
  legendText: {
    color: 'var(--text-dim)'
  },
  percentageGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(5, 1fr)',
    gap: '10px',
    marginTop: '24px'
  },
  percentCard: {
    background: 'var(--card2)',
    padding: '16px 12px',
    borderRadius: '6px',
    border: '1px solid var(--border)'
  },
  percentLabel: {
    fontSize: '10px',
    color: 'var(--text-dim)',
    marginBottom: '8px'
  },
  percentValue: {
    fontSize: '28px',
    fontWeight: 300
  }
};
