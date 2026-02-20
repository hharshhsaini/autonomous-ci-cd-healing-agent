import React, { useState, useEffect } from "react";
import "./styles/global.css";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import RunPage from "./pages/RunPage";
import ResultsPage from "./pages/ResultsPage";
import LandingPage from "./pages/LandingPage";

export default function App() {
  const [screen, setScreen] = useState("dashboard");
  const [currentRunId, setCurrentRunId] = useState(null);
  const [user, setUser] = useState(null);

  // Load user from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem("user");
      }
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
    setScreen("dashboard");
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("user");
    localStorage.removeItem("github_token");
    setScreen("dashboard");
  };

  // Not logged in → show landing page
  if (!user) {
    return <LandingPage onLogin={handleLogin} />;
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <Navbar user={user} onLogout={handleLogout} />

      {screen === "dashboard" && (
        <Dashboard setScreen={setScreen} setCurrentRunId={setCurrentRunId} />
      )}

      {screen === "run" && (
        <RunPage setScreen={setScreen} setCurrentRunId={setCurrentRunId} />
      )}

      {screen === "results" && (
        <ResultsPage runId={currentRunId} setScreen={setScreen} />
      )}
    </div>
  );
}
