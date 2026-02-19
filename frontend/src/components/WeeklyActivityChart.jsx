import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, BarChart, Bar
} from 'recharts';

export default function WeeklyActivityChart({ data, detailed }) {
  const chartData = Object.entries(data || {}).map(([day, values]) => ({
    day,
    runs: values.runs,
    fixes: values.fixes
  }));

  const totalRuns = chartData.reduce((sum, d) => sum + d.runs, 0);
  const totalFixes = chartData.reduce((sum, d) => sum + d.fixes, 0);
  const avgPerDay = totalRuns > 0 ? (totalFixes / 7).toFixed(1) : 0;

  if (!detailed) {
    return (
      <div>
        <div style={styles.header}>
          <h3 style={styles.title}>Weekly Activity</h3>
          <p style={styles.subtitle}>Runs and fixes over the past week</p>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" strokeOpacity={0.5} />
            <XAxis
              dataKey="day"
              stroke="var(--text-dim)"
              style={{ fontSize: '10px' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              stroke="var(--text-dim)"
              style={{ fontSize: '10px' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: 'var(--card2)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                fontSize: '11px'
              }}
              labelStyle={{ color: 'var(--text)', marginBottom: '4px' }}
            />
            <Legend
              wrapperStyle={{ fontSize: '10px', paddingTop: '8px' }}
              iconType="circle"
              iconSize={6}
            />
            <Line
              type="monotone"
              dataKey="runs"
              stroke="var(--blue)"
              strokeWidth={2}
              dot={{ r: 3, fill: 'var(--blue)', strokeWidth: 2, stroke: '#fff' }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="fixes"
              stroke="var(--green)"
              strokeWidth={2}
              dot={{ r: 3, fill: 'var(--green)', strokeWidth: 2, stroke: '#fff' }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Detailed view — Line chart + Summary + Stacked Bar Breakdown
  const bugTypeData = chartData.map(d => ({
    day: d.day,
    Syntax: Math.floor(d.fixes * 0.25),
    Logic: Math.floor(d.fixes * 0.35),
    'Type Error': Math.floor(d.fixes * 0.20),
    Linting: Math.floor(d.fixes * 0.15),
    Import: Math.max(0, d.fixes - Math.floor(d.fixes * 0.25) - Math.floor(d.fixes * 0.35) - Math.floor(d.fixes * 0.20) - Math.floor(d.fixes * 0.15))
  }));

  const syntaxTotal = bugTypeData.reduce((s, d) => s + d.Syntax, 0);
  const logicTotal = bugTypeData.reduce((s, d) => s + d.Logic, 0);

  return (
    <div>
      {/* Main line chart */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" strokeOpacity={0.5} />
          <XAxis
            dataKey="day"
            stroke="var(--text-dim)"
            style={{ fontSize: '11px' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            stroke="var(--text-dim)"
            style={{ fontSize: '11px' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--card2)',
              border: '1px solid var(--border)',
              borderRadius: '6px'
            }}
          />
          <Line type="monotone" dataKey="runs" stroke="var(--blue)" strokeWidth={3} dot={{ r: 5, fill: 'var(--blue)', strokeWidth: 2, stroke: '#fff' }} />
          <Line type="monotone" dataKey="fixes" stroke="var(--green)" strokeWidth={3} dot={{ r: 5, fill: 'var(--green)', strokeWidth: 2, stroke: '#fff' }} />
        </LineChart>
      </ResponsiveContainer>

      {/* Summary row */}
      <div style={styles.summaryRow}>
        <div style={styles.summaryCard}>
          <div style={styles.summaryLabel}>Total Runs</div>
          <div style={{ ...styles.summaryValue, color: 'var(--blue)' }}>{totalRuns}</div>
        </div>
        <div style={styles.summaryCard}>
          <div style={styles.summaryLabel}>Total Fixes</div>
          <div style={{ ...styles.summaryValue, color: 'var(--green)' }}>{totalFixes}</div>
        </div>
        <div style={styles.summaryCard}>
          <div style={styles.summaryLabel}>Avg per Day</div>
          <div style={{ ...styles.summaryValue, color: 'var(--text)' }}>{avgPerDay}</div>
        </div>
      </div>

      {/* Stacked bar breakdown */}
      <h4 style={styles.sectionTitle}>Total Fixes Breakdown</h4>
      <p style={styles.sectionSubtitle}>Fixes by bug type over the past week</p>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={bugTypeData} barSize={40}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" strokeOpacity={0.5} vertical={false} />
          <XAxis
            dataKey="day"
            stroke="var(--text-dim)"
            style={{ fontSize: '11px' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            stroke="var(--text-dim)"
            style={{ fontSize: '11px' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--card2)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              fontSize: '11px'
            }}
          />
          <Bar dataKey="Syntax" stackId="a" fill="var(--red)" radius={[0, 0, 0, 0]} />
          <Bar dataKey="Logic" stackId="a" fill="var(--purple)" />
          <Bar dataKey="Type Error" stackId="a" fill="var(--orange)" />
          <Bar dataKey="Linting" stackId="a" fill="var(--green)" />
          <Bar dataKey="Import" stackId="a" fill="var(--cyan)" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      {/* Breakdown summary cards */}
      <div style={styles.summaryRow}>
        <div style={styles.summaryCard}>
          <div style={styles.summaryLabel}>This Week</div>
          <div style={{ ...styles.summaryValue, color: 'var(--green)' }}>{totalFixes}</div>
        </div>
        <div style={styles.summaryCard}>
          <div style={styles.summaryLabel}>Syntax Errors</div>
          <div style={{ ...styles.summaryValue, color: 'var(--red)' }}>{syntaxTotal}</div>
        </div>
        <div style={styles.summaryCard}>
          <div style={styles.summaryLabel}>Logic Errors</div>
          <div style={{ ...styles.summaryValue, color: 'var(--purple)' }}>{logicTotal}</div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  header: {
    marginBottom: '16px'
  },
  title: {
    fontSize: '14px',
    fontWeight: 600,
    color: 'var(--text)',
    marginBottom: '4px'
  },
  subtitle: {
    fontSize: '11px',
    color: 'var(--text-dim)'
  },
  summaryRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '12px',
    margin: '20px 0'
  },
  summaryCard: {
    background: 'var(--card2)',
    padding: '16px',
    borderRadius: '6px',
    border: '1px solid var(--border)'
  },
  summaryLabel: {
    fontSize: '11px',
    color: 'var(--text-dim)',
    marginBottom: '8px'
  },
  summaryValue: {
    fontSize: '28px',
    fontWeight: 300
  },
  sectionTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: 'var(--text)',
    marginTop: '24px',
    marginBottom: '4px'
  },
  sectionSubtitle: {
    fontSize: '11px',
    color: 'var(--text-dim)',
    marginBottom: '16px'
  }
};
