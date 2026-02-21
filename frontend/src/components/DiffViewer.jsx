import React from 'react';

const DiffViewer = ({ diff }) => {
    if (!diff) return null;

    const lines = diff.split('\n');

    // Remove the file headers (first two lines) since we already know the file
    const hunkLines = lines.filter(line =>
        !line.startsWith('--- a/') && !line.startsWith('+++ b/')
    );

    return (
        <div style={styles.container}>
            <div style={styles.codeBlock}>
                {hunkLines.map((line, idx) => {
                    const type = line.startsWith('+') ? 'add' :
                        line.startsWith('-') ? 'remove' :
                            line.startsWith('@@') ? 'hunk' : 'context';

                    return (
                        <div key={idx} style={{ ...styles.line, ...styles[type] }}>
                            <span style={styles.content}>{line}</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

const styles = {
    container: {
        marginTop: '12px',
        background: '#0d1117',
        border: '1px solid var(--border)',
        borderRadius: '6px',
        overflow: 'hidden',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: '11px',
        lineHeight: '1.5',
    },
    codeBlock: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        overflowX: 'auto',
    },
    line: {
        display: 'flex',
        padding: '0 12px',
        whiteSpace: 'pre',
        borderBottom: '1px solid transparent',
    },
    add: {
        backgroundColor: 'rgba(0, 255, 136, 0.1)',
        color: '#00ff88',
    },
    remove: {
        backgroundColor: 'rgba(248, 81, 73, 0.1)',
        color: '#f85149',
    },
    hunk: {
        backgroundColor: 'rgba(88, 166, 255, 0.1)',
        color: '#58a6ff',
        padding: '4px 12px',
        borderBottom: '1px solid var(--border)',
        borderTop: '1px solid var(--border)',
    },
    context: {
        color: 'var(--text-dim)',
    },
    content: {
        paddingLeft: '4px',
    }
};

export default DiffViewer;
