import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function SuccessRateTrend({ thisMonth, lastMonth, detailed }) {
    const chartData = [
        { month: 'Jan', rate: Math.round(lastMonth || 0) },
        { month: 'Feb', rate: Math.round(thisMonth || 0) }
    ];

    const maxRate = Math.max(...chartData.map(d => d.rate), 100);

    if (!detailed) {
        return (
            <div>
                <div style={styles.header}>
                    <h3 style={styles.title}>Success Rate Trend</h3>
                </div>
                <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={chartData} barSize={60}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                        <XAxis
                            dataKey="month"
                            stroke="var(--text-dim)"
                            style={{ fontSize: '11px' }}
                            axisLine={false}
                            tickLine={false}
                        />
                        <YAxis
                            stroke="var(--text-dim)"
                            style={{ fontSize: '11px' }}
                            domain={[0, maxRate]}
                            axisLine={false}
                            tickLine={false}
                        />
                        <Tooltip
                            contentStyle={{
                                background: 'var(--card2)',
                                border: '1px solid var(--border)',
                                borderRadius: '4px',
                                fontSize: '11px'
                            }}
                            formatter={(value) => [`${value}%`, 'Success Rate']}
                        />
                        <Bar dataKey="rate" radius={[4, 4, 0, 0]}>
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.rate >= 70 ? '#00ff88' : '#ffa657'} fillOpacity={0.85} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        );
    }

    // Detailed modal view
    const improvement = thisMonth - lastMonth;
    const avgRate = ((thisMonth + lastMonth) / 2).toFixed(1);

    return (
        <div>
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData} barSize={80}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis
                        dataKey="month"
                        stroke="var(--text-dim)"
                        style={{ fontSize: '12px' }}
                        axisLine={false}
                        tickLine={false}
                    />
                    <YAxis
                        stroke="var(--text-dim)"
                        style={{ fontSize: '12px' }}
                        domain={[0, 100]}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(v) => `${v}%`}
                    />
                    <Tooltip
                        contentStyle={{
                            background: 'var(--card2)',
                            border: '1px solid var(--border)',
                            borderRadius: '6px'
                        }}
                        formatter={(value) => [`${value}%`, 'Success Rate']}
                    />
                    <Bar dataKey="rate" radius={[6, 6, 0, 0]}>
                        {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.rate >= 70 ? '#00ff88' : '#ffa657'} fillOpacity={0.9} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>

            <div style={styles.summaryRow}>
                <div style={styles.summaryCard}>
                    <div style={styles.summaryLabel}>This Month</div>
                    <div style={{ ...styles.summaryValue, color: 'var(--green)' }}>{Math.round(thisMonth)}%</div>
                </div>
                <div style={styles.summaryCard}>
                    <div style={styles.summaryLabel}>Last Month</div>
                    <div style={{ ...styles.summaryValue, color: 'var(--orange)' }}>{Math.round(lastMonth)}%</div>
                </div>
                <div style={styles.summaryCard}>
                    <div style={styles.summaryLabel}>Improvement</div>
                    <div style={{ ...styles.summaryValue, color: improvement >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {improvement >= 0 ? '+' : ''}{improvement.toFixed(0)}%
                    </div>
                </div>
                <div style={styles.summaryCard}>
                    <div style={styles.summaryLabel}>Average</div>
                    <div style={{ ...styles.summaryValue, color: 'var(--blue)' }}>{avgRate}%</div>
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
    summaryRow: {
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '12px',
        marginTop: '20px'
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
    }
};
