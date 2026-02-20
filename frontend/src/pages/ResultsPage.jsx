import React, { useState, useEffect } from "react";
import { getRunResults } from "../utils/api";
import { useAgentStream } from "../hooks/useAgentStream";
import { formatTime } from "../utils/formatters";

// Pipeline steps in order
const PIPELINE_STEPS = [
  { key: "cloning", label: "Clone", icon: "download", agent: "Clone Agent" },
  { key: "testing", label: "Test", icon: "science", agent: "Test Agent" },
  {
    key: "analyzing",
    label: "Analyze",
    icon: "search",
    agent: "Analyze Agent",
  },
  { key: "fixing", label: "Fix", icon: "build", agent: "Fix Agent" },
  {
    key: "verifying",
    label: "Verify",
    icon: "verified",
    agent: "Verify Agent",
  },
  { key: "pushing", label: "Push", icon: "upload", agent: "Git Push Agent" },
];

function getStepState(stepKey, currentStatus) {
  const statusOrder = [
    "cloning",
    "testing",
    "analyzing",
    "fixing",
    "verifying",
    "pushing",
    "done",
    "failed",
  ];
  const currentIdx = statusOrder.indexOf(currentStatus);
  const stepIdx = statusOrder.indexOf(stepKey);

  if (currentStatus === "done" || currentStatus === "failed") return "done";
  if (stepIdx < currentIdx) return "done";
  if (stepIdx === currentIdx) return "active";
  return "pending";
}

export default function ResultsPage({ runId, setScreen }) {
  const [run, setRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [elapsed, setElapsed] = useState(0);

  const { data: streamData, isComplete } = useAgentStream(runId);

  useEffect(() => {
    if (!runId) {
      setLoading(false);
      return;
    }
    const fetchResults = async () => {
      try {
        const result = await getRunResults(runId);
        if (result.error) {
          setLoading(false);
          return;
        }
        setRun(result);
        setLoading(false);
      } catch (err) {
        console.warn("Results fetch failed, relying on stream:", err.message);
        setLoading(false);
      }
    };
    fetchResults();
  }, [runId]);

  useEffect(() => {
    if (streamData) {
      setRun(streamData);
      setLoading(false);
    }
  }, [streamData]);

  // Live elapsed timer
  useEffect(() => {
    if (!run || ["done", "failed"].includes(run.status)) return;
    const start = run.start_time ? run.start_time * 1000 : Date.now();
    const tick = () => setElapsed(Math.floor((Date.now() - start) / 1000));
    tick();
    const iv = setInterval(tick, 1000);
    return () => clearInterval(iv);
  }, [run?.status, run?.start_time]);

  if (loading) {
    return (
      <div style={s.container}>
        <div style={s.loadingCard}>
          <div className="rift-spinner" />
          <p style={s.loadingText}>Connecting to agent...</p>
        </div>
      </div>
    );
  }

  if (!run || run.error) {
    return (
      <div style={s.container}>
        <div style={s.emptyCard}>
          <span
            className="material-icons"
            style={{ fontSize: 48, marginBottom: 16, color: "var(--text-dim)" }}
          >
            description
          </span>
          <h2 style={s.title}>Run Not Found</h2>
          <p style={s.subtitle}>
            {error || "The requested run could not be found."}
          </p>
          <button style={s.backBtn} onClick={() => setScreen("dashboard")}>
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const isRunning = !["done", "failed"].includes(run.status);
  const passed = run.ci_status === "PASSED";
  const repoName = run.repo || run.repo_url || "Unknown Repository";
  const displayElapsed = isRunning ? elapsed : run.score?.elapsed_seconds || 0;

  return (
    <div style={s.container}>
      {/* CSS animations */}
      <style>{`
                @keyframes rift-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
                @keyframes rift-spin { to { transform: rotate(360deg); } }
                @keyframes rift-glow { 0%,100% { box-shadow: 0 0 4px rgba(0,255,136,0.3); } 50% { box-shadow: 0 0 16px rgba(0,255,136,0.6); } }
                @keyframes rift-slide { from { width: 0%; } }
                @keyframes rift-dot { 0%,80%,100% { transform: scale(0); } 40% { transform: scale(1); } }
                .rift-spinner { width: 32px; height: 32px; border: 3px solid var(--border); border-top-color: var(--green); border-radius: 50%; animation: rift-spin 0.8s linear infinite; }
                .rift-active-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); animation: rift-glow 1.5s ease-in-out infinite; }
                .rift-step-line-active { background: linear-gradient(90deg, var(--green), transparent) !important; animation: rift-pulse 1.5s ease-in-out infinite; }
                .rift-typing-dot { width: 4px; height: 4px; border-radius: 50%; background: var(--green); display: inline-block; animation: rift-dot 1.4s ease-in-out infinite; }
                .rift-typing-dot:nth-child(2) { animation-delay: 0.2s; }
                .rift-typing-dot:nth-child(3) { animation-delay: 0.4s; }
            `}</style>

      <button style={s.backLink} onClick={() => setScreen("dashboard")}>
        ← Back to Dashboard
      </button>

      {/* Header */}
      <div style={s.header}>
        <div>
          <h2 style={s.title}>{repoName}</h2>
          <div style={s.metaRow}>
            {run.team_name && <span style={s.teamBadge}>{run.team_name}</span>}
            {run.branch_name && (
              <span style={s.branchBadge}>
                <span
                  className="material-icons"
                  style={{
                    fontSize: 14,
                    verticalAlign: "middle",
                    marginRight: 4,
                  }}
                >
                  account_tree
                </span>
                {run.branch_name}
              </span>
            )}
            {run.repo_language && run.repo_language !== "unknown" && (
              <span style={s.langBadge}>{run.repo_language}</span>
            )}
          </div>
        </div>
        <div
          style={{
            ...s.statusBadge,
            background: isRunning
              ? "rgba(88,166,255,0.15)"
              : passed
                ? "rgba(0,255,136,0.15)"
                : "rgba(248,81,73,0.15)",
            color: isRunning
              ? "#58a6ff"
              : passed
                ? "var(--green)"
                : "var(--red)",
          }}
        >
          {isRunning ? (
            <>
              <span
                className="material-icons"
                style={{
                  fontSize: 16,
                  verticalAlign: "middle",
                  marginRight: 4,
                }}
              >
                hourglass_empty
              </span>
              {run.current_agent || run.status}
            </>
          ) : passed ? (
            <>
              <span
                className="material-icons"
                style={{
                  fontSize: 16,
                  verticalAlign: "middle",
                  marginRight: 4,
                }}
              >
                check_circle
              </span>
              PASSED
            </>
          ) : (
            <>
              <span
                className="material-icons"
                style={{
                  fontSize: 16,
                  verticalAlign: "middle",
                  marginRight: 4,
                }}
              >
                cancel
              </span>
              FAILED
            </>
          )}
        </div>
      </div>

      {/* ═══════ LIVE PIPELINE STATUS ═══════ */}
      <div style={s.pipelineContainer}>
        <div style={s.pipelineHeader}>
          <span style={s.pipelineTitle}>
            {isRunning ? (
              <>
                <span
                  className="rift-active-dot"
                  style={{
                    display: "inline-block",
                    marginRight: 8,
                    verticalAlign: "middle",
                  }}
                />
                Pipeline Running
              </>
            ) : (
              <>
                <span
                  className="material-icons"
                  style={{
                    fontSize: 16,
                    verticalAlign: "middle",
                    marginRight: 4,
                  }}
                >
                  {passed ? "check_circle" : "cancel"}
                </span>
                Pipeline {passed ? "Complete" : "Failed"}
              </>
            )}
          </span>
          <span style={s.pipelineTimer}>
            {isRunning && (
              <span
                className="rift-spinner"
                style={{
                  width: 14,
                  height: 14,
                  borderWidth: 2,
                  display: "inline-block",
                  verticalAlign: "middle",
                  marginRight: 6,
                }}
              />
            )}
            {formatTime(displayElapsed)}
          </span>
        </div>

        <div style={s.stepsRow}>
          {PIPELINE_STEPS.map((step, i) => {
            const state = getStepState(step.key, run.status);
            const isActive = state === "active";
            const isDone = state === "done";
            const isLast = i === PIPELINE_STEPS.length - 1;

            return (
              <React.Fragment key={step.key}>
                <div
                  style={{
                    ...s.stepNode,
                    ...(isActive ? s.stepActive : {}),
                    ...(isDone ? s.stepDone : {}),
                  }}
                >
                  <div
                    style={{
                      ...s.stepCircle,
                      background: isDone
                        ? "var(--green)"
                        : isActive
                          ? "rgba(0,255,136,0.15)"
                          : "var(--card2)",
                      border: isActive
                        ? "2px solid var(--green)"
                        : isDone
                          ? "2px solid var(--green)"
                          : "2px solid var(--border)",
                      ...(isActive
                        ? { animation: "rift-glow 1.5s ease-in-out infinite" }
                        : {}),
                    }}
                  >
                    {isDone ? (
                      <span
                        className="material-icons"
                        style={{
                          color: "#0d1117",
                          fontSize: 16,
                          fontWeight: 700,
                        }}
                      >
                        check
                      </span>
                    ) : isActive ? (
                      <span
                        className="material-icons"
                        style={{ fontSize: 18, color: "var(--green)" }}
                      >
                        {step.icon}
                      </span>
                    ) : (
                      <span
                        className="material-icons"
                        style={{
                          fontSize: 18,
                          opacity: 0.4,
                          color: "var(--text-dim)",
                        }}
                      >
                        {step.icon}
                      </span>
                    )}
                  </div>
                  <span
                    style={{
                      ...s.stepLabel,
                      color: isDone
                        ? "var(--green)"
                        : isActive
                          ? "var(--text)"
                          : "var(--text-dim)",
                      fontWeight: isActive ? 600 : 400,
                    }}
                  >
                    {step.label}
                  </span>
                  {isActive && (
                    <div style={s.activeIndicator}>
                      <span className="rift-typing-dot" />
                      <span className="rift-typing-dot" />
                      <span className="rift-typing-dot" />
                    </div>
                  )}
                </div>
                {!isLast && (
                  <div
                    style={{
                      ...s.stepLine,
                      background: isDone ? "var(--green)" : "var(--border)",
                    }}
                    className={isActive ? "rift-step-line-active" : ""}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Live status message */}
        {isRunning && run.current_agent && (
          <div style={s.liveStatus}>
            <span
              className="rift-active-dot"
              style={{ display: "inline-block", marginRight: 8 }}
            />
            <span style={{ color: "#58a6ff", fontWeight: 600 }}>
              {run.current_agent}
            </span>
            <span style={{ color: "var(--text-dim)", margin: "0 8px" }}>—</span>
            <span style={{ color: "var(--text-dim)" }}>
              {run.status === "cloning" && "Cloning repository..."}
              {run.status === "testing" && "Running linters and test suites..."}
              {run.status === "analyzing" &&
                "Parsing errors from test output..."}
              {run.status === "fixing" &&
                `Fixing ${run.errors_found || 0} errors with GPT-4o...`}
              {run.status === "verifying" &&
                `Re-running tests (attempt ${(run.retry_count || 0) + 1}/5)...`}
              {run.status === "pushing" &&
                "Committing and pushing to branch..."}
            </span>
            {run.retry_count > 0 && (
              <span style={s.retryBadge}>retry #{run.retry_count}</span>
            )}
          </div>
        )}
      </div>

      {/* Progress bar */}
      {isRunning && (
        <div style={s.progressContainer}>
          <div style={s.progressTrack}>
            <div style={{ ...s.progressBar, width: `${run.progress || 0}%` }} />
          </div>
          <span style={s.progressLabel}>{run.progress || 0}%</span>
        </div>
      )}

      {/* Stats */}
      <div style={s.statsRow}>
        <div style={s.statCard}>
          <div style={s.statLabel}>Score</div>
          <div
            style={{
              ...s.statValue,
              color: passed
                ? "var(--green)"
                : isRunning
                  ? "#58a6ff"
                  : "var(--red)",
            }}
          >
            {run.score?.total || 0}
          </div>
        </div>
        <div style={s.statCard}>
          <div style={s.statLabel}>Errors Found</div>
          <div style={s.statValue}>{run.errors_found || 0}</div>
        </div>
        <div style={s.statCard}>
          <div style={s.statLabel}>Errors Fixed</div>
          <div style={{ ...s.statValue, color: "var(--green)" }}>
            {run.errors_fixed || 0}
          </div>
        </div>
        <div style={s.statCard}>
          <div style={s.statLabel}>{isRunning ? "Elapsed" : "Duration"}</div>
          <div style={s.statValue}>{formatTime(displayElapsed)}</div>
        </div>
      </div>

      {/* Score Breakdown Panel */}
      {!isRunning && run.score && (
        <div style={s.scorePanel}>
          <h3 style={s.sectionTitle}>Score Breakdown</h3>
          <div style={s.scoreRow}>
            <span style={s.scoreLabel}>Base Score</span>
            <div style={s.scoreBarTrack}>
              <div
                style={{
                  ...s.scoreBarFill,
                  width: "100%",
                  background: "var(--green)",
                }}
              />
            </div>
            <span style={s.scorePoints}>100</span>
          </div>
          <div style={s.scoreRow}>
            <span style={s.scoreLabel}>Speed Bonus</span>
            <div style={s.scoreBarTrack}>
              <div
                style={{
                  ...s.scoreBarFill,
                  width: (run.score?.speed_bonus || 0) > 0 ? "100%" : "0%",
                  background: "#58a6ff",
                }}
              />
            </div>
            <span style={{ ...s.scorePoints, color: "#58a6ff" }}>
              +{run.score?.speed_bonus || 0}
            </span>
          </div>
          <div style={s.scoreRow}>
            <span style={s.scoreLabel}>Commit Penalty</span>
            <div style={s.scoreBarTrack}>
              <div
                style={{
                  ...s.scoreBarFill,
                  width:
                    (run.score?.commit_penalty || 0) > 0
                      ? `${Math.min(((run.score?.commit_penalty || 0) / 20) * 100, 100)}%`
                      : "0%",
                  background: "var(--red)",
                }}
              />
            </div>
            <span style={{ ...s.scorePoints, color: "var(--red)" }}>
              -{run.score?.commit_penalty || 0}
            </span>
          </div>
          <div style={s.scoreDivider} />
          <div style={s.scoreRow}>
            <span
              style={{ ...s.scoreLabel, fontWeight: 700, color: "var(--text)" }}
            >
              Final Score
            </span>
            <div style={s.scoreBarTrack}>
              <div
                style={{
                  ...s.scoreBarFill,
                  width: `${Math.min(((run.score?.total || 0) / 110) * 100, 100)}%`,
                  background: "linear-gradient(90deg, var(--green), #58a6ff)",
                }}
              />
            </div>
            <span
              style={{
                ...s.scorePoints,
                fontWeight: 700,
                color: passed ? "var(--green)" : "var(--red)",
                fontSize: "16px",
              }}
            >
              {run.score?.total || 0}
            </span>
          </div>
        </div>
      )}

      {/* Timeline */}
      {run.timeline && run.timeline.length > 0 && (
        <div style={s.section}>
          <h3 style={s.sectionTitle}>Pipeline Timeline</h3>
          <div style={s.timelineList}>
            {run.timeline.map((item, i) => (
              <div key={i} style={s.timelineRow}>
                <span style={s.timelineTime}>
                  {item.timestamp || new Date().toLocaleTimeString()}
                </span>
                <span
                  style={{
                    ...s.timelineDot,
                    background: item.passed ? "var(--green)" : "var(--red)",
                  }}
                />
                <span style={s.timelineAgent}>{item.agent}</span>
                <span style={s.timelineMsg}>{item.msg}</span>
                {item.iteration > 0 && (
                  <span style={s.retryBadge}>retry #{item.iteration}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Test Cases */}
      {run.fixes && run.fixes.length > 0 && (
        <div style={s.section}>
          <h3 style={s.sectionTitle}>
            Test Cases ({run.fixes.filter((f) => f.status === "fixed").length}/
            {run.fixes.length} fixed)
          </h3>
          <div style={s.testCaseList}>
            {run.fixes.map((fix, i) => (
              <div
                key={i}
                style={{
                  ...s.testCaseRow,
                  borderLeftColor:
                    fix.status === "fixed"
                      ? "var(--green)"
                      : fix.status === "failed"
                        ? "var(--red)"
                        : "#58a6ff",
                }}
              >
                <div style={s.testCaseHeader}>
                  <span
                    style={{
                      ...s.typeBadge,
                      background:
                        {
                          SYNTAX: "rgba(248,81,73,0.15)",
                          LOGIC: "rgba(188,140,255,0.15)",
                          TYPE_ERROR: "rgba(255,166,87,0.15)",
                          LINTING: "rgba(0,255,136,0.15)",
                          IMPORT: "rgba(88,166,255,0.15)",
                          INDENTATION: "rgba(139,148,158,0.15)",
                        }[fix.type] || "rgba(139,148,158,0.15)",
                      color:
                        {
                          SYNTAX: "#f85149",
                          LOGIC: "#bc8cff",
                          TYPE_ERROR: "#ffa657",
                          LINTING: "#00ff88",
                          IMPORT: "#58a6ff",
                          INDENTATION: "#8b949e",
                        }[fix.type] || "#8b949e",
                    }}
                  >
                    {fix.type}
                  </span>
                  <span
                    style={{
                      ...s.statusIcon,
                      color:
                        fix.status === "fixed"
                          ? "var(--green)"
                          : fix.status === "failed"
                            ? "var(--red)"
                            : "#58a6ff",
                    }}
                  >
                    {fix.status === "fixed" ? (
                      <>
                        <span
                          className="material-icons"
                          style={{
                            fontSize: 14,
                            verticalAlign: "middle",
                            marginRight: 4,
                          }}
                        >
                          check_circle
                        </span>
                        FIXED
                      </>
                    ) : fix.status === "failed" ? (
                      <>
                        <span
                          className="material-icons"
                          style={{
                            fontSize: 14,
                            verticalAlign: "middle",
                            marginRight: 4,
                          }}
                        >
                          cancel
                        </span>
                        FAILED
                      </>
                    ) : (
                      <span
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "6px",
                        }}
                      >
                        <span
                          className="rift-spinner"
                          style={{ width: 12, height: 12, borderWidth: 2 }}
                        />
                        FIXING
                      </span>
                    )}
                  </span>
                </div>
                <div style={s.formattedOutput}>
                  {fix.formatted ||
                    `${fix.type} error in ${fix.file} line ${fix.line} → Fix: ${fix.fix_description || fix.message}`}
                </div>
                {fix.commit_message && (
                  <div style={s.commitMsg}>
                    <span
                      className="material-icons"
                      style={{
                        fontSize: 13,
                        verticalAlign: "middle",
                        marginRight: 4,
                        opacity: 0.6,
                      }}
                    >
                      commit
                    </span>
                    {fix.commit_message}
                  </div>
                )}
                <div style={s.fileInfo}>
                  <span style={s.fileLabel}>
                    <span
                      className="material-icons"
                      style={{
                        fontSize: 14,
                        verticalAlign: "middle",
                        marginRight: 4,
                      }}
                    >
                      description
                    </span>
                    {fix.file}
                  </span>
                  {fix.line > 0 && (
                    <span style={s.lineLabel}>Line {fix.line}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {run.error_message && (
        <div style={s.section}>
          <h3 style={s.sectionTitle}>Error</h3>
          <pre style={s.errorPre}>{run.error_message}</pre>
        </div>
      )}

      {/* Raw output */}
      {run.raw_test_output && (
        <details style={s.rawSection}>
          <summary style={s.rawSummary}>
            <span
              className="material-icons"
              style={{ fontSize: 16, verticalAlign: "middle", marginRight: 6 }}
            >
              terminal
            </span>
            Raw Test Output
          </summary>
          <pre style={s.rawPre}>{run.raw_test_output}</pre>
        </details>
      )}
    </div>
  );
}

const s = {
  container: { padding: "24px", maxWidth: "950px", margin: "0 auto" },
  loadingCard: {
    textAlign: "center",
    padding: "80px 40px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "16px",
  },
  loadingText: { color: "var(--text-dim)", fontSize: "14px" },
  emptyCard: {
    background: "var(--card)",
    border: "1px solid var(--border)",
    borderRadius: "8px",
    padding: "40px",
    textAlign: "center",
    marginTop: "40px",
  },
  backLink: {
    background: "none",
    border: "none",
    color: "var(--text-dim)",
    fontSize: "13px",
    cursor: "pointer",
    marginBottom: "20px",
    padding: "4px 0",
    display: "inline-block",
  },
  backBtn: {
    padding: "10px 20px",
    background: "var(--card2)",
    color: "var(--text-dim)",
    borderRadius: "6px",
    fontSize: "13px",
    border: "1px solid var(--border)",
    cursor: "pointer",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "20px",
  },
  title: {
    fontSize: "22px",
    fontWeight: 600,
    color: "var(--text)",
    marginBottom: "6px",
  },
  subtitle: {
    fontSize: "13px",
    color: "var(--text-dim)",
    marginBottom: "24px",
  },
  metaRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flexWrap: "wrap",
  },
  teamBadge: {
    fontSize: "11px",
    color: "var(--text-dim)",
    background: "var(--card2)",
    padding: "3px 8px",
    borderRadius: "4px",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  branchBadge: {
    fontSize: "11px",
    color: "#58a6ff",
    background: "rgba(88,166,255,0.1)",
    padding: "3px 8px",
    borderRadius: "4px",
    fontFamily: "JetBrains Mono, monospace",
  },
  langBadge: {
    fontSize: "11px",
    color: "#bc8cff",
    background: "rgba(188,140,255,0.1)",
    padding: "3px 8px",
    borderRadius: "4px",
    textTransform: "capitalize",
  },
  statusBadge: {
    padding: "6px 14px",
    borderRadius: "20px",
    fontSize: "12px",
    fontWeight: 600,
    letterSpacing: "0.5px",
    whiteSpace: "nowrap",
    flexShrink: 0,
  },

  // Pipeline
  pipelineContainer: {
    background: "var(--card)",
    border: "1px solid var(--border)",
    borderRadius: "10px",
    padding: "20px 24px",
    marginBottom: "20px",
  },
  pipelineHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
  },
  pipelineTitle: {
    fontSize: "14px",
    fontWeight: 600,
    color: "var(--text)",
    display: "flex",
    alignItems: "center",
  },
  pipelineTimer: {
    fontSize: "13px",
    color: "var(--text-dim)",
    fontFamily: "JetBrains Mono, monospace",
    display: "flex",
    alignItems: "center",
  },
  stepsRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "0",
    marginBottom: "16px",
  },
  stepNode: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "6px",
    minWidth: "60px",
    position: "relative",
  },
  stepCircle: {
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "all 0.3s ease",
  },
  stepLabel: {
    fontSize: "11px",
    letterSpacing: "0.3px",
    transition: "all 0.3s ease",
  },
  stepLine: {
    height: "2px",
    flex: 1,
    minWidth: "30px",
    borderRadius: "1px",
    transition: "all 0.3s ease",
    alignSelf: "center",
    marginTop: "-16px",
  },
  stepActive: {},
  stepDone: {},
  activeIndicator: { display: "flex", gap: "3px", marginTop: "2px" },
  liveStatus: {
    display: "flex",
    alignItems: "center",
    fontSize: "12px",
    padding: "8px 12px",
    background: "rgba(0,255,136,0.05)",
    borderRadius: "6px",
    border: "1px solid rgba(0,255,136,0.1)",
  },

  progressContainer: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "20px",
  },
  progressTrack: {
    flex: 1,
    height: "4px",
    background: "var(--card2)",
    borderRadius: "2px",
    overflow: "hidden",
  },
  progressBar: {
    height: "100%",
    background: "linear-gradient(90deg, var(--green), #58a6ff)",
    borderRadius: "2px",
    transition: "width 0.5s ease",
  },
  progressLabel: {
    fontSize: "12px",
    color: "var(--text-dim)",
    minWidth: "36px",
    textAlign: "right",
  },

  statsRow: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "12px",
    marginBottom: "24px",
  },
  statCard: {
    background: "var(--card)",
    border: "1px solid var(--border)",
    borderRadius: "6px",
    padding: "16px",
  },
  statLabel: {
    fontSize: "11px",
    color: "var(--text-dim)",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    marginBottom: "8px",
  },
  statValue: { fontSize: "28px", fontWeight: 300, color: "var(--text)" },

  section: { marginBottom: "24px" },
  sectionTitle: {
    fontSize: "15px",
    fontWeight: 600,
    color: "var(--text)",
    marginBottom: "12px",
  },

  timelineList: { display: "flex", flexDirection: "column", gap: "4px" },
  timelineRow: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "8px 14px",
    background: "var(--card)",
    border: "1px solid var(--border)",
    borderRadius: "4px",
    fontSize: "12px",
  },
  timelineTime: {
    fontSize: "10px",
    color: "var(--text-dim)",
    fontFamily: "JetBrains Mono, monospace",
    minWidth: "70px",
    opacity: 0.7,
  },
  timelineDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    flexShrink: 0,
  },
  timelineAgent: { color: "#58a6ff", fontWeight: 600, minWidth: "110px" },
  timelineMsg: { color: "var(--text-dim)", flex: 1 },
  retryBadge: {
    fontSize: "10px",
    color: "#ffa657",
    background: "rgba(255,166,87,0.1)",
    padding: "2px 6px",
    borderRadius: "3px",
    marginLeft: "8px",
  },

  // Score breakdown
  scorePanel: {
    background: "var(--card)",
    border: "1px solid var(--border)",
    borderRadius: "10px",
    padding: "20px 24px",
    marginBottom: "24px",
  },
  scoreRow: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "10px",
  },
  scoreLabel: { fontSize: "13px", color: "var(--text-dim)", minWidth: "120px" },
  scoreBarTrack: {
    flex: 1,
    height: "8px",
    background: "var(--card2)",
    borderRadius: "4px",
    overflow: "hidden",
  },
  scoreBarFill: {
    height: "100%",
    borderRadius: "4px",
    transition: "width 1s ease",
  },
  scorePoints: {
    fontSize: "13px",
    color: "var(--text)",
    minWidth: "40px",
    textAlign: "right",
    fontFamily: "JetBrains Mono, monospace",
  },
  scoreDivider: {
    height: "1px",
    background: "var(--border)",
    margin: "12px 0",
  },

  testCaseList: { display: "flex", flexDirection: "column", gap: "6px" },
  testCaseRow: {
    background: "var(--card)",
    border: "1px solid var(--border)",
    borderLeft: "3px solid",
    borderRadius: "6px",
    padding: "14px 16px",
  },
  testCaseHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "8px",
  },
  typeBadge: {
    fontWeight: 600,
    padding: "3px 8px",
    borderRadius: "4px",
    textTransform: "uppercase",
    fontSize: "10px",
    letterSpacing: "0.5px",
  },
  statusIcon: { fontSize: "11px", fontWeight: 600, letterSpacing: "0.5px" },
  formattedOutput: {
    fontFamily: "JetBrains Mono, monospace",
    fontSize: "12px",
    color: "var(--text)",
    background: "rgba(0,0,0,0.3)",
    padding: "10px 14px",
    borderRadius: "4px",
    marginBottom: "8px",
    lineHeight: 1.6,
    wordBreak: "break-word",
  },
  commitMsg: {
    fontFamily: "JetBrains Mono, monospace",
    fontSize: "11px",
    color: "var(--text-dim)",
    padding: "6px 12px",
    background: "rgba(88,166,255,0.05)",
    border: "1px solid rgba(88,166,255,0.1)",
    borderRadius: "4px",
    marginBottom: "8px",
  },
  fileInfo: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    fontSize: "11px",
    color: "var(--text-dim)",
  },
  fileLabel: { fontFamily: "JetBrains Mono, monospace" },
  lineLabel: { color: "#58a6ff" },

  errorPre: {
    background: "rgba(248,81,73,0.08)",
    border: "1px solid rgba(248,81,73,0.2)",
    borderRadius: "6px",
    padding: "16px",
    color: "#f85149",
    fontSize: "12px",
    fontFamily: "JetBrains Mono, monospace",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
    overflow: "auto",
    maxHeight: "300px",
  },
  rawSection: { marginTop: "16px" },
  rawSummary: {
    fontSize: "13px",
    color: "var(--text-dim)",
    cursor: "pointer",
    padding: "8px 0",
    userSelect: "none",
  },
  rawPre: {
    background: "var(--card)",
    border: "1px solid var(--border)",
    borderRadius: "6px",
    padding: "16px",
    color: "var(--text-dim)",
    fontSize: "11px",
    fontFamily: "JetBrains Mono, monospace",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
    overflow: "auto",
    maxHeight: "400px",
    marginTop: "8px",
  },
};
