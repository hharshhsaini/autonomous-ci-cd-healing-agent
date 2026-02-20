import React, { useState, useEffect } from "react";
import { checkHealth } from "../utils/api";

export default function Navbar({ user, onLogout }) {
  const [backendStatus, setBackendStatus] = useState("checking");

  useEffect(() => {
    const ping = async () => {
      try {
        const data = await checkHealth();
        setBackendStatus(data.status === "ok" ? "online" : "offline");
      } catch {
        setBackendStatus("offline");
      }
    };

    ping();
    const interval = setInterval(ping, 10000);
    return () => clearInterval(interval);
  }, []);

  const isOnline = backendStatus === "online";

  return (
    <nav style={styles.nav}>
      <div style={styles.left}>
        <div style={styles.logo}>
          <span className="material-icons" style={styles.bolt}>
            bolt
          </span>
          <span style={styles.title}>RIFT</span>
        </div>
        <span style={styles.divider}></span>
        <span style={styles.tagline}>Healing Agent</span>
      </div>
      <div style={styles.right}>
        <div
          style={{
            ...styles.statusDot,
            background: isOnline ? "var(--green)" : "#f85149",
            boxShadow: isOnline
              ? "0 0 8px rgba(0,255,136,0.5)"
              : "0 0 8px rgba(248,81,73,0.5)",
          }}
        ></div>
        <span style={styles.statusText}>
          {backendStatus === "checking"
            ? "Connecting..."
            : isOnline
              ? "Agent Online"
              : "Agent Offline"}
        </span>

        {/* User info and logout */}
        {user && (
          <div style={styles.userSection}>
            <span style={styles.userDivider}></span>
            {user.avatar_url && (
              <img
                src={user.avatar_url}
                alt={user.username}
                style={styles.avatar}
              />
            )}
            <span style={styles.username}>{user.username}</span>
            <button onClick={onLogout} style={styles.logoutBtn} title="Logout">
              <span className="material-icons" style={{ fontSize: "16px" }}>
                logout
              </span>
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}

const styles = {
  nav: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 32px",
    borderBottom: "1px solid var(--border)",
    background:
      "linear-gradient(180deg, rgba(13,17,23,1) 0%, rgba(22,27,34,0.8) 100%)",
  },
  left: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  bolt: {
    fontSize: "18px",
  },
  title: {
    fontSize: "16px",
    fontWeight: 700,
    color: "var(--green)",
    letterSpacing: "1px",
  },
  divider: {
    width: "1px",
    height: "16px",
    background: "var(--border)",
  },
  tagline: {
    fontSize: "12px",
    color: "var(--text-dim)",
    fontWeight: 400,
  },
  right: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  statusDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    animation: "pulse 2s ease-in-out infinite",
  },
  statusText: {
    fontSize: "12px",
    color: "var(--text-dim)",
  },
  userSection: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginLeft: "4px",
  },
  userDivider: {
    width: "1px",
    height: "16px",
    background: "var(--border)",
    marginRight: "4px",
  },
  avatar: {
    width: "24px",
    height: "24px",
    borderRadius: "50%",
    border: "1px solid var(--border)",
  },
  username: {
    fontSize: "13px",
    color: "var(--text)",
    fontWeight: 500,
  },
  logoutBtn: {
    background: "none",
    border: "1px solid var(--border)",
    color: "var(--text-dim)",
    borderRadius: "6px",
    padding: "4px 6px",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    transition: "all 0.2s",
  },
};
