const STORAGE_KEY = "rift_runs";
const MAX_RUNS = 50;

export function useRunHistory() {
  const saveRun = (runData) => {
    try {
      const runs = getRuns();
      runs.unshift(runData);
      const trimmed = runs.slice(0, MAX_RUNS);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
    } catch (err) {
      console.error("Failed to save run:", err);
    }
  };

  const getRuns = () => {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (err) {
      console.error("Failed to get runs:", err);
      return [];
    }
  };

  const getRunById = (id) => {
    const runs = getRuns();
    return runs.find(r => r.id === id);
  };

  const clearRuns = () => {
    localStorage.removeItem(STORAGE_KEY);
  };

  const computeStats = (runs) => {
    if (!runs || runs.length === 0) {
      return {
        successRate: 0,
        totalFixes: 0,
        avgFixTime: 0,
        byDay: {},
        byBugType: {},
        thisMonth: 0,
        lastMonth: 0
      };
    }

    // Success rate
    const passed = runs.filter(r => r.ci_status === "PASSED").length;
    const successRate = (passed / runs.length) * 100;

    // Total fixes
    const totalFixes = runs.reduce((sum, r) => sum + (r.errors_fixed || 0), 0);

    // Avg fix time
    const totalTime = runs.reduce((sum, r) => sum + (r.score?.elapsed_seconds || 0), 0);
    const avgFixTime = totalTime / runs.length;

    // By day (last 7 days)
    const byDay = {};
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const now = new Date();
    
    for (let i = 6; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const dayName = days[d.getDay()];
      byDay[dayName] = { runs: 0, fixes: 0 };
    }

    runs.forEach(r => {
      const date = new Date(r.timestamp);
      const dayName = days[date.getDay()];
      if (byDay[dayName]) {
        byDay[dayName].runs++;
        byDay[dayName].fixes += r.errors_fixed || 0;
      }
    });

    // By bug type
    const byBugType = {};
    runs.forEach(r => {
      if (r.fixes && Array.isArray(r.fixes)) {
        r.fixes.forEach(fix => {
          const type = fix.type || "UNKNOWN";
          byBugType[type] = (byBugType[type] || 0) + 1;
        });
      }
    });

    // This month vs last month
    const thisMonth = new Date().getMonth();
    const thisYear = new Date().getFullYear();
    
    const thisMonthRuns = runs.filter(r => {
      const d = new Date(r.timestamp);
      return d.getMonth() === thisMonth && d.getFullYear() === thisYear;
    });
    
    const lastMonthRuns = runs.filter(r => {
      const d = new Date(r.timestamp);
      const lastMonth = thisMonth === 0 ? 11 : thisMonth - 1;
      const lastYear = thisMonth === 0 ? thisYear - 1 : thisYear;
      return d.getMonth() === lastMonth && d.getFullYear() === lastYear;
    });

    const thisMonthRate = thisMonthRuns.length > 0
      ? (thisMonthRuns.filter(r => r.ci_status === "PASSED").length / thisMonthRuns.length) * 100
      : 0;
    
    const lastMonthRate = lastMonthRuns.length > 0
      ? (lastMonthRuns.filter(r => r.ci_status === "PASSED").length / lastMonthRuns.length) * 100
      : 0;

    return {
      successRate,
      totalFixes,
      avgFixTime,
      byDay,
      byBugType,
      thisMonth: thisMonthRate,
      lastMonth: lastMonthRate
    };
  };

  return {
    saveRun,
    getRuns,
    getRunById,
    clearRuns,
    computeStats
  };
}
