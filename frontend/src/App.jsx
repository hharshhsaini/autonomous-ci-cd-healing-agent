import React, { useState } from 'react';
import './styles/global.css';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import RunPage from './pages/RunPage';
import ResultsPage from './pages/ResultsPage';

export default function App() {
  const [screen, setScreen] = useState('dashboard');
  const [currentRunId, setCurrentRunId] = useState(null);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      <Navbar />

      {screen === 'dashboard' && (
        <Dashboard
          setScreen={setScreen}
          setCurrentRunId={setCurrentRunId}
        />
      )}

      {screen === 'run' && (
        <RunPage
          setScreen={setScreen}
          setCurrentRunId={setCurrentRunId}
        />
      )}

      {screen === 'results' && (
        <ResultsPage
          runId={currentRunId}
          setScreen={setScreen}
        />
      )}
    </div>
  );
}
